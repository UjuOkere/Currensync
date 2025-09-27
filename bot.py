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
    for entry in feed.entries[:2]:  # take 2 per site
        last_post_num += 1
        slug = f"blog/post{last_post_num}.html"
        date_str = datetime.now().strftime("%Y-%m-%d")

        post_entry = {
            "title": entry.get("title", "Untitled"),
            "date": date_str,
            "author": "CurrenSync.vip",
            "slug": slug,
            "summary": entry.get("summary", "")[:200] + "...",
            "tags": "news, celebrity, fintech",
        }

        # Append to JSON structure
        blogdata.append(post_entry)
        new_posts.append((slug, entry, post_entry))

        # Save HTML post
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{post_entry['title']}</title>
            <meta name="description" content="{post_entry['summary']}">
            <meta name="keywords" content="{post_entry['tags']}">

            <!-- Google AdSense -->
            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
        </head>
        <body>
            <h1>{post_entry['title']}</h1>
            <p><em>By {post_entry['author']} on {post_entry['date']}</em></p>

            <!-- AdSense Banner -->
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="ca-pub-6539693262305451"
                 data-ad-slot="8720273670"
                 data-ad-format="auto"></ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({});
            </script>

            <div>
                {entry.get("summary", "")}
                <br>
                <a href="{entry.get("link", "#")}" target="_blank">Read full story</a>
            </div>

            <!-- Bottom AdSense Banner -->
            <ins class="adsbygoogle"
                 style="display:block; margin-top:20px"
                 data-ad-client="ca-pub-6539693262305451"
                 data-ad-slot="8720273670"
                 data-ad-format="auto"></ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </body>
        </html>
        """

        with open(slug.replace("blog/", ""), "w", encoding="utf-8") as
