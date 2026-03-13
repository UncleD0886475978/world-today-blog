#!/usr/bin/env python3
import os
import json
import datetime
import time
import random
import subprocess
import requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
AUTHOR = "The World Today Editorial"
POSTS_OUTPUT_DIR = os.environ.get("POSTS_OUTPUT_DIR", "_posts")
BLOG_REPO_DIR = os.environ.get("BLOG_REPO_DIR", "/app/blog_repo")

TOPICS = [
    {
        "slot": 1,
        "focus": "A deep-dive analysis of a major current geopolitical event",
        "category": "Geopolitics"
    },
    {
        "slot": 2,
        "focus": "A current conflict, war, or military development anywhere in the world",
        "category": "Conflict & Security"
    },
    {
        "slot": 3,
        "focus": "Historical context: connect a current event to a historical parallel",
        "category": "History & Analysis"
    }
]

SYSTEM_PROMPT = """You are a senior journalist writing for 'The World Today' blog.
Style: Journalistic. Tone: Neutral and authoritative. Length: 500-700 words.
Include: headline, dateline, 3-4 subheadings, closing analytical paragraph.
You MUST return ONLY a valid JSON object with these exact keys: title, category, summary, content.
Use ## for subheadings inside content. No markdown fences, no preamble, no explanation."""


def call_gemini_with_backoff(payload, max_retries=6, base_delay=30):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
    )
    # Flat backoff: 30, 60, 90, 120, 150, 180 — avoids runaway wait times
    delays = [base_delay * (i + 1) + random.uniform(0, 10) for i in range(max_retries)]
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                if attempt == max_retries - 1:
                    raise
                delay = delays[attempt]
                print(f"    Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {delay:.0f}s...")
                time.sleep(delay)
            else:
                raise
    raise RuntimeError("Max retries exceeded")


def generate_post(topic, date_str):
    user_prompt = (
        f"Today is {date_str}. Write a blog post for category: {topic['category']}.\n"
        f"Focus: {topic['focus']}\n"
        "Search for today's most relevant real news story on this topic.\n"
        "Return ONLY a JSON object with keys: title, category, summary, content "
        "(use ## for subheadings)."
    )
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4000}
    }
    data = call_gemini_with_backoff(payload)
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    # Strip markdown fences if present
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                return json.loads(part)
            except json.JSONDecodeError:
                continue
    # Extract raw JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    return json.loads(text)


def save_post(post, date_str, slot):
    slug = "".join(
        c if c.isalnum() or c == "-" else "-"
        for c in post["title"].lower().replace(" ", "-")
    )[:60].strip("-")
    filename = f"{date_str}-slot{slot}-{slug}.md"
    posts_dir = os.path.join(BLOG_REPO_DIR, POSTS_OUTPUT_DIR)
    os.makedirs(posts_dir, exist_ok=True)
    filepath = os.path.join(posts_dir, filename)
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S +0000")
    front_matter = (
        "---\n"
        f"layout: post\n"
        f"title: \"{post['title'].replace(chr(34), chr(39))}\"\n"
        f"date: {now}\n"
        f"categories: [{post['category']}]\n"
        f"author: \"{AUTHOR}\"\n"
        f"excerpt: \"{post['summary'].replace(chr(34), chr(39))[:200]}\"\n"
        "---\n\n"
    )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(front_matter)
        f.write(post["content"])
    print(f"    Saved: {filename}")
    return filepath


def git_push(date_str):
    posts_dir = os.path.join(BLOG_REPO_DIR, POSTS_OUTPUT_DIR)
    try:
        subprocess.run(["git", "-C", BLOG_REPO_DIR, "add", posts_dir], check=True)
        subprocess.run(["git", "-C", BLOG_REPO_DIR, "commit", "-m", f"Auto-publish posts for {date_str}"], check=True)
        subprocess.run(["git", "-C", BLOG_REPO_DIR, "push"], check=True)
        print("    Git push successful.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git push failed: {e}")


def main():
    now = datetime.datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    day_label = now.strftime("%A, %B %-d, %Y")
    try:
        subprocess.run(["git", "-C", BLOG_REPO_DIR, "pull"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass
    print(f"Generating {len(TOPICS)} posts for {day_label}...")
    posts = []
    for i, topic in enumerate(TOPICS):
        print(f"[{i + 1}/{len(TOPICS)}] {topic['category']}...")
        try:
            post = generate_post(topic, day_label)
            save_post(post, date_str, topic["slot"])
            posts.append(post)
            print(f"    Done: {post['title']}")
        except Exception as e:
            print(f"    ERROR: {e}")
        if i < len(TOPICS) - 1:
            print("    Waiting 90s before next post...")
            time.sleep(90)
    if posts:
        print(f"\nPushing {len(posts)} post(s) to GitHub...")
        try:
            git_push(date_str)
        except RuntimeError as e:
            print(f"    ERROR: {e}")
    else:
        print("\nNo posts generated — skipping git push.")


if __name__ == "__main__":
    main()
