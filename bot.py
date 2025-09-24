import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

print("🤖 Bot started... running blog update process")

# ----------------------------
# Configuration
# ----------------------------
BLOG_FOLDER = "blog"
POSTS_FOLDER = os.path.join(BLOG_FOLDER, "posts")
BACKUP_FOLDER = os.path.join(BLOG_FOLDER, "backups")
BLOGDATA_FILE = "blogdata.json"

# Example sources (replace with real gossip/celebrity sites)
SOURCES = [
    {
        "url": "https://www.lindaikejisblog.com/",
        "base": "https://www.lindaikejisblog.com",
        "article_selector": "div.post h2 a"
    },
    {
        "url": "https://www.ghgossip.com/",
        "base": "https://www.ghgossip.com",
        "article_selector": "h3.post-title a"
    }
]

# ----------------------------
# Helpers
# ----------------------------
def ensure_dirs():
    """Ensure required directories exist."""
    print("🔹 Ensuring directories exist")
    os.makedirs(POSTS_FOLDER, exist_ok=True)
    os.makedirs(BACKUP_FOLDER, exist_ok=True)

def load_blogdata():
    """Load blogdata.json if exists, else return empty list."""
    if os.path.exists(BLOGDATA_FILE):
        with open(BLOGDATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ blogdata.json corrupted, starting fresh.")
                return []
    return []

def save_blogdata(data):
    """Save updated blogdata.json"""
    with open(BLOGDATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def fetch_articles():
    """Scrape articles from all sources."""
    articles = []
    for source in SOURCES:
        print(f"🌍 Scraping {source['url']}")
        try:
            r = requests.get(source["url"], timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")
            links = soup.select(source["article_selector"])
            for link in links[:5]:  # limit for now
                title = link.get_text(strip=True)
                href = link.get("href")
                if href and not href.startswith("http"):
                    href = source["base"] + href
                articles.append({
                    "title": title,
                    "url": href,
                    "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "source_url": source["url"]
                })
        except Exception as e:
            print(f"❌ Error scraping {source['url']}: {e}")
    return articles

def generate_post_html(article, index):
    """Generate HTML for a single post."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{article['title']}</title>
  <meta name="description" content="{article['title']} - Auto scraped post">
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <h1>{article['title']}</h1>
  <p><em>Source: <a href="{article['url']}">{article['url']}</a></em></p>
  <p>Date: {article['date']}</p>

  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
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

# ----------------------------
# Main flow
# ----------------------------
def main():
    ensure_dirs()
    blogdata = load_blogdata()
    existing_titles = {p["title"] for p in blogdata}

    new_articles = fetch_articles()
    count = 0

    for article in new_articles:
        if article["title"] in existing_titles:
            continue  # skip duplicates
        index = len(blogdata) + 1
        filename = f"post{index}.html"
        filepath = os.path.join(POSTS_FOLDER, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(generate_post_html(article, index))

        blogdata.append({
            "title": article["title"],
            "date": article["date"],
            "author": "CurrenSync Bot",
            "slug": f"{POSTS_FOLDER}/{filename}",
            "summary": article["title"],
            "tags": "auto, gossip, news",
            "source_url": article["url"]
        })
        count += 1

    save_blogdata(blogdata)
    print(f"✅ Added {count} new posts.")

if __name__ == "__main__":
    main()
