#!/usr/bin/env python3
"""
Build static JSON feeds from markdown sources.

Reads sources/<segment>/*.md, writes feeds/<segment>.json.

Each source file must have a frontmatter block:

    ---
    title: ...
    desc: ...
    tag: news
    date: 2026-09-29T12:00:00Z
    order: 1
    ---

Only `title` is required. Missing fields get sensible defaults.
"""

import json
import os
import glob
from datetime import datetime, timezone


SEGMENTS = ['news', 'tutorials', 'games', 'docs']
SOURCES_DIR = 'sources'
FEEDS_DIR = 'feeds'


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


def build_segment(segment):
    source_dir = os.path.join(SOURCES_DIR, segment)
    if not os.path.isdir(source_dir):
        return None

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

    return {
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'items': items,
    }


def main():
    os.makedirs(FEEDS_DIR, exist_ok=True)
    any_built = False

    for segment in SEGMENTS:
        feed = build_segment(segment)
        if feed is None:
            continue

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
