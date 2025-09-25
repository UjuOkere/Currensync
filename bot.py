import os
import json
import datetime
import feedparser

# -------------------------------
# CONFIG
# -------------------------------
BLOG_FOLDER = "blog"
BACKUP_FOLDER = os.path.join(BLOG_FOLDER, "backups")
DATA_FILE = "blogdata.json"

RSS_FEEDS = {
    "Linda Ikeji": "https://www.lindaikejisblog.com/feed",
    "BellaNaija": "https://www.bellanaija.com/feed",
    "PulseNG": "https://www.pulse.ng/entertainment/rss",
}

MAX_POSTS = 20  # limit JSON size

# -------------------------------
# HELPERS
# -------------------------------
def ensure_dirs():
    os.makedirs(BLOG_FOLDER, exist_ok=True)
    os.makedirs(BACKUP_FOLDER, exist_ok=True)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    if os.path.exists(DATA_FILE):
        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_file = os.path.join(BACKUP_FOLDER, f"blogdata_{ts}.json")
        os.rename(DATA_FILE, backup_file)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def sanitize_filename(title):
    return "".join(c if c.isalnum() else "-" for c in title).strip("-").lower()

def create_post_html(post_num, title, summary, link, source):
    filename = os.path.join(BLOG_FOLDER, f"post{post_num}.html")
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{summary}">
  <meta name="keywords" content="celebrity, gossip, news, {source}">
  <link rel="stylesheet" href="../styles.css">

  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
</head>
<body>
  <h1>{title}</h1>
  <p><em>Source: {source}</em></p>
  <article>{summary}</article>
  <p><a href="{link}" target="_blank">Read full story</a></p>

  <!-- AdSense Ad -->
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="ca-pub-6539693262305451"
       data-ad-slot="8720273670"
       data-ad-format="auto"></ins>
  <script>
       (adsbygoogle = window.adsbygoogle || []).push({});
  </script>
</body>
</html>"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

def scrape_rss():
    all_posts = []
    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:  # limit per source
            post = {
                "title": entry.title,
                "date": entry.get("published", str(datetime.date.today())),
                "author": source,
                "slug": f"{BLOG_FOLDER}/post{len(all_posts)+1}.html",
                "summary": entry.get("summary", ""),
                "source_url": entry.link,
            }
            all_posts.append(post)
    return all_posts

def main():
    ensure_dirs()
    old_data = load_data()
    scraped_posts = scrape_rss
