import json
import os
from datetime import datetime

# === SETTINGS ===
BLOGDATA_PATH = "blogdata.json"          # root folder
POST_TEMPLATE_PATH = "blog/post-template.html"
BLOG_FOLDER = "blog"
AUTHOR = "CurrenSync.vip"

# === FUNCTION TO CREATE POST FILE ===
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

# === MAIN BOT FUNCTION ===
def main():
    # Load existing blogdata.json safely
    blogdata = []
    if os.path.exists(BLOGDATA_PATH):
        with open(BLOGDATA_PATH, "r", encoding="utf-8") as f:
            try:
                blogdata = json.load(f)
                if not isinstance(blogdata, list):
                    blogdata = []
            except json.JSONDecodeError:
                print("⚠ blogdata.json corrupted, starting with empty list.")
                blogdata = []

    # Determine next post number safely
    existing_numbers = [
        int(item["slug"].replace("blog/post", "").replace(".html", ""))
        for item in blogdata if "slug" in item and item["slug"].startswith("blog/post")
    ]
    next_post_number = max(existing_numbers) + 1 if existing_numbers else 1

    # === BOT-GENERATED POST CONTENT ===
    title = "Breaking: AI-Powered Bot Posts Are Live!"
    today_iso = datetime.now().strftime("%Y-%m-%d")       # for JSON sorting
    today_display = datetime.now().strftime("%B %d, %Y")  # human-readable in HTML
    summary = "Our blog bot just created its first post — fully automated!"
    content = """
    <p>This is a test post generated automatically by our blog bot. 
    From now on, new blog posts will be created dynamically without breaking the site!</p>
    <p>Each post gets its own HTML page and is added to <code>blogdata.json</code> automatically.</p>
    """
    tags = ["Automation", "CurrenSync", "Tech News"]
    thumbnail = "https://placehold.co/600x400?text=New+Post"

    new_entry = {
        "title": title,
        "date": today_iso,
        "author": AUTHOR,
        "slug": f"blog/post{next_post_number}.html",
        "summary": summary,
        "tags": tags,
        "thumbnail": thumbnail
    }

    # Check for duplicates to avoid overwriting
    if not any(p["slug"] == new_entry["slug"] for p in blogdata):
        blogdata.insert(0, new_entry)
    else:
        print("⚠ Post already exists, skipping addition to JSON.")

    # Write JSON safely
    with open(BLOGDATA_PATH, "w", encoding="utf-8") as f:
        json.dump(blogdata, f, indent=2)
        print(f"✅ Added post{next_post_number} to {BLOGDATA_PATH}")

    # Create the actual post HTML file
    create_post_file(next_post_number, title, today_display, summary, content, tags, thumbnail)


if __name__ == "__main__":
    main()
