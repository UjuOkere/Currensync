import os
import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ----------------------------
# Blog & File Config
# ----------------------------
BLOG_FOLDER = "blog"
DATA_FILE = os.path.join(BLOG_FOLDER, "blogdata.json")

# Where to scrape from
SOURCES = {
    "Nairaland": "https://www.nairaland.com/",
    "BellaNaija": "https://www.bellanaija.com/",
    "Gistlover": "https://www.gistlover.com/",
    "LindaIkeji": "https://www.lindaikejisblog.com/"
}

# HTML template for new posts
POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{summary}">
  <meta name="keywords" content="{tags}">
  <link rel="stylesheet" href="../styles.css">
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6539693262305451" crossorigin="anonymous"></script>
</head>
<body>
  <article class="post">
    <h1>{title}</h1>
    <p><em>By {author} | {date}</em></p>
    <img src="{image}" alt="{title}" style="max-width:100%; border-radius:10px;">
    <div>{content}</div>
  </article>
  <!-- Ad block -->
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="ca-pub-6539693262305451"
       data-ad-slot="8720273670"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</body>
</html>
"""

# ----------------------------
# Helper Functions
# ----------------------------

def get_last_post_number():
    """Check blog folder for last post number (postX.html)."""
    files = os.listdir(BLOG_FOLDER)
    numbers = []
    for f in files:
        match = re.match(r"post(\d+)\.html", f)
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers) if numbers else 0

def load_blogdata():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_blogdata(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def fetch_site(url):
    """Fetch a page and return soup."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def scrape_sources():
    """Scrape each source and return list of posts."""
    posts = []

    # Example: scrape headlines from each source
    for name, url in SOURCES.items():
        soup = fetch_site(url)
        if not soup:
            continue

        if name == "Nairaland":
            items = soup.select("td a[href^='/']")[:1]
        elif name == "BellaNaija":
            items = soup.select("h2.entry-title a")[:1]
        elif name == "Gistlover":
            items = soup.select("h3.post-title a")[:1]
        elif name == "LindaIkeji":
            items = soup.select("h3.post-title a")[:1]
        else:
            items = []

        for a in items:
            title = a.get_text(strip=True)
            link = a.get("href")
            summary = f"Latest update from {name}: {title}"
            posts.append({
                "title": title,
                "author": name,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "summary": summary,
                "link": link,
                "content": f"<p>{summary}</p><p>Read more on <a href='{link}' target='_blank'>{name}</a></p>",
                "image": "https://via.placeholder.com/600x400.png?text=" + name,
                "tags": name
            })

    return posts

def create_post_file(post, number):
    """Save post as HTML file."""
    filename = f"post{number}.html"
    filepath = os.path.join(BLOG_FOLDER, filename)

    html = POST_TEMPLATE.format(
        title=post["title"],
        summary=post["summary"],
        tags=post["tags"],
        author=post["author"],
        date=post["date"],
        image=post["image"],
        content=post["content"]
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filename

# ----------------------------
# Main Bot Logic
# ----------------------------
def main():
    last_num = get_last_post_number()
    print(f"Last post number = {last_num}")

    blogdata = load_blogdata()
    scraped = scrape_sources()

    new_entries = []
    for i, post in enumerate(scraped, start=1):
        new_num = last_num + i
        filename = create_post_file(post, new_num)

        entry = {
            "title": post["title"],
            "date": post["date"],
            "author": post["author"],
            "slug": f"blog/{filename}",
            "summary": post["summary"],
            "tags": post["tags"]
        }
        new_entries.append(entry)

    if new_entries:
        blogdata = new_entries + blogdata  # prepend new posts
        save_blogdata(blogdata)
        print(f"Added {len(new_entries)} new posts.")
    else:
        print("No new posts scraped.")

if __name__ == "__main__":
    main()
