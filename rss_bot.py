import feedparser
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup

# === CONFIGURATION ===
RSS_FEEDS = [
    "https://techcrunch.com/feed/",                         
    "https://www.nairametrics.com/feed/",                   
    "https://www.tmz.com/rss.xml",                          
    "https://www.lindaikejisblog.com/feeds/posts/default?alt=rss"  
]

BLOG_JSON = "blogdata.json"
POSTS_DIR = "posts"
AUTHOR = "CurrenSync.vip"

# Load existing blogdata.json
if os.path.exists(BLOG_JSON):
    with open(BLOG_JSON, "r", encoding="utf-8") as f:
        blog_data = json.load(f)
else:
    blog_data = []

# Determine next post number
existing_posts = [int(item["slug"].replace("blog/post","").replace(".html","")) for item in blog_data]
next_post_num = max(existing_posts, default=0) + 1

added_posts = []

for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:5]:  # Limit to 5 latest entries per feed
        title = entry.title.strip()
        link = entry.link
        summary_html = getattr(entry, "summary", "")
        summary_text = BeautifulSoup(summary_html, "html.parser").get_text()[:300]  # Clean text, limit length
        date = getattr(entry, "published", datetime.utcnow().strftime("%Y-%m-%d"))
        tags = [tag.term for tag in getattr(entry, "tags", [])] if hasattr(entry, "tags") else []

        # Attempt to extract image from RSS entry
        image_url = ""
        if hasattr(entry, "media_content") and entry.media_content:
            image_url = entry.media_content[0]["url"]
        elif hasattr(entry, "links"):
            for l in entry.links:
                if l.get("type", "").startswith("image"):
                    image_url = l["href"]
                    break

        # SEO metadata
        meta_description = summary_text
        keywords = tags if tags else [word for word in title.split() if len(word) > 3]

        slug = f"blog/post{next_post_num}.html"

        # Skip duplicates by title or link
        if any(post["title"] == title or post.get("link","") == link for post in blog_data):
            continue

        # Append to JSON
        blog_data.append({
            "title": title,
            "date": date,
            "author": AUTHOR,
            "slug": slug,
            "summary": summary_text,
            "tags": tags,
            "image": image_url,
            "meta_description": meta_description,
            "keywords": keywords,
            "link": link
        })

        # Generate HTML post
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <meta name="description" content="{meta_description}">
          <meta name="keywords" content="{', '.join(keywords)}">
          <title>{title}</title>
          <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 700px; margin: auto; }}
            img {{ max-width: 100%; height: auto; margin: 20px 0; }}
            h1 {{ color: #c00; }}
            a.button {{ display: inline-block; padding: 10px 15px; background: #c00; color: #fff; text-decoration: none; border-radius: 5px; }}
          </style>
        </head>
        <body>
          <h1>{title}</h1>
          <p><em>By {AUTHOR} | {date}</em></p>
          {f'<img src="{image_url}" alt="Featured Image">' if image_url else ''}
          <p>{summary_text}</p>
          <p><a href="{link}" class="button">Read Full Article</a></p>
        </body>
        </html>
        """

        os.makedirs(POSTS_DIR, exist_ok=True)
        with open(f"{POSTS_DIR}/post{next_post_num}.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        added_posts.append(title)
        next_post_num += 1

# Write back JSON
with open(BLOG_JSON, "w", encoding="utf-8") as f:
    json.dump(blog_data, f, indent=2)

print(f"Added {len(added_posts)} new posts: {added_posts}")
