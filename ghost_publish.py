#!/usr/bin/env python3
import jwt, requests, os
from datetime import datetime as dt

GHOST_API_URL = os.environ.get("GHOST_API_URL", "http://192.168.142.158:2368")
GHOST_API_KEY = os.environ["GHOST_API_KEY"]

def get_token():
    key_id, secret = GHOST_API_KEY.split(":")
    iat = int(dt.now().timestamp())
    payload = {"iat": iat, "exp": iat + 300, "aud": "/admin/"}
    return jwt.encode(payload, bytes.fromhex(secret), algorithm="HS256", headers={"kid": key_id})

def publish_to_ghost(title, content, summary, category, visibility="paid"):
    token = get_token()
    headers = {"Authorization": f"Ghost {token}", "Content-Type": "application/json"}
    mobiledoc = {
        "version": "0.3.1",
        "atoms": [],
        "cards": [["markdown", {"markdown": content}]],
        "markups": [],
        "sections": [[10, 0]]
    }
    import json
    post = {
        "posts": [{
            "title": title,
            "mobiledoc": json.dumps(mobiledoc),
            "status": "published",
            "visibility": visibility,
            "tags": [{"name": category}],
            "custom_excerpt": summary[:300]
        }]
    }
    r = requests.post(f"{GHOST_API_URL}/ghost/api/admin/posts/", json=post, headers=headers)
    if r.status_code == 201:
        url = r.json()["posts"][0]["url"]
        print(f"    Ghost: published — {url}")
        return url
    else:
        print(f"    Ghost error: {r.status_code} — {r.text[:200]}")
        return None

if __name__ == "__main__":
    publish_to_ghost("Test Post", "## Hello\nThis is a test.", "Test summary.", "Test")
