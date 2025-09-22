import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# === SETTINGS ===
BLOGDATA_PATH = "blogdata.json"          # root folder
POST_TEMPLATE_PATH = "blog/post-template.html"
BLOG_FOLDER = "blog"
AUTHOR = "CurrenSync.vip"
MAX_POSTS_PER_RUN = 10

# === HELPER FUNCTIONS ===
def load_blogdata():
    if os.path.exists(BLOGDATA_PATH):
        with open(BLOGDATA_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_blogdata(blogdata):
    with open(BLOGDATA_PATH, "w", encoding="utf-8") as f:
        json.dump(blogdata, f, indent=2)

def create_post_file(post_number, title, date, summary, content, tags, thumbnail):
    new_post_path = f"{BLOG_FOLDER}/post{post_number}.html"

    with open(POST_TEMPLATE_PATH, "r", encoding="utf-8") as template:
        html = template.read()

    html = html.replace("{{title}}", title)
    html = html.replace("{{date}}", date)
    html = html.replace("{{summary}}", summary)
    html = html.replace("{{content}}", content)
    html = html.replace("{{tags}}", ", ".join(tags))
    html = html.replace("{{thumbnail}}", thumbnail)

    with open(new_post_path, "w", encoding="utf-8") as new_post:
        new_post.write(html)
    print(f"✅ Created {new_post_path}")

# === SCRAPER FUNCTIONS ===
def fetch_gistlover_posts():
    url = "https://www.gistlover.com/"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    posts = []

    articles = soup.select("article")[:MAX_POSTS_PER_RUN]  # limit number per site
    for art in articles:
        try:
            title_tag = art.find("h2") or art.find("h3")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link_tag = art.find("a")
            link = link_tag["href"] if link_tag else "#"
            summary = art.find("p").get_text(strip=True) if art.find("p") else ""
            thumbnail_tag = art.find("img")
            thumbnail = thumbnail_tag["src"] if thumbnail_tag else "https://placehold.co/600x400?text=Gistlover"
            posts.append({
                "title": title,
                "summary": summary,
                "thumbnail": thumbnail,
                "url": link,
                "tags": ["celebrity", "gossip", "Gistlover"]
            })
        except Exception as e:
            continue
    return posts

def fetch_bellanaija_posts():
    url = "https://www.bellanaija.com/category/entertainment/"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    posts = []

    articles = soup.select(".jeg_post")[:MAX_POSTS_PER_RUN]
    for art in articles:
        try:
            title_tag = art.find("h3")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link_tag = art.find("a")
            link = link_tag["href"] if link_tag else "#"
            summary = art.find("p").get_text(strip=True) if art.find("p") else ""
            thumbnail_tag = art.find("img")
            thumbnail = thumbnail_tag["src"] if thumbnail_tag else "https://placehold.co/600x400?text=BellaNaija"
            posts.append({
                "title": title,
                "summary": summary,
                "thumbnail": thumbnail,
                "url": link,
                "tags": ["celebrity", "gossip", "BellaNaija"]
            })
        except Exception as e:
            continue
    return posts

# === MAIN FUNCTION ===
def main():
    blogdata = load_blogdata()
    existing_titles = {post["title"] for post in blogdata}

    # Fetch posts from both sites
    new_posts = fetch_gistlover_posts() + fetch_bellanaija_posts()

    # Filter out duplicates already in blogdata
    new_posts = [p for p in new_posts if p["title"] not in existing_titles][:MAX_POSTS_PER_RUN]

    if not new_posts:
        print("No new posts found today.")
        return

    # Determine next post number
    existing_numbers = [
        int(post["slug"].replace("blog/post", "").replace(".html", ""))
        for post in blogdata if "slug" in post and post["slug"].startswith("blog/post")
    ]
    next_post_number = max(existing_numbers) + 1 if existing_numbers else 1

    for p in new_posts:
        today_iso = datetime.now().strftime("%Y-%m-%d")
        today_display = datetime.now().strftime("%B %d, %Y")
        slug = f"blog/post{next_post_number}.html"

        # Create HTML post
        content_html = f'<p>{p["summary"]}</p><p>Read more: <a href="{p["url"]}" target="_blank">{p["title"]}</a></p>'
        create_post_file(next_post_number, p["title"], today_display, p["summary"], content_html, p["tags"], p["thumbnail"])

        # Add to blogdata.json
        blogdata.insert(0, {
            "title": p["title"],
            "date": today_iso,
            "author": AUTHOR,
            "slug": slug,
            "summary": p["summary"],
            "tags": p["tags"],
            "thumbnail": p["thumbnail"]
        })
        next_post_number += 1

    save_blogdata(blogdata)
    print(f"✅ Added {len(new_posts)} new posts to {BLOGDATA_PATH}")

if __name__ == "__main__":
    main()
