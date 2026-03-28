#!/usr/bin/env python3
import os, json, datetime, time, random, requests, hashlib

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
AUTHOR = "The World Today Editorial"
POSTS_OUTPUT_DIR = os.environ.get("POSTS_OUTPUT_DIR", "_posts")
BLOG_REPO_DIR = os.environ.get("BLOG_REPO_DIR", "/app/blog_repo")

TWITTER_API_KEY       = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_SECRET    = os.environ.get("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN  = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET", "")
FACEBOOK_PAGE_TOKEN   = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
FACEBOOK_PAGE_ID      = os.environ.get("FACEBOOK_PAGE_ID", "")
THREADS_TOKEN         = os.environ.get("THREADS_TOKEN", "")

AFRICAN_COUNTRIES = [
    "Nigeria","Ethiopia","Egypt","DR Congo","Tanzania","South Africa","Kenya","Uganda",
    "Algeria","Sudan","Morocco","Angola","Mozambique","Ghana","Madagascar","Cameroon",
    "Ivory Coast","Niger","Burkina Faso","Mali","Malawi","Zambia","Senegal","Chad",
    "Somalia","Zimbabwe","Guinea","Rwanda","Benin","Burundi","Tunisia","South Sudan",
    "Togo","Sierra Leone","Libya","Congo","Liberia","Central African Republic","Mauritania",
    "Eritrea","Gambia","Botswana","Namibia","Gabon","Lesotho","Guinea-Bissau","Equatorial Guinea",
    "Mauritius","Eswatini","Djibouti","Comoros","Cape Verde","Sao Tome and Principe","Seychelles"
]

SPORTS_TOPICS = [
    {"focus": "Latest soccer/football results, transfers, or major league developments worldwide", "category": "Sports - Soccer"},
    {"focus": "Basketball news: NBA, FIBA, EuroLeague, or international basketball developments", "category": "Sports - Basketball"},
    {"focus": "CAF Champions League, AFCON qualifiers, or African football developments", "category": "Sports - CAF/AFCON"},
    {"focus": "UEFA Champions League, Europa League, or major European football cup news", "category": "Sports - Champions League"},
    {"focus": "World Cup 2026 qualifiers, preparations, or major international football news", "category": "Sports - World Cup"},
    {"focus": "Club team news: transfers, injuries, manager changes, or match analysis", "category": "Sports - Club Teams"},
]

# All 8 topic slots — rotated 3 per run across the day
ALL_TOPICS = [
    {"slot": 1, "region": "Africa",              "focus": "A major current political, economic, or social development in Africa",                         "category": "Africa"},
    {"slot": 2, "region": "Europe",              "focus": "A significant current event, political development, or conflict in Europe",                   "category": "Europe"},
    {"slot": 3, "region": "Asia",                "focus": "A major current geopolitical, economic, or social event in Asia",                             "category": "Asia"},
    {"slot": 4, "region": "North America",       "focus": "A significant current political, economic, or social development in North America",            "category": "North America"},
    {"slot": 5, "region": "South America",       "focus": "A major current event or development in South America",                                       "category": "South America"},
    {"slot": 6, "region": "Middle East",         "focus": "A significant current conflict, diplomatic, or political development in the Middle East",      "category": "Middle East"},
    {"slot": 7, "region": "Sports",              "focus": "", "category": ""},
    {"slot": 8, "region": "African Culture",     "focus": "", "category": "African Culture"},
]

SYSTEM_PROMPT = """You are a senior journalist writing for 'The World Today' blog.
Style: Journalistic. Tone: Neutral and authoritative.
Return ONLY a valid JSON object with these exact keys:
- title: compelling headline
- category: exact category provided
- summary: 70-90 words. Punchy social media teaser. No hashtags. No percent signs. End with: Read more at The World Today.
- content: 500-700 words with ## subheadings. No percent signs. No curly braces. No Liquid tags.
No markdown fences, no preamble. JSON only."""

def get_run_slot():
    """Return which 3 topics to generate based on current UTC hour."""
    hour = datetime.datetime.utcnow().hour
    if hour < 13:
        return [0, 1, 2]   # 07:00 run: Africa, Europe, Asia
    elif hour < 19:
        return [3, 4, 5]   # 13:00 run: North America, South America, Middle East
    else:
        return [6, 7]   # 19:00 run: Sports + African Culture (slot 8 uses index 7)

def get_today_african_country():
    day = datetime.date.today().timetuple().tm_yday
    return AFRICAN_COUNTRIES[day % len(AFRICAN_COUNTRIES)]

def get_today_sport():
    day = datetime.date.today().timetuple().tm_yday
    return SPORTS_TOPICS[day % len(SPORTS_TOPICS)]

def post_already_exists(slot, date):
    posts_dir = os.path.join(BLOG_REPO_DIR, POSTS_OUTPUT_DIR)
    if not os.path.exists(posts_dir):
        return False
    prefix = f"{date.isoformat()}-slot{slot}-"
    for f in os.listdir(posts_dir):
        if f.startswith(prefix):
            print(f"    Skipping — already exists: {f}")
            return True
    return False

def call_gemini(payload, max_retries=3, base_delay=60):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=90)
            if response.status_code == 429:
                wait = base_delay * (attempt + 1) + random.uniform(0, 10)
                if attempt == max_retries - 1:
                    raise Exception("Rate limited — max retries reached")
                print(f"    Rate limited. Waiting {wait:.0f}s...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            wait = base_delay * (attempt + 1)
            print(f"    Error: {e}. Retrying in {wait:.0f}s...")
            time.sleep(wait)

def generate_post(topic, date_str):
    user_prompt = f"""Today is {date_str}. Write a blog post about: {topic['region']}.
Focus: {topic['focus']}
Category must be exactly: {topic['category']}
Summary: 70-90 words ending with: Read more at The World Today.
Content: 500-700 words with ## subheadings. No percent signs. No curly braces.
Return ONLY valid JSON with keys: title, category, summary, content."""

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4000}
    }
    data = call_gemini(payload)
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())

def clean(text):
    return text.replace("%", " percent ").replace("{", "(").replace("}", ")")

def save_post(post, date, slot):
    slug = "".join(c if c.isalnum() or c == " " else "" for c in post["title"].lower()).replace(" ", "-")[:55]
    filename = f"{date.isoformat()}-slot{slot}-{slug}.md"
    content = clean(post["content"])
    summary = clean(post["summary"])
    title = post["title"].replace('"', "'")
    # Derive sport/region/culture tags from category
    cat = post['category']
    extra = ""
    if cat.startswith("Sports -"):
        sport_name = cat.replace("Sports - ", "").lower().replace("/", "").replace(" ", "-")
        extra = f"sport: {sport_name}\nsport_label: {cat.replace('Sports - ', '')}"
    elif cat == "African Culture":
        extra = "culture: african"
    else:
        extra = f"region: {cat}"

    front_matter = f"""---
layout: post
title: {json.dumps(title)}
date: {date.isoformat()} {slot * 2:02d}:00:00 +0000
categories: [{post['category']}]
author: {AUTHOR}
description: {json.dumps(summary)}
{extra}
---

{content}
"""
    posts_dir = os.path.join(BLOG_REPO_DIR, POSTS_OUTPUT_DIR)
    os.makedirs(posts_dir, exist_ok=True)
    with open(os.path.join(posts_dir, filename), "w", encoding="utf-8") as f:
        f.write(front_matter)
    print(f"    Saved: {filename}")
    return summary, title

def get_post_url(title, date):
    slug = "".join(c if c.isalnum() or c == " " else "" for c in title.lower()).replace(" ", "-")[:55]
    return f"https://UncleD0886475978.github.io/world-today-blog/{date.year}/{date.month:02d}/{date.day:02d}/{slug}/"

def post_to_facebook(summary, url):
    if not all([FACEBOOK_PAGE_TOKEN, FACEBOOK_PAGE_ID]):
        print("    Facebook: no credentials, skipping")
        return
    try:
        r = requests.post(
            f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/feed",
            data={"message": f"{summary}\n\n{url}", "access_token": FACEBOOK_PAGE_TOKEN},
            timeout=30
        )
        print(f"    Facebook: {'posted' if r.status_code == 200 else f'error {r.status_code}'}")
    except Exception as e:
        print(f"    Facebook error: {e}")

def post_to_threads(summary, url):
    if not THREADS_TOKEN:
        print("    Threads: no credentials, skipping")
        return
    try:
        r1 = requests.post(
            "https://graph.threads.net/v1.0/me/threads",
            data={"media_type": "TEXT", "text": f"{summary}\n\n{url}", "access_token": THREADS_TOKEN},
            timeout=30
        )
        if r1.status_code != 200:
            print(f"    Threads container error: {r1.status_code}")
            return
        time.sleep(5)
        r2 = requests.post(
            "https://graph.threads.net/v1.0/me/threads_publish",
            data={"creation_id": r1.json().get("id"), "access_token": THREADS_TOKEN},
            timeout=30
        )
        print(f"    Threads: {'posted' if r2.status_code == 200 else f'error {r2.status_code}'}")
    except Exception as e:
        print(f"    Threads error: {e}")

def post_to_twitter(summary, url):
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        print("    Twitter/X: no credentials, skipping")
        return
    try:
        import hmac, base64, urllib.parse
        text = f"{summary}\n\n{url}"[:280]
        ts = str(int(time.time()))
        nonce = hashlib.md5(f"{ts}{random.random()}".encode()).hexdigest()
        params = {
            "oauth_consumer_key": TWITTER_API_KEY,
            "oauth_nonce": nonce,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": ts,
            "oauth_token": TWITTER_ACCESS_TOKEN,
            "oauth_version": "1.0",
        }
        base = "&".join([
            "POST",
            urllib.parse.quote("https://api.twitter.com/2/tweets", safe=""),
            urllib.parse.quote("&".join(f"{k}={urllib.parse.quote(v,safe='')}" for k,v in sorted(params.items())), safe="")
        ])
        key = f"{urllib.parse.quote(TWITTER_API_SECRET,safe='')}&{urllib.parse.quote(TWITTER_ACCESS_SECRET,safe='')}"
        sig = base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()
        params["oauth_signature"] = sig
        auth = "OAuth " + ", ".join(f'{k}="{urllib.parse.quote(v,safe="")}"' for k,v in sorted(params.items()))
        r = requests.post(
            "https://api.twitter.com/2/tweets",
            headers={"Authorization": auth, "Content-Type": "application/json"},
            json={"text": text}, timeout=30
        )
        print(f"    Twitter/X: {'posted' if r.status_code in [200,201] else f'error {r.status_code}'}")
    except Exception as e:
        print(f"    Twitter/X error: {e}")

def share_to_social(title, summary, date):
    url = get_post_url(title, date)
    print("    Sharing to social platforms...")
    post_to_facebook(summary, url)
    post_to_threads(summary, url)
    post_to_twitter(summary, url)

def main():
    today = datetime.date.today()
    date_str = today.strftime("%A, %B %d, %Y")
    sport = get_today_sport()
    country = get_today_african_country()

    # Build today's full topic list
    topics = []
    for t in ALL_TOPICS:
        topic = t.copy()
        if topic["slot"] == 7:
            topic["focus"] = sport["focus"]
            topic["category"] = sport["category"]
        elif topic["slot"] == 8:
            topic["focus"] = (
                f"Celebrate and explore the culture of {country}: food, traditional dress, "
                f"lifestyle, music, art, festivals, or daily life. Make it vivid, respectful, and educational."
            )
            topic["region"] = f"African Culture - {country}"
        topics.append(topic)

    # Pick 3 topics for this run based on time of day
    indices = get_run_slot()
    run_topics = [topics[i] for i in indices]

    print(f"=== Generating {len(run_topics)} posts for {date_str} ===")

    generated = 0
    for i, topic in enumerate(run_topics):
        print(f"\n[{i+1}/{len(run_topics)}] {topic['region']}...")

        if post_already_exists(topic["slot"], today):
            continue

        try:
            post = generate_post(topic, date_str)
            summary, title = save_post(post, today, topic["slot"])
            print(f"    Title: {title}")
            print(f"    Summary ({len(summary.split())} words): {summary[:80]}...")
            share_to_social(title, summary, today)
            generated += 1
        except Exception as e:
            print(f"    ERROR: {e}")

        if i < len(run_topics) - 1:
            print("    Waiting 30s before next post...")
            time.sleep(30)

    print(f"\nDone! Generated {generated} new posts.")

if __name__ == "__main__":
    main()
