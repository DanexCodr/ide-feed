#!/usr/bin/env python3
"""
Build static JSON feeds.
1. Reads local markdown sources.
2. Fetches live news from Hacker News API.
3. Fetches live tutorials from Dev.to API.
"""

import json
import os
import glob
import urllib.request
import urllib.parse
from datetime import datetime, timezone

SEGMENTS = ['news', 'tutorials', 'games', 'docs']
SOURCES_DIR = 'sources'
FEEDS_DIR = 'feeds'

# --- 1. EXISTING MARKDOWN LOGIC ---
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

# --- 2. LIVE NEWS FETCHERS ---
def fetch_hacker_news():
    """Fetches top stories from the official Hacker News API."""
    print("Fetching Hacker News...")
    items = []
    try:
        # Step 1: Get the IDs of the top 15 stories
        req = urllib.request.Request(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers={'User-Agent': 'DroidBuild-Agent/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            story_ids = json.loads(response.read().decode('utf-8'))

        # Step 2: Fetch details for each story
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

            # Convert Unix timestamp to ISO 8601
            pub_date = datetime.fromtimestamp(time_unix, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

            # Format the card description
            desc = f"By {by} | {score} points | {descendants} comments"

            # Format the viewer body
            if text:
                # It's a text post (Ask HN, Show HN, etc.)
                body = text + f"\n\n[Discuss on Hacker News](https://news.ycombinator.com/item?id={story_id})"
            else:
                # It's a link post
                body = f"[Read the full article here]({url})\n\n[Discuss on Hacker News](https://news.ycombinator.com/item?id={story_id})"

            items.append({
                'id': f"hn-{story_id}",
                'title': title,
                'desc': desc,
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

def fetch_dev_to():
    """Fetches top tutorials from Dev.to API."""
    print("Fetching Dev.to...")
    url = "https://dev.to/api/articles?per_page=15&top=7&tag=programming"
    items = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        for i, article in enumerate(data):
            items.append({
                'id': f"devto-{article['id']}",
                'title': article['title'],
                'desc': f"By {article['user']['name']} | {article['reading_time_minutes']} min read",
                'tag': 'tutorial',
                'published': article['published_at'],
                'order': i + 1,
                'body': article['description'],
                'url': article['url']
            })
        print(f"Fetched {len(items)} Dev.to items.")
    except Exception as e:
        print(f"Error fetching Dev.to: {e}")
    return items

# --- 3. MAIN MERGE LOGIC ---
def main():
    os.makedirs(FEEDS_DIR, exist_ok=True)
    any_built = False

    for segment in SEGMENTS:
        local_items = build_segment_from_markdown(segment)
        
        live_items = []
        if segment == 'news':
            live_items = fetch_hacker_news()
        elif segment == 'tutorials':
            live_items = fetch_dev_to()
        
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
