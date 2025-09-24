#!/usr/bin/env python3
import os
import re
import json
import requests
import traceback
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

# ----------------------------
# Blog & File Config
# ----------------------------
BLOG_FOLDER = "blog"                   # HTML posts live here (e.g. blog/post1.html)
DATA_FILE = "blogdata.json"            # JSON tracker stays at repo root
BACKUP_FOLDER = os.path.join("blog", "backups")

# scraping limits
MAX_PER_SOURCE = 2
MAX_TOTAL = 8

# sources (use main BellaNaija homepage as requested)
SOURCES = {
    "BellaNaija": "https://www.bellanaija.com/",
    "LindaIkeji": "https://www.lindaikejisblog.com/",
    "Gistlover": "https://www.gistlover.com/",
    "Nairaland": "https://www.nairaland.com/entertainment"
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
    """
    Ensure blog folder and backups folder exist.
    This function tolerantly creates directories and handles the case where
    a file exists with the same name by raising a clear error.
    """
    try:
        if os.path.isfile(BLOG_FOLDER):
            raise RuntimeError(f"Expected '{BLOG_FOLDER}' to be a directory but found a file.")
        os.makedirs(BLOG_FOLDER, exist_ok=True)
        # backups folder inside blog
        if os.path.isfile(BACKUP_FOLDER):
            raise RuntimeError(f"Expected '{BACKUP_FOLDER}' to be a directory but found a file.")
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
    except Exception as e:
        print(f"❌ ensure_dirs error: {e}")
        raise

def backup_file(path):
    """
    Save a timestamped backup of the file at 'path' into BACKUP_FOLDER.
    Returns destination path or None if not performed.
    """
    if not os.path.exists(path):
        return None
    try:
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        base = os.path.basename(path)
        dest = os.path.join(BACKUP_FOLDER, f"{base}.{ts}.bak")
        with open(path, "rb") as src, open(dest, "wb") as dst:
            dst.write(src.read())
        print(f"🔒 Backup saved: {dest}")
        return dest
    except Exception as e:
        print(f"⚠️ Backup failed for {path}: {e}")
        return None

def atomic_write_json(path, data):
    """
    Write JSON atomically: write to tmp file then replace.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

def load_blogdata():
    """
    Load blogdata.json safely. If the file is absent or invalid, return [].
    """
    if not os.path.exists(DATA_FILE):
        print("ℹ️ blogdata.json not found; starting with empty list.")
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print("⚠️ blogdata.json is not a list; backing up and starting fresh.")
            backup_file(DATA_FILE)
            return []
        return data
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON decode error loading {DATA_FILE}: {e}. Backing up and starting fresh.")
        backup_file(DATA_FILE)
        return []
    except Exception as e:
        print(f"⚠️ Unexpected error loading {DATA_FILE}: {e}")
        backup_file(DATA_FILE)
        return []

def save_blogdata(data):
    """
    Backup existing file and write the provided data atomically.
    """
    try:
        if os.path.exists(DATA_FILE):
            backup_file(DATA_FILE)
        atomic_write_json(DATA_FILE, data)
        print(f"✅ Successfully wrote {DATA_FILE} (entries: {len(data)})")
    except Exception as e:
        print(f"❌ Failed to write {DATA_FILE}: {e}")
        traceback.print_exc()

def get_last_post_number():
    """
    Inspect BLOG_FOLDER for files matching post(\d+).html (case-insensitive)
    and return the highest number found, or 0.
    """
    try:
        files = [f for f in os.listdir(BLOG_FOLDER) if os.path.isfile(os.path.join(BLOG_FOLDER, f))]
    except Exception as e:
        print(f"⚠️ Could not list {BLOG_FOLDER}: {e}")
        return 0
    pattern = re.compile(r"post(\d+)\.html$", re.IGNORECASE)
    nums = []
    for f in files:
        m = pattern.match(f)
        if m:
            try:
                nums.append(int(m.group(1)))
            except:
                pass
    return max(nums) if nums else 0

# ----------------------------
# Fetching & scraping helpers
# ----------------------------
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CurrenSyncBot/1.0)"}

def fetch_soup(url, parser="lxml"):
    """
    Fetch a page and return BeautifulSoup object. Returns None on failure.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        return BeautifulSoup(r.text, parser)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def absolute_url(base, link):
    if not link:
        return None
    return urljoin(base, link)

def find_image_from_page(url):
    """
    Attempt to find a representative image from an article page:
    1) og:image
    2) twitter:image
    3) first <article> img
    4) first <img> on page
    """
    soup = fetch_soup(url)
    if not soup:
        return None
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return absolute_url(url, og["content"])
    tw = soup.find("meta", property="twitter:image")
    if tw and tw.get("content"):
        return absolute_url(url, tw["content"])
    article = soup.find("article")
    if article:
        img = article.find("img")
        if img and img.get("src"):
            return absolute_url(url, img.get("src"))
    img = soup.find("img")
    if img and img.get("src"):
        return absolute_url(url, img.get("src"))
    return None

# ----------------------------
# RSS fallback (no extra deps)
# ----------------------------
def scrape_rss(url, max_posts=MAX_PER_SOURCE):
    """
    Simple RSS parser using BeautifulSoup (xml parser).
    Returns list of post dicts.
    """
    out = []
    soup = fetch_soup(url, parser="xml")
    if not soup:
        return out
    items = soup.find_all("item")[:max_posts]
    for item in items:
        title = item.title.string if item.title else "No title"
        link = item.link.string if item.link else None
        desc = ""
        if item.description:
            desc = item.description.string or ""
        # try enclosure or media:thumbnail
        img = None
        enc = item.find("enclosure")
        if enc and enc.get("url"):
            img = enc.get("url")
        media = item.find("media:thumbnail")
        if media and media.get("url"):
            img = img or media.get("url")
        # fallback placeholder
        img = img or f"https://via.placeholder.com/600x400.png?text=RSS"
        content = f"<p>{desc}</p><p>Read more: <a href='{link}' target='_blank'>{link}</a></p>"
        out.append({
            "title": title.strip(),
            "url": link,
            "author": "",
            "summary": title.strip(),
            "content": content,
            "image": img,
            "tags": []
        })
    return out

# ----------------------------
# Generic scraper with tolerant selectors
# ----------------------------
def scrape_generic(base, selectors, placeholder, author, max_posts=MAX_PER_SOURCE):
    """
    Try a list of selectors until we gather up to max_posts.
    Returns list of post dicts with title/url/content/image.
    """
    out = []
    soup = fetch_soup(base)
    if not soup:
        return out
    seen = set()
    for sel in selectors:
        try:
            for a in soup.select(sel):
                if len(out) >= max_posts:
                    break
                # anchor might be the <a> or inside <h*> tag
                if a.name != "a":
                    link_tag = a.find("a")
                else:
                    link_tag = a
                if not link_tag:
                    continue
                href = link_tag.get("href") or link_tag.get("data-href")
                title = link_tag.get_text(strip=True) or (a.get_text(strip=True) if a else "")
                href = absolute_url(base, href)
                if not href or href in seen:
                    continue
                seen.add(href)
                thumb = find_image_from_page(href) or placeholder
                content = f"<p>{title}</p><p>Read more: <a href='{href}' target='_blank'>{href}</a></p>"
                out.append({
                    "title": title,
                    "url": href,
                    "author": author,
                    "summary": title,
                    "content": content,
                    "image": thumb,
                    "tags": ["celebrity", "gossip", "Nigeria"] if author.lower() in ("bellanaija","lindaikeji","gistlover") else ["community"]
                })
        except Exception as e:
            print(f"⚠️ Error applying selector '{sel}' on {base}: {e}")
        if len(out) >= max_posts:
            break
    return out

# ----------------------------
# Per-site scraper wrappers (selectors tuned and tolerant)
# ----------------------------
def scrape_bellanaija(base):
    selectors = [
        "h3.entry-title a",
        "h2.entry-title a",
        "article h2 a",
        "a.td-module-title-link",
        "a[href*='/202']"  # heuristic: many posts include year in URL
    ]
    return scrape_generic(base, selectors, "https://via.placeholder.com/600x400.png?text=BellaNaija", "BellaNaija")

def scrape_lindaikeji(base):
    selectors = [
        "h3.post-title a",
        "h2.post-title a",
        "h3.entry-title a",
        "a[href*='/20']"
    ]
    return scrape_generic(base, selectors, "https://via.placeholder.com/600x400.png?text=LindaIkeji", "LindaIkeji")

def scrape_gistlover(base):
    selectors = [
        "h3.entry-title a",
        "h2.entry-title a",
        "article h2 a",
        "a[href*='/20']"
    ]
    return scrape_generic(base, selectors, "https://via.placeholder.com/600x400.png?text=Gistlover", "Gistlover")

def scrape_nairaland(base):
    """
    Nairaland uses table and link patterns; select anchors with relative links.
    """
    out = []
    soup = fetch_soup(base)
    if not soup:
        return out
    # pick anchors whose href starts with '/'
    anchors = soup.select("td a[href^='/']")[:MAX_PER_SOURCE * 3]
    seen = set()
    for a in anchors:
        if len(out) >= MAX_PER_SOURCE:
            break
        title = a.get_text(strip=True)
        href = a.get("href")
        href = absolute_url("https://www.nairaland.com", href)
        if not href or href in seen:
            continue
        seen.add(href)
        content = f"<p>{title}</p><p>Read more: <a href='{href}' target='_blank'>{href}</a></p>"
        out.append({
            "title": title,
            "url": href,
            "author": "Nairaland",
            "summary": title,
            "content": content,
            "image": f"https://via.placeholder.com/600x400.png?text=Nairaland",
            "tags": ["community", "Nigeria"]
        })
    return out

# ----------------------------
# Create post HTML file
# ----------------------------
def create_post_file(post, number):
    filename = f"post{number}.html"
    path = os.path.join(BLOG_FOLDER, filename)
    html = POST_TEMPLATE.format(
        title=escape_html(post.get("title", "Untitled")),
        summary=escape_html(post.get("summary", "")),
        filename=filename,
        author=escape_html(post.get("author", "CurrenSync.vip")),
        human_date=datetime.utcnow().strftime("%B %d, %Y"),
        image=post.get("image", ""),
        content=post.get("content", ""),
        year=datetime.utcnow().year
    )
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"📝 Created {path}")
    except Exception as e:
        print(f"❌ Failed to create {path}: {e}")
        traceback.print_exc()
    return filename

def escape_html(s):
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
    try:
        print("🔹 Starting bot run:", datetime.utcnow().isoformat())
        ensure_dirs()
    except Exception as e:
        print("❌ ensure_dirs failed — cannot continue:", e)
        return

    last_num = get_last_post_number()
    print(f"ℹ️ Last detected post number: {last_num}")

    existing = load_blogdata()
    print(f"ℹ️ Existing blogdata entries: {len(existing)}")

    existing_urls = set()
    for e in existing:
        if isinstance(e, dict):
            if e.get("source_url"):
                existing_urls.add(e.get("source_url"))
            elif e.get("slug"):
                existing_urls.add(e.get("slug"))

    # Collect scraped posts from all sources (with fallback to RSS if necessary)
    scraped = []

    # BellaNaija
    try:
        scraped_b = scrape_bellanaija(SOURCES["BellaNaija"])
        if not scraped_b:
            # try RSS fallback
            scraped_b = scrape_rss(urljoin(SOURCES["BellaNaija"], "feed/"))
            print("ℹ️ BellaNaija fallback RSS count:", len(scraped_b))
        scraped.extend(scraped_b)
        print(f"ℹ️ BellaNaija scraped: {len(scraped_b)}")
    except Exception as e:
        print(f"❌ BellaNaija scrape error: {e}")
        traceback.print_exc()

    # Linda Ikeji
    try:
        scraped_l = scrape_lindaikeji(SOURCES["LindaIkeji"])
        if not scraped_l:
            scraped_l = scrape_rss(urljoin(SOURCES["LindaIkeji"], "feeds/posts/default"))
            print("ℹ️ LindaIkeji fallback RSS count:", len(scraped_l))
        scraped.extend(scraped_l)
        print(f"ℹ️ LindaIkeji scraped: {len(scraped_l)}")
    except Exception as e:
        print(f"❌ LindaIkeji scrape error: {e}")
        traceback.print_exc()

    # Gistlover
    try:
        scraped_g = scrape_gistlover(SOURCES["Gistlover"])
        if not scraped_g:
            scraped_g = scrape_rss(urljoin(SOURCES["Gistlover"], "feed/"))
            print("ℹ️ Gistlover fallback RSS count:", len(scraped_g))
        scraped.extend(scraped_g)
        print(f"ℹ️ Gistlover scraped: {len(scraped_g)}")
    except Exception as e:
        print(f"❌ Gistlover scrape error: {e}")
        traceback.print_exc()

    # Nairaland
    try:
        scraped_n = scrape_nairaland(SOURCES["Nairaland"])
        if not scraped_n:
            # Nairaland does not always provide RSS for the section; try homepage RSS
            scraped_n = scrape_rss("https://www.nairaland.com/feeds")
            print("ℹ️ Nairaland fallback RSS count:", len(scraped_n))
        scraped.extend(scraped_n)
        print(f"ℹ️ Nairaland scraped: {len(scraped_n)}")
    except Exception as e:
        print(f"❌ Nairaland scrape error: {e}")
        traceback.print_exc()

    # Deduplicate scraped and filter out existing
    unique = []
    seen = set()
    for p in scraped:
        key = (p.get("url") or p.get("title") or "").strip()
        if not key:
            continue
        if key in seen:
            continue
        if key in existing_urls:
            # skip duplicates already in blogdata.json
            continue
        seen.add(key)
        unique.append(p)
        if len(unique) >= MAX_TOTAL:
            break

    print(f"ℹ️ Unique new scraped posts to add: {len(unique)}")
    if not unique:
        print("ℹ️ No new unique posts found — exiting.")
        return

    new_entries = []
    for i, post in enumerate(unique, start=1):
        new_num = last_num + i
        filename = create_post_file(post, new_num)
        entry = {
            "title": post.get("title", "Untitled"),
            "date": post.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
            "author": post.get("author", "CurrenSync.vip"),
            "slug": f"blog/{filename}",
            "source_url": post.get("url"),
            "summary": post.get("summary", "") or post.get("title", ""),
            "thumbnail": post.get("image", ""),
            "tags": post.get("tags") if isinstance(post.get("tags"), list) else [post.get("tags")] if post.get("tags") else []
        }
        new_entries.append(entry)

    combined = new_entries + existing
    save_blogdata(combined)

    print(f"✅ Added {len(new_entries)} new posts. Total entries now: {len(combined)}")
    for e in new_entries:
        print(f"  • {e['title']} -> {e['slug']}")

if __name__ == "__main__":
    main()
