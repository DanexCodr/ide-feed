#!/usr/bin/env python3
"""
Build static JSON feeds for DroidBuild.

This script uses a hybrid approach:
1. AI-powered curation: Google Gemini (free tier) selects the most relevant articles.
2. AI-powered extraction: Gemini converts raw HTML into clean Markdown.
3. Deterministic fallback: readability-lxml + html2text if the AI fails.
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

# ============================================================
# AI CONFIGURATION
# ============================================================
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
AI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'
AI_MODEL = 'gemini-2.5-flash'

SEGMENTS = ['news', 'tutorials', 'ai', 'research']
SOURCES_DIR = 'sources'
FEEDS_DIR = 'feeds'

# ============================================================
# AI HELPERS
# ============================================================

def ai_query(prompt, max_tokens=2048, temperature=0.2):
    """Send a query to the Gemini API and return the text response."""
    if not GEMINI_API_KEY:
        return None

    payload = {
        "model": AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    req = urllib.request.Request(
        AI_API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {GEMINI_API_KEY}',
            'Content-Type': 'application/json',
            'User-Agent': 'DroidBuild-Agent/1.0',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"  [AI Error] {e}")
        return None

def ai_select_items(items, segment, max_items=15):
    """Use AI to select the most relevant items from a list."""
    if not GEMINI_API_KEY or not items:
        return items[:max_items]

    candidates = []
    for i, item in enumerate(items):
        title = item.get('title', 'No Title')
        desc = item.get('desc', '')[:200]
        candidates.append(f"{i+1}. {title} — {desc}")
    candidate_text = "\n".join(candidates)

    prompt = f"""You are a curation assistant for a software developer news feed.
Segment: "{segment}"

Select the {max_items} most relevant and high-quality articles for professional software developers.
Prioritize programming, software engineering, AI/ML, compilers, algorithms, and systems design.
Exclude promotional content, clickbait, low-quality items, and off-topic posts.

Return ONLY a comma-separated list of item numbers (e.g., "1, 3, 5, 7"). Do not include any other text.

Candidates:
{candidate_text}"""

    response = ai_query(prompt, max_tokens=100, temperature=0.1)
    if not response:
        return items[:max_items]

    try:
        selected_indices = [int(x.strip()) - 1 for x in response.split(',') if x.strip().isdigit()]
        selected = [items[i] for i in selected_indices if 0 <= i < len(items)]
        return selected if selected else items[:max_items]
    except Exception:
        return items[:max_items]

def ai_extract_body(html, url):
    """Use AI to extract the main article content as Markdown."""
    if not GEMINI_API_KEY:
        return None

    # Truncate HTML to avoid token limits. Gemini has a huge context
    # window, but 30k characters is plenty for an article and keeps
    # responses fast.
    html_snippet = html[:30000]

    prompt = f"""You are an expert web content extractor.
Given the raw HTML of a web page, extract ONLY the main article content.
Remove navigation, sidebars, footers, ads, comments, and any non-article elements.
Convert the extracted content to clean Markdown.
Preserve headings, paragraphs, lists, tables, code blocks, bold, and italic formatting.

Return ONLY the Markdown. Do not include any commentary or explanations.
Article URL: {url}

Raw HTML:
{html_snippet}"""

    return ai_query(prompt, max_tokens=4096, temperature=0.0)

# ============================================================
# DETERMINISTIC FALLBACK EXTRACTION
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

def fallback_extract(url):
    """Readability + html2text. Used only when AI extraction fails."""
    try:
        html = fetch_html(url)
        summary = Document(html).summary()
        h = html2text.HTML2Text()
        h.body_width = 0
        h.ignore_images = True
        h.ignore_emphasis = False
        h.protect_links = True
        return h.handle(summary).strip()
    except Exception:
        return ""

def extract_article(url):
    """Fetch and extract an article using AI, falling back to readability."""
    if not url:
        return ""
    
    html = ""
    try:
        html = fetch_html(url)
    except Exception as e:
        print(f"  [Fetch Error] {url}: {e}")
        return ""

    # 1. Primary: AI Extraction
    if GEMINI_API_KEY:
        print(f"  [AI] Extracting {url}")
        ai_body = ai_extract_body(html, url)
        if ai_body:
            return ai_body

    # 2. Fallback: Readability + html2text
    print(f"  [Fallback] Extracting {url}")
    return fallback_extract(url)

# ============================================================
# FETCHERS (WITH AI CURATION)
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

        # Fetch top 30 to give the AI something to curate
        for i, story_id in enumerate(story_ids[:30]):
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

            # For AI curation, we just need title and score/desc.
            raw_items.append({
                'id': f"hn-{story_id}",
                'title': title,
                'desc': f"By {by} | {score} points | {descendants} comments",
                'tag': 'news',
                'published': pub_date,
                'url': url,
                'text': text
            })

        # AI Curation
        selected = ai_select_items(raw_items, 'news', max_items=15)
        
        # AI Extraction for selected items
        for item in selected:
            if item.get('text'):
                item['body'] = item['text'] + f"\n\n[Discuss on Hacker News](https://news.ycombinator.com/item?id={item['id'].replace('hn-', '')})"
            else:
                item['body'] = extract_article(item['url'])
                if not item['body']:
                    item['body'] = f"[Read the full article]({item['url']})"
                item['body'] += f"\n\n[Discuss on Hacker News](https://news.ycombinator.com/item?id={item['id'].replace('hn-', '')})"
            
            # Remove the temporary 'text' field
            item.pop('text', None)
            # Fix order
            item['order'] = selected.index(item) + 1
            
        print(f"Fetched {len(selected)} HN items.")
        return selected
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
        
        for item in selected:
            item['body'] = extract_article(item['url'])
            if not item['body']:
                item['body'] = f"[Read the full article]({item['url']})"
            item['order'] = selected.index(item) + 1

        print(f"Fetched {len(selected)} Lobsters items.")
        return selected
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
        
        for item in selected:
            item['body'] = extract_article(item['url'])
            if not item['body']:
                item['body'] = f"[Read the full article]({item['url']})"
            item['order'] = selected.index(item) + 1

        print(f"Fetched {len(selected)} i-programmer items.")
        return selected
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
            # Dev.to already provides clean Markdown, so we skip AI extraction
            # and just use the API's body_markdown.
            detail_url = f"https://dev.to/api/articles/{article['id']}"
            req = urllib.request.Request(detail_url, headers={'User-Agent': 'DroidBuild-Agent/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                detail = json.loads(resp.read().decode('utf-8'))

            items.append({
                'id': f"devto-{article['id']}",
                'title': article['title'],
                'desc': f"By {article['user']['name']} | {article['reading_time_minutes']} min read",
                'tag': 'tutorial',
                'published': article['published_at'],
                'order': i + 1,
                'body': detail.get('body_markdown', article.get('description', '')),
                'url': article['url'],
            })
        print(f"Fetched {len(items)} Dev.to items.")
        return items
    except Exception as e:
        print(f"Error fetching Dev.to: {e}")
        return []

def fetch_daily_dev():
    print("Fetching daily.dev...")
    items = []
    token = os.environ.get('DAILY_DEV_TOKEN', '')
    if not token:
        print("  DAILY_DEV_TOKEN not set; skipping daily.dev.")
        return items

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
                'summary': post.get('summary', '')
            })

        selected = ai_select_items(raw_items, 'ai', max_items=15)
        for item in selected:
            item['body'] = item.get('summary', '')
            if not item['body']:
                item['body'] = extract_article(item['url'])
            item.pop('summary', None)
            item['order'] = selected.index(item) + 1

        print(f"Fetched {len(selected)} daily.dev items.")
        return selected
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
        
        for item in selected:
            item['body'] = extract_article(item['url'])
            if not item['body']:
                item['body'] = f"[Read the full article]({item['url']})"
            item['order'] = selected.index(item) + 1

        print(f"Fetched {len(selected)} MIT News items.")
        return selected
    except Exception as e:
        print(f"Error fetching MIT News: {e}")
        return []

# ============================================================
# MAIN
# ============================================================

def main():
    if not GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY not set. AI curation and extraction will be skipped.")
    
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

if __name__ == '__main__':
    main()
