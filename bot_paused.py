#!/usr/bin/env python3
# rss bot - writes posts to blogdata.json only (headless)
# safe: does not overwrite existing blogdata entries, starts counting after last postNN

import os
import json
import feedparser
from datetime import datetime
import random

# ---------- CONFIG ----------
DATA_FILE = "blogdata.json"
RSS_FEEDS = [
    "https://lindaikejisblog.com/feed/",
    "https://www.gistlover.com/feed/",
    "https://www.bellanaija.com/feed/",
    "https://www.tmz.com/rss.xml",
]
MAX_PER_RUN = 5   # max posts per run
AUTHOR = "CurrenSync.vip"
DEFAULT_START = 15  # last existing post number in your current JSON
IMAGE_POOL = [
    # Add a few generic image URLs in case feed has no image
    "https://picsum.photos/800/400?random=1",
    "https://picsum.photos/800/400?random=2",
    "https://picsum.photos/800/400?random=3",
]
# ----------------------------

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

def sanitize_text(text):
    if not text:
        return ""
    return str(text).strip()

def unique_headline(title):
    """Make headline unique by adding a catchy modifier"""
    modifiers = ["BREAKING:", "SHOCKING:", "EXCLUSIVE:", "MUST SEE:", "LATEST:"]
    return f"{random.choice(modifiers)} {title}"[:80]

def get_image(entry):
    # Try to get image from feed
    if 'media_content' in entry and entry['media_content']:
        return entry['media_content'][0].get('url', '')
    return random.choice(IMAGE_POOL)

def paraphrase(content):
    # Simple paraphrase: shuffle sentences and remove HTML tags
    import re
    sentences = re.split(r'(?<=[.!?]) +', content)
    random.shuffle(sentences)
    clean = [re.sub(r'<[^>]+>', '', s).strip() for s in sentences if s.strip()]
    return ' '.join(clean)[:1000]  # limit length

def main():
    blogdata = load_blogdata(DATA_FILE)
    last_num = find_last_post_number(blogdata)
    next_num = last_num + 1
    total_added = 0

    for feed_url in RSS_FEEDS:
        print(f"[INFO] Fetching {feed_url}")
        d = feedparser.parse(feed_url)
        entries = d.entries[:MAX_PER_RUN]  # limit per feed

        for entry in entries:
            if total_added >= MAX_PER_RUN:
                break

            title = sanitize_text(entry.get("title", ""))
            summary = sanitize_text(entry.get("summary", ""))
            if not title:
                continue

            # generate slug as before, but no actual file
            slug = f"post{next_num}.html"
            post_entry = {
                "title": unique_headline(title),
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "author": AUTHOR,
                "slug": slug,
                "summary": paraphrase(summary),
                "image": get_image(entry),
                "tags": "news, celebrity, fintech"
            }

            blogdata.append(post_entry)
            total_added += 1
            next_num += 1
            print(f"[OK] Added post {slug} → {title}")

        if total_added >= MAX_PER_RUN:
            break

    if total_added > 0:
        save_blogdata(DATA_FILE, blogdata)
        print(f"[DONE] Added {total_added} new posts in this run.")
    else:
        print("[INFO] No new posts added (feeds returned empty).")

if __name__ == "__main__":
    main()
