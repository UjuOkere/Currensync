#!/usr/bin/env python3
# rss bot - writes posts to posts/ and appends to blogdata.json
# safe: does not overwrite existing blogdata entries, starts counting after last postNN.html

import os
import json
import feedparser
from datetime import datetime

# ---------- CONFIG ----------
DATA_FILE = "blogdata.json"
POSTS_DIR = "posts"
RSS_FEEDS = [
    "https://lindaikejisblog.com/feed/",
    "https://www.gistlover.com/feed/",
    "https://www.bellanaija.com/feed/",
    "https://www.tmz.com/rss.xml",
]
MAX_PER_FEED = 2   # number of items to take per feed each run
AUTHOR = "CurrenSync.vip"
DEFAULT_START = 15  # last existing post number in your current JSON (you said post15 exists)
# ----------------------------

os.makedirs(POSTS_DIR, exist_ok=True)

def load_blogdata(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not load {path}: {e}")
        return []

def save_blogdata(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Could not write {path}: {e}")
        return False

def find_last_post_number(blogdata):
    nums = []
    for item in blogdata:
        slug = item.get("slug", "")
        if "post" in slug and slug.endswith(".html"):
            try:
                num = int(slug.split("post")[-1].split(".html")[0])
                nums.append(num)
            except Exception:
                continue
    return max(nums) if nums else DEFAULT_START

# AdSense snippet must be a plain string (avoid braces in f-strings)
ADSENSE_SNIPPET = """
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-6539693262305451"
     data-ad-slot="8720273670"
     data-ad-format="auto"></ins>
<script>
    (adsbygoogle = window.adsbygoogle || []).push({});
</script>
"""

def sanitize_text(text):
    # simple clean: ensure string and trim
    if not text:
        return ""
    return str(text).strip()

def make_html(post_entry, original_entry):
    # post_entry contains title, date, author, summary, slug
    title = post_entry.get("title", "Untitled")
    date = post_entry.get("date", "")
    author = post_entry.get("author", AUTHOR)
    summary = post_entry.get("summary", "")
    link = original_entry.get("link", "#")
    content_html = original_entry.get("summary", "") or original_entry.get("content", "") or ""
    # Use the adsense snippet as a variable insertion so Python f-string doesn't misinterpret {}
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{summary}" />
  <meta name="keywords" content="{post_entry.get('tags','')}" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
  <style>
    body {{ font-family: Arial, Helvetica, sans-serif; line-height: 1.6; padding: 18
