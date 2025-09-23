import json
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import random
import re

# === SETTINGS ===
BLOGDATA_PATH = "blogdata.json"
POST_TEMPLATE_PATH = "blog/post-template.html"
BLOG_FOLDER = "blog"
AUTHOR = "CurrenSync.vip"
MAX_POSTS_PER_RUN = 10

# Sites to scrape
CELEB_SITES = [
    {"name": "Gistlover", "url": "https://www.gistlover.com/category/celebrity-news/", "base": "https://www.gistlover.com"},
    {"name": "BellaNaija", "url": "https://www.bellanaija.com/category/entertainment/", "base": "https://www.bellanaija.com"}
]

# === FUNCTIONS ===
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

def scrape_site(site):
    try:
        resp = requests.get(site["url"], timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch {site['name']}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []

    if site["name"] == "Gistlover":
        for item in soup.select("article.post")[:MAX_POSTS_PER_RUN]:
            title_tag = item.select_one("h2.entry-title a")
            if not title_tag: continue
            title = title_tag.get_text(strip=True)
            link = title_tag['href']
            summary_tag = item.select_one("div.entry-summary p")
            summary = summary_tag.get_text(strip=True) if summary_tag else title
            # get first image from article page
            thumb = fetch_first_image(link) or "https://placehold.co/600x400?text=Gistlover"
            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
                "thumbnail": thumb,
                "source": "Gistlover"
            })

    elif site["name"] == "BellaNaija":
        for item in soup.select("div.td_module_10")[:MAX_POSTS_PER_RUN]:
            title_tag = item.select_one("h3.entry-title a")
            if not title_tag: continue
            title = title_tag.get_text(strip=True)
            link = title_tag['href']
            summary = title
            thumb = fetch_first_image(link) or "https://placehold.co/600x400?text=BellaNaija"
            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
                "thumbnail": thumb,
                "source": "BellaNaija"
            })
    return articles

def fetch_article_content(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return "<p>Content unavailable.</p>"
    soup = BeautifulSoup(resp.text, "html.parser")
    paragraphs = soup.select("p")
    content = ""
    for p in paragraphs[:5]:  # first 5 paragraphs
        text = re.sub(r'\s+', ' ', p.get_text(strip=True))
        if text:
            content += f"<p>{text}</p>"
    return content or "<p>Content unavailable.</p>"

def fetch_first_image(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None
    soup = BeautifulSoup(resp.text, "html.parser")
    img_tag = soup.find("img")
    if img_tag and img_tag.has_attr("src"):
        return img_tag["src"]
    return None

def generate_tags(title):
    title_clean = re.sub(r'[^a-zA-Z0-9 ]', '', title)
    tags = title_clean.split()
    tags = [t.capitalize() for t in tags if len(t) > 2]
    return list(set(tags))[:6]

# === MAIN BOT ===
def main():
    if os.path.exists(BLOGDATA_PATH):
        with open(BLOGDATA_PATH, "r", encoding="utf-8") as f:
            try:
                blogdata = json.load(f)
            except json.JSONDecodeError:
                blogdata = []
    else:
        blogdata = []

    existing_numbers = [
        int(item["slug"].replace("blog/post", "").replace(".html", ""))
        for item in blogdata if "slug" in item and item["slug"].startswith("blog/post")
    ]
    next_post_number = max(existing_numbers) + 1 if existing_numbers else 1

    all_new_articles = []
    for site in CELEB_SITES:
        articles = scrape_site(site)
        all_new_articles.extend(articles)

    random.shuffle(all_new_articles)
    all_new_articles = all_new_articles[:MAX_POSTS_PER_RUN]

    for art in all_new_articles:
        today_iso = datetime.now().strftime("%Y-%m-%d")
        today_display = datetime.now().strftime("%B %d, %Y")
        content = fetch_article_content(art["link"])
        tags = generate_tags(art["title"])
        new_entry = {
            "title": art["title"],
            "date": today_iso,
            "author": AUTHOR,
            "slug": f"blog/post{next_post_number}.html",
            "summary": art["summary"],
            "tags": tags,
            "thumbnail": art["thumbnail"]
        }
        blogdata.insert(0, new_entry)
        create_post_file(next_post_number, art["title"], today_display, art["summary"], content, tags, art["thumbnail"])
        next_post_number += 1

    with open(BLOGDATA_PATH, "w", encoding="utf-8") as f:
        json.dump(blogdata, f, indent=2)

    print(f"✅ Added {len(all_new_articles)} new posts to {BLOGDATA_PATH}")

if __name__ == "__main__":
    main()
