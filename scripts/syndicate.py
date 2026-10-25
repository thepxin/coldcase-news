"""Share posts to Dev.to and Hashnode, and ping IndexNow.

Modes:
  python scripts/syndicate.py --due
      Shares every post that is at least SYNDICATE_DELAY_HOURS old (default 20) and not yet
      shared, oldest first, at most SYNDICATE_MAX_PER_RUN per run (default 2). Run daily.
      The delay gives you a day to fix a post on the site before copies go out.
      Progress is kept in scripts/syndicated.json so nothing is ever posted twice.
  python scripts/syndicate.py --indexnow content/posts/<file>.md
      Waits until the new page is live, then pings IndexNow only (fast indexing on publish).
  python scripts/syndicate.py content/posts/<file>.md
      Manual: share these posts right now.

Every step is optional: a missing key just skips that service.
Exit code is always 0 so a syndication hiccup never fails the workflow.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "https://coldcasetech.com"
INDEXNOW_KEY = "cctindexnow2026key8941"
DEVTO_API_KEY = os.environ.get("DEVTO_API_KEY", "")
HASHNODE_TOKEN = os.environ.get("HASHNODE_TOKEN", "")
HASHNODE_PUB_ID = os.environ.get("HASHNODE_PUB_ID", "")
WAIT_SECONDS = int(os.environ.get("SYNDICATE_WAIT_SECONDS", "900"))
POLL_EVERY = int(os.environ.get("SYNDICATE_POLL_SECONDS", "30"))
DELAY_HOURS = float(os.environ.get("SYNDICATE_DELAY_HOURS", "20"))
MAX_PER_RUN = int(os.environ.get("SYNDICATE_MAX_PER_RUN", "2"))
MAX_ATTEMPTS = 3
LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "syndicated.json")
POSTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "content", "posts")


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
    try:
        import yaml
        parsed = yaml.safe_load(fm) or {}
        stored_sources = parsed.get("sources") or []
        updates = parsed.get("updates") or []
    except Exception:
        stored_sources, updates = [], []
    return {"title": field("title"), "cover": cover, "body": body, "sources": stored_sources,
            "verdict": field("verdict"), "then": field("then"), "now": field("now"),
            "toolkit": field("toolkit"), "date": field("date"), "desk": field("desk"),
            "status": field("status"), "due": field("due"), "updates": updates}


_COVERS = None


def site_cover(path):
    """The article's own ColdCaseTech cover (1200x504, made by the site; listed in /share/index.json), or ""."""
    global _COVERS
    if _COVERS is None:
        try:
            r = requests.get(f"{BASE_URL}/share/index.json", params={"t": int(time.time())}, timeout=20)
            _COVERS = {i["slug"]: i.get("cover", "") for i in r.json().get("items", [])} if r.ok else {}
        except Exception:
            _COVERS = {}
    return _COVERS.get(os.path.splitext(os.path.basename(path))[0], "")


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
        kit_md = ("\n\n### " + ("Tools related to this case" if post.get("desk") == "tech" else "Toolkit for this kind of incident") + "\n" + lines +
                  "\n\n*These are affiliate links: we may earn a commission at no extra cost to you"
                  + (". As an Amazon Associate, ColdCaseTech earns from qualifying purchases" if amazon else "") + ".*")
    return card_md, kit_md


def build_body(post, canonical):
    body = post["body"].replace("](/go/", f"]({BASE_URL}/go/")
    card_md, kit_md = affiliate_markdown(post)
    src = list(post.get("sources") or [])
    ups = [u for u in post.get("updates") or [] if isinstance(u, dict)]
    for u in ups:
        src += [x for x in u.get("sources") or [] if isinstance(x, dict)]
    if ups:  # dated updates go first, newest first, like on the site
        lines = [f"- **{u.get('date', '')}**: {u.get('text', '')}" for u in sorted(ups, key=lambda u: str(u.get("date")), reverse=True)]
        body = "## Case updates\n" + "\n".join(lines) + "\n\n## Original case\n\n" + body
    if src and "## Sources" not in body:
        body = body.rstrip() + "\n\n## Sources\n" + "\n".join(
            f"- [{x.get('outlet', '')}, {x.get('date', '')}]({x.get('url', '')})" for x in src if x.get("url"))
    body = body.replace("{{< recommend >}}", card_md).rstrip() + kit_md
    disclosure = ("*Disclosure: this post contains affiliate links. We may earn a commission at no extra cost to you.*\n\n"
                  if "/go/" in body else "")
    case = ""
    if post.get("then") and post.get("now"):
        label = ("Open case, no verdict yet" + (f", due {post['due']}" if post.get("due") else "")) \
            if post.get("status") == "open" else ("News report" if post.get("status") == "report"
                                                  else (post.get("verdict") or "Under review"))
        case = (f"> **Then vs. Now ({label}):** "
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
        return "skipped"
    try:
        article = {
            "title": post["title"], "published": True, "body_markdown": md,
            "canonical_url": canonical,
            "tags": ["technology", "news", "tech", "ai"],
        }
        if post["cover"]:
            article["main_image"] = post["cover"]
        r = requests.post("https://dev.to/api/articles",
                          headers={"api-key": DEVTO_API_KEY, "Content-Type": "application/json"},
                          json={"article": article}, timeout=30)
        if r.status_code in (200, 201):
            url = r.json().get("url") or "posted"
            print(f"Dev.to OK -> {url}")
            return url
        print(f"Dev.to WARNING {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"Dev.to ERROR: {e}")
    return None


def post_hashnode(post, canonical, md):
    if not (HASHNODE_TOKEN and HASHNODE_PUB_ID):
        print("Hashnode: skipped (missing token or publication id)")
        return "skipped"
    pub = HASHNODE_PUB_ID.replace("dashboards/", "").strip("/")
    query = "mutation P($input: PublishPostInput!){publishPost(input:$input){post{url}}}"
    inp = {
        "title": post["title"], "publicationId": pub, "contentMarkdown": md,
        "originalArticleURL": canonical,
        "tags": [{"slug": "technology", "name": "Technology"},
                 {"slug": "news", "name": "News"},
                 {"slug": "tech", "name": "Tech"}],
    }
    if post["cover"]:
        inp["coverImageOptions"] = {"coverImageURL": post["cover"]}
    try:
        r = requests.post("https://gql.hashnode.com",
                          headers={"Authorization": HASHNODE_TOKEN, "Content-Type": "application/json"},
                          json={"query": query, "variables": {"input": inp}}, timeout=30)
        data = r.json() if r.status_code == 200 else {}
        if r.status_code == 200 and "errors" not in data:
            url = data["data"]["publishPost"]["post"]["url"] or "posted"
            print(f"Hashnode OK -> {url}")
            return url
        print(f"Hashnode WARNING {r.status_code}: {r.text[:300]}")
    except Exception as e:
        print(f"Hashnode ERROR: {e}")
    return None


def ping_indexnow(urls):
    try:
        r = requests.post("https://api.indexnow.org/indexnow", timeout=15, json={
            "host": "coldcasetech.com", "key": INDEXNOW_KEY,
            "keyLocation": f"{BASE_URL}/{INDEXNOW_KEY}.txt", "urlList": urls})
        print(f"IndexNow status {r.status_code}")
    except Exception as e:
        print(f"IndexNow ERROR: {e}")


def load_ledger():
    try:
        return json.load(open(LEDGER, encoding="utf-8"))
    except Exception:
        return {}


def save_ledger(ledger):
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def post_age_hours(post):
    try:
        d = datetime.strptime(str(post.get("date", ""))[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - d).total_seconds() / 3600
    except Exception:
        return None


def ledger_key(path):
    return "content/posts/" + os.path.basename(path)


def share(path, ledger):
    """Post to every platform not yet done for this file; record results in the ledger."""
    key = ledger_key(path)
    entry = ledger.get(key, {"devto": None, "hashnode": None, "attempts": 0})
    post = read_post(path)
    canonical = canonical_for(path)
    if not wait_until_live(canonical):
        print(f"{key}: page not live yet; will try again next run.")
        return
    md = build_body(post, canonical)
    post["cover"] = site_cover(path) or post["cover"]   # our own cover, not the old stock photo
    entry["attempts"] = entry.get("attempts", 0) + 1
    if not entry.get("devto"):
        entry["devto"] = post_devto(post, canonical, md)
    if not entry.get("hashnode"):
        entry["hashnode"] = post_hashnode(post, canonical, md)
    entry["done"] = bool(entry.get("devto") and entry.get("hashnode")) or entry["attempts"] >= MAX_ATTEMPTS
    if entry["done"] and not (entry.get("devto") and entry.get("hashnode")):
        print(f"{key}: giving up on the failed platform(s) after {MAX_ATTEMPTS} attempts.")
    ledger[key] = entry
    save_ledger(ledger)


def run_due():
    ledger = load_ledger()
    due = []
    for name in sorted(os.listdir(POSTS_DIR)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(POSTS_DIR, name)
        if ledger.get(ledger_key(path), {}).get("done"):
            continue
        try:
            import check_posts
            broken = check_posts.check_file(path)
        except Exception as e:
            broken = [(0, f"citation check could not run: {e}")]
        if broken:
            print(f"{name}: NOT shared: {len(broken)} citation problem(s), e.g. {broken[0][1]}. Fix the post; it is shared on the next run after that.")
            continue
        try:
            age = post_age_hours(read_post(path))
        except Exception as e:
            print(f"{name}: unreadable ({e})")
            continue
        if age is None:
            print(f"{name}: no valid date; skipping.")
        elif age < DELAY_HOURS:
            print(f"{name}: {age:.1f} h old; will share after {DELAY_HOURS:.0f} h (time to fix it on the site first).")
        else:
            due.append(path)
    if not due:
        print("Nothing due for syndication.")
    for path in due[:MAX_PER_RUN]:
        try:
            share(path, ledger)
        except Exception as e:
            print(f"ERROR sharing {path}: {e}")
    if len(due) > MAX_PER_RUN:
        print(f"{len(due) - MAX_PER_RUN} more post(s) due; they will go out on the next runs.")


def run_indexnow(paths):
    urls = [canonical_for(p) for p in paths if wait_until_live(canonical_for(p))]
    if urls:
        ping_indexnow(urls)


def main(paths):
    ledger = load_ledger()
    for path in paths:
        try:
            share(path, ledger)
        except Exception as e:
            print(f"ERROR on {path}: {e}")


if __name__ == "__main__":
    args = sys.argv[1:]
    try:
        if args[:1] == ["--due"]:
            run_due()
        elif args[:1] == ["--indexnow"]:
            run_indexnow(args[1:])
        elif args:
            main(args)
        else:
            print("Usage: syndicate.py --due | --indexnow <post.md>... | <post.md>...")
    except Exception as e:
        print(f"syndicate: unexpected error: {e}")
    sys.exit(0)
