# ide-feed

Static JSON feeds for the DroidBuild Learn page.

The app fetches `feeds/<segment>.json` from
`raw.githubusercontent.com` on launch, caches the response, and
renders it alongside the items shipped in the APK.

## How it works

- Sources live in `sources/<segment>/*.md`.
- A GitHub Action runs `tools/build_feeds.py` on every push to
  `sources/`, and every six hours.
- The script writes `feeds/<segment>.json`.
- The action commits the regenerated JSON.

No server, no build step on the client. To publish something new,
add a markdown file to `sources/news/` and push.

## Source file format

Each source file has a frontmatter block followed by markdown:

    ---
    title: DroidBuild v1.3 Released
    desc: Word wrap improvements and a new terminal.
    tag: news
    date: 2026-09-29T12:00:00Z
    order: 1
    ---

    # v1.3

    Body here.

The `id` is the filename without the `.md` extension.

## Feed format

    {
      "updated": "2026-09-29T14:00:00Z",
      "items": [
        {
          "id": "2026-09-29-v1-3-released",
          "title": "...",
          "desc": "...",
          "tag": "news",
          "published": "2026-09-29T12:00:00Z",
          "order": 1,
          "body": "# v1.3\n\n..."
        }
      ]
    }
