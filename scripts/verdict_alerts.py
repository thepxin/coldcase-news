"""Email the verdict to the readers who asked for it ("Email me the verdict" on open case pages).

How it fits together:
  1. On an open case page a reader leaves their email. Kit signs them up to ColdCase Weekly as usual, and
     functions/api/follow.js gives them the Kit tag "Verdict: <case slug>".
  2. When the bot closes that case with a verdict, this script (run after every daily run) creates ONE Kit
     broadcast to that tag: the verdict, what was promised, what happened, and a link to the case.
  3. data/verdict_alerts.json remembers which cases were emailed, so nobody gets the same verdict twice.

Kit only sends broadcasts to confirmed (active) subscribers, so a reader who never confirmed gets nothing.

Settings (GitHub > Settings > Secrets and variables > Actions):
  secret   KIT_API_KEY          the same Kit V4 key the weekly email uses
  variable VERDICT_EMAIL_MODE   send (default: Kit sends it ~15 minutes later) or draft (it waits in Kit for you)
Usage: python scripts/verdict_alerts.py [--dry-run]
"""
import html
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cases  # noqa: E402

BASE_URL = "https://coldcasetech.com"
KIT_API = os.environ.get("KIT_API_URL", "https://api.kit.com/v4").rstrip("/")
LEDGER = "data/verdict_alerts.json"
UTM = "?utm_source=verdict-alert&utm_medium=email"
TAG_PREFIX = "Verdict: "
GIVE_UP_DAYS = 7   # a case nobody confirmed for within a week of closing is marked done (0 emails)


def esc(t):
    return html.escape(str(t or ""), quote=True)


def load_ledger():
    try:
        return json.load(open(LEDGER, encoding="utf-8"))
    except Exception:
        return {"sent": {}}


def save_ledger(led):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(led, f, ensure_ascii=False, indent=1)
        f.write("\n")


def closed_on(case):
    """Date the case went from open to closed (from its updates), else its last activity."""
    day = None
    for u in case.get("updates") or []:
        if u.get("status_from") == "open" and u.get("status_to") == "closed":
            day = cases._day(u.get("date"))
    return day or cases.last_activity(case)


class Kit:
    def __init__(self, key):
        self.h = {"X-Kit-Api-Key": key, "Content-Type": "application/json", "Accept": "application/json"}

    def get(self, path, **params):
        r = requests.get(f"{KIT_API}{path}", headers=self.h, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def verdict_tags(self):
        """{case slug: tag id} for every "Verdict: <slug>" tag in the account."""
        out, after = {}, None
        while True:
            page = self.get("/tags", per_page=1000, **({"after": after} if after else {}))
            for t in page.get("tags", []):
                name = str(t.get("name", ""))
                if name.lower().startswith(TAG_PREFIX.lower()):
                    out[name[len(TAG_PREFIX):].strip()] = t["id"]
            pg = page.get("pagination") or {}
            if not pg.get("has_next_page"):
                return out
            after = pg.get("end_cursor")

    def active_count(self, tag_id):
        page = self.get(f"/tags/{tag_id}/subscribers", status="active", per_page=1000, slim="true")
        return len(page.get("subscribers", []))

    def broadcast(self, payload):
        r = requests.post(f"{KIT_API}/broadcasts", headers=self.h, json=payload, timeout=30)
        return r.status_code, r.text


def email_for(case):
    url = f"{BASE_URL}/posts/{case['_slug']}/"
    verdict = case.get("verdict") or "Closed"
    title = str(case.get("title", ""))
    subject = f"Verdict: {verdict}. {title}"
    if len(subject) > 140:
        subject = subject[:137].rstrip() + "..."
    preview = f"You asked to hear when this case closed. Verdict: {verdict}."
    parts = [
        "<p>You asked us to email you when this case closed. It has.</p>",
        f"<h2>{esc(title)}</h2>",
        f"<p><b>Verdict: {esc(verdict)}</b></p>",
    ]
    if case.get("then"):
        parts.append(f"<p><b>Promised:</b> {esc(case['then'])}</p>")
    if case.get("now"):
        parts.append(f"<p><b>What happened:</b> {esc(case['now'])}</p>")
    parts.append(f'<p><a href="{esc(url + UTM)}">Read the verdict and every source</a></p>')
    parts.append("<p>This is the only email about this case. ColdCase Weekly continues as usual. "
                 "Spotted an error? Reply to this email.</p>")
    return subject, preview, "\n".join(parts)


def main(dry_run=False):
    now = datetime.now(timezone.utc)
    mode = os.environ.get("VERDICT_EMAIL_MODE", "send").strip().lower()
    mode = mode if mode in ("send", "draft") else "send"
    led = load_ledger()
    sent = led.setdefault("sent", {})
    closed = [c for c in cases.load_cases() if c.get("status") == "closed" and c.get("verdict")
              and c["_slug"] not in sent]
    if not closed:
        print("Verdict emails: no newly closed cases.")
        return 0
    key = os.environ.get("KIT_API_KEY", "").strip()
    if not key:
        print("Verdict emails: KIT_API_KEY is not set, so no verdict emails are sent.")
        return 0
    kit = Kit(key)
    try:
        tags = kit.verdict_tags()
    except Exception as e:
        print(f"::warning::Verdict emails: could not read Kit tags ({str(e)[:160]}). Will try again next run.")
        return 0
    changed = False
    for c in closed:
        slug = c["_slug"]
        tag = tags.get(slug)
        if not tag:
            continue   # nobody asked for this verdict
        try:
            n = kit.active_count(tag)
        except Exception as e:
            print(f"::warning::Verdict emails: could not count readers for {slug} ({str(e)[:120]}).")
            continue
        if n == 0:
            day = closed_on(c)
            if day and (now - day).days >= GIVE_UP_DAYS:
                sent[slug] = {"date": now.strftime("%Y-%m-%d"), "readers": 0, "note": "no confirmed readers"}
                changed = True
            print(f"Verdict emails: {slug}: no confirmed readers yet.")
            continue
        subject, preview, body = email_for(c)
        print(f"Verdict emails: {slug}: {n} reader(s). Subject: {subject}")
        if dry_run:
            print(body)
            continue
        payload = {"subject": subject, "preview_text": preview, "content": body,
                   "description": f"Verdict email for {slug} (created automatically)", "public": False,
                   "published_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "send_at": (now + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ") if mode == "send" else None,
                   "subscriber_filter": [{"all": [{"type": "tag", "ids": [int(tag)]}], "any": None, "none": None}]}
        code, text = kit.broadcast(payload)
        if code not in (200, 201):
            print(f"::warning::Verdict emails: Kit did not accept the email for {slug} ({code}): {text[:300]}")
            continue
        try:
            bid = json.loads(text).get("broadcast", {}).get("id")
        except Exception:
            bid = None
        sent[slug] = {"date": now.strftime("%Y-%m-%d"), "readers": n, "mode": mode, "broadcast_id": bid}
        changed = True
        print(f"Verdict emails: {'scheduled (Kit sends it in about 15 minutes)' if mode == 'send' else 'draft created in Kit'}"
              f" for {slug}.")
    if changed and not dry_run:
        save_ledger(led)
    return 0


if __name__ == "__main__":
    sys.exit(main(dry_run="--dry-run" in sys.argv))
