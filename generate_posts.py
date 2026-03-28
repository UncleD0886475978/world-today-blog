#!/usr/bin/env python3
import os, json, datetime, requests, time, random

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
AUTHOR = "The World Today Editorial"
POSTS_OUTPUT_DIR = os.environ.get("POSTS_OUTPUT_DIR", "_posts")

TOPICS = [
    {"slot": 1, "region": "Africa",              "focus": "A major current political, economic, or social development in Africa",                                                           "category": "Africa"},
    {"slot": 2, "region": "Europe",              "focus": "A significant current event, political development, or conflict in Europe",                                                     "category": "Europe"},
    {"slot": 3, "region": "Asia",                "focus": "A major current geopolitical, economic, or social event in Asia",                                                               "category": "Asia"},
    {"slot": 4, "region": "North America",       "focus": "A significant current political, economic, or social development in North America",                                             "category": "North America"},
    {"slot": 5, "region": "South America",       "focus": "A major current event or development in South America",                                                                        "category": "South America"},
    {"slot": 6, "region": "Middle East",         "focus": "A significant current conflict, diplomatic, or political development in the Middle East",                                       "category": "Middle East"},
    {"slot": 7, "region": "Australia & Oceania", "focus": "A notable current event or development in Australia, New Zealand, or the Pacific Islands",                                     "category": "Australia & Oceania"},
    {"slot": 8, "region": "Antarctica",          "focus": "A recent scientific discovery, climate research finding, or geopolitical development related to Antarctica or the polar region","category": "Antarctica"},
]

SYSTEM_PROMPT = """You are a senior journalist writing for 'The World Today' blog.
Style: Journalistic. Tone: Neutral and authoritative.
You MUST return ONLY a valid JSON object with these exact keys:
- title: headline of the article
- category: the region/category
- summary: 70-90 words maximum. A punchy social media teaser that hooks the reader. No hashtags. End with: Read more at The World Today.
- content: full article body, 500-700 words, with ## subheadings. No percent signs.
No markdown fences, no preamble, no explanation. JSON only."""

def call_gemini(payload, max_retries=6, base_delay=30):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    delays = [base_delay * (i + 1) + random.uniform(0, 10) for i in range(max_retries)]
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 429:
                delay = delays[attempt]
                if attempt == max_retries - 1:
                    raise Exception(f"Rate limited after {max_retries} attempts")
                print(f"    Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {delay:.0f}s...")
                time.sleep(delay)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            print(f"    Request error: {e}. Retrying...")
            time.sleep(delays[attempt])

def generate_post(topic, date_str):
    user_prompt = f"""Today is {date_str}. Write a blog post about: {topic['region']}.
Focus: {topic['focus']}
Search for today's most relevant real news story from this region.
The summary field must be 70-90 words only — a social media teaser ending with: Read more at The World Today.
The content field must be the full article, 500-700 words, with ## subheadings. Do not use percent signs anywhere.
Return ONLY a JSON object with keys: title, category, summary, content.
The category value must be exactly: {topic['category']}"""

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

def save_post(post, date, slot):
    slug = "".join(c if c.isalnum() or c == " " else "" for c in post["title"].lower()).replace(" ", "-")[:60]
    filename = f"{date.isoformat()}-slot{slot}-{slug}.md"
    # Clean content — remove any percent signs to prevent Jekyll issues
    content = post["content"].replace("%", " percent ")
    summary = post["summary"].replace("%", " percent ")
    front_matter = f"""---
layout: post
title: {json.dumps(post['title'])}
date: {date.isoformat()} {slot * 2:02d}:00:00 +0000
categories: [{post['category']}]
author: {AUTHOR}
description: {json.dumps(summary)}
---\n\n"""
    os.makedirs(POSTS_OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(POSTS_OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(front_matter + content)
    print(f"    Saved: {filename}")
    return summary

def main():
    today = datetime.date.today()
    date_str = today.strftime("%A, %B %d, %Y")
    print(f"Generating 8 regional posts for {date_str}...")
    for i, topic in enumerate(TOPICS):
        print(f"[{topic['slot']}/8] {topic['region']}...")
        try:
            post = generate_post(topic, date_str)
            summary = save_post(post, today, topic["slot"])
            print(f"    Title: {post['title']}")
            print(f"    Social ({len(summary.split())} words): {summary[:80]}...")
        except Exception as e:
            print(f"    ERROR: {e}")
        if i < len(TOPICS) - 1:
            print("    Waiting 20s...")
            time.sleep(20)

if __name__ == "__main__":
    main()
