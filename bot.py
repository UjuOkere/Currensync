import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import random

JSON_FILE = "blogdata.json"
NUM_POSTS = 10

CELEB_SOURCES = [
    {"name": "Gistlover", "url": "https://gistlover.com", "tag": "celebrity"},
    {"name": "Bellanaija", "url": "https://www.bellanaija.com/category/entertainment/", "tag": "celebrity"},
    {"name": "Linda Ikeji", "url": "https://www.lindaikejisblog.com/", "tag": "celebrity"},
    {"name": "StellaDimokoKorkus", "url": "https://www.stelladimokokorkus.com/", "tag": "celebrity"},
    {"name": "Nairaland Entertainment", "url": "https://www.nairaland.com/entertainment", "tag": "celebrity"}
]

FINTECH_SOURCES = [
    {"name": "Finextra", "url": "https://www.finextra.com/news/latest", "tag": "fintech"},
    {"name": "TechCabal", "url": "https://techcabal.com/", "tag": "fintech"},
    {"name": "Premium Times", "url": "https://www.premiumtimesng.com/news/top-news", "tag": "news"}
]

def paraphrase_summary(text):
    # Optional: use a simple shuffle or sentence extraction to avoid plagiarism
    sentences = text.split(".")
    random.shuffle(sentences)
    return ". ".join(sentences[:2]) + "..."

def fetch_posts(source_list, max_posts):
    posts = []
    for source in source_list:
        try:
            res = requests.get(source["url"], timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Generic article extraction; tweak per site if needed
            articles = soup.select("article, .post, .listing .row, .news-item")[:max_posts]
            for art in articles:
                title_tag = art.find(["h2", "h3"])
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                link = art.find("a")["href"] if art.find("a") else "#"
                summary_tag = art.find("p")
                summary = paraphrase_summary(summary_tag.get_text(strip=True)) if summary_tag else title
                thumb_tag = art.find("img")
                thumbnail = thumb_tag["src"] if thumb_tag else "https://via.placeholder.com/600x400"
                
                if link.startswith("/"):
                    link = source["url"].rstrip("/") + link
                
                posts.append({
                    "title": title,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "author": "CurrenSync.vip",
                    "slug": link,
                    "summary": summary,
                    "thumbnail": thumbnail,
                    "tags": [source["tag"], "Nigeria"]
                })
        except Exception as e:
            print(f"Error fetching {source['name']}: {e}")
    return posts

celeb_posts = fetch_posts(CELEB_SOURCES, max_posts=8)
fintech_posts = fetch_posts(FINTECH_SOURCES, max_posts=2)

all_posts = celeb_posts + fintech_posts
random.shuffle(all_posts)
all_posts = all_posts[:NUM_POSTS]

with open(JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(all_posts, f, ensure_ascii=False, indent=2)

print(f"{len(all_posts)} posts written to {JSON_FILE}")
