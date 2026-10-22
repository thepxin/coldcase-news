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
    return {"title": field("title"), "cover": cover, "body": body,
            "verdict": field("verdict"), "then": field("then"), "now": field("now"),
            "toolkit": field("toolkit")}


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


AFFILIATES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "affiliates.json")


def affiliate_markdown(post):
    """Same picks as the site templates: card + up to 3 toolkit items, skipping products already linked."""
    try:
        d = json.load(open(AFFILIATES_FILE, encoding="utf-8"))
        cat = d["categories"][post.get("toolkit") or ""]
    except Exception:
        return "", ""
    products = d["products"]
    pool = [cat["card"]] + list(cat["toolkit"])
    free = [k for k in pool if k in products and f"/go/{k}.html" not in post["body"]]
    card = next((k for k in free if products[k].get("card_title")), "")
    kit = [k for k in free if k != card][:3]
    card_md = ""
    if card:
        c = products[card]
        card_md = (f"> **{c['card_title']}.** {c['card_text']} "
                   f"[{c['card_cta']}]({BASE_URL}{c['url']}) *(affiliate link)*")
    kit_md = ""
    if kit:
        amazon = any(products[k].get("amazon") for k in kit)
        lines = "\n".join(f"- {products[k]['kit_line']}: [{products[k]['name']}]({BASE_URL}{products[k]['url']})" for k in kit)
        kit_md = ("\n\n### Toolkit for this kind of incident\n" + lines +
                  "\n\n*These are affiliate links: we may earn a commission at no extra cost to you"
                  + (". As an Amazon Associate, ColdCaseTech earns from qualifying purchases" if amazon else "") + ".*")
    return card_md, kit_md


def build_body(post, canonical):
    body = post["body"].replace("](/go/", f"]({BASE_URL}/go/")
    card_md, kit_md = affiliate_markdown(post)
    body = body.replace("{{< recommend >}}", card_md).rstrip() + kit_md
    disclosure = ("*Disclosure: this post contains affiliate links. We may earn a commission at no extra cost to you.*\n\n"
                  if "/go/" in body else "")
    case = ""
    if post.get("then") and post.get("now"):
        case = (f"> **Then vs. Now ({post.get('verdict') or 'Under review'}):** "
                f"**Then:** {post['then']} **Now:** {post['now']}\n\n")
    return (
        f"> **Originally published on [ColdCaseTech]({canonical}).**\n\n"
        f"{disclosure}"
        f"{case}"
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
