import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ----------------------
# Configuration
# ----------------------
BLOG_FOLDER = "blog"
BACKUP_FOLDER = os.path.join(BLOG_FOLDER, "backups")
DATA_FILE = "blogdata.json"

SOURCES = [
    "https://www.lindaikejisblog.com/",
    "https://www.bellanaija.com/",
    "https://www.pulse.ng/entertainment/celebrities",
]

ADSENSE_CODE = """
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6539693262305451"
     crossorigin="anonymous"></script>
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-6539693262305451"
     data-ad-slot="8720273670"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({});
</script>
"""

# ----------------------
# Helpers
# ----------------------
def ensure_dirs():
    print("🔹 Ensuring directories exist")
    os.makedirs(BLOG_FOLDER, exist_ok=True)
    os.makedirs(BACKUP_FOLDER, exist_ok=True)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def fetch_html(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"⚠️ Failed to fetch {url}: {e}")
        return None

def parse_articles(url, html):
    soup = BeautifulSoup(html, "lxml")
    articles = []

    if "lindaikejisblog" in url:
        posts = soup.select("div.post")[:2]
        for p in posts:
            title = p.select_one("h2 a").get_text(strip=True)
            link = p.select_one("h2 a")["href"]
            summary = p.select_one("p").get_text(strip=True) if p.select_one("p") else ""
            articles.append({"title": title, "link": link, "summary": summary})

    elif "bellanaija" in url:
        posts = soup.select("div.td-module-thumb a")[:2]
        for p in posts:
            title = p.get("title", "").strip()
           
