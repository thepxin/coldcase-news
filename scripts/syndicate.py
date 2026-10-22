"""Publish the newest post to Dev.to and Hashnode, then ping IndexNow.

Runs AFTER the post is committed and pushed. It waits until the live page
returns HTTP 200 (your host builds on push), so canonical links are valid.

Usage:  python scripts/syndicate.py content/posts/<file>.md [more files...]
Every step is optional: a missing key just skips that service.
Exit code is always 0 so a syndication hiccup never fails the workflow.
"""
import json
import os
import re
import sys
import time

import requests

BASE_URL = "https://coldcasetech.com"
INDEXNOW_KEY = "cctindexnow2026key8941"
DEVTO_API_KEY = os.environ.get("DEVTO_API_KEY", "")
HASHNODE_TOKEN = os.environ.get("HASHNODE_TOKEN", "")
HASHNODE_PUB_ID = os.environ.get("HASHNODE_PUB_ID", "")
WAIT_SECONDS = int(os.environ.get("SYNDICATE_WAIT_SECONDS", "900"))
POLL_EVERY = int(os.environ.get("SYNDICATE_POLL_SECONDS", "30"))


def read_post(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"No front matter in {path}")
    fm, body = m.group(1), m.group(2).strip()

    def field(name):
        mm = re.search(rf"^{name}:\s*(.+)$", fm, re.M)
        if not mm:
            return ""
        val = mm.group(1).strip()
        try:
            return json.loads(val)
        except Exception:
            return val.strip("\"'")

    img = re.search(r"^\s+image:\s*(.+)$", fm, re.M)
    cover = img.group(1).strip().strip("\"'") if img else ""
    return {"title": field("title"), "cover": cover, "body": body}


def canonical_for(path):
    slug = os.path.splitext(os.path.basename(path))[0]
    return f"{BASE_URL}/posts/{slug}/"


def wait_until_live(url):
    deadline = time.time() + WAIT_SECONDS
    while True:
        try:
            r = requests.get(url, timeout=15, headers={"User-Agent": "cct-syndicate"})
            if r.status_code == 200:
                print(f"LIVE: {url}")
                return True
        except Exception as e:
            print(f"waiting ({e})")
        if time.time() >= deadline:
            print(f"WARNING: {url} not live after {WAIT_SECONDS}s")
            return False
        time.sleep(POLL_EVERY)


def build_body(post, canonical):
    body = post["body"].replace("](/go/", f"]({BASE_URL}/go/")
    return (
        f"> **Originally published on [ColdCaseTech]({canonical}).**\n\n"
        f"{body}\n\n---\n"
        f"*Live KEV + EPSS data is on the [ColdCaseTech Threat Radar]({BASE_URL}/radar/) "
        f"- follow us on [X (@coldcasetech)](https://x.com/coldcasetech).*\n"
    )


def post_devto(post, canonical, md):
    if not DEVTO_API_KEY:
        print("Dev.to: skipped (no DEVTO_API_KEY)")
        return
    try:
        article = {
            "title": post["title"], "published": True, "body_markdown": md,
            "canonical_url": canonical,
            "tags": ["security", "cybersecurity", "cloud", "devops"],
        }
        if post["cover"]:
            article["main_image"] = post["cover"]
        r = requests.post("https://dev.to/api/articles",
                          headers={"api-key": DEVTO_API_KEY, "Content-Type": "application/json"},
                          json={"article": article}, timeout=30)
        if r.status_code in (200, 201):
            print(f"Dev.to OK -> {r.json().get('url')}")
        else:
            print(f"Dev.to WARNING {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"Dev.to ERROR: {e}")


def post_hashnode(post, canonical, md):
    if not (HASHNODE_TOKEN and HASHNODE_PUB_ID):
        print("Hashnode: skipped (missing token or publication id)")
        return
    pub = HASHNODE_PUB_ID.replace("dashboards/", "").strip("/")
    query = "mutation P($input: PublishPostInput!){publishPost(input:$input){post{url}}}"
    inp = {
        "title": post["title"], "publicationId": pub, "contentMarkdown": md,
        "originalArticleURL": canonical,
        "tags": [{"slug": "cybersecurity", "name": "Cybersecurity"},
                 {"slug": "security", "name": "Security"},
                 {"slug": "cloud", "name": "Cloud"}],
    }
    if post["cover"]:
        inp["coverImageOptions"] = {"coverImageURL": post["cover"]}
    try:
        r = requests.post("https://gql.hashnode.com",
                          headers={"Authorization": HASHNODE_TOKEN, "Content-Type": "application/json"},
                          json={"query": query, "variables": {"input": inp}}, timeout=30)
        data = r.json() if r.status_code == 200 else {}
        if r.status_code == 200 and "errors" not in data:
            print(f"Hashnode OK -> {data['data']['publishPost']['post']['url']}")
        else:
            print(f"Hashnode WARNING {r.status_code}: {r.text[:300]}")
    except Exception as e:
        print(f"Hashnode ERROR: {e}")


def ping_indexnow(urls):
    try:
        r = requests.post("https://api.indexnow.org/indexnow", timeout=15, json={
            "host": "coldcasetech.com", "key": INDEXNOW_KEY,
            "keyLocation": f"{BASE_URL}/{INDEXNOW_KEY}.txt", "urlList": urls})
        print(f"IndexNow status {r.status_code}")
    except Exception as e:
        print(f"IndexNow ERROR: {e}")


def main(paths):
    live_urls = []
    for path in paths:
        try:
            post = read_post(path)
            canonical = canonical_for(path)
            live = wait_until_live(canonical)
            md = build_body(post, canonical)
            post_devto(post, canonical, md)
            post_hashnode(post, canonical, md)
            if live:
                live_urls.append(canonical)
        except Exception as e:
            print(f"ERROR on {path}: {e}")
    if live_urls:
        ping_indexnow(live_urls)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/syndicate.py <post.md> ...")
    else:
        main(sys.argv[1:])
    sys.exit(0)
