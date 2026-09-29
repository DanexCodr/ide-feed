#!/usr/bin/env python3
"""
Build static JSON feeds for DroidBuild.

Pipeline for each article (in order):
  1. AI extraction via Groq (Llama 3.3 70B).
  2. Dual-pipeline extraction:
       a. trafilatura produces a plain-text mask of the article.
       b. BeautifulSoup walks the raw HTML into semantic blocks.
       c. Each block is kept if a substantial fraction of its 5-grams
          appear in the mask. Kept blocks are emitted as Markdown,
          preserving bold, italic, tables, code, and links.
  3. Readability-lxml + html2text.

If all three fail, the item is DROPPED from the feed. No item is
ever published with only a "read the full article" link.

The AI acts strictly as a formatter. It does not rephrase,
summarize, paraphrase, or rewrite.

Groq is used because its free tier is permanent, requires no
credit card, and offers an OpenAI-compatible endpoint that the
openai Python SDK can talk to directly.
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
from bs4 import BeautifulSoup, NavigableString
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
    'llama-3.3-70b-versatile',
    'llama-3.1-70b-versatile',
    'llama-3.1-8b-instant',
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


# ============================================================
# EXTRACTION PROMPT
# ============================================================

EXTRACTION_SYSTEM_PROMPT = """You are a Markdown conversion tool. You are not an editor, summarizer, or writer.

YOUR ONLY JOB: find the main article in the HTML and emit it as Markdown.

ABSOLUTE RULES — VIOLATING ANY OF THESE IS A FAILURE:

1. DO NOT rephrase, paraphrase, summarize, shorten, expand, or rewrite any sentence. Copy the author's exact wording.

2. DO NOT add any text of your own. No introductions ("Here is the article:"), no conclusions, no TL;DRs, no editorial notes, no section summaries, no title that the article does not contain.

3. DO NOT remove content from the article. Paragraphs, captions, subheadings, footnotes referenced inline, and block quotes all stay.

4. DO NOT change capitalization, punctuation, or spacing. Preserve em dashes (—), en dashes (–), curly quotes (" " ' '), ellipses (…), and every other typographic mark exactly as written.

5. DO NOT translate. If the article is in a language other than English, keep it in that language.

6. DO NOT merge or split paragraphs. One source paragraph = one Markdown paragraph, separated by a blank line.

WHAT TO REMOVE (this is the only removal allowed):
- Navigation menus, breadcrumbs, header links.
- Sidebars, "related posts", "you might also like".
- Footer, copyright lines, social share buttons.
- Advertisements, newsletter signup forms, cookie banners.
- Comment sections and reader responses.
- Author bio boxes at the bottom, unless the article itself ends with one.
- Image attribution captions that are not part of the article's voice.

HOW TO FORMAT EACH ELEMENT:

- Article headings: use `##` for top-level sections, `###` for subsections. Do not create headings the source did not have. Do not use `#` — the viewer already supplies the title.

- Bold: `**text**`. Italic: `*text*`. Use them only where the source uses emphasis.

- Links: `[anchor text](url)`. Use absolute URLs. If the source shows a link the user can click, it becomes a Markdown link.

- Images: `![alt text](url)`. Keep the alt text if present, empty otherwise.

- Inline code: single backticks.

- Code blocks: fenced with triple backticks and the language tag if the source indicates one (e.g. ```python). If the language is unknown, use a bare fence.

- Tables: Markdown pipe tables. Preserve every row and column. Use `---` in the separator row. Keep alignment markers (`:---`, `:---:`, `---:`) if the source implies them.

- Ordered lists: `1.`, `2.`, etc. Unordered lists: `-`. Nested lists indent by two spaces.

- Block quotes: prefix each line with `> `.

- Horizontal rules: `---`.

- Line breaks within a paragraph: two trailing spaces, then a newline. Use sparingly — only when the source has a hard break.

OUTPUT: Markdown only. No wrappers, no code fences around the whole document, no explanation."""


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


def ai_query(prompt, max_tokens=2048, temperature=0.2, json_mode=False):
    model_name = _pick_model()
    if model_name is None:
        return None
    try:
        kwargs = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = GROQ_CLIENT.chat.completions.create(**kwargs)
        if not response or not response.choices:
            return None
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [AI Error] {type(e).__name__}: {e}")
        return None


def ai_select_items(items, segment, max_items=15):
    if GROQ_CLIENT is None or not items:
        return items[:max_items]

    candidates = []
    for i, item in enumerate(items):
        title = item.get('title', 'No Title')
        desc = (item.get('desc', '') or '')[:200]
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
        f'Return ONLY a JSON object with this exact shape:\n'
        f'{{"selected": [1, 3, 5, 7]}}\n\n'
        f'Where the array contains the "index" values of the items you '
        f'selected, in the order you want them to appear.\n\n'
        f'Candidates:\n{json.dumps(candidates, ensure_ascii=False)}'
    )

    response = ai_query(prompt, max_tokens=200, temperature=0.1, json_mode=True)
    if not response:
        return items[:max_items]

    try:
        parsed = json.loads(response)
        selected_indices = parsed.get("selected", [])
        selected = []
        for idx in selected_indices:
            if isinstance(idx, int) and 1 <= idx <= len(items):
                selected.append(items[idx - 1])
        return selected if selected else items[:max_items]
    except Exception as e:
        print(f"  [AI Parse Error] {e}: {response[:200]}")
        return items[:max_items]


def ai_extract_body(html, url):
    if GROQ_CLIENT is None:
        return None

    html_snippet = html[:60000]

    prompt = (
        EXTRACTION_SYSTEM_PROMPT +
        "\n\n---\n\n"
        f"ARTICLE URL: {url}\n\n"
        "RAW HTML:\n" + html_snippet + "\n\n"
        "Now produce the Markdown. Remember: do not rephrase, do not "
        "summarize, do not add commentary. Copy the author's exact words."
    )

    return ai_query(prompt, max_tokens=8192, temperature=0.0)


# ============================================================
# DUAL-PIPELINE EXTRACTOR (fallback)
# ============================================================

BLOCK_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "pre", "blockquote", "ul", "ol", "hr",
}

STRIP_TAGS = ["script", "style", "noscript", "svg", "iframe", "form"]


def build_mask(html):
    mask = ""
    if HAS_TRAFILATURA:
        try:
            mask = trafilatura.extract(
                html,
                output_format="txt",
                include_tables=True,
                include_formatting=False,
                include_links=False,
            ) or ""
        except Exception:
            mask = ""

    if not mask.strip():
        try:
            summary_html = Document(html).summary()
            mask = BeautifulSoup(summary_html, "html.parser").get_text(" ")
        except Exception:
            mask = ""

    return mask


def tokenize(text):
    if not text:
        return []
    return re.findall(r"\w+", text.lower())


def ngrams(tokens, n):
    if len(tokens) < n:
        return set()
    return set(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))


def extract_language(code_el):
    classes = code_el.get("class", []) or []
    for c in classes:
        if c.startswith("language-"):
            return c[len("language-"):]
        if c.startswith("lang-"):
            return c[len("lang-"):]
    return ""


def absolute_url(base, href):
    if not href:
        return ""
    try:
        return urllib.parse.urljoin(base, href)
    except Exception:
        return href


def inline_markdown(el, base_url):
    parts = []
    for child in el.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
            continue
        if not hasattr(child, "name") or child.name is None:
            continue

        name = child.name
        if name in ("strong", "b"):
            parts.append("**" + inline_markdown(child, base_url) + "**")
        elif name in ("em", "i"):
            parts.append("*" + inline_markdown(child, base_url) + "*")
        elif name == "code":
            parts.append("`" + child.get_text() + "`")
        elif name == "a":
            href = absolute_url(base_url, child.get("href", ""))
            label = inline_markdown(child, base_url).strip()
            if href and label:
                parts.append("[" + label + "](" + href + ")")
            else:
                parts.append(label)
        elif name == "br":
            parts.append("  \n")
        elif name == "img":
            src = absolute_url(base_url, child.get("src", ""))
            alt = child.get("alt", "") or ""
            if src:
                parts.append("![" + alt + "](" + src + ")")
        elif name in ("sub", "sup", "del", "s", "kbd", "mark", "small"):
            parts.append("<" + name + ">" +
                         inline_markdown(child, base_url) +
                         "</" + name + ">")
        else:
            parts.append(inline_markdown(child, base_url))
    return "".join(parts)


def table_to_markdown(table_el, base_url):
    rows = []
    for tr in table_el.find_all("tr"):
        cells = []
        for cell in tr.find_all(["td", "th"], recursive=False):
            text = inline_markdown(cell, base_url).strip()
            text = text.replace("|", "\\|")
            text = re.sub(r"\s+", " ", text).strip()
            cells.append(text)
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]

    out = []
    out.append("| " + " | ".join(rows[0]) + " |")
    out.append("| " + " | ".join(["---"] * width) + " |")
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def list_to_markdown(list_el, base_url, depth=0):
    lines = []
    ordered = list_el.name == "ol"
    items = list_el.find_all("li", recursive=False)

    for i, li in enumerate(items):
        prefix = ("%d. " % (i + 1)) if ordered else "- "
        prefix = "  " * depth + prefix

        inline_parts = []
        nested_lists = []
        for child in li.children:
            if hasattr(child, "name") and child.name in ("ul", "ol"):
                nested_lists.append(child)
            elif isinstance(child, NavigableString):
                inline_parts.append(str(child))
            else:
                inline_parts.append(inline_markdown(child, base_url))

        content = "".join(inline_parts)
        content = re.sub(r"\s+", " ", content).strip()
        lines.append(prefix + content)

        for nested in nested_lists:
            lines.append(list_to_markdown(nested, base_url, depth + 1))

    return "\n".join(lines)


def block_to_markdown(el, base_url):
    name = el.name

    if name == "pre":
        code = el.find("code")
        if code is not None:
            lang = extract_language(code)
            text = code.get_text()
        else:
            lang = ""
            text = el.get_text()
        if text.endswith("\n"):
            text = text[:-1]
        return "```" + lang + "\n" + text + "\n```"

    if name == "table":
        return table_to_markdown(el, base_url)

    if name == "blockquote":
        inner_blocks = []
        walk(el, inner_blocks, base_url)
        inner_md = "\n\n".join(b["md"] for b in inner_blocks)
        if not inner_md:
            inner_md = inline_markdown(el, base_url).strip()
        return "\n".join("> " + line if line else ">" for line in inner_md.split("\n"))

    if name in ("ul", "ol"):
        return list_to_markdown(el, base_url)

    if name == "hr":
        return "---"

    if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(name[1])
        text = inline_markdown(el, base_url).strip()
        return ("#" * level) + " " + text

    text = inline_markdown(el, base_url)
    return text.strip()


def walk(node, out, base_url):
    for child in list(node.children):
        if not hasattr(child, "name") or child.name is None:
            continue
        if child.name in STRIP_TAGS:
            continue
        if child.name in BLOCK_TAGS:
            plain = child.get_text(" ", strip=True)
            md = block_to_markdown(child, base_url)
            if md:
                out.append({"text": plain, "md": md, "tag": child.name})
        else:
            walk(child, out, base_url)


def align_blocks(blocks, mask_text):
    mask_tokens = tokenize(mask_text)
    mask_normalized = " " + " ".join(mask_tokens) + " "
    mask_grams = ngrams(mask_tokens, 5)

    kept = []
    for block in blocks:
        tokens = tokenize(block["text"])
        if not tokens:
            continue

        if len(tokens) < 5:
            needle = " " + " ".join(tokens) + " "
            if needle in mask_normalized:
                kept.append(block["md"])
        else:
            grams = ngrams(tokens, 5)
            if not grams:
                continue
            overlap = len(grams & mask_grams) / float(len(grams))
            if overlap >= 0.5:
                kept.append(block["md"])

    return kept


def dual_pipeline_extract(html, url):
    if not html:
        return ""
    mask = build_mask(html)
    if not mask.strip():
        return ""

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(STRIP_TAGS):
        tag.decompose()
    body = soup.body if soup.body else soup

    blocks = []
    walk(body, blocks, url)

    kept = align_blocks(blocks, mask)
    if not kept:
        return ""
    return "\n\n".join(kept)


# ============================================================
# READABILITY FALLBACK (last resort)
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


def readability_extract(html):
    try:
        summary = Document(html).summary()
        h = html2text.HTML2Text()
        h.body_width = 0
        h.ignore_images = True
        h.ignore_emphasis = False
        h.protect_links = True
        return h.handle(summary).strip()
    except Exception:
        return ""


# ============================================================
# EXTRACTION ORCHESTRATION
#
# Returns a non-empty Markdown string if any strategy succeeded.
# Returns None if every strategy failed. Callers MUST treat None
# as "drop this item from the feed."
# ============================================================

def extract_article(url):
    if not url:
        return None

    html = ""
    try:
        html = fetch_html(url)
    except Exception as e:
        print(f"  [Fetch Error] {url}: {e}")
        return None

    # 1. AI extraction
    if GROQ_CLIENT is not None:
        print(f"  [AI] Extracting {url}")
        ai_body = ai_extract_body(html, url)
        if ai_body and ai_body.strip():
            return ai_body

    # 2. Dual-pipeline extraction
    print(f"  [Dual] Extracting {url}")
    dual_body = dual_pipeline_extract(html, url)
    if dual_body and dual_body.strip():
        return dual_body

    # 3. Readability + html2text
    print(f"  [Readability] Extracting {url}")
    readability_body = readability_extract(html)
    if readability_body and readability_body.strip():
        return readability_body

    # 4. Total failure. Return None so the caller drops the item.
    print(f"  [Drop] All extractors failed for {url}")
    return None


# ============================================================
# FETCHERS
#
# Each fetcher is responsible for dropping items whose extraction
# returned None. The feed contains only items with real content.
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

        for story_id in story_ids[:30]:
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
            # Ask HN / Show HN items ship their body inline.
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
                # Every extractor failed. Drop.
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

        for i, item in enumerate(root.findall('.//item')[:30]):
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

        for i, item in enumerate(root.findall('.//item')[:30]):
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
            # Dev.to always returns real content, but guard anyway.
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
        for i, post in enumerate(data.get('data', [])[:30]):
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

        for i, item in enumerate(root.findall('.//item')[:30]):
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
            print("WARNING: openai is not installed. AI features disabled.")
        elif not GROQ_API_KEY:
            print("WARNING: GROQ_API_KEY is not set. AI features disabled.")
        else:
            print("WARNING: Groq client failed to initialize. AI features disabled.")

    if not HAS_TRAFILATURA:
        print("WARNING: trafilatura is not installed. Dual-pipeline mask will fall back to readability.")

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
