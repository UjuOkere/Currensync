#!/usr/bin/env python3
# rss bot - writes posts to blog/postXX.html and appends to blogdata.json
# includes paraphrasing + daily cap of 10 posts

import os
import json
import feedparser
from datetime import datetime
import random
import re

# ---------- CONFIG ----------
DATA_FILE = "blogdata.json"
POSTS_DIR = "blog"
RSS_FEEDS = [
    "https://lindaikejisblog.com/feed/",
    "https://www.gistlover.com/feed/",
    "https://www.bellanaija.com/feed/",
    "https://www.tmz.com/rss.xml",
]
MAX_PER_FEED = 3   # number of items to take per feed each run
AUTHOR = "CurrenSync.vip"
DEFAULT_START = 15
DAILY_CAP = 10      # maximum posts allowed per UTC day
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

def count_today_posts(blogdata):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return sum(1 for item in blogdata if item.get("date") == today)

# --- paraphrasing helper ---
def paraphrase(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)  # strip HTML tags

    replacements = {
        "Breaking": "Latest update",
        "shocking": "surprising",
        "reportedly": "allegedly",
        "reveals": "shows",
        "confirms": "indicates",
        "drama": "incident",
        "exclusive": "inside scoop",
    }
    for k, v in replacements.items():
        text = text.replace(k, v).replace(k.lower(), v)

    sentences = re.split(r'(?<=[.!?]) +', text)
    random.shuffle(sentences)
    return " ".join(sentences[: min(len(sentences), 5)])  # keep 5 sentences max

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

def make_html(post_entry, content_html):
    title = post_entry.get("title", "Untitled")
    date = post_entry.get("date", "")
    author = post_entry.get("author", AUTHOR)
    summary = post_entry.get("summary", "")

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
  </div>
  {ADSENSE_SNIPPET}
</body>
</html>"""
    return html

def main():
    blogdata = load_blogdata(DATA_FILE)
    last_num = find_last_post_number(blogdata)
    next_num = last_num + 1

    today_count = count_today_posts(blogdata)
    if today_count >= DAILY_CAP:
        print("[INFO] Daily cap reached, skipping new posts.")
        return

    new_entries = []
    for feed_url in RSS_FEEDS:
        print(f"[INFO] Fetching {feed_url}")
        d = feedparser.parse(feed_url)

        for entry in d.entries[:MAX_PER_FEED]:
            if count_today_posts(blogdata) >= DAILY_CAP:
                print("[INFO] Daily cap reached mid-run, stopping.")
                break

            title = sanitize_text(entry.get("title", ""))
            summary = sanitize_text(entry.get("summary", ""))
            if not title:
                continue

            slug = f"blog/post{next_num}.html"
            post_entry = {
                "title": title,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "author": AUTHOR,
                "slug": slug,
                "summary": paraphrase(summary),
                "tags": "news, celebrity, fintech"
            }

            content_html = paraphrase(
                entry.get("summary", "") or entry.get("content", "")
            )
            html_content = make_html(post_entry, content_html)

            with open(slug, "w", encoding="utf-8") as f:
                f.write(html_content)

            blogdata.append(post_entry)
            new_entries.append(post_entry)
            print(f"[OK] Wrote {slug} → {title}")
            next_num += 1

    if new_entries:
        save_blogdata(DATA_FILE, blogdata)
        print(f"[DONE] Added {len(new_entries)} new posts in this run.")
    else:
        print("[INFO] No new posts added (feeds returned empty or capped).")

if __name__ == "__main__":
    main()
