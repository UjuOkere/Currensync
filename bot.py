import json
import os
from datetime import datetime

BLOGDATA_PATH = "blogdata.json"
NEW_POSTS_PATH = "new_posts.json"

def load_json(path):
    """Load JSON file safely, return empty list if missing or invalid."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ Warning: {path} contains invalid JSON, starting fresh.")
        return []

def save_json(path, data):
    """Save JSON with pretty formatting and UTF-8 encoding."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # Load existing blog posts
    existing_posts = load_json(BLOGDATA_PATH)

    # Load fresh posts to add (from bot or manually dropped file)
    fresh_posts = load_json(NEW_POSTS_PATH)

    if not fresh_posts:
        print("✅ No new posts found, blogdata.json left unchanged.")
        return

    # Find the highest numbered post in existing posts
    highest_num = 0
    for post in existing_posts:
        slug = post.get("slug", "")
        if slug.startswith("blog/post") and slug.endswith(".html"):
            try:
                num = int(slug.replace("blog/post", "").replace(".html", ""))
                if num > highest_num:
                    highest_num = num
            except ValueError:
                pass

    # Assign new slugs sequentially starting from highest number
    new_posts_with_slugs = []
    for i, post in enumerate(fresh_posts, start=1):
        next_num = highest_num + i
        post["slug"] = f"blog/post{next_num}.html"
        if "date" not in post:
            post["date"] = datetime.now().strftime("%Y-%m-%d")
        new_posts_with_slugs.append(post)

    # Merge (new posts go first)
    updated_posts = new_posts_with_slugs + existing_posts

    # Save back to blogdata.json
    save_json(BLOGDATA_PATH, updated_posts)
    print(f"✅ Added {len(new_posts_with_slugs)} new posts to {BLOGDATA_PATH}")

    # Optionally, clear new_posts.json so we don't re-add them
    save_json(NEW_POSTS_PATH, [])

if __name__ == "__main__":
    main()
