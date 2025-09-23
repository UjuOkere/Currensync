import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Paths
BLOGDATA_PATH = "blogdata.json"
POSTS_FOLDER = "blog/posts"

# Ensure posts folder exists
os.makedirs(POSTS_FOLDER, exist_ok=True)

# Sources
SOURCES = {
    "BellaNaija": "https://www.bellanaija.com/entertainment/",
    "Naijaloaded": "https://www.naijaloaded.com.ng/entertainment",
}

# -------- SCRAPERS -------- #
def fetch_bellanaija():
    posts = []
    try:
        r = requests.get(SOURCES["BellaNaija"], timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        articles = soup.select("h3.entry-title a")[:5]
        for a in articles:
            title = a.get_text(strip=True)
            link = a["href"]
            img_tag = soup.find("img")
            img = img_tag["src"] if img_tag else "https://via.placeholder.com/600x400?text=BellaNaija"
            posts.append({"title": title, "url": link, "thumbnail": img})
    except Exception as e:
        print("BellaNaija error:", e)
    return posts

def fetch_naijaloaded():
    posts = []
    try:
        r = requests.get(SOURCES["Naijaloaded"], timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        articles = soup.select("h2.post-title a")[:5]
        for a in articles:
            title = a.get_text(strip=True)
            link = a["href"]
            img_tag = soup.find("img")
            img = img_tag["src"] if img_tag else "https://via.placeholder.com/600x400?text=Naijaloaded"
            posts.append({"title": title, "url": link, "thumbnail": img})
    except Exception as e:
        print("Naijaloaded error:", e)
    return posts

# -------- UTILITIES -------- #
def load_blogdata():
    if os.path.exists(BLOGDATA_PATH):
        with open(BLOGDATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_blogdata(data):
    with open(BLOGDATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_next_post_number():
    existing = os.listdir(POSTS_FOLDER)
    nums = [int(f.replace("post", "").replace(".html", "")) for f in existing if f.startswith("post")]
    return max(nums) + 1 if nums else 1

def create_post_html(post_number, title, content, img, tags):
    filename = os.path.join(POSTS_FOLDER, f"post{post_number}.html")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{title}">
  <meta name="keywords" content="{', '.join(tags)}">
  <link rel="stylesheet" href="../styles.css">
  <!-- AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6539693262305451" crossorigin="anonymous"></script>
</head>
<body>
  <article>
    <h1>{title}</h1>
    <img src="{img}" alt="{title}" style="width:100%; border-radius:10px;">
    <p>{content}</p>
  </article>
  <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6539693262305451" data-ad-slot="8720273670" data-ad-format="auto"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</body>
</html>""")

# -------- MAIN -------- #
def main():
    blogdata = load_blogdata()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    new_posts = fetch_bellanaija() + fetch_naijaloaded()
    new_posts = new_posts[:10]  # max 10/day

    for post in new_posts:
        # prevent duplicates
        if any(entry["title"] == post["title"] for entry in blogdata):
            continue

        post_number = get_next_post_number()
        tags = ["celebrity", "gossip", "Nigeria"]

        create_post_html(
            post_number,
            post["title"],
            f"Full story here: <a href='{post['url']}' target='_blank'>Read more</a>",
            post["thumbnail"],
            tags
        )

        blog_entry = {
            "title": post["title"],
            "date": today,
            "author": "CurrenSync.vip",
            "slug": f"blog/posts/post{post_number}.html",
            "summary": post["title"],
            "thumbnail": post["thumbnail"],
            "tags": tags
        }
        blogdata.insert(0, blog_entry)

    save_blogdata(blogdata)
    print(f"Added {len(new_posts)} posts.")

if __name__ == "__main__":
    main()
