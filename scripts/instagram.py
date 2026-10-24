"""Post new ColdCaseTech articles to Instagram, automatically and through Instagram's official API.

How it works
  1. Reads https://coldcasetech.com/share/index.json (built by the site): every recent article with its 1080x1350
     JPEG image and its fact-checked caption.
  2. Posts each article that is not yet in data/instagram_log.json and is less than MAX_AGE_HOURS old
     (oldest first, at most MAX_PER_RUN per run), using the Instagram Graph API:
     create a media container (image_url + caption) -> wait until it is FINISHED -> media_publish.
  3. Records every post in data/instagram_log.json, so nothing is ever posted twice.

Needs one GitHub secret: IG_ACCESS_TOKEN (a long-lived Instagram User token with instagram_business_basic and
instagram_business_content_publish, from Meta's App Dashboard). It lasts 60 days. This script refreshes it every
REFRESH_DAYS days; if the secret GH_SECRETS_TOKEN is also set, the new token is saved back to IG_ACCESS_TOKEN
automatically. Without it, the log warns you 10 days before the token expires.

Modes (env IG_MODE): post (default) | dry-run (prints what it would post) | skip-existing (marks the current
articles as done without posting them, e.g. if you already posted them by hand).
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

SITE = os.environ.get("SITE_BASE", "https://coldcasetech.com").rstrip("/")
GRAPH = os.environ.get("GRAPH_BASE", "https://graph.instagram.com/v26.0").rstrip("/")
REFRESH_URL = os.environ.get("REFRESH_URL", "https://graph.instagram.com/refresh_access_token")
LOG = "data/instagram_log.json"
MAX_AGE_HOURS = int(os.environ.get("IG_MAX_AGE_HOURS", "48"))
MAX_PER_RUN = 3
REFRESH_DAYS = 7
WAIT_FOR_SITE_MIN = int(os.environ.get("IG_WAIT_MINUTES", "15"))  # the site rebuilds 1-3 minutes after a new article
POLL = int(os.environ.get("IG_POLL_SECONDS", "30"))


def now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def load_log():
    try:
        with open(LOG, encoding="utf-8") as f:
            log = json.load(f)
    except (OSError, ValueError):
        log = {}
    log.setdefault("posted", {})
    log.setdefault("token", {})
    return log


def save_log(log):
    os.makedirs("data", exist_ok=True)
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def api_error(r):
    try:
        e = r.json().get("error", {})
        return f"{r.status_code} {e.get('type', '')}: {e.get('message', r.text[:200])}"
    except ValueError:
        return f"{r.status_code}: {r.text[:200]}"


def local_recent_posts():
    """Articles in this checkout that are recent and have a share kit: the site should list them once it has rebuilt."""
    out = []
    cut = now() - timedelta(hours=MAX_AGE_HOURS)
    for name in sorted(os.listdir("content/posts")) if os.path.isdir("content/posts") else []:
        path = os.path.join("content/posts", name)
        head = open(path, encoding="utf-8").read().split("\n---\n", 1)[0]
        if "\nsocial:\n" not in head:
            continue
        for line in head.splitlines():
            if line.startswith("date:"):
                try:
                    if parse(line.split(":", 1)[1].strip().strip('"')) > cut:
                        out.append(name[:-3])
                except ValueError:
                    pass
    return out


def fetch_index(expect):
    """Fetch the site's list, waiting (up to WAIT_FOR_SITE_MIN) until it includes every article this checkout has."""
    deadline = time.time() + WAIT_FOR_SITE_MIN * 60
    while True:
        try:
            r = requests.get(f"{SITE}/share/index.json", params={"t": int(time.time())}, timeout=30)
            items = r.json().get("items", []) if r.ok else []
        except (requests.RequestException, ValueError):
            items = []
        missing = sorted(set(expect) - {i["slug"] for i in items})
        if not missing or time.time() > deadline:
            if missing:
                print(f"The site does not list these yet (still rebuilding?): {', '.join(missing)}. They will be posted next run.")
            return items
        print(f"Waiting for the site to rebuild ({len(missing)} new article(s) not listed yet)...")
        time.sleep(POLL)


def publish(token, user_id, item):
    """Container -> wait for FINISHED -> publish. Returns (media_id, "") or ("", error)."""
    img = requests.head(item["image"], timeout=30, allow_redirects=True)
    if not img.ok or "jpeg" not in img.headers.get("content-type", ""):
        return "", f"image not reachable as JPEG ({img.status_code} {img.headers.get('content-type', '')})"
    r = requests.post(f"{GRAPH}/{user_id}/media", data={"image_url": item["image"], "caption": item["caption"],
                                                       "access_token": token}, timeout=60)
    if not r.ok:
        return "", "create: " + api_error(r)
    cid = r.json()["id"]
    for _ in range(10):  # Meta: check about once a minute, no more than 5 minutes
        s = requests.get(f"{GRAPH}/{cid}", params={"fields": "status_code", "access_token": token}, timeout=30)
        code = s.json().get("status_code", "") if s.ok else ""
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            return "", f"container {code}"
        time.sleep(POLL)
    else:
        return "", "container not ready after 5 minutes"
    p = requests.post(f"{GRAPH}/{user_id}/media_publish", data={"creation_id": cid, "access_token": token}, timeout=60)
    if not p.ok:
        return "", "publish: " + api_error(p)
    return p.json()["id"], ""


def maybe_refresh(token, log):
    """Keep the 60-day token alive. Never prints the token."""
    fp = hashlib.sha256(token.encode()).hexdigest()[:12]
    t = log["token"]
    if t.get("fingerprint") != fp:  # a new token was pasted into the secret
        t.clear()
        t.update({"fingerprint": fp, "first_seen": iso(now())})
    since = parse(t.get("refreshed") or t["first_seen"])
    age_days = (now() - since).days
    if age_days >= 50:
        print(f"WARNING: the Instagram token is about {age_days} days old and stops working at 60. "
              "Generate a new one in Meta's App Dashboard and paste it into the IG_ACCESS_TOKEN secret.")
    if age_days < REFRESH_DAYS or not os.environ.get("GH_SECRETS_TOKEN"):
        return token
    r = requests.get(REFRESH_URL, params={"grant_type": "ig_refresh_token", "access_token": token}, timeout=30)
    if not r.ok:
        print("Token refresh failed: " + api_error(r))
        return token
    new = r.json().get("access_token", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if new and repo:
        done = subprocess.run(["gh", "secret", "set", "IG_ACCESS_TOKEN", "--repo", repo, "--body", new],
                              env={**os.environ, "GH_TOKEN": os.environ["GH_SECRETS_TOKEN"]},
                              capture_output=True, text=True)
        if done.returncode == 0:
            t.update({"fingerprint": hashlib.sha256(new.encode()).hexdigest()[:12], "refreshed": iso(now())})
            print("Instagram token refreshed and saved (valid for 60 more days).")
            return new
        print("Token refreshed, but saving it to GitHub failed: " + (done.stderr or "")[:200])
    return token


def main():
    mode = (os.environ.get("IG_MODE") or "post").strip().lower()
    token = (os.environ.get("IG_ACCESS_TOKEN") or "").strip()
    if not token:
        print("Instagram is not connected yet (no IG_ACCESS_TOKEN secret). Nothing to do.")
        return 0
    log = load_log()
    items = fetch_index(local_recent_posts())
    cut = now() - timedelta(hours=MAX_AGE_HOURS)
    todo = [i for i in items if i["slug"] not in log["posted"] and parse(i["date"]) > cut]
    print(f"{len(items)} article(s) on the share list; {len(todo)} not yet on Instagram.")
    if mode == "skip-existing":
        for i in todo:
            log["posted"][i["slug"]] = {"skipped": True, "posted_at": iso(now())}
            print(f"  marked as done without posting: {i['slug']}")
        save_log(log)
        return 0
    if mode == "dry-run":
        for i in todo[:MAX_PER_RUN]:
            print(f"\n--- would post {i['slug']}\nimage: {i['image']}\ncaption:\n{i['caption']}")
        return 0
    me = requests.get(f"{GRAPH}/me", params={"fields": "user_id,username", "access_token": token}, timeout=30)
    if not me.ok:
        print("Instagram rejected the token: " + api_error(me))
        print("Fix: generate a new token in Meta's App Dashboard and paste it into the IG_ACCESS_TOKEN secret.")
        return 1
    user_id = os.environ.get("IG_USER_ID") or me.json().get("user_id") or me.json().get("id")
    print(f"Posting as @{me.json().get('username', '?')}.")
    token = maybe_refresh(token, log)
    failed = 0
    for i in todo[:MAX_PER_RUN]:
        media_id, err = publish(token, user_id, i)
        if media_id:
            log["posted"][i["slug"]] = {"media_id": media_id, "posted_at": iso(now())}
            print(f"  POSTED {i['slug']} (media {media_id})")
        else:
            failed += 1
            print(f"  NOT posted {i['slug']}: {err.rstrip('.')}. It will be tried again next run.")
        save_log(log)
    if len(todo) > MAX_PER_RUN:
        print(f"{len(todo) - MAX_PER_RUN} more will be posted next run.")
    save_log(log)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
