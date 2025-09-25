import os
import json
import feedparser
from datetime import datetime

# -------------------
# Config
# -------------------
BLOGDATA_FILE = "blogdata.json"
POSTS_FOLDER = "blog"
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
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
  <script>
       (adsbygoogle = window.adsbygoogle || []).push({{}});
  </script>
</head>
<body>
  <article>
    <h1>{title}</h1>
    <p><em>By {author} on {date}</em></p>
    <div>{content}</div>
  </article>

  <!-- Ad block -->
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="ca-pub-6539693262305451"
       data-ad-slot="8720273670"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</body>
</html>
"""

RSS_FEEDS = {
    "BellaNaija": "https://www.bellanaija.com/feed/",
    "Linda Ikeji": "https://www.lindaikejisblog.com/feed
