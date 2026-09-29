#!/usr/bin/env python3
"""
Build static JSON feeds for DroidBuild.

Pipeline for each article:
  1. Fetch raw HTML.
  2. trafilatura extracts the article as clean HTML (nav, ads,
     sidebars, comments removed; tables, links, emphasis kept).
  3. html2text converts that HTML to Markdown with tables intact.
  4. AI (Groq) polishes the Markdown: fixes spacing, ensures code
     fences, tidies tables. Does NOT rewrite wording.
  5. If AI fails or is unavailable, the Markdown from step 3 is
     used as-is.

If trafilatura produces nothing, readability-lxml is used as a
last resort. If that also fails, the item is DROPPED from the feed.
No item is ever published with only a "read the full article" link.

GROQ FREE TIER CONSTRAINTS (as of September 2026):
  - 8,000 tokens per minute per model, charged against the declared
    max_tokens up front. A request with max_tokens=8192 fails even
    if the prompt is 20 tokens.
  - openai/gpt-oss-120b does not support response_format. JSON must
    be requested in the prompt and parsed from the raw response.
  - 30 RPM, 1,000 RPD per chat model.

The script therefore:
  - Pre-cleans HTML to Markdown before sending it to the AI. The
    Markdown input is roughly 4-6k characters, well inside the
    token budget.
  - Caps max_tokens at 4,000 for polishing and 200 for curation.
  - Never uses response_format.
"""

import json
import os
import glob
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from readability import Document
from bs4 import BeautifulSoup
import html2text

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

# ============================================================
# AI CONFIGURATION
# ============================================================

try:
    from openai import OpenAI
    HAS_OPENAI_SDK = True
except ImportError:
    HAS_OPENAI_SDK = False

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

GROQ_MODELS = [
    'openai/gpt-oss-120b',
    'openai/gpt-oss-20b',
    'qwen/qwen3.8-27b',
    'groq/compound-mini',
]

GROQ_CLIENT = None
GROQ_ACTIVE_MODEL = None

if HAS_OPENAI_SDK and GROQ_API_KEY:
    try:
        GROQ_CLIENT = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
    except Exception as e:
        print(f"[AI Init Error] {e}")
        GROQ_CLIENT = None

SEGMENTS = ['news', 'tutorials', 'ai', 'research']
SOURCES_DIR = 'sources'
FEEDS_DIR = 'feeds'

AI_POLISH_MAX_TOKENS = 4000
AI_CURATE_MAX_TOKENS = 200
AI_INPUT_CHAR_LIMIT = 16000


# ============================================================
# POLISH PROMPT
#
# The AI receives Markdown, not HTML. Its job is to make the
# Markdown render cleanly, not to reconstruct lost structure.
# ============================================================

POLISH_PROMPT = """You are a Markdown formatting tool. You are not an editor, summarizer, or writer.

You will receive a Markdown document that was extracted from an article. Your job is to make it render cleanly in a Markdown viewer. You are NOT to change the wording.

ABSOLUTE RULES — VIOLATING ANY OF THESE IS A FAILURE:

1. DO NOT rephrase, paraphrase, summarize, shorten, expand, or rewrite any sentence. The author's wording is final.

2. DO NOT add any text of your own. No introductions, no conclusions, no TL;DRs, no editorial notes, no headings the source did not have.

3. DO NOT remove content. Paragraphs, captions, subheadings, and block quotes all stay.

4. DO NOT change capitalization, punctuation, or spacing inside sentences. Preserve em dashes (—), en dashes (–), curly quotes (" " ' '), ellipses (…), and every other typographic mark.

5. DO NOT translate. If the document is in a language other than English, keep it in that language.

WHAT YOU MAY FIX:

- Spacing around headings, paragraphs, lists, and code blocks. Ensure a blank line separates block elements.
- Headings: ensure top-level sections use `##` and subsections use `###`. Do not introduce `#`.
- Code: ensure fenced code blocks use triple backticks. If a language tag is present in the source, keep it. If not, use a bare fence.
- Tables: ensure pipe tables have a `---` separator row after the header. Ensure cells are separated by ` | `. Do not restructure tables beyond making them valid Markdown.
- Lists: ensure a blank line before the first item and after the last. Nested lists indent by two spaces.
- Links: ensure `[text](url)` formatting. If a URL is bare and Markdown-linkable, leave it as-is.
- Block quotes: prefix each line with `> `.
- Horizontal rules: use `---`.
- Inline code: single backticks. Remove any stray backticks that are clearly errors.

WHAT YOU MUST NOT DO:
- Reorder paragraphs.
- Rename headings.
- Merge or split paragraphs.
- Touch the content of code blocks.
- Invent links or images.

OUTPUT: The corrected Markdown, ready to render. No wrapper, no code fences around the whole document, no explanation, no commentary."""


# ============================================================
# AI HELPERS
# ============================================================

def _pick_model():
    global GROQ_ACTIVE_MODEL
    if GROQ_ACTIVE_MODEL is not None:
        return GROQ_ACTIVE_MODEL
    if GROQ_CLIENT is None:
        return None
    for name in GROQ_MODELS:
        try:
            GROQ_CLIENT.chat.completions.create(
                model=name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
            GROQ_ACTIVE_MODEL = name
            print(f"[AI] Using model: {name}")
            return name
        except Exception as e:
            print(f"[AI] Model {name} unavailable: {type(e).__name__}: {e}")
            continue
    return None


def ai_query(prompt, max_tokens=2048, temperature=0.2):
    """Send a prompt to Groq. Returns the text response, or None.

    Never passes response_format. openai/gpt-oss-120b returns 400
    json_validate_failed when it is set. JSON is requested in the
    prompt and parsed by the caller.
    """
    model_name = _pick_model()
    if model_name is None:
        return None
    try:
        response = GROQ_CLIENT.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if not response or not response.choices:
            return None
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [AI Error] {type(e).__name__}: {e}")
        return None


def ai_polish_markdown(markdown, url):
    """Ask the AI to make the extracted Markdown render cleanly.

    The input is already Markdown. The AI does not reconstruct
    structure; it corrects formatting.
    """
    if GROQ_CLIENT is None:
        return None

    snippet = markdown[:AI_INPUT_CHAR_LIMIT]

    prompt = (
        POLISH_PROMPT +
        "\n\n---\n\n"
        f"ARTICLE URL: {url}\n\n"
        "MARKDOWN:\n" + snippet + "\n\n"
        "Now output the corrected Markdown."
    )

    return ai_query(prompt, max_tokens=AI_POLISH_MAX_TOKENS, temperature=0.0)


def ai_select_items(items, segment, max_items=15):
    """Ask the AI to pick the best N items from a candidate list.

    No response_format. The prompt asks for a bare JSON array and
    the response is parsed with a tolerant regex extractor.
    """
    if GROQ_CLIENT is None or not items:
        return items[:max_items]

    candidates = []
    for i, item in enumerate(items):
        title = item.get('title', 'No Title')
        desc = (item.get('desc', '') or '')[:120]
        candidates.append({
            "index": i + 1,
            "title": title,
            "desc": desc,
        })

    prompt = (
        f'You are a curation assistant for a software developer news feed.\n'
        f'Segment: "{segment}".\n\n'
        f'Pick the {max_items} most relevant and high-quality articles for '
        f'professional software developers. Prioritize programming, software '
        f'engineering, AI/ML, compilers, algorithms, and systems design. '
        f'Exclude promotional content, clickbait, low-quality items, and '
        f'off-topic posts.\n\n'
        f'Do not rewrite, reword, or summarize anything. You are only '
        f'choosing indices.\n\n'
        f'Respond with ONLY a JSON array of integer indices, in the order '
        f'you want them to appear. Example: [1, 3, 5, 7]\n\n'
        f'Candidates:\n{json.dumps(candidates, ensure_ascii=False)}'
    )

    response = ai_query(prompt, max_tokens=AI_CURATE_MAX_TOKENS, temperature=0.1)
    if not response:
        return items[:max_items]

    try:
        match = re.search(r'\[[\s,0-9]+\]', response)
        if not match:
            return items[:max_items]
        selected_indices = json.loads(match.group(0))
        selected = []
        for idx in selected_indices:
            if isinstance(idx, int) and 1 <= idx <= len(items):
                selected.append(items[idx - 1])
        return selected if selected else items[:max_items]
    except Exception as e:
        print(f"  [AI Parse Error] {e}: {response[:200]}")
        return items[:max_items]


# ============================================================
# EXTRACTION
#
# trafilatura produces clean HTML; html2text converts it to
# Markdown with tables, links, bold, and code intact. The result
# is both what the AI sees and what the feed falls back to if the
# AI is unavailable.
# ============================================================

def fetch_html(url):
    req = urllib.request.Request(
        url, headers={'User-Agent': 'Mozilla/5.0 (compatible; DroidBuild/1.0)'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
    ctype = resp.headers.get('Content-Type', '')
    m = re.search(r'charset=([\w-]+)', ctype)
    if m:
        try:
            return raw.decode(m.group(1), errors='replace')
        except Exception:
            pass
    return raw.decode('utf-8', errors='replace')


def html_to_markdown(html):
    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_images = True
    h.ignore_emphasis = False
    h.protect_links = True
    try:
        return h.handle(html).strip()
    except Exception:
        return ""


def extract_clean_markdown(html):
    """Return the article as Markdown, or '' on failure.

    trafilatura does the content selection (drops nav, ads,
    sidebars, comments). html2text does the HTML→Markdown
    conversion, which is what preserves tables, links, bold, and
    code blocks. If trafilatura is unavailable or returns nothing,
    readability-lxml is used as a last-resort cleaner.
    """
    if not html:
        return ""

    cleaned_html = ""

    if HAS_TRAFILATURA:
        try:
            cleaned_html = trafilatura.extract(
                html,
                output_format="html",
                include_tables=True,
                include_formatting=True,
                include_links=True,
            ) or ""
        except Exception:
            cleaned_html = ""

    if not cleaned_html.strip():
        try:
            cleaned_html = Document(html).summary()
        except Exception:
            return ""

    if not cleaned_html.strip():
        return ""

    return html_to_markdown(cleaned_html)


def extract_article(url):
    """Fetch and extract an article, trying each strategy in order.

    Returns a non-empty Markdown string if any strategy succeeded.
    Returns None if every strategy failed. Callers MUST treat None
    as "drop this item from the feed."
    """
    if not url:
        return None

    html = ""
    try:
        html = fetch_html(url)
    except Exception as e:
        print(f"  [Fetch Error] {url}: {e}")
        return None

    markdown = extract_clean_markdown(html)
    if not markdown or not markdown.strip():
        print(f"  [Drop] No clean content for {url}")
        return None

    if GROQ_CLIENT is not None:
        print(f"  [AI] Polishing {url}")
        polished = ai_polish_markdown(markdown, url)
        if polished and polished.strip():
            return polished
        print(f"  [AI] Polish failed; using raw Markdown for {url}")

    return markdown


# ============================================================
# FETCHERS
# ============================================================

def fetch_hacker_news():
    print("Fetching Hacker News...")
    raw_items = []
    try:
        req = urllib.request.Request(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers={'User-Agent': 'DroidBuild-Agent/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            story_ids = json.loads(response.read().decode('utf-8'))

        for story_id in story_ids[:12]:
            req = urllib.request.Request(
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                headers={'User-Agent': 'DroidBuild-Agent/1.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                story = json.loads(response.read().decode('utf-8'))
            if not story:
                continue

            title = story.get('title', 'No Title')
            url = story.get('url', f"https://news.ycombinator.com/item?id={story_id}")
            by = story.get('by', 'unknown')
            score = story.get('score', 0)
            descendants = story.get('descendants', 0)
            text = story.get('text', '')
            time_unix = story.get('time', 0)
            pub_date = datetime.fromtimestamp(time_unix, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

            raw_items.append({
                'id': f"hn-{story_id}",
                'title': title,
                'desc': f"By {by} | {score} points | {descendants} comments",
                'tag': 'news',
                'published': pub_date,
                'url': url,
                'text': text,
                'hn_id': story_id,
            })

        selected = ai_select_items(raw_items, 'news', max_items=15)

        final = []
        for item in selected:
            if item.get('text'):
                body = item['text']
                body += f"\n\n[Discuss on Hacker News](https://news.ycombinator.com/item?id={item['hn_id']})"
                item['body'] = body
                item.pop('text', None)
                item.pop('hn_id', None)
                final.append(item)
                continue

            body = extract_article(item['url'])
            if body is None:
                continue

            body += f"\n\n[Discuss on Hacker News](https://news.ycombinator.com/item?id={item['hn_id']})"
            item['body'] = body
            item.pop('text', None)
            item.pop('hn_id', None)
            final.append(item)

        for order, item in enumerate(final, start=1):
            item['order'] = order

        print(f"Fetched {len(final)} HN items (dropped {len(selected) - len(final)}).")
        return final
    except Exception as e:
        print(f"Error fetching HN: {e}")
        return []


def fetch_lobsters():
    print("Fetching Lobsters...")
    raw_items = []
    try:
        req = urllib.request.Request(
            "https://lobste.rs/rss",
            headers={'User-Agent': 'DroidBuild-Agent/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())

        for i, item in enumerate(root.findall('.//item')[:12]):
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            raw_items.append({
                'id': f"lobsters-{i}",
                'title': title,
                'desc': "Source: Lobsters",
                'tag': 'news',
                'published': pub_date,
                'url': link,
            })

        selected = ai_select_items(raw_items, 'news', max_items=15)

        final = []
        for item in selected:
            body = extract_article(item['url'])
            if body is None:
                continue
            item['body'] = body
            final.append(item)

        for order, item in enumerate(final, start=1):
            item['order'] = order

        print(f"Fetched {len(final)} Lobsters items (dropped {len(selected) - len(final)}).")
        return final
    except Exception as e:
        print(f"Error fetching Lobsters: {e}")
        return []


def fetch_i_programmer():
    print("Fetching i-programmer...")
    raw_items = []
    try:
        url = "https://www.i-programmer.info/component/ninjarsssyndicator/?feed_id=3&format=raw"
        req = urllib.request.Request(url, headers={'User-Agent': 'DroidBuild-Agent/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())

        for i, item in enumerate(root.findall('.//item')[:12]):
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            raw_items.append({
                'id': f"iprog-{i}",
                'title': title,
                'desc': "Source: I Programmer",
                'tag': 'news',
                'published': pub_date,
                'url': link,
            })

        selected = ai_select_items(raw_items, 'news', max_items=15)

        final = []
        for item in selected:
            body = extract_article(item['url'])
            if body is None:
                continue
            item['body'] = body
            final.append(item)

        for order, item in enumerate(final, start=1):
            item['order'] = order

        print(f"Fetched {len(final)} i-programmer items (dropped {len(selected) - len(final)}).")
        return final
    except Exception as e:
        print(f"Error fetching i-programmer: {e}")
        return []


def fetch_devto_full():
    print("Fetching Dev.to...")
    items = []
    try:
        list_url = "https://dev.to/api/articles?per_page=15&top=7&tag=programming"
        req = urllib.request.Request(list_url, headers={'User-Agent': 'DroidBuild-Agent/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            articles = json.loads(resp.read().decode('utf-8'))

        for i, article in enumerate(articles):
            detail_url = f"https://dev.to/api/articles/{article['id']}"
            req = urllib.request.Request(detail_url, headers={'User-Agent': 'DroidBuild-Agent/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                detail = json.loads(resp.read().decode('utf-8'))

            body = detail.get('body_markdown', '') or ''
            if not body.strip():
                continue

            items.append({
                'id': f"devto-{article['id']}",
                'title': article['title'],
                'desc': f"By {article['user']['name']} | {article['reading_time_minutes']} min read",
                'tag': 'tutorial',
                'published': article['published_at'],
                'order': i + 1,
                'body': body,
                'url': article['url'],
            })
        print(f"Fetched {len(items)} Dev.to items.")
        return items
    except Exception as e:
        print(f"Error fetching Dev.to: {e}")
        return []


def fetch_daily_dev():
    print("Fetching daily.dev...")
    token = os.environ.get('DAILY_DEV_TOKEN', '')
    if not token:
        print("  DAILY_DEV_TOKEN not set; skipping daily.dev.")
        return []

    try:
        url = "https://api.daily.dev/public/v1/feeds"
        req = urllib.request.Request(url, headers={
            'Authorization': f'Bearer {token}',
            'User-Agent': 'DroidBuild-Agent/1.0'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        raw_items = []
        for i, post in enumerate(data.get('data', [])[:12]):
            raw_items.append({
                'id': f"dailydev-{post.get('id', i)}",
                'title': post.get('title', 'Untitled'),
                'desc': f"Source: {post.get('source', {}).get('name', 'daily.dev')}",
                'tag': 'ai',
                'published': post.get('createdAt', ''),
                'url': post.get('url', ''),
                'summary': post.get('summary', ''),
            })

        selected = ai_select_items(raw_items, 'ai', max_items=15)

        final = []
        for item in selected:
            body = item.get('summary', '') or ''
            if not body.strip():
                body = extract_article(item['url'])
                if body is None:
                    continue
            item.pop('summary', None)
            item['body'] = body
            final.append(item)

        for order, item in enumerate(final, start=1):
            item['order'] = order

        print(f"Fetched {len(final)} daily.dev items (dropped {len(selected) - len(final)}).")
        return final
    except Exception as e:
        print(f"Error fetching daily.dev: {e}")
        return []


def fetch_mit_news():
    print("Fetching MIT News CSAIL...")
    raw_items = []
    try:
        url = "https://news.mit.edu/topic/mitcomputer-science-and-artificial-intelligence-laboratory-csail-rss.xml"
        req = urllib.request.Request(url, headers={'User-Agent': 'DroidBuild-Agent/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())

        for i, item in enumerate(root.findall('.//item')[:12]):
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            raw_items.append({
                'id': f"mit-{i}",
                'title': title,
                'desc': "Source: MIT News CSAIL",
                'tag': 'research',
                'published': pub_date,
                'url': link,
            })

        selected = ai_select_items(raw_items, 'research', max_items=15)

        final = []
        for item in selected:
            body = extract_article(item['url'])
            if body is None:
                continue
            item['body'] = body
            final.append(item)

        for order, item in enumerate(final, start=1):
            item['order'] = order

        print(f"Fetched {len(final)} MIT News items (dropped {len(selected) - len(final)}).")
        return final
    except Exception as e:
        print(f"Error fetching MIT News: {e}")
        return []


# ============================================================
# LOCAL MARKDOWN SOURCES
# ============================================================

def read_frontmatter(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    if not text.startswith('---\n'):
        return {}, text
    end = text.find('\n---\n', 4)
    if end < 0:
        return {}, text
    meta = {}
    for line in text[4:end].split('\n'):
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        meta[key.strip()] = value.strip()
    body = text[end + 5:]
    return meta, body


def item_id_from_path(path):
    name = os.path.basename(path)
    if name.endswith('.md'):
        name = name[:-3]
    return name


def build_segment_from_markdown(segment):
    source_dir = os.path.join(SOURCES_DIR, segment)
    if not os.path.isdir(source_dir):
        return []
    items = []
    for path in sorted(glob.glob(os.path.join(source_dir, '*.md'))):
        meta, body = read_frontmatter(path)
        item_id = item_id_from_path(path)
        try:
            order = int(meta.get('order', 999))
        except ValueError:
            order = 999
        items.append({
            'id': item_id,
            'title': meta.get('title', item_id),
            'desc': meta.get('desc', ''),
            'tag': meta.get('tag', segment.rstrip('s')),
            'published': meta.get('date', ''),
            'order': order,
            'body': body.lstrip('\n'),
        })
    items.sort(key=lambda x: (x['order'], x['id']))
    return items


# ============================================================
# MAIN
# ============================================================

def main():
    if GROQ_CLIENT is None:
        if not HAS_OPENAI_SDK:
            print("WARNING: openai is not installed. AI polish disabled.")
        elif not GROQ_API_KEY:
            print("WARNING: GROQ_API_KEY is not set. AI polish disabled.")
        else:
            print("WARNING: Groq client failed to initialize. AI polish disabled.")

    if not HAS_TRAFILATURA:
        print("WARNING: trafilatura is not installed. Falling back to readability only.")

    os.makedirs(FEEDS_DIR, exist_ok=True)
    any_built = False

    for segment in SEGMENTS:
        local_items = build_segment_from_markdown(segment)
        live_items = []

        if segment == 'news':
            live_items = fetch_hacker_news() + fetch_lobsters() + fetch_i_programmer()
        elif segment == 'tutorials':
            live_items = fetch_devto_full()
        elif segment == 'ai':
            live_items = fetch_daily_dev()
        elif segment == 'research':
            live_items = fetch_mit_news()

        all_items = live_items + local_items
        if not all_items:
            continue

        feed = {
            'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'items': all_items,
        }

        out_path = os.path.join(FEEDS_DIR, segment + '.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(feed, f, indent=2, ensure_ascii=False)
            f.write('\n')

        print(f'wrote {out_path} ({len(feed["items"])} items)')
        any_built = True

    if not any_built:
        print('no source directories found; nothing written')


if __name__ == '__main__':
    main()
