import os
import re
import json
import requests
import feedparser
from datetime import datetime

# ----------------------------
# Blog & File Config
# ----------------------------
BLOG_FOLDER = "blog"                   # HTML posts live here
DATA_FILE = "blogdata.json"           # JSON tracker stays at root
BACKUP_FOLDER = os.path.join("blog", "backups")

# scraping limits
MAX_TOTAL = 8

# RSS feed sources
SOURCES = {
    "BellaNaija": "https://www.bellanaija.com/feed/",
    "Linda Ikeji": "https://www.lindaikejisblog.com/feed/",
    "Gistlover": "https://www.gistlover.com/feed/",
    "Nairaland": "https://www.nairaland.com/feed/"
}

# Post HTML template
POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{summary}" />
  <meta name="author" content="CurrenSync.vip" />
  <link rel="canonical" href="https://currensync.vip/blog/{filename}" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6539693262305451" crossorigin="anonymous"></script>
  <style>
    body {{
      font-family: Arial, sans-serif;
      padding: 20px;
      background: #f5f5f5;
      color: #333;
      line-height: 1.7;
      max-width: 800px;
      margin: auto;
    }}
    h1 {{ color: #0c2d57; }}
    .ads {{ margin: 2rem 0; text-align: center; }}
    a {{ color: #0c2d57; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p><em>By {author} | Updated {human_date}</em></p>

  <div class="ads">
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="ca-pub-6539693262305451"
         data-ad-slot="8720273670"
         data-ad-format="auto"
         data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({{});</script>
  </div>

  <img src="{image}" alt="{title}" style="width:100%; border-radius:10px; margin-bottom:1rem;">
  <div>{content}</div>

  <div class="ads" style="margin-top:2rem;">
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="ca-pub-6539693262305451"
         data-ad-slot="8720273670"
         data-ad-format="auto"
         data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({{});</script>
  </div>

  <footer style="margin-top: 3rem; font-size: 0.9rem; text-align: center;">
    &copy; {year} CurrenSync.vip — Smarter Currency, Smarter Travel
  </footer>
</body>
</html>
"""

# ----------------------------
# Helpers: filesystem & JSON
# ----------------------------
def ensure_dirs():
    os.makedirs(BLOG_FOLDER, exist_ok=True)
    os.makedirs(BACKUP_FOLDER, exist_ok=True)

def backup_file(path):
    if not os.path.exists(path):
        return None
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    base = os.path.basename(path)
    dest = os.path.join(BACKUP_FOLDER, f"{base}.{ts}.bak")
    try:
        with open(path, "rb") as src, open(dest, "wb") as dst:
            dst.write(src.read())
        return dest
    except Exception as e:
        print(f"⚠️ Backup failed: {e}")
        return None

def atomic_write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

def load_blogdata():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            backup_file(DATA_FILE)
            return []
        return data
    except Exception:
        backup_file(DATA_FILE)
        return []

def save_blogdata(data):
    if os.path.exists(DATA_FILE):
        backup_file(DATA_FILE)
    atomic_write_json(DATA_FILE, data)

def get_last_post_number():
    try:
        files = os.listdir(BLOG_FOLDER)
    except FileNotFoundError:
        return 0
    nums = [int(re.match(r"post(\d+)\.html$", f).group(1)) for f in files if re.match(r"post(\d+)\.html$", f)]
    return max(nums) if nums else 0

def escape_html(s):
    if not isinstance(s, str):
        return s
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))

# ----------------------------
# Create post HTML file
# ----------------------------
def create_post_file(post, number):
    filename = f"post{number}.html"
    path = os.path.join(BLOG_FOLDER, filename)
    html = POST_TEMPLATE.format(
        title=escape_html(post["title"]),
        summary=escape_html(post.get("summary","")),
        filename=filename,
        author=escape_html(post.get("author","CurrenSync.vip")),
        human_date=datetime.utcnow().strftime("%B %Y"),
        image=post.get("image",""),
        content=post.get("content",""),
        year=datetime.utcnow().year
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return filename

# ----------------------------
# Main
# ----------------------------
def main():
    ensure_dirs()
    last_num = get_last_post_number()
    existing = load_blogdata()
    existing_urls = {e.get("source_url") for e in existing if isinstance(e, dict) and e.get("source_url")}
    scraped = []

    # Fetch posts from RSS feeds
    for source, feed_url in SOURCES.items():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:2]:  # limit per source
            if entry.link in existing_urls:
                continue
            post = {
                "title": entry.title,
                "url": entry.link,
                "author": source,
                "summary": entry.get("summary", entry.title),
                "content": entry.get("description", entry.title),
                "image": entry.get("image", "https://via.placeholder.com/600x400.png?text=" + source),
                "tags": ["celebrity", "gossip", "Nigeria"]
            }
            scraped.append(post)
            if len(scraped) >= MAX_TOTAL:
                break
        if len(scraped) >= MAX_TOTAL:
            break

    if not scraped:
        print("⚠️ No new posts found from RSS feeds.")
        return

    new_entries = []
    for i, post in enumerate(scraped, start=1):
        new_num = last_num + i
        filename = create_post_file(post, new_num)
        entry = {
            "title": post["title"],
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "author": post["author"],
            "slug": f"blog/{filename}",
            "source_url": post["url"],
            "summary": post.get("summary",""),
            "thumbnail": post.get("image",""),
            "tags": post.get("tags")
        }
        new_entries.append(entry)

    combined = new_entries + existing
    save_blogdata(combined)

if __name__ == "__main__":
    main()
