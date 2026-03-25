#!/usr/bin/env python3
"""
Auto-fetches Unsplash images for posts missing an image field.
Saves thumbnails to assets/images/ and adds image: URL to front matter.
Usage: python3 _scripts/fetch_images.py
"""
import os, re, sys, json, urllib.request, urllib.parse, time

# ── CONFIG ──────────────────────────────────────────────────────────────────
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")
POSTS_DIR = "_posts"
IMAGES_DIR = "assets/images"
# Keyword map: category → search terms
CATEGORY_KEYWORDS = {
    "Geopolitics":        "world map geopolitics diplomacy",
    "Conflict & Security":"military conflict security war",
    "History & Analysis": "history archive newspaper vintage",
    "Politics":           "politics government parliament",
    "Sports":             "sports stadium crowd",
    "soccer":             "soccer football pitch",
    "basketball":         "basketball court NBA",
    "worldcup":           "FIFA world cup trophy",
    "caf":                "africa football stadium",
    "ucl":                "champions league trophy night",
    "clubs":              "football club jersey fans",
}
# ────────────────────────────────────────────────────────────────────────────

os.makedirs(IMAGES_DIR, exist_ok=True)

def extract_keywords(title, category, sport=None):
    key = sport or category or "world news"
    base = CATEGORY_KEYWORDS.get(key, "world news journalism")
    # pull meaningful words from title (4+ chars, not stopwords)
    stops = {"with","from","that","this","have","will","been","they",
             "their","into","about","over","after","amid","amid","also","amid"}
    words = [w for w in re.findall(r'[a-zA-Z]{4,}', title.lower()) if w not in stops]
    extra = " ".join(words[:3])
    return f"{base} {extra}".strip()

def fetch_unsplash(query, post_slug):
    if not UNSPLASH_ACCESS_KEY:
        # Fallback: use source.unsplash.com (no key needed, random per query)
        encoded = urllib.parse.quote(query.replace(" ", ","))
        return f"https://source.unsplash.com/1200x630/?{encoded}", None
    
    url = f"https://api.unsplash.com/photos/random?query={urllib.parse.quote(query)}&orientation=landscape&content_filter=high"
    req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            full_url = data["urls"]["regular"]  # ~1080px wide
            thumb_url = data["urls"]["small"]   # ~400px wide
            return full_url, thumb_url
    except Exception as e:
        print(f"  ⚠ Unsplash API error: {e}")
        encoded = urllib.parse.quote(query.replace(" ", ","))
        return f"https://source.unsplash.com/1200x630/?{encoded}", None

def save_thumbnail(thumb_url, slug):
    if not thumb_url:
        return None
    local_path = f"{IMAGES_DIR}/{slug}.jpg"
    if os.path.exists(local_path):
        return local_path
    try:
        urllib.request.urlretrieve(thumb_url, local_path)
        print(f"  ✓ Saved thumbnail: {local_path}")
        return local_path
    except Exception as e:
        print(f"  ⚠ Could not save thumbnail: {e}")
        return None

def process_post(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has image
    if re.search(r'^image:', content, re.MULTILINE):
        print(f"  ↷ Already has image: {os.path.basename(filepath)}")
        return False
    
    # Parse front matter
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        return False
    
    fm = fm_match.group(1)
    title = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', fm, re.MULTILINE)
    category = re.search(r'categories:\s*\[([^\]]+)\]', fm)
    sport = re.search(r'^sport:\s*(\S+)', fm, re.MULTILINE)
    
    title_str = title.group(1) if title else ""
    cat_str = category.group(1).split(",")[0].strip().strip('"\'') if category else ""
    sport_str = sport.group(1) if sport else None
    
    # Generate slug from filename
    slug = os.path.splitext(os.path.basename(filepath))[0]
    
    # Get keywords and fetch image
    keywords = extract_keywords(title_str, cat_str, sport_str)
    print(f"  🔍 Searching: '{keywords}'")
    
    full_url, thumb_url = fetch_unsplash(keywords, slug)
    
    # Save thumbnail locally
    local_thumb = save_thumbnail(thumb_url, slug)
    
    # Use local path for thumbnail if saved, else use full URL
    image_url = full_url  # large = external (Cloudinary/Unsplash CDN)
    thumb_field = f"{site_baseurl}/assets/images/{slug}.jpg" if local_thumb else full_url
    
    # Inject into front matter
    new_fm = fm.rstrip() + f'\nimage: "{image_url}"\nimage_thumb: "{thumb_field}"\n'
    new_content = content.replace(fm_match.group(1), new_fm, 1)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  ✓ Added image to: {os.path.basename(filepath)}")
    return True

# Read baseurl from _config.yml
site_baseurl = "/world-today-blog"
try:
    with open("_config.yml") as f:
        for line in f:
            if line.startswith("baseurl:"):
                site_baseurl = line.split(":",1)[1].strip().strip('"\'')
                break
except:
    pass

posts = sorted([f for f in os.listdir(POSTS_DIR) if f.endswith('.md')], reverse=True)
updated = 0
print(f"🖼  Processing {len(posts)} posts...\n")
for post in posts:
    path = os.path.join(POSTS_DIR, post)
    print(f"→ {post}")
    if process_post(path):
        updated += 1
    time.sleep(0.3)  # be polite to API

print(f"\n✅ Done! Updated {updated} posts with images.")
