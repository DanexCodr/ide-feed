#!/usr/bin/env python3
"""
Build static JSON feeds for DroidBuild.

Segments produced:
  - news       : Hacker News + Lobsters + I Programmer + MIT News + daily.dev
  - tutorials  : Dev.to (filtered)

Feed shape:
  - feeds/{segment}.json          metadata only (title, desc, tag,
                                  url, image, preview, color, published)
  - feeds/bodies/{segment}/*.md   article body text, one file per item

Body text is split out of the feed JSON so the WebView can parse
the feed instantly even when the pool grows to hundreds of items.
The app fetches a body lazily the first time a reader is opened,
and caches it in memory for the rest of the app session.

Retention:
  Each build merges the freshly fetched items with the previous
  feed, keeps every item newer than RETENTION_DAYS, prunes older
  items, and deletes their body files. The pool therefore grows
  during busy periods and shrinks during quiet ones, without
  needing a database.

Pipeline for each article:
  1. Fetch raw HTML. Strip XML-incompatible control characters.
  2. trafilatura produces a plain-text mask.
  3. BeautifulSoup walks the raw HTML into semantic blocks.
  4. Blocks whose text appears in the mask are kept, in order.
  5. The title is stripped, the body trimmed, prose enforced.
  6. og:image is extracted. The image is fetched, analyzed for
     solidity, downscaled to a preview, and both URLs are written
     into the item.

No AI. No API keys. No model retirements. Deterministic output.
"""

import base64
import json
import os
import glob
import html
import io
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

from readability import Document
from bs4 import BeautifulSoup, NavigableString
import html2text

try:
    from PIL import Image, ImageStat
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

SEGMENTS = ['news', 'tutorials']
SOURCES_DIR = 'sources'
FEEDS_DIR = 'feeds'

BLOCK_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "pre", "blockquote", "ul", "ol", "hr",
    "figure",
}

STRIP_TAGS = ["script", "style", "noscript", "svg", "iframe", "form"]

MIN_PROSE_CONTENT = 200
MIN_SENTENCE_LENGTH = 40

PREVIEW_WIDTH = 32
PREVIEW_QUALITY = 30
PREVIEW_MAX_BASE64_BYTES = 8192

RETENTION_DAYS = 7


# ============================================================
# HTML SANITIZATION
# ============================================================

_CONTROL_CHARS_RE = re.compile(
    '[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\x80-\x9F]'
)

_REPLACEMENT_CHARS_RE = re.compile('\uFFFD')


def sanitize_html_text(text):
    """Remove XML-incompatible control characters from an HTML
    string. Preserves tab, newline, and carriage return."""
    if not text:
        return text
    return _CONTROL_CHARS_RE.sub('', text)


# ============================================================
# SOURCE COLORS
# ============================================================

SOURCE_COLORS = {
    'hackernews': '#FF6600',
    'lobsters': '#AC130D',
    'iprogrammer': '#2196F3',
    'mitnews': '#8B0000',
    'dailydev': '#7B61FF',
    'devto': '#3B49DF',
}


# ============================================================
# DEV.TO FILTERS
# ============================================================

EMOJI_RANGES = (
    (0x1F300, 0x1F5FF),
    (0x1F600, 0x1F64F),
    (0x1F680, 0x1F6FF),
    (0x1F700, 0x1F77F),
    (0x1F780, 0x1F7FF),
    (0x1F800, 0x1F8FF),
    (0x1F900, 0x1F9FF),
    (0x1FA00, 0x1FA6F),
    (0x1FA70, 0x1FAFF),
    (0x2600,  0x26FF),
    (0x2700,  0x27BF),
    (0x2B00,  0x2BFF),
    (0x1F1E6, 0x1F1FF),
)


def contains_emoji(s):
    if not s:
        return False
    for ch in s:
        cp = ord(ch)
        for lo, hi in EMOJI_RANGES:
            if lo <= cp <= hi:
                return True
    return False


DEVTO_SKIP_TITLE_SUBSTRINGS = [
    "congrats",
    "congratulations",
]


def devto_should_skip(title):
    if contains_emoji(title):
        return True, "emoji in title"
    if title:
        t = title.lower()
        for s in DEVTO_SKIP_TITLE_SUBSTRINGS:
            if s in t:
                return True, f"title contains '{s}'"
    return False, ""


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

def _is_html_content_type(ctype):
    if not ctype:
        return True
    c = ctype.lower()
    if 'text/html' in c:
        return True
    if 'application/xhtml' in c:
        return True
    if c.startswith('text/plain'):
        return True
    return False


def _looks_like_pdf_url(url):
    if not url:
        return False
    path = url.split('?', 1)[0].split('#', 1)[0].lower()
    return path.endswith('.pdf')


# ============================================================
# ROBOTS.TXT
# ============================================================

_robots_cache = {}


def _robots_allows(url):
    try:
        parsed = urllib.parse.urlparse(url)
        origin = parsed.scheme + '://' + parsed.netloc
        path = parsed.path or '/'
    except Exception:
        return True

    if origin in _robots_cache:
        rules = _robots_cache[origin]
    else:
        rules = ''
        try:
            req = urllib.request.Request(
                origin + '/robots.txt',
                headers={'User-Agent': 'DroidBuild/1.0 (+feed builder)'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                rules = resp.read(65536).decode('utf-8', errors='ignore')
        except Exception:
            rules = ''
        _robots_cache[origin] = rules

    if not rules:
        return True

    in_star = False
    disallowed = []
    for line in rules.splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith('user-agent:'):
            ua = line.split(':', 1)[1].strip()
            in_star = (ua == '*')
        elif in_star and lower.startswith('disallow:'):
            rule = line.split(':', 1)[1].strip()
            if rule:
                disallowed.append(rule)

    for rule in disallowed:
        pattern = re.escape(rule).replace(r'\*', '.*')
        if pattern.endswith(r'\$'):
            pattern = pattern[:-2] + '$'
        try:
            if re.match(pattern, path):
                return False
        except re.error:
            continue

    return True


def fetch_html(url):
    req = urllib.request.Request(
        url, headers={
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
    with urllib.request.urlopen(req, timeout=15) as resp:
        ctype = resp.headers.get('Content-Type', '') or ''
        if not _is_html_content_type(ctype):
            return None
        raw = resp.read()

    if raw[:5] == b'%PDF-':
        return None
    if raw[:2] == b'\x1f\x8b':
        return None

    m = re.search(r'charset=([\w-]+)', ctype)
    text = None
    if m:
        try:
            text = raw.decode(m.group(1), errors='replace')
        except Exception:
            text = None
    if text is None:
        text = raw.decode('utf-8', errors='replace')
    return sanitize_html_text(text)


def fetch_bytes(url, timeout=10, referer=None):
    if not url:
        return b''
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120 Mobile Safari/537.36',
        }
        if referer:
            headers['Referer'] = referer
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return b''


# ============================================================
# IMAGE URL EXTRACTION HELPERS
# ============================================================

def _is_placeholder(url):
    if not url:
        return True
    lower = url.lower().strip()
    if lower.startswith("data:"):
        return True
    if "blank.gif" in lower or "spacer.gif" in lower:
        return True
    if lower.startswith("about:"):
        return True
    return False


def _is_usable_article_image(url):
    if _is_placeholder(url):
        return False

    lower = url.lower().split('?', 1)[0].split('#', 1)[0]

    if lower.endswith('.svg'):
        return False

    ui_markers = (
        '/icons/', '/icon/', '/social/', '/share/',
        '/assets/img/social/', '/assets/icons/',
        '/avatar', '/logo', '/favicon',
        'apple-touch', 'sprite',
    )
    for m in ui_markers:
        if m in lower:
            return False

    name = lower.rsplit('/', 1)[-1]
    stem = name.rsplit('.', 1)[0]

    for marker in ('icon', 'logo', 'avatar', 'badge', 'share'):
        if stem == marker:
            return False
        if len(stem) <= 20:
            if stem.startswith(marker + '-') or stem.endswith('-' + marker):
                return False

    return True


def _pick_from_srcset(srcset):
    candidates = []
    for part in srcset.split(","):
        part = part.strip()
        if not part:
            continue
        tokens = part.split()
        url = tokens[0]
        weight = 0
        if len(tokens) > 1:
            desc = tokens[1]
            try:
                if desc.endswith("w"):
                    weight = int(desc[:-1])
                elif desc.endswith("x"):
                    weight = int(float(desc[:-1]) * 1000)
            except ValueError:
                weight = 0
        candidates.append((weight, url))
    if not candidates:
        return ""
    best = candidates[0]
    for c in candidates[1:]:
        if c[0] >= best[0]:
            best = c
    return best[1]


def extract_image_src(img_el, base_url):
    for attr in ("srcset", "data-srcset"):
        srcset = img_el.get(attr)
        if srcset:
            best = _pick_from_srcset(srcset)
            if best and not _is_placeholder(best):
                return absolute_url(base_url, best)

    for attr in ("data-src", "data-lazy-src", "data-original", "data-url"):
        url = img_el.get(attr)
        if url and not _is_placeholder(url):
            return absolute_url(base_url, url)

    src = img_el.get("src", "")
    if src and not _is_placeholder(src):
        return absolute_url(base_url, src)

    return ""


def extract_picture_src(picture_el, base_url):
    for source in picture_el.find_all("source"):
        srcset = source.get("srcset") or source.get("data-srcset")
        if srcset:
            candidate = _pick_from_srcset(srcset)
            if candidate and not _is_placeholder(candidate):
                return absolute_url(base_url, candidate)
    img = picture_el.find("img")
    if img is not None:
        return extract_image_src(img, base_url)
    return ""


# ============================================================
# OG:IMAGE EXTRACTION
# ============================================================

def extract_og_image(html_text, base_url):
    if not html_text or not base_url:
        return ""

    try:
        soup = BeautifulSoup(html_text, "html.parser")
    except Exception:
        return ""

    for prop in ('og:image', 'og:image:url', 'og:image:secure_url',
                 'twitter:image', 'twitter:image:src'):
        tag = (soup.find('meta', attrs={'property': prop})
               or soup.find('meta', attrs={'name': prop}))
        if tag and tag.get('content'):
            url = tag['content'].strip()
            if not _is_placeholder(url):
                return _resolve_image_url(url, base_url)

    tag = soup.find('link', attrs={'rel': 'image_src'})
    if tag and tag.get('href'):
        url = tag['href'].strip()
        if not _is_placeholder(url):
            return _resolve_image_url(url, base_url)

    for container_sel in ('article', 'main', '[role=main]',
                          '.post-content', '.entry-content',
                          '.article-body', '.story-body'):
        try:
            container = soup.select_one(container_sel)
        except Exception:
            container = None
        if not container:
            continue
        for img in container.find_all('img'):
            src = extract_image_src(img, base_url)
            if src and _is_usable_article_image(src):
                return src
        for pic in container.find_all('picture'):
            src = extract_picture_src(pic, base_url)
            if src and _is_usable_article_image(src):
                return src

    return ""


def _resolve_image_url(url, base_url):
    if not url:
        return ""
    url = url.strip()
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith(('http://', 'https://')):
        return url
    return urllib.parse.urljoin(base_url, url)


# ============================================================
# IMAGE ANALYSIS
#
# Two things happen here:
#
#   1. Every decoded image is composited over white if it has
#      an alpha channel. Without this, transparent PNGs would
#      become black rectangles after a naive RGB conversion,
#      both in the preview and in the solid-color check.
#
#   2. The image is classified as "solid" or "not solid". A
#      solid image is one whose per-channel pixel variance is
#      below a small threshold after downsampling. Such images
#      are useless as card visuals — they look identical to the
#      placeholder — so the pipeline clears both the image
#      and preview fields on the item and lets the app fall
#      back to its CSS placeholder.
#
# Threshold rationale: after LANCZOS downsampling to 16x16,
# a true solid color (even through JPEG compression) has a
# per-channel standard deviation under 3. A near-solid image
# with a small logo or a single dot has stddev in the 15-30
# range. Real photographs are 30+. The cutoff is set at 8.
#
# The statistics are computed by ImageStat, which is a
# long-stable Pillow module that runs in optimized C. It is
# used instead of manual pixel iteration because the old
# Image.Image.getdata() API is deprecated and will be removed
# in Pillow 14 (October 2027).
# ============================================================

def _pil_image_is_solid(img):
    """Return True if the image is effectively a single color.

    The image is reduced to a 16x16 thumbnail first, which
    averages out JPEG compression noise while preserving any
    real visual structure. If no channel has a standard
    deviation above 8, the image is treated as solid.

    ImageStat computes per-channel standard deviation in C.
    If any channel has meaningful variance, the image is not
    a single flat color.
    """
    try:
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS

        small = img.resize((16, 16), resample)

        stat = ImageStat.Stat(small)
        stddevs = stat.stddev
        if not stddevs:
            return False
        return max(stddevs) < 8.0
    except Exception:
        return False


def _composite_over_white(img):
    """If the image has an alpha channel, composite it over a
    white background. Returns an RGB image. Without this step a
    transparent PNG would become a black rectangle after a
    naive RGB conversion."""
    try:
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            return background
        if img.mode == 'LA':
            background = Image.new('L', img.size, 255)
            background.paste(img, mask=img.split()[1])
            return background.convert('RGB')
        if img.mode not in ('RGB', 'L'):
            return img.convert('RGB')
        return img
    except Exception:
        return img


def _encode_preview_data_url(img):
    """Encode a PIL image as a 32px JPEG data URL. Retries at
    progressively smaller sizes and lower qualities until the
    base64 representation fits under PREVIEW_MAX_BASE64_BYTES.
    Returns '' on any failure."""
    try:
        w, h = img.size
        if w <= 0 or h <= 0:
            return ''

        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS

        for target_w in (32, 24, 16):
            new_h = max(1, int(round(h * (target_w / float(w)))))
            resized = img.resize((target_w, new_h), resample)

            for quality in (30, 20, 10):
                buf = io.BytesIO()
                resized.save(buf, format='JPEG', quality=quality,
                             optimize=True, progressive=True)
                data = buf.getvalue()
                if not data:
                    continue

                encoded = base64.b64encode(data).decode('ascii')
                data_url = "data:image/jpeg;base64," + encoded

                if len(data_url) <= PREVIEW_MAX_BASE64_BYTES:
                    return data_url
    except Exception:
        pass

    return ''


def analyze_image(image_url, referer=None):
    """Fetch, decode, and classify an image.

    Returns a dict with two keys:

      solid   : True if the image is effectively one color.
      preview : a base64 JPEG data URL, or '' on any failure
                or when the image is solid.

    A caller that has both an image URL and a preview field to
    populate should use this function directly. A caller that
    only wants the preview string can read result['preview'].
    """
    result = {'solid': False, 'preview': ''}

    if not image_url or not HAS_PIL:
        return result

    raw = fetch_bytes(image_url, timeout=10, referer=referer)
    if not raw:
        return result

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception:
        return result

    try:
        img = _composite_over_white(img)
    except Exception:
        return result

    try:
        if _pil_image_is_solid(img):
            result['solid'] = True
            return result
    except Exception:
        pass

    try:
        result['preview'] = _encode_preview_data_url(img)
    except Exception:
        pass

    return result


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
        except Exception as e:
            print(f"    [Mask] readability failed: {type(e).__name__}")
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
            src = extract_image_src(child, base_url)
            alt = (child.get("alt", "") or "").replace("]", "\\]")
            if src:
                parts.append("![" + alt + "](" + src + ")")
        elif name == "picture":
            src = extract_picture_src(child, base_url)
            inner = child.find("img")
            alt = ""
            if inner is not None:
                alt = (inner.get("alt", "") or "").replace("]", "\\]")
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
    if name == "figure":
        src = ""
        alt = ""
        picture = el.find("picture")
        if picture is not None:
            src = extract_picture_src(picture, base_url)
            inner = picture.find("img")
            if inner is not None:
                alt = (inner.get("alt", "") or "").replace("]", "\\]")
        else:
            img = el.find("img")
            if img is not None:
                src = extract_image_src(img, base_url)
                alt = (img.get("alt", "") or "").replace("]", "\\]")

        lines = []
        if src:
            lines.append("![" + alt + "](" + src + ")")

        caption_el = el.find("figcaption")
        if caption_el is not None:
            cap = inline_markdown(caption_el, base_url).strip()
            if cap:
                lines.append("*" + cap + "*")

        if not lines:
            text = inline_markdown(el, base_url).strip()
            return text
        return "\n\n".join(lines)
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

def _has_image_markdown(md):
    return md is not None and "![" in md and "](" in md


def align_blocks(blocks, mask_text):
    mask_tokens = tokenize(mask_text)
    mask_normalized = " " + " ".join(mask_tokens) + " "
    mask_grams = ngrams(mask_tokens, 5)
    kept = []
    for block in blocks:
        has_image = _has_image_markdown(block["md"])
        tokens = tokenize(block["text"])

        if not tokens:
            if has_image:
                kept.append(block["md"])
            continue

        if len(tokens) < 5:
            needle = " " + " ".join(tokens) + " "
            if needle in mask_normalized or has_image:
                kept.append(block["md"])
        else:
            grams = ngrams(tokens, 5)
            if not grams:
                continue
            overlap = len(grams & mask_grams) / float(len(grams))
            threshold = 0.3 if has_image else 0.5
            if overlap >= threshold:
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
    if not markdown:
        return 0
    total = 0
    for b in split_into_blocks(markdown):
        total += len(prose_text(b))
    return total


def trim_to_prose_region(markdown):
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
    except Exception as e:
        print(f"    [Readability] {type(e).__name__}: {e}")
        return ""


def extract_article(url):
    if not url:
        return None, ""

    if not _robots_allows(url):
        print(f"  [Skip] Disallowed by robots.txt: {url}")
        return None, ""

    if _looks_like_pdf_url(url):
        print(f"  [Skip] PDF link (by extension): {url}")
        return None, ""

    html_text = None
    try:
        html_text = fetch_html(url)
    except Exception as e:
        print(f"  [Fetch Error] {url}: {e}")
        return None, ""

    if html_text is None:
        print(f"  [Skip] Non-HTML response (PDF, image, or binary): {url}")
        return None, ""

    if not html_text.strip():
        print(f"  [Skip] Empty response body: {url}")
        return None, ""

    og_image = extract_og_image(html_text, url)

    print(f"  [Dual] Extracting {url}")
    dual_body = dual_pipeline_extract(html_text, url)
    if dual_body and dual_body.strip():
        return dual_body, og_image

    print(f"  [Readability] Extracting {url}")
    readability_body = readability_extract(html_text)
    if readability_body and readability_body.strip():
        return readability_body, og_image

    print(f"  [Drop] No extractor succeeded for {url}")
    return None, ""


def prepare_body(url, title):
    body, image = extract_article(url)
    if body is None:
        return None, "", ""

    body = strip_title_from_body(body, title)
    if not body or not body.strip():
        print(f"  [Drop] Body empty after stripping title: {url}")
        return None, "", ""

    body = trim_to_prose_region(body)
    if not body or not body.strip():
        print(f"  [Drop] Body empty after prose trim: {url}")
        return None, "", ""

    if not looks_like_article(body):
        chars = len(body.strip())
        prose = total_prose_length(body)
        print(f"  [Drop] Only {prose} chars of prose in {chars}-char body: {url}")
        return None, "", ""

    preview = ""
    if image:
        result = analyze_image(image, referer=url)
        if result['solid']:
            print(f"  [Solid] Solid-color image, treated as no image: {image}")
            image = ""
        else:
            preview = result['preview']
            if preview:
                print(f"  [Preview] {len(preview)} bytes from {image}")
            else:
                print(f"  [Preview] Failed for {image}")

    return body, image, preview


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
                'color': SOURCE_COLORS['hackernews'],
            })

        raw_items.sort(key=lambda x: x.get('score', 0), reverse=True)

        final = []
        for item in raw_items[:36]:
            if item.get('text'):
                body = item['text']
                body += f"\n\n[Discuss on Hacker News](https://news.ycombinator.com/item?id={item['hn_id']})"
                item['body'] = body
                item['image'] = ""
                item['preview'] = ""
                item.pop('text', None)
                item.pop('hn_id', None)
                item.pop('score', None)
                final.append(item)
                continue

            body, image, preview = prepare_body(item['url'], item['title'])
            if body is None:
                continue

            body += f"\n\n[Discuss on Hacker News](https://news.ycombinator.com/item?id={item['hn_id']})"
            item['body'] = body
            item['image'] = image
            item['preview'] = preview
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

        for i, item in enumerate(root.findall('.//item')[:30]):
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
                'color': SOURCE_COLORS['lobsters'],
            })

        final = []
        for item in raw_items:
            body, image, preview = prepare_body(item['url'], item['title'])
            if body is None:
                continue
            item['body'] = body
            item['image'] = image
            item['preview'] = preview
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

        for i, item in enumerate(root.findall('.//item')[:45]):
            title = decode_entities(item.find('title').text)
            link = item.find('link').text
            pub_date = item.find('pubDate').text

            if "/book-watch-archive/" in link:
                print(f"  [Skip] Book Watch listing: {link}")
                continue

            raw_items.append({
                'id': f"iprog-{i}",
                'title': title,
                'desc': "Source: I Programmer",
                'tag': 'news',
                'published': pub_date,
                'url': link,
                'color': SOURCE_COLORS['iprogrammer'],
            })

        final = []
        for item in raw_items:
            body, image, preview = prepare_body(item['url'], item['title'])
            if body is None:
                continue
            item['body'] = body
            item['image'] = image
            item['preview'] = preview
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
        list_url = "https://dev.to/api/articles?per_page=30&top=14&tag=programming"
        print(f"  [Dev.to] List URL: {list_url}")
        req = urllib.request.Request(list_url, headers={'User-Agent': 'DroidBuild-Agent/1.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            articles = json.loads(resp.read().decode('utf-8'))
        print(f"  [Dev.to] List returned {len(articles)} articles")

        skipped = 0
        kept = 0

        for article in articles:
            if kept >= 45:
                break

            list_title = article.get('title', '')
            skip, reason = devto_should_skip(list_title)
            if skip:
                print(f"  [Skip] Dev.to: {reason} — {list_title[:70]}")
                skipped += 1
                continue

            detail_url = f"https://dev.to/api/articles/{article['id']}"
            try:
                req = urllib.request.Request(
                    detail_url,
                    headers={'User-Agent': 'DroidBuild-Agent/1.0'})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    detail = json.loads(resp.read().decode('utf-8'))
            except Exception as detail_err:
                print(f"  [Dev.to] Detail fetch failed for "
                      f"{article['id']}: {type(detail_err).__name__}: {detail_err}")
                skipped += 1
                continue

            body = detail.get('body_markdown', '') or ''
            if not body.strip():
                print(f"  [Dev.to] Empty body_markdown for {article['id']}")
                skipped += 1
                continue

            image = detail.get('cover_image', '') or ''
            if not image:
                image = detail.get('social_image', '') or ''

            preview = ""
            if image:
                result = analyze_image(image, referer=article['url'])
                if result['solid']:
                    print(f"  [Solid] Skipping solid cover: {image}")
                    image = ""
                else:
                    preview = result['preview']
                    if preview:
                        print(f"  [Preview] {len(preview)} bytes from {image}")

            items.append({
                'id': f"devto-{article['id']}",
                'title': decode_entities(article['title']),
                'desc': f"By {article['user']['name']} | {article['reading_time_minutes']} min read",
                'tag': 'tutorial',
                'published': article['published_at'],
                'order': kept + 1,
                'body': body,
                'url': article['url'],
                'image': image,
                'preview': preview,
                'color': SOURCE_COLORS['devto'],
            })
            kept += 1

        print(f"Fetched {len(items)} Dev.to items (skipped {skipped}).")
        return items
    except Exception as e:
        print(f"Error fetching Dev.to: {type(e).__name__}: {e}")
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
                'title': decode_entities(post.get('title', 'Untitled')),
                'desc': f"Source: {post.get('source', {}).get('name', 'daily.dev')}",
                'tag': 'ai',
                'published': post.get('createdAt', ''),
                'url': post.get('url', ''),
                'summary': post.get('summary', ''),
                'image': post.get('image', '') or '',
                'color': SOURCE_COLORS['dailydev'],
            })

        final = []
        for item in raw_items:
            body = item.get('summary', '') or ''
            if not body.strip():
                body, image, preview = prepare_body(item['url'], item['title'])
                if body is None:
                    continue
                if not item.get('image'):
                    item['image'] = image
                item['preview'] = preview
            else:
                body = strip_title_from_body(body, item['title'])
                body = trim_to_prose_region(body)
                if not looks_like_article(body):
                    print(f"  [Drop] daily.dev summary too short: {item['url']}")
                    continue

                preview = ""
                if item.get('image'):
                    result = analyze_image(
                        item['image'], referer=item.get('url'))
                    if result['solid']:
                        print(f"  [Solid] Skipping solid cover: {item['image']}")
                        item['image'] = ""
                    else:
                        preview = result['preview']
                        if preview:
                            print(f"  [Preview] {len(preview)} bytes from {item['image']}")
                item['preview'] = preview

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

        for i, item in enumerate(root.findall('.//item')[:30]):
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
                'color': SOURCE_COLORS['mitnews'],
            })

        final = []
        for item in raw_items:
            body, image, preview = prepare_body(item['url'], item['title'])
            if body is None:
                continue
            item['body'] = body
            item['image'] = image
            item['preview'] = preview
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

        image = meta.get('image', '')
        preview = ""
        if image:
            result = analyze_image(image)
            if result['solid']:
                print(f"  [Solid] Solid local image, treated as no image: {image}")
                image = ""
            else:
                preview = result['preview']

        items.append({
            'id': item_id,
            'title': decode_entities(meta.get('title', item_id)),
            'desc': decode_entities(meta.get('desc', '')),
            'tag': meta.get('tag', segment.rstrip('s')),
            'published': meta.get('date', ''),
            'order': order,
            'body': body.lstrip('\n'),
            'image': image,
            'preview': preview,
            'color': meta.get('color', '#333333'),
        })
    items.sort(key=lambda x: (x['order'], x['id']))
    return items


# ============================================================
# FEED WRITE WITH RETENTION
# ============================================================

def _body_path_for(segment, item_id):
    safe = re.sub(r'[^A-Za-z0-9_\-]', '_', item_id)
    return os.path.join(FEEDS_DIR, 'bodies', segment, safe + '.md')


def build_feed_with_retention(segment, new_items):
    """Merge new items with the previous feed, prune by age,
    write bodies to disk, write the metadata-only feed JSON.
    Returns the final item count."""
    feed_path = os.path.join(FEEDS_DIR, segment + '.json')
    bodies_dir = os.path.join(FEEDS_DIR, 'bodies', segment)
    os.makedirs(bodies_dir, exist_ok=True)

    gitkeep_path = os.path.join(bodies_dir, '.gitkeep')
    if not os.path.isfile(gitkeep_path):
        try:
            with open(gitkeep_path, 'w', encoding='utf-8') as f:
                f.write('')
        except Exception:
            pass

    prev_items = []
    if os.path.isfile(feed_path):
        try:
            with open(feed_path, 'r', encoding='utf-8') as f:
                prev_items = json.load(f).get('items', []) or []
        except Exception:
            prev_items = []

    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

    seen = set()
    merged = []

    for item in new_items:
        iid = item.get('id')
        if not iid or iid in seen:
            continue
        seen.add(iid)
        merged.append(item)

    for item in prev_items:
        iid = item.get('id')
        if not iid or iid in seen:
            continue
        pub = item.get('published', '')
        if pub:
            try:
                dt = datetime.fromisoformat(pub.replace('Z', '+00:00'))
                if dt < cutoff:
                    continue
            except Exception:
                pass
        seen.add(iid)
        merged.append(item)

    for item in merged:
        body = item.pop('body', '') or ''
        if not body:
            continue
        path = _body_path_for(segment, item['id'])
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(body)
        except Exception as e:
            print(f"  [Body] Write failed for {item['id']}: {e}")

    live_ids = set()
    for item in merged:
        live_ids.add(re.sub(r'[^A-Za-z0-9_\-]', '_', item.get('id', '')))
    try:
        for fn in os.listdir(bodies_dir):
            if fn == '.gitkeep':
                continue
            if not fn.endswith('.md'):
                continue
            stem = fn[:-3]
            if stem not in live_ids:
                try:
                    os.remove(os.path.join(bodies_dir, fn))
                except Exception:
                    pass
    except Exception:
        pass

    feed = {
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'items': merged,
    }

    with open(feed_path, 'w', encoding='utf-8') as f:
        json.dump(feed, f, indent=2, ensure_ascii=False)
        f.write('\n')

    return len(merged)


# ============================================================
# MAIN
# ============================================================

def main():
    if not HAS_TRAFILATURA:
        print("WARNING: trafilatura is not installed. Dual-pipeline mask will fall back to readability.")
    if not HAS_PIL:
        print("WARNING: Pillow is not installed. Preview generation disabled.")

    os.makedirs(FEEDS_DIR, exist_ok=True)
    any_built = False

    for segment in SEGMENTS:
        local_items = build_segment_from_markdown(segment)
        live_items = []

        if segment == 'news':
            live_items = (
                fetch_hacker_news()
                + fetch_lobsters()
                + fetch_i_programmer()
                + fetch_mit_news()
                + fetch_daily_dev()
            )
        elif segment == 'tutorials':
            live_items = fetch_devto_full()

        new_items = live_items + local_items

        count = build_feed_with_retention(segment, new_items)
        if count > 0:
            print(f'wrote {FEEDS_DIR}/{segment}.json ({count} items)')
            any_built = True

    if not any_built:
        print('no source directories found; nothing written')


if __name__ == '__main__':
    main()
