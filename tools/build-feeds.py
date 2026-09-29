#!/usr/bin/env python3
"""
Build static JSON feeds for DroidBuild.
Fetches from:
- Hacker News (for news)
- Lobsters (for news)
- i-programmer (for news)
- Dev.to (for tutorials)
- daily.dev (for AI)
- MIT News CSAIL (for research)
"""

import json
import os
import glob
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Use trafilatura if available for better extraction; fallback to readability
try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

from readability import Document

SEGMENTS = ['news', 'tutorials', 'ai', 'research']
SOURCES_DIR = 'sources'
FEEDS_DIR = 'feeds'

# --- Markdown Source Logic (Unchanged) ---
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

# --- Extraction Helper ---
def extract_full_text(url):
    """Fetch URL and extract main article text."""
    if not url:
        return ""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read()

        if HAS_TRAFILATURA:
            text = trafilatura.extract(html)
            if text:
                return text

        # Fallback to readability-lxml
        doc = Document(html)
        return doc.summary()
    except Exception:
        return ""

# --- Fetchers ---

def fetch_hacker_news():
    """Fetch top stories from HN API."""
    print("Fetching Hacker News...")
    items = []
    try:
        req = urllib.request.Request(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers={'User-Agent': 'DroidBuild-Agent/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            story_ids = json.loads(response.read().decode('utf-8'))

        for i, story_id in enumerate(story_ids[:15]):
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

            # Use API text for Ask HN, otherwise extract full text
            if text:
                body = text
            else:
                body = extract_full_text(url)
                if not body:
                    body = f"[Read the full article]({url})"

            items.append({
                'id': f"hn-{story_id}",
                'title': title,
                'desc': f"By {by} | {score} points | {descendants} comments",
                'tag': 'news',
                'published': pub_date,
                'order': i + 1,
                'body': body,
                'url': url
            })
        print(f"Fetched {len(items)} HN items.")
    except Exception as e:
        print(f"Error fetching HN: {e}")
    return items

def fetch_lobsters():
    """Fetch Lobsters RSS and extract full text."""
    print("Fetching Lobsters...")
    items = []
    try:
        req = urllib.request.Request(
            "https://lobste.rs/rss",
            headers={'User-Agent': 'DroidBuild-Agent/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())

        for i, item in enumerate(root.findall('.//item')[:15]):
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            description = item.find('description').text or ""

            # Try to extract full text, fallback to description
            body = extract_full_text(link)
            if not body:
                body = description

            items.append({
                'id': f"lobsters-{i}",
                'title': title,
                'desc': "Source: Lobsters",
                'tag': 'news',
                'published': pub_date,
                'order': i + 1,
                'body': body,
                'url': link
            })
        print(f"Fetched {len(items)} Lobsters items.")
    except Exception as e:
        print(f"Error fetching Lobsters: {e}")
    return items

def fetch_i_programmer():
    """Fetch i-programmer RSS and extract full text."""
    print("Fetching i-programmer...")
    items = []
    try:
        url = "https://www.i-programmer.info/component/ninjarsssyndicator/?feed_id=3&format=raw"
        req = urllib.request.Request(url, headers={'User-Agent': 'DroidBuild-Agent/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())

        for i, item in enumerate(root.findall('.//item')[:15]):
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text

            body = extract_full_text(link)
            if not body:
                body = item.find('description').text or ""

            items.append({
                'id': f"iprog-{i}",
                'title': title,
                'desc': "Source: I Programmer",
                'tag': 'news',
                'published': pub_date,
                'order': i + 1,
                'body': body,
                'url': link
            })
        print(f"Fetched {len(items)} i-programmer items.")
    except Exception as e:
        print(f"Error fetching i-programmer: {e}")
    return items

def fetch_devto_full():
    """Fetch full article bodies from Dev.to API."""
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

            items.append({
                'id': f"devto-{article['id']}",
                'title': article['title'],
                'desc': f"By {article['user']['name']} | {article['reading_time_minutes']} min read",
                'tag': 'tutorial',
                'published': article['published_at'],
                'order': i + 1,
                'body': detail.get('body_markdown', article.get('description', '')),
                'url': article['url']
            })
        print(f"Fetched {len(items)} Dev.to items.")
    except Exception as e:
        print(f"Error fetching Dev.to: {e}")
    return items

def fetch_daily_dev():
    """Fetch AI content from daily.dev API."""
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

        feed_items = data.get('data', [])
        for i, post in enumerate(feed_items[:15]):
            items.append({
                'id': f"dailydev-{post.get('id', i)}",
                'title': post.get('title', 'Untitled'),
                'desc': f"Source: {post.get('source', {}).get('name', 'daily.dev')}",
                'tag': 'ai',
                'published': post.get('createdAt', ''),
                'order': i + 1,
                'body': post.get('summary', ''),
                'url': post.get('url', '')
            })
        print(f"Fetched {len(items)} daily.dev items.")
    except Exception as e:
        print(f"Error fetching daily.dev: {e}")
    return items

def fetch_mit_news():
    """Fetch MIT CSAIL news and extract full text."""
    print("Fetching MIT News CSAIL...")
    items = []
    try:
        url = "https://news.mit.edu/topic/mitcomputer-science-and-artificial-intelligence-laboratory-csail-rss.xml"
        req = urllib.request.Request(url, headers={'User-Agent': 'DroidBuild-Agent/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())

        for i, item in enumerate(root.findall('.//item')[:15]):
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text

            # Try content:encoded first, then description
            content = item.find('content:encoded', {'content': 'http://purl.org/rss/1.0/modules/content/'})
            if content is not None and content.text:
                body = content.text
            else:
                body = item.find('description').text or ""

            items.append({
                'id': f"mit-{i}",
                'title': title,
                'desc': "Source: MIT News CSAIL",
                'tag': 'research',
                'published': pub_date,
                'order': i + 1,
                'body': body,
                'url': link
            })
        print(f"Fetched {len(items)} MIT News items.")
    except Exception as e:
        print(f"Error fetching MIT News: {e}")
    return items

# --- Main Merge Logic ---
def main():
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
