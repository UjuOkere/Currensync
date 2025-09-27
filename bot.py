#!/usr/bin/env python3
# rss bot - writes posts to posts/ and appends to blogdata.json
# safe: does not overwrite existing blogdata entries, starts counting after last postNN.html

import os
import json
import feedparser
from datetime import datetime

# ---------- CONFIG ----------
DATA_FILE = "blogdata.json"
POSTS_DIR = "posts"
RSS_FEEDS = [
    "https://lindaikejisblog.com/feed/",
    "https://www.gistlover.com/feed/",
    "https://www.bellanaija.com/feed/",
    "https://www.tmz.com/rss.xml",
]
MAX_PER_FEED = 2   # number of items to take per feed each run
AUTHOR = "CurrenSync.vip"
DEFAULT_START = 15  # last existing post number in your current JSON (you said post15 exists)
# ----------------------------

os.makedirs(POSTS_DIR, exist_ok=True)

def load_blogdata(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not load {path}: {e}")
        return []

def save_blogdata(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Could not write {path}: {e}")
        return False

def find_last_post_number(blogdata):
    nums = []
    for item in blogdata:
        slug = item.get("slug", "")
        if "post" in slug and slug.endswith(".html"):
            try:
                num = int(slug.split("post")[-1].split(".html")[0])
                nums.append(num)
            except Exception:
                continue
    return max(nums) if nums else DEFAULT_START

# AdSense snippet kept as plain string (no f-string braces conflict)
ADSENSE_SNIPPET = """
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-6539693262305451"
     data-ad-slot="8720273670"
     data-ad-format="auto"></ins>
<script>
    (adsbygoogle = window.adsbygoogle || []).push({});
</script>
"""

def sanitize_text(text):
    if not text:
        return ""
    return str(text).strip()

def make_html(post_entry, original_entry):
    title = post_entry.get("title", "Untitled")
    date = post_entry.get("date", "")
    author = post_entry.get("author", AUTHOR)
    summary = post_entry.get("summary", "")
    link = original_entry.get("link", "#")
    content_html = original_entry.get("summary", "") or original_entry.get("content", "") or ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{summary}" />
  <meta name="keywords" content="{post_entry.get('tags','')}" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
  <style>
    body {{
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.6;
      padding: 18px;
      max-width: 800px;
      margin: auto;
      background: #fdfdfd;
    }}
    h1 {{ color: #c00; }}
    .meta {{ font-size: 0.9em; color: #666; }}
    .content img {{ max-width: 100%; height: auto; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="meta">By {author} | {date}</div>
  {ADSENSE_SNIPPET}
  <div class="content">
    {content_html}
    <p><a href="{link}" target="_blank">Read original source</a></p>
  </div>
  {ADSENSE_SNIPPET}
</body>
</html>"""
    return html

def main():
    blogdata = load_blogdata(DATA_FILE)
    last_num = find_last_post_number(blogdata)
    next_num = last_num + 1

    new_entries = []
    for feed_url in RSS_FEEDS:
        print(f"[INFO] Fetching {feed_url}")
        d = feedparser.parse(feed_url)
        for entry in d.entries[:MAX_PER_FEED]:
            title = sanitize_text(entry.get("title", ""))
            summary = sanitize_text(entry.get("summary", ""))
            if not title:
                continue

            slug = f"posts/post{next_num}.html"
            post_entry = {
                "title": title,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "author": AUTHOR,
                "slug": slug,
                "summary": summary,
                "tags": "news, celebrity, fintech"
            }

            # Write HTML file
            html_content = make_html(post_entry, entry)
            with open(slug, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Add to blogdata
            blogdata.append(post_entry)
            new_entries.append(post_entry)
            print(f"[OK] Wrote {slug}")
            next_num += 1

    if new_entries:
        save_blogdata(DATA_FILE, blogdata)
        print(f"[DONE] Added {len(new_entries)} new posts.")
    else:
        print("[INFO] No new posts added.")

if __name__ == "__main__":
    main()
