import os
import json
import re
from datetime import datetime

# ----------------------------
# Paths
# ----------------------------
BLOG_FOLDER = os.path.join("blog", "posts")
DATA_FILE = "blogdata.json"

# ----------------------------
# Helpers
# ----------------------------
def check_folder(path):
    if not os.path.exists(path):
        print(f"❌ Folder missing: {path}")
        return False
    else:
        print(f"✅ Folder exists: {path}")
        return True

def check_file(path):
    if not os.path.exists(path):
        print(f"❌ File missing: {path}")
        return False
    else:
        print(f"✅ File exists: {path}")
        return True

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print(f"❌ JSON is not a list in {path}")
            return None
        print(f"✅
