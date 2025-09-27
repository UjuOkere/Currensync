#!/usr/bin/env python3
# rss bot - writes posts to blog/postXX.html and appends to blogdata.json
# 5 posts per run, max 10/day with unique headlines and top images

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
MAX_PER_RUN = 5   # 5 posts per run
AUTHOR = "CurrenSync.vip"
DEFAULT_START = 15
# Fallback images for posts without feed images
IMAGE_POOL = [
    "https://images.unsplash.com/photo-1581091215361-9b9df7efbfc4?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1593642632559-0c8e6a0b3a2c?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1503264116251-35a269479413?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1511988617509-a57c8a288659?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1526045612212-70caf35c14df?auto=format&fit=crop&w=800&q=80"
]
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

# --- paraphrase content ---
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
    return " ".join(sentences[: min(len(sentences), 5)])  # keep max 5 sentences

# --- generate unique headline ---
def unique_headline(title):
    if not title:
        return "Untitled Post"
    replacements = {
        "Breaking": "Latest",
        "shocking": "Surprising",
        "reportedly": "Allegedly",
        "reveals": "Shows",
        "confirms": "Indicates",
        "drama": "Incident",
        "exclusive": "Inside Scoop",
        "fans": "followers",
        "says": "claims",
        "accuses": "calls out",
        "broke": "announced"
    }
    for k, v in replacements.items():
        title = title.replace(k, v).replace(k.lower(), v)
    
    modifiers = [" | CurrenSync Exclusive", " – Inside Scoop", " Today", ""]
    title += random.choice(modifiers)
    return title[:80]

# AdSense snippet
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

def make_html(post_entry, content_html, image_url):
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
    .content img {{ max-width: 100%; height: auto; margin-bottom: 12px; }}
  </style>
</head>
<body>
  <div class="content">
    <img src="{image_url}" alt="Post Image">
    <h1>{title}</h1>
    <div class="meta">By {author} | {date}</div>
    {ADSENSE_SNIPPET}
    {content_html}
    {ADSENSE_SNIPPET}
  </div>
</body>
</html>"""
    return html

def main():
    blogdata = load_blogdata(DATA_FILE)
    last_num = find_last_post_number(blogdata)
    next_num = last_num + 1

    new_entries = []
    total_added = 0

    for feed_url in RSS_FEEDS:
        print(f"[INFO] Fetching {feed_url}")
        d = feedparser.parse(feed_url)

        for entry in d.entries:
            if total_added >= MAX_PER_RUN:
                break

            raw_title = sanitize_text(entry.get("title", ""))
            title = unique_headline(raw_title)
            summary = sanitize_text(entry.get("summary", ""))

            # Determine image
            image_url = ""
            if "media_content" in entry:
                media = entry.media_content
                if media and len(media) > 0:
                    image_url = media[0].get("url", "")
            if not image_url:
                image_url = random.choice(IMAGE_POOL)

            slug = f"blog/post{next_num}.html"
            post_entry = {
                "title": title,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "author": AUTHOR,
                "slug": slug,
                "summary": paraphrase(summary),
                "tags": "news, celebrity, fintech"
            }

            content_html = paraphrase(entry.get("summary", "") or entry.get("content", ""))
            html_content = make_html(post_entry, content_html, image_url)

            with open(slug, "w", encoding="utf-8") as f:
                f.write(html_content)

            blogdata.append(post_entry)
            new_entries.append(post_entry)
            print(f"[OK] Wrote {slug} → {title}")
            next_num += 1
            total_added += 1

    if new_entries:
        save_blogdata(DATA_FILE, blogdata)
        print(f"[DONE] Added {len(new_entries)} new posts this run.")
    else:
        print("[INFO] No new posts added.")

if __name__ == "__main__":
    main()
