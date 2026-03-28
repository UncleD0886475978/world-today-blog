#!/usr/bin/env python3
"""
Manual or automated 70-word social push for The World Today.
Pushes latest post to X/Twitter, Facebook, Threads, and Substack RSS.
Usage: python3 social_push.py
"""
import os, re, json, glob, urllib.request, urllib.parse
from datetime import datetime

# ── CONFIG — set these as env vars or fill in directly ──────────────────────
TWITTER_API_KEY       = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_SECRET    = os.environ.get("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN  = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET", "")
FACEBOOK_PAGE_ID      = os.environ.get("FACEBOOK_PAGE_ID", "")
FACEBOOK_PAGE_TOKEN   = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
THREADS_USER_ID       = os.environ.get("THREADS_USER_ID", "")
THREADS_ACCESS_TOKEN  = os.environ.get("THREADS_ACCESS_TOKEN", "")
SITE_URL              = "https://UncleD0886475978.github.io/world-today-blog"
SUBSTACK_URL          = "https://uncled0886.substack.com"
# ────────────────────────────────────────────────────────────────────────────

def get_latest_post():
    posts = sorted(glob.glob("/app/blog_repo/_posts/*.md"), reverse=True)
    if not posts:
        posts = sorted(glob.glob("/home/derick/world-today-blog/_posts/*.md"), reverse=True)
    if not posts:
        print("No posts found!")
        return None, None, None
    
    latest = posts[0]
    with open(latest) as f:
        content = f.read()
    
    fm = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not fm:
        return None, None, None
    
    front = fm.group(1)
    title   = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', front, re.MULTILINE)
    excerpt = re.search(r'^excerpt:\s*["\']?(.*?)["\']?\s*$', front, re.MULTILINE)
    date    = re.search(r'^date:\s*(\S+)', front, re.MULTILINE)
    cats    = re.search(r'categories:\s*\[([^\]]+)\]', front)
    image   = re.search(r'^image:\s*["\']?(.*?)["\']?\s*$', front, re.MULTILINE)
    
    title_str   = title.group(1).strip() if title else "New Story"
    excerpt_str = excerpt.group(1).strip() if excerpt else ""
    cat_str     = cats.group(1).split(",")[0].strip().strip('"\'') if cats else "News"
    image_url   = image.group(1).strip() if image else ""
    
    # Build post URL from filename
    slug = os.path.splitext(os.path.basename(latest))[0]
    parts = slug.split("-", 3)
    if len(parts) >= 4:
        post_url = f"{SITE_URL}/{parts[0]}/{parts[1]}/{parts[2]}/{parts[3]}/"
    else:
        post_url = SITE_URL
    
    return title_str, excerpt_str, cat_str, image_url, post_url

def build_caption(title, excerpt, cat, url, max_words=70):
    # Clean excerpt
    clean = re.sub(r'<[^>]+>', '', excerpt)
    words = clean.split()
    short = " ".join(words[:50]) + ("..." if len(words) > 50 else "")
    
    # Build hashtags from category
    tag = "#" + re.sub(r'[^a-zA-Z]', '', cat)
    
    caption = f"📰 {title}\n\n{short}\n\n{tag} #WorldToday #GlobalNews\n\n🔗 {url}"
    return caption

def push_twitter(caption, image_url):
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        print("  ↷ Twitter: no keys configured")
        return
    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        auth = tweepy.OAuth1UserHandler(
            TWITTER_API_KEY, TWITTER_API_SECRET,
            TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
        )
        api = tweepy.API(auth)
        
        tweet = caption[:278]
        media_id = None
        
        if image_url:
            try:
                import tempfile, urllib.request
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    urllib.request.urlretrieve(image_url, tmp.name)
                    media = api.media_upload(tmp.name)
                    media_id = media.media_id
                    print("  ✓ Twitter: image uploaded")
            except Exception as e:
                print(f"  ⚠ Twitter image: {e}")
        
        r = client.create_tweet(
            text=tweet,
            media_ids=[media_id] if media_id else None
        )
        print(f"  ✅ Twitter posted! ID: {r.data['id']}")
        print(f"     https://twitter.com/i/web/status/{r.data['id']}")
    except ImportError:
        print("  ✗ Twitter: install tweepy — pip install tweepy")
    except Exception as e:
        print(f"  ✗ Twitter error: {e}")

def push_facebook(caption, image_url, post_url):
    if not all([FACEBOOK_PAGE_ID, FACEBOOK_PAGE_TOKEN]):
        print("  ↷ Facebook: no keys configured")
        return
    try:
        import urllib.request, urllib.parse
        
        if image_url:
            data = urllib.parse.urlencode({
                "url": image_url,
                "caption": caption,
                "access_token": FACEBOOK_PAGE_TOKEN
            }).encode()
            req = urllib.request.Request(
                f"https://graph.facebook.com/{FACEBOOK_PAGE_ID}/photos",
                data=data, method="POST"
            )
        else:
            data = urllib.parse.urlencode({
                "message": caption,
                "link": post_url,
                "access_token": FACEBOOK_PAGE_TOKEN
            }).encode()
            req = urllib.request.Request(
                f"https://graph.facebook.com/{FACEBOOK_PAGE_ID}/feed",
                data=data, method="POST"
            )
        
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
            print(f"  ✅ Facebook posted! ID: {result.get('id','')}")
    except Exception as e:
        print(f"  ✗ Facebook error: {e}")

def push_threads(caption, image_url):
    if not all([THREADS_USER_ID, THREADS_ACCESS_TOKEN]):
        print("  ↷ Threads: no keys configured")
        return
    try:
        import time
        
        # Step 1: create container
        payload = {
            "text": caption[:500],
            "access_token": THREADS_ACCESS_TOKEN
        }
        if image_url:
            payload["media_type"] = "IMAGE"
            payload["image_url"] = image_url
        else:
            payload["media_type"] = "TEXT"
        
        data = urllib.parse.urlencode(payload).encode()
        req = urllib.request.Request(
            f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads",
            data=data, method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            container_id = json.loads(r.read())["id"]
        
        # Step 2: wait then publish
        time.sleep(5)
        data2 = urllib.parse.urlencode({
            "creation_id": container_id,
            "access_token": THREADS_ACCESS_TOKEN
        }).encode()
        req2 = urllib.request.Request(
            f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish",
            data=data2, method="POST"
        )
        with urllib.request.urlopen(req2, timeout=15) as r2:
            result = json.loads(r2.read())
            print(f"  ✅ Threads posted! ID: {result.get('id','')}")
    except Exception as e:
        print(f"  ✗ Threads error: {e}")

def push_substack_note(caption):
    """Substack uses RSS auto-import. Print reminder."""
    print(f"  ℹ Substack: auto-imports from RSS feed")
    print(f"     RSS: {SITE_URL}/feed.xml")
    print(f"     Dashboard: {SUBSTACK_URL}/publish/posts")
    print(f"     Set up RSS import at: {SUBSTACK_URL}/publish/settings")

# ── MAIN ────────────────────────────────────────────────────────────────────
result = get_latest_post()
if result[0] is None:
    print("No posts found to push.")
    exit(1)

title, excerpt, cat, image_url, post_url = result

print(f"\n{'='*60}")
print(f"THE WORLD TODAY — Social Push")
print(f"{'='*60}")
print(f"Title:    {title[:70]}")
print(f"Category: {cat}")
print(f"URL:      {post_url}")
print(f"Image:    {image_url[:60] if image_url else 'none'}...")
print(f"{'='*60}\n")

caption = build_caption(title, excerpt, cat, post_url)
print(f"Caption ({len(caption.split())} words):\n")
print(caption)
print(f"\n{'='*60}")
print("Pushing to social platforms...\n")

push_twitter(caption, image_url)
print()
push_facebook(caption, image_url, post_url)
print()
push_threads(caption, image_url)
print()
push_substack_note(caption)

print(f"\n{'='*60}")
print("Done!")
