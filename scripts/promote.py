"""Promote each new article on Bluesky and on a Telegram channel, automatically, through their official APIs.

For every article published in the last MAX_AGE_HOURS that is not yet in data/promoted.json:
  Bluesky   a post with the fact-checked hook (and the verdict or due date), plus a link card showing the article's
            ColdCaseTech share image, title and summary. 300-character limit.
  Telegram  a photo post in your channel: the share image, the headline, the hook, and a "Read the full story" button.
Both use only text that already passed the fact-check (the article's hook, headline and summary).

Each platform turns on when its secrets exist and stays off otherwise:
  Bluesky:  BLUESKY_HANDLE (e.g. coldcasetech.bsky.social) and BLUESKY_APP_PASSWORD (Settings > App passwords)
  Telegram: TELEGRAM_BOT_TOKEN (from @BotFather) and TELEGRAM_CHAT_ID (e.g. @coldcasetech; the bot must be a channel admin)

Modes (env PROMOTE_MODE): post (default) | dry-run (show what would be posted) | skip-existing (mark current articles as
done without posting, e.g. on the first run). Nothing is ever posted twice: data/promoted.json records each post.
"""
import html
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import requests
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import social  # noqa: E402

SITE = os.environ.get("SITE_BASE", "https://coldcasetech.com").rstrip("/")
BSKY = os.environ.get("BSKY_BASE", "https://bsky.social").rstrip("/")
TG = os.environ.get("TELEGRAM_BASE", "https://api.telegram.org").rstrip("/")
LOG = "data/promoted.json"
POSTS = "content/posts"
MAX_AGE_HOURS = int(os.environ.get("PROMOTE_MAX_AGE_HOURS", "48"))
MAX_PER_RUN = 3
WAIT_FOR_SITE_MIN = int(os.environ.get("PROMOTE_WAIT_MINUTES", "15"))
POLL = int(os.environ.get("PROMOTE_POLL_SECONDS", "30"))
BSKY_LIMIT = 300
THUMB_MAX = 950_000   # Bluesky rejects link-card images over ~1 MB
TG_CAPTION = 1024


def now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def load_log():
    try:
        with open(LOG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_log(log):
    os.makedirs("data", exist_ok=True)
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def recent_articles():
    """Articles from this checkout published in the last MAX_AGE_HOURS that have a share kit, oldest first."""
    out, cut = [], now() - timedelta(hours=MAX_AGE_HOURS)
    for name in sorted(os.listdir(POSTS)) if os.path.isdir(POSTS) else []:
        if not name.endswith(".md"):
            continue
        text = open(os.path.join(POSTS, name), encoding="utf-8").read()
        if not text.startswith("---\n"):
            continue
        try:
            fm = yaml.safe_load(text[4:].split("\n---\n", 1)[0]) or {}
        except yaml.YAMLError:
            continue
        try:
            date = datetime.strptime(str(fm.get("date", ""))[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if date > cut and fm.get("social"):
            out.append({"slug": name[:-3], "fm": fm, "date": date})
    return sorted(out, key=lambda a: a["date"])


def site_cards(expect):
    """{slug: share-image URL} from the site, waiting (up to WAIT_FOR_SITE_MIN) until the new articles are listed."""
    deadline = time.time() + WAIT_FOR_SITE_MIN * 60
    while True:
        try:
            r = requests.get(f"{SITE}/share/index.json", params={"t": int(time.time())}, timeout=30)
            cards = {i["slug"]: i.get("card", "") for i in r.json().get("items", [])} if r.ok else {}
        except (requests.RequestException, ValueError):
            cards = {}
        missing = sorted(set(expect) - set(cards))
        if not missing or time.time() > deadline:
            if missing:
                print(f"The site does not list these yet (still rebuilding?): {', '.join(missing)}. Next run.")
            return cards
        print(f"Waiting for the site to rebuild ({len(missing)} article(s) not listed yet)...")
        time.sleep(POLL)


def pieces(a):
    fm, s = a["fm"], a["fm"]["social"]
    status = social._status_line(fm.get("status", ""), fm.get("verdict", ""), fm.get("due", ""))
    field = next((t for t in fm.get("tags", []) if str(t).lower() != "tech"), "")
    return {"title": fm.get("title", ""), "hook": (s.get("hook") or fm.get("description") or "").strip(),
            "summary": (fm.get("description") or "").strip(), "status": status, "field": field,
            "url": f"{SITE}/posts/{a['slug']}/"}


# ---------------- Bluesky ----------------
def bluesky_text(p):
    short = social.FIELD_TAGS.get(p["field"].lower(), re.sub(r"[^A-Za-z0-9]", "", p["field"])) if p["field"] else ""
    tags = ["TechNews"] + ([short] if short else [])   # e.g. "Cloud and Infrastructure" -> #Cloud
    tag_line = " ".join("#" + t for t in tags if t)
    for parts in ([p["hook"], p["status"], tag_line], [p["hook"], p["status"]], [p["hook"]]):
        text = "\n\n".join(x for x in parts if x)
        if len(text) <= BSKY_LIMIT:
            return text
    return social._trim(p["hook"], BSKY_LIMIT)


def hashtag_facets(text):
    """Make #tags clickable: Bluesky needs their byte positions."""
    facets, b = [], text.encode("utf-8")
    for m in re.finditer(r"(?<!\w)#([A-Za-z][A-Za-z0-9]*)", text):
        start = len(text[:m.start()].encode("utf-8"))
        end = start + len(m.group(0).encode("utf-8"))
        if b[start:end].decode("utf-8") == m.group(0):
            facets.append({"index": {"byteStart": start, "byteEnd": end},
                           "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": m.group(1)}]})
    return facets


def bluesky_login():
    handle, pw = os.environ.get("BLUESKY_HANDLE", "").strip(), os.environ.get("BLUESKY_APP_PASSWORD", "").strip()
    if not (handle and pw):
        return None, "not connected (no BLUESKY_HANDLE / BLUESKY_APP_PASSWORD secrets)"
    r = requests.post(f"{BSKY}/xrpc/com.atproto.server.createSession", json={"identifier": handle.lstrip("@"), "password": pw},
                      timeout=30)
    if not r.ok:
        return None, f"login failed ({r.status_code}: {r.text[:160]}). Check the handle and the app password."
    d = r.json()
    return {"did": d["did"], "jwt": d["accessJwt"]}, ""


def bluesky_post(sess, p, card_url):
    head = {"Authorization": f"Bearer {sess['jwt']}"}
    external = {"uri": p["url"], "title": p["title"][:300], "description": p["summary"][:300]}
    if card_url:
        try:
            img = requests.get(card_url, timeout=30)
            if img.ok and len(img.content) <= THUMB_MAX:
                up = requests.post(f"{BSKY}/xrpc/com.atproto.repo.uploadBlob", data=img.content, timeout=60,
                                   headers={**head, "Content-Type": img.headers.get("content-type", "image/png")})
                if up.ok:
                    external["thumb"] = up.json()["blob"]
        except requests.RequestException:
            pass   # the post still goes out, just without the picture on the link card
    text = bluesky_text(p)
    record = {"$type": "app.bsky.feed.post", "text": text, "createdAt": iso(now()), "langs": ["en"],
              "embed": {"$type": "app.bsky.embed.external", "external": external}}
    facets = hashtag_facets(text)
    if facets:
        record["facets"] = facets
    r = requests.post(f"{BSKY}/xrpc/com.atproto.repo.createRecord", headers=head, timeout=30,
                      json={"repo": sess["did"], "collection": "app.bsky.feed.post", "record": record})
    if not r.ok:
        return "", f"{r.status_code}: {r.text[:200]}"
    return r.json().get("uri", "posted"), ""


# ---------------- Telegram ----------------
def telegram_caption(p):
    e = lambda t: html.escape(t, quote=False)
    parts = [f"<b>{e(p['title'])}</b>", e(p["hook"]) if p["hook"] != p["title"] else "", e(p["status"]),
             "Every line links to its source."]
    text = "\n\n".join(x for x in parts if x)
    if len(re.sub(r"<[^>]+>", "", html.unescape(text))) > TG_CAPTION:
        text = f"<b>{e(p['title'])}</b>"
    return text


def telegram_post(p, card_url):
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(), os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    button = {"inline_keyboard": [[{"text": "Read the full story", "url": p["url"]}]]}
    if card_url:
        r = requests.post(f"{TG}/bot{token}/sendPhoto", timeout=60, json={
            "chat_id": chat, "photo": card_url, "caption": telegram_caption(p), "parse_mode": "HTML", "reply_markup": button})
    else:
        r = requests.post(f"{TG}/bot{token}/sendMessage", timeout=60, json={
            "chat_id": chat, "text": telegram_caption(p) + f"\n\n{html.escape(p['url'])}", "parse_mode": "HTML",
            "reply_markup": button})
    d = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if not (r.ok and d.get("ok")):
        return "", f"{r.status_code}: {d.get('description', r.text[:200])}"
    return str(d["result"]["message_id"]), ""


def main():
    mode = (os.environ.get("PROMOTE_MODE") or "post").strip().lower()
    want = {"bluesky": bool(os.environ.get("BLUESKY_HANDLE") and os.environ.get("BLUESKY_APP_PASSWORD")),
            "telegram": bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))}
    on = [k for k, v in want.items() if v]
    if not on and mode != "dry-run":
        print("Neither Bluesky nor Telegram is connected yet (no secrets). Nothing to do.")
        return 0
    log = load_log()
    articles = recent_articles()
    todo = [a for a in articles if any(not log.get(a["slug"], {}).get(ch) for ch in (on or want))]
    print(f"Connected: {', '.join(on) or 'none'}. {len(articles)} recent article(s); {len(todo)} still to share.")
    if mode == "skip-existing":
        for a in todo:
            for ch in on:
                log.setdefault(a["slug"], {}).setdefault(ch, "skipped")
            print(f"  marked as done without posting: {a['slug']}")
        save_log(log)
        return 0
    cards = site_cards([a["slug"] for a in todo]) if todo else {}
    if mode == "dry-run":
        for a in todo[:MAX_PER_RUN]:
            p = pieces(a)
            print(f"\n--- {a['slug']}\ncard: {cards.get(a['slug'], '(not listed yet)')}\n"
                  f"BLUESKY ({len(bluesky_text(p))}/{BSKY_LIMIT}):\n{bluesky_text(p)}\n[link card: {p['url']}]\n"
                  f"TELEGRAM:\n{telegram_caption(p)}\n[button: Read the full story -> {p['url']}]")
        return 0
    sess, why = (bluesky_login() if "bluesky" in on else (None, ""))
    failed = 0
    if "bluesky" in on and not sess:
        print("Bluesky: " + why)
        on.remove("bluesky")
        failed += 1
    for a in [a for a in todo if a["slug"] in cards][:MAX_PER_RUN]:
        p, card = pieces(a), cards.get(a["slug"], "")
        entry = log.setdefault(a["slug"], {})
        for ch in on:
            if entry.get(ch):
                continue
            ref, err = bluesky_post(sess, p, card) if ch == "bluesky" else telegram_post(p, card)
            if ref:
                entry[ch] = ref
                print(f"  {ch}: POSTED {a['slug']}")
            else:
                failed += 1
                print(f"  {ch}: NOT posted {a['slug']} ({err}). It will be tried again next run.")
        if entry:
            entry["at"] = iso(now())
        save_log(log)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
