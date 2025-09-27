import json
import os
import feedparser
from datetime import datetime

# Paths
DATA_FILE = "blogdata.json"
POSTS_DIR = "posts"

# Ensure posts directory exists
os.makedirs(POSTS_DIR, exist_ok=True)

# RSS feeds
RSS_FEEDS = [
    "https://lindaikejisblog.com/feed/",
    "https://www.gistlover.com/feed/",
    "https://www.bellanaija.com/feed/",
    "https://www.tmz.com/rss.xml"
]

# Load existing JSON data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            blogdata = json.load(f)
        except json.JSONDecodeError:
            blogdata = []
else:
    blogdata = []

# Find the last post number (default to 15 if none exist)
if blogdata:
    last_slug = blogdata[-1]["slug"]
    last_post_num = int(last_slug.replace("blog/post", "").replace(".html", ""))
else:
    last_post_num = 15

new_posts = []

for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:2]:  # take 2 per site to avoid spam
        last_post_num += 1
        slug = f"blog/post{last_post_num}.html"
        date_str = datetime.now().strftime("%Y-%m-%d")

        post_entry = {
            "title": entry.get("title", "Untitled"),
            "date": date_str,
            "author": "CurrenSync.vip",
            "slug": slug,
            "summary": entry.get("summary", "")[:200
