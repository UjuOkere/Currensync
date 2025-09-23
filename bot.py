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
DATA_FILE = os.path.join(BLOG_FOLDER, "blogdata

BACKUP_FOLDER = os.path.join(BLOG_FOLDER, "backups")

# scraping limits
MAX_PER_SOURCE = 2    # max posts per source per run
MAX_TOTAL = 8         # overall max posts per run

# sources
SOURCES = {
    "BellaNaija": "https://www.bellanaija.com/entertainment/",
    "LindaIkeji": "https://www.lindaikejisblog.com/",
    "Gistlover": "https://www.gistlover.com/",
    "Nairaland": "https://www.nairaland.com/entertainment"
}

# Post HTML template (uses the look you provided)
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
        print(f"🔒 Backup saved: {dest}")
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
    """Load blogdata.json safely. If corrupted, backup and return [] (so bot can proceed)."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print("⚠️ blogdata.json is not a list — backing up and resetting to empty list.")
            backup_file(DATA_FILE)
            return []
        return data
    except json.JSONDecodeError as e:
        print(f"⚠️ blogdata.json JSON decode error: {e} — backing up and resetting.")
        backup_file(DATA_FILE)
        return []
    except Exception as e:
        print(f"⚠️ Unexpected error loading blogdata.json: {e}")
        backup_file(DATA_FILE)
        return []

def save_blogdata(data):
    """Backup existing file then write atomically."""
    try:
        if os.path.exists(DATA_FILE):
            backup_file(DATA_FILE)
        atomic_write_json(DATA_FILE, data)
        print("✅ blogdata.json updated.")
    except Exception as e:
        print(f"❌ Failed to write blogdata.json: {e}")

def get_last_post_number():
    """Return highest postN.html in blog folder (0 if none)."""
    try:
        files = os.listdir(BLOG_FOLDER)
    except FileNotFoundError:
        return 0
    nums = []
    for f in files:
        m = re.match(r"post(\d+)\.html$", f)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) if nums else 0

# ----------------------------
# Fetching & scraping helpers
# ----------------------------
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CurrenSyncBot/1.0)"}

def fetch_soup(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def absolute_url(base, link):
    if not link:
        return None
    return urljoin(base, link)

def find_image_from_page(url):
    """Try to get og:image or first <img> from the article page."""
    soup = fetch_soup(url)
    if not soup:
        return None
    # og:image
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return og["content"]
    # first in-content image
    img = soup.find("article")
    if img:
        first = img.find("img")
        if first and first.get("src"):
            return absolute_url(url, first.get("src"))
    first = soup.find("img")
    if first and first.get("src"):
        return absolute_url(url, first.get("src"))
    return None

# ----------------------------
# Per-source scraping
# (selectors are tolerant; we only grab top N)
# ----------------------------
def scrape_bellanaija(base):
    out = []
    soup = fetch_soup(base)
    if not soup:
        return out
    selectors = ["h3.entry-title a", "h2.entry-title a", "article h2 a", "a.td-module-title-link"]
    seen = set()
    for sel in selectors:
        for a in soup.select(sel):
            if len(out) >= MAX_PER_SOURCE:
                break
            title = a.get_text(strip=True)
            href = absolute_url(base, a.get("href"))
            if not href or href in seen:
                continue
            seen.add(href)
            thumb = find_image_from_page(href) or f"https://via.placeholder.com/600x400.png?text=BellaNaija"
            summary = title
            content = f"<p>{summary}</p><p>Read more: <a href='{href}' target='_blank'>{href}</a></p>"
            out.append({"title": title, "url": href, "author": "BellaNaija", "summary": summary, "content": content, "image": thumb, "tags": ["celebrity","gossip","Nigeria"]})
        if len(out) >= MAX_PER_SOURCE:
            break
    return out

def scrape_lindaikeji(base):
    out = []
    soup = fetch_soup(base)
    if not soup:
        return out
    selectors = ["h3.post-title a", "h2.post-title a", "h3.entry-title a"]
    seen = set()
    for sel in selectors:
        for a in soup.select(sel):
            if len(out) >= MAX_PER_SOURCE:
                break
            title = a.get_text(strip=True)
            href = absolute_url(base, a.get("href"))
            if not href or href in seen:
                continue
            seen.add(href)
            thumb = find_image_from_page(href) or f"https://via.placeholder.com/600x400.png?text=LindaIkeji"
            summary = title
            content = f"<p>{summary}</p><p>Read more: <a href='{href}' target='_blank'>{href}</a></p>"
            out.append({"title": title, "url": href, "author": "LindaIkeji", "summary": summary, "content": content, "image": thumb, "tags": ["celebrity","gossip","Nigeria"]})
        if len(out) >= MAX_PER_SOURCE:
            break
    return out

def scrape_gistlover(base):
    out = []
    soup = fetch_soup(base)
    if not soup:
        return out
    selectors = ["h3.entry-title a", "h3.post-title a", "h2.entry-title a"]
    seen = set()
    for sel in selectors:
        for a in soup.select(sel):
            if len(out) >= MAX_PER_SOURCE:
                break
            title = a.get_text(strip=True)
            href = absolute_url(base, a.get("href"))
            if not href or href in seen:
                continue
            seen.add(href)
            thumb = find_image_from_page(href) or f"https://via.placeholder.com/600x400.png?text=Gistlover"
            summary = title
            content = f"<p>{summary}</p><p>Read more: <a href='{href}' target='_blank'>{href}</a></p>"
            out.append({"title": title, "url": href, "author": "Gistlover", "summary": summary, "content": content, "image": thumb, "tags": ["celebrity","gossip","Nigeria"]})
        if len(out) >= MAX_PER_SOURCE:
            break
    return out

def scrape_nairaland(base):
    out = []
    soup = fetch_soup(base)
    if not soup:
        return out
    # Nairaland uses many table structures; this picks relative links in the page
    items = soup.select("td a[href^='/']")[:MAX_PER_SOURCE * 2]
    seen = set()
    for a in items:
        if len(out) >= MAX_PER_SOURCE:
            break
        title = a.get_text(strip=True)
        href = absolute_url("https://www.nairaland.com", a.get("href"))
        if not href or href in seen:
            continue
        seen.add(href)
        thumb = f"https://via.placeholder.com/600x400.png?text=Nairaland"
        summary = title
        content = f"<p>{summary}</p><p>Read more: <a href='{href}' target='_blank'>{href}</a></p>"
        out.append({"title": title, "url": href, "author": "Nairaland", "summary": summary, "content": content, "image": thumb, "tags": ["community","Nigeria"]})
    return out

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
        image=post.get("image", ""),
        content=post.get("content",""),
        year=datetime.utcnow().year
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"📝 Created {path}")
    return filename

def escape_html(s):
    """Minimal HTML-escape for template interpolation (keeps it simple)."""
    if not isinstance(s, str):
        return s
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&#39;"))

# ----------------------------
# Main
# ----------------------------
def main():
    ensure_dirs()
    last_num = get_last_post_number()
    print(f"Last detected post number: {last_num}")

    existing = load_blogdata()
    existing_urls = set()
    for e in existing:
        if isinstance(e, dict):
            if e.get("source_url"):
                existing_urls.add(e["source_url"])
            elif e.get("slug"):
                # older manual entries may not have source_url; use title as fallback key
                existing_urls.add(e.get("title",""))

    scraped = []
    # gather from each source
    try:
        scraped.extend(scrape_bellanaija(SOURCES["BellaNaija"]))
    except Exception as e:
        print("BellaNaija scrape error:", e)
    try:
        scraped.extend(scrape_lindaikeji(SOURCES["LindaIkeji"]))
    except Exception as e:
        print("LindaIkeji scrape error:", e)
    try:
        scraped.extend(scrape_gistlover(SOURCES["Gistlover"]))
    except Exception as e:
        print("Gistlover scrape error:", e)
    try:
        scraped.extend(scrape_nairaland(SOURCES["Nairaland"]))
    except Exception as e:
        print("Nairaland scrape error:", e)

    # dedupe scraped by url + title
    unique = []
    seen = set()
    for p in scraped:
        key = p.get("url") or p.get("title")
        if not key:
            continue
        if key in seen or key in existing_urls:
            print(f"Skipping duplicate (already exists): {key}")
            continue
        seen.add(key)
        unique.append(p)
        if len(unique) >= MAX_TOTAL:
            break

    if not unique:
        print("No new unique items scraped. Exiting.")
        return

    # create files and build new blogdata entries
    new_entries = []
    for i, post in enumerate(unique, start=1):
        new_num = last_num + i
        filename = create_post_file(post, new_num)
        entry = {
            "title": post["title"],
            "date": post.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
            "author": post.get("author", "CurrenSync.vip"),
            "slug": f"blog/{filename}",
            "source_url": post.get("url"),
            "summary": post.get("summary", ""),
            "thumbnail": post.get("image", ""),
            "tags": post.get("tags") if isinstance(post.get("tags"), list) else [post.get("tags")]
        }
        new_entries.append(entry)

    # prepend new entries so newest appear first
    combined = new_entries + existing
    save_blogdata(combined)
    print(f"✅ Added {len(new_entries)} new posts to blogdata.json and created HTML files.")

if __name__ == "__main__":
    main()
