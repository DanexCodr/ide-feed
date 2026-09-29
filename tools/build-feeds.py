#!/usr/bin/env python3
"""
Build static JSON feeds for DroidBuild.

Pipeline for each article:
  1. Fetch raw HTML.
  2. trafilatura produces a plain-text mask of the article.
  3. BeautifulSoup walks the raw HTML into semantic blocks.
     Single-column tables (title boxes, date boxes, related-
     links rows) are dropped.
  4. Blocks whose text appears in the mask are kept, in document
     order, and emitted as Markdown.
  5. The title is stripped from the body if present.
  6. The body is trimmed to the region between the first and last
     prose blocks.
  7. The body must contain at least MIN_PROSE_CONTENT characters
     of real prose (complete sentences ending in . ! or ?).
     Everything else is chrome and the item is dropped.

The final check measures prose length, not total body length.
This catches CMS pages that wrap related-content rows in <div>s
or <table>s — the prose is what matters, not the markup shape.

No AI. No API keys. No model retirements. Deterministic output.
"""

import json
import os
import glob
import html
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

SEGMENTS = ['news', 'tutorials', 'ai', 'research']
SOURCES_DIR = 'sources'
FEEDS_DIR = 'feeds'

BLOCK_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "pre", "blockquote", "ul", "ol", "hr",
}

STRIP_TAGS = ["script", "style", "noscript", "svg", "iframe", "form"]

# Body-quality thresholds. MIN_PROSE_CONTENT is the amount of
# text that must actually be sentences — not headings, not link
# labels, not table rows. A real article has hundreds of
# characters of this. A title + related-links page has almost
# none.
MIN_PROSE_CONTENT = 200
MIN_SENTENCE_LENGTH = 40


# ============================================================
# TEXT HELPERS
# ============================================================

def decode_entities(s):
    if not s:
        return s
    try:
        return html.unescape(s)
    except Exception:
        return s


def strip_links(text):
    return re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)


def strip_non_prose(text):
    text = re.sub(r'```[\s\S]*?```', ' ', text)
    text = re.sub(r'`[^`]*`', ' ', text)
    text = re.sub(r'[#*_>|]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_for_compare(s):
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s


def prose_text(block):
    """Return the prose portion of a block, or empty string.

    Prose means: at least one complete sentence of MIN_SENTENCE_
    LENGTH characters ending in . ! or ?. The terminator is
    required. Without it, table row labels, dates, and link
    anchors all masquerade as sentences.
    """
    if not block:
        return ""

    text = strip_links(block)
    text = strip_non_prose(text)
    if not text:
        return ""

    parts = re.split(r'(?<=[.!?])\s+', text)
    good = []
    for p in parts:
        p = p.strip()
        if len(p) >= MIN_SENTENCE_LENGTH and p and p[-1] in '.!?':
            good.append(p)
    return " ".join(good)


def is_prose_block(block):
    return bool(prose_text(block))


# ============================================================
# FETCHING
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


# ============================================================
# MASK
# ============================================================

def build_mask(html_text):
    mask = ""
    if HAS_TRAFILATURA:
        try:
            mask = trafilatura.extract(
                html_text,
                output_format="txt",
                include_tables=True,
                include_formatting=False,
                include_links=False,
                favor_precision=True,
            ) or ""
        except Exception:
            mask = ""

    if not mask.strip():
        try:
            summary_html = Document(html_text).summary()
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


# ============================================================
# LAYOUT TABLE DETECTION
# ============================================================

def is_layout_table(table_el):
    """True if this table is site chrome rather than a data table.

    Layout tables have one column. Data tables have two or more.
    """
    rows = table_el.find_all("tr")
    if not rows:
        return False
    max_cells = 0
    for tr in rows:
        cells = tr.find_all(["td", "th"], recursive=False)
        if len(cells) > max_cells:
            max_cells = len(cells)
    return max_cells < 2


# ============================================================
# BLOCK WALKER
# ============================================================

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

        if child.name == "table" and is_layout_table(child):
            continue

        if child.name in BLOCK_TAGS:
            plain = child.get_text(" ", strip=True)
            md = block_to_markdown(child, base_url)
            if md:
                out.append({"text": plain, "md": md, "tag": child.name})
        else:
            walk(child, out, base_url)


# ============================================================
# ALIGNMENT
# ============================================================

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


# ============================================================
# BODY FILTERS
# ============================================================

def split_into_blocks(markdown):
    if not markdown:
        return []
    lines = markdown.split('\n')
    blocks = []
    current = []
    for line in lines:
        if line.strip() == '':
            if current:
                blocks.append('\n'.join(current))
                current = []
        else:
            current.append(line)
    if current:
        blocks.append('\n'.join(current))
    return blocks


def strip_title_from_body(body, title):
    if not body or not title:
        return body

    title_norm = normalize_for_compare(title)
    if not title_norm:
        return body

    blocks = split_into_blocks(body)
    out = []
    for b in blocks:
        b_norm = normalize_for_compare(strip_links(b))
        if b_norm == title_norm:
            continue
        out.append(b)
    body = '\n\n'.join(out).strip()

    lines = body.split('\n')
    if lines:
        first_norm = normalize_for_compare(strip_links(lines[0]))
        if first_norm == title_norm:
            lines = lines[1:]
            while lines and not lines[0].strip():
                lines = lines[1:]
            body = '\n'.join(lines).strip()

    return body


def total_prose_length(markdown):
    """Sum the length of the prose portion of every block.

    This is the amount of text in the body that is actually
    sentences. Headings, link labels, dates, and table rows do
    not contribute. If the total is tiny, the body has no
    article — only chrome.
    """
    if not markdown:
        return 0
    total = 0
    for b in split_into_blocks(markdown):
        total += len(prose_text(b))
    return total


def trim_to_prose_region(markdown):
    """Keep only the region between the first and last prose blocks."""
    if not markdown:
        return markdown

    blocks = split_into_blocks(markdown)
    if not blocks:
        return markdown

    first = -1
    last = -1
    for i, b in enumerate(blocks):
        if is_prose_block(b):
            if first < 0:
                first = i
            last = i

    if first < 0 or last < 0:
        return markdown

    return '\n\n'.join(blocks[first:last + 1]).strip()


def looks_like_article(markdown):
    """True if the body has enough real prose to be an article.

    Measured by prose length, not total body length. A page that
    is a title and a table of related links has almost no prose,
    no matter how long the total body is.
    """
    if not markdown:
        return False
    if total_prose_length(markdown) < MIN_PROSE_CONTENT:
        return False
    return True


# ============================================================
# EXTRACTION
# ============================================================

def dual_pipeline_extract(html_text, url):
    if not html_text:
        return ""
    mask = build_mask(html_text)
    if not mask.strip():
        return ""

    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(STRIP_TAGS):
        tag.decompose()
    body = soup.body if soup.body else soup

    blocks = []
    walk(body, blocks, url)

    kept = align_blocks(blocks, mask)
    if not kept:
        return ""
    return "\n\n".join(kept)


def readability_extract(html_text):
    try:
        summary = Document(html_text).summary()
        h = html2text.HTML2Text()
        h.body_width = 0
        h.ignore_images = True
        h.ignore_emphasis = False
        h.protect_links = True
        return h.handle(summary).strip()
    except Exception:
        return ""


def extract_article(url):
    if not url:
        return None

    html_text = ""
    try:
        html_text = fetch_html(url)
    except Exception as e:
        print(f"  [Fetch Error] {url}: {e}")
        return None

    print(f"  [Dual] Extracting {url}")
    dual_body = dual_pipeline_extract(html_text, url)
    if dual_body and dual_body.strip():
        return dual_body

    print(f"  [Readability] Extracting {url}")
    readability_body = readability_extract(html_text)
    if readability_body and readability_body.strip():
        return readability_body

    print(f"  [Drop] No extractor succeeded for {url}")
    return None


def prepare_body(url, title):
    """Extract, strip title, trim, and require enough prose."""
    body = extract_article(url)
    if body is None:
        return None

    body = strip_title_from_body(body, title)
    if not body or not body.strip():
        print(f"  [Drop] Body empty after stripping title: {url}")
        return None

    body = trim_to_prose_region(body)
    if not body or not body.strip():
        print(f"  [Drop] Body empty after prose trim: {url}")
        return None

    if not looks_like_article(body):
        chars = len(body.strip())
        prose = total_prose_length(body)
        print(f"  [Drop] Only {prose} chars of prose in {chars}-char body: {url}")
        return None

    return body


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

        for story_id in story_ids[:30]:
            req = urllib.request.Request(
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                headers={'User-Agent': 'DroidBuild-Agent/1.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                story = json.loads(response.read().decode('utf-8'))
            if not story:
                continue

            title = decode_entities(story.get('title', 'No Title'))
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
                'score': score,
            })

        raw_items.sort(key=lambda x: x.get('score', 0), reverse=True)

        final = []
        for item in raw_items[:15]:
            if item.get('text'):
                body = item['text']
                body += f"\n\n[Discuss on Hacker News](https://news.ycombinator.com/item?id={item['hn_id']})"
                item['body'] = body
                item.pop('text', None)
                item.pop('hn_id', None)
                item.pop('score', None)
                final.append(item)
                continue

            body = prepare_body(item['url'], item['title'])
            if body is None:
                continue

            body += f"\n\n[Discuss on Hacker News](https://news.ycombinator.com/item?id={item['hn_id']})"
            item['body'] = body
            item.pop('text', None)
            item.pop('hn_id', None)
            item.pop('score', None)
            final.append(item)

        for order, item in enumerate(final, start=1):
            item['order'] = order

        print(f"Fetched {len(final)} HN items.")
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

        for i, item in enumerate(root.findall('.//item')[:15]):
            title = decode_entities(item.find('title').text)
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

        final = []
        for item in raw_items:
            body = prepare_body(item['url'], item['title'])
            if body is None:
                continue
            item['body'] = body
            final.append(item)

        for order, item in enumerate(final, start=1):
            item['order'] = order

        print(f"Fetched {len(final)} Lobsters items.")
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

        for i, item in enumerate(root.findall('.//item')[:15]):
            title = decode_entities(item.find('title').text)
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

        final = []
        for item in raw_items:
            body = prepare_body(item['url'], item['title'])
            if body is None:
                continue
            item['body'] = body
            final.append(item)

        for order, item in enumerate(final, start=1):
            item['order'] = order

        print(f"Fetched {len(final)} i-programmer items.")
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
                'title': decode_entities(article['title']),
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
        for i, post in enumerate(data.get('data', [])[:15]):
            raw_items.append({
                'id': f"dailydev-{post.get('id', i)}",
                'title': decode_entities(post.get('title', 'Untitled')),
                'desc': f"Source: {post.get('source', {}).get('name', 'daily.dev')}",
                'tag': 'ai',
                'published': post.get('createdAt', ''),
                'url': post.get('url', ''),
                'summary': post.get('summary', ''),
            })

        final = []
        for item in raw_items:
            body = item.get('summary', '') or ''
            if not body.strip():
                body = prepare_body(item['url'], item['title'])
                if body is None:
                    continue
            else:
                body = strip_title_from_body(body, item['title'])
                body = trim_to_prose_region(body)
                if not looks_like_article(body):
                    print(f"  [Drop] daily.dev summary too short: {item['url']}")
                    continue
            item.pop('summary', None)
            item['body'] = body
            final.append(item)

        for order, item in enumerate(final, start=1):
            item['order'] = order

        print(f"Fetched {len(final)} daily.dev items.")
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

        for i, item in enumerate(root.findall('.//item')[:15]):
            title = decode_entities(item.find('title').text)
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

        final = []
        for item in raw_items:
            body = prepare_body(item['url'], item['title'])
            if body is None:
                continue
            item['body'] = body
            final.append(item)

        for order, item in enumerate(final, start=1):
            item['order'] = order

        print(f"Fetched {len(final)} MIT News items.")
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
            'title': decode_entities(meta.get('title', item_id)),
            'desc': decode_entities(meta.get('desc', '')),
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
