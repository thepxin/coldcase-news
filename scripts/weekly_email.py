"""ColdCase Weekly: build the weekly email from the published case files and create it in Kit.

What goes in (only cases already live on the site, never drafts or unmerged pull requests):
  1. Verdicts this week: open cases that closed, and verdicts that changed (old -> new, with the date)
  2. New cases: every case published since the last email
  3. Other updates: dated updates that did not change a verdict
  4. Still watching: open cases and their due dates (only shown when there is something new above)
If nothing new happened, no email is created.

Each item is sent once: data/weekly_email.json remembers what was already included.

Usage (from .github/workflows/weekly_email.yml):
  python scripts/weekly_email.py preview   -> writes the email to the Actions page only (no Kit call)
  python scripts/weekly_email.py draft     -> creates a DRAFT in Kit; you review it and press Send in Kit
  python scripts/weekly_email.py send      -> schedules it in Kit to go out 15 minutes later
Needs the GitHub secret KIT_API_KEY (a Kit V4 API key) for draft and send.
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
KIT_API = os.environ.get("KIT_API_URL", "https://api.kit.com/v4")
LEDGER = "data/weekly_email.json"
LOOKBACK_DAYS = 21          # items older than this are never sent (so a first run does not dump the archive)
UTM = "?utm_source=coldcase-weekly&utm_medium=email"


def _day(v):
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def load_ledger():
    try:
        return json.load(open(LEDGER, encoding="utf-8"))
    except Exception:
        return {"sent": [], "emails": []}


def save_ledger(led, now):
    # keep only recent keys so the file stays small
    cutoff = (now - timedelta(days=LOOKBACK_DAYS + 30)).strftime("%Y-%m-%d")
    led["sent"] = sorted({k for k in led["sent"] if k.split("|")[-1] >= cutoff})
    led["emails"] = led["emails"][-20:]
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(led, f, ensure_ascii=False, indent=1)
        f.write("\n")


def url_for(case):
    return f"{BASE_URL}/posts/{case['_slug']}/"


def collect(all_cases, sent, now):
    """Return (verdicts, new_cases, other_updates, watching, keys)."""
    since = now - timedelta(days=LOOKBACK_DAYS)
    verdicts, new_cases, other, keys = [], [], [], []
    for c in all_cases:
        pub = _day(c.get("date"))
        k = f"case|{c['_slug']}|{pub.strftime('%Y-%m-%d') if pub else ''}"
        if pub and since <= pub <= now and k not in sent:
            new_cases.append(c)
            keys.append(k)
        for u in c.get("updates") or []:
            d = _day(u.get("date"))
            uk = f"update|{c['_slug']}|{u.get('date', '')}"
            if not d or not (since <= d <= now) or uk in sent:
                continue
            keys.append(uk)
            changed = u.get("verdict_to") and u.get("verdict_to") != u.get("verdict_from")
            (verdicts if changed else other).append((c, u))
    watching = sorted([c for c in all_cases if c.get("status") == "open"], key=lambda c: str(c.get("due_by") or "9999"))
    closed_now = {c["_slug"] for c, _ in verdicts}
    new_cases = [c for c in new_cases if c["_slug"] not in closed_now]  # already listed under "Verdicts this week"
    new_cases.sort(key=lambda c: str(c.get("date")), reverse=True)
    return verdicts, new_cases, other, watching, keys


def nice(v):
    d = _day(v)
    return d.strftime("%b %-d") if d else str(v or "")


def esc(t):
    return html.escape(str(t or ""), quote=True)


def label(c):
    if c.get("status") == "open":
        return f"Open case, due {c.get('due', '')}".strip(", ")
    if c.get("status") == "report":
        return "News report"
    return c.get("verdict") or ""


def desk(c):
    return "Security Friday" if c.get("desk") == "security" else "Tech"


def build(verdicts, new_cases, other, watching, now):
    """Returns (subject, preview_text, html, markdown)."""
    parts, md = [], []
    n_v, n_new = len(verdicts), len(new_cases)
    bits = []
    if n_v:
        bits.append(f"{n_v} verdict{'s' if n_v != 1 else ''} in")
    if n_new:
        bits.append(f"{n_new} new case{'s' if n_new != 1 else ''}")
    if other and not bits:
        bits.append(f"{len(other)} case update{'s' if len(other) != 1 else ''}")
    subject = "ColdCase Weekly: " + ", ".join(bits)
    first = (verdicts[0][0].get("title") if verdicts else (new_cases[0].get("title") if new_cases else other[0][0].get("title")))
    preview = str(first or "What they promised. What actually happened.")[:140]

    parts.append("<p>What they promised, what actually happened: the cases that moved this week. "
                 "Every case links to its sources.</p>")
    md.append("What they promised, what actually happened: the cases that moved this week.")

    if verdicts:
        parts.append("<h2>Verdicts this week</h2><ul>")
        md.append("\n## Verdicts this week")
        for c, u in verdicts:
            frm = u.get("verdict_from") or "Open case"
            parts.append(f'<li><a href="{esc(url_for(c))}{UTM}"><strong>{esc(c.get("title"))}</strong></a><br>'
                         f'<s>{esc(frm)}</s> &rarr; <strong>{esc(u.get("verdict_to"))}</strong> on {esc(nice(u.get("date")))}. '
                         f'{esc(u.get("summary"))}</li>')
            md.append(f"- **{c.get('title')}**: ~~{frm}~~ -> {u.get('verdict_to')} on {nice(u.get('date'))}. {u.get('summary')}")
        parts.append("</ul>")

    if new_cases:
        parts.append("<h2>New cases</h2><ul>")
        md.append("\n## New cases")
        for c in new_cases:
            parts.append(f'<li><a href="{esc(url_for(c))}{UTM}"><strong>{esc(c.get("title"))}</strong></a><br>'
                         f'{esc(desk(c))} &middot; {esc(label(c))}<br>'
                         f'<em>Then:</em> {esc(c.get("then"))}<br><em>Now:</em> {esc(c.get("now"))}</li>')
            md.append(f"- **{c.get('title')}** ({desk(c)}, {label(c)})")
        parts.append("</ul>")

    if other:
        parts.append("<h2>Other case updates</h2><ul>")
        md.append("\n## Other case updates")
        for c, u in other:
            parts.append(f'<li><a href="{esc(url_for(c))}{UTM}">{esc(c.get("title"))}</a>: {esc(u.get("summary"))} '
                         f'({esc(nice(u.get("date")))})</li>')
            md.append(f"- {c.get('title')}: {u.get('summary')} ({nice(u.get('date'))})")
        parts.append("</ul>")

    new_slugs = {c["_slug"] for c in new_cases}
    still = [c for c in watching if c["_slug"] not in new_slugs]
    if still:
        parts.append("<h2>Still watching</h2><ul>")
        md.append("\n## Still watching")
        for c in still[:8]:
            parts.append(f'<li><a href="{esc(url_for(c))}{UTM}">{esc(c.get("title"))}</a>: due {esc(c.get("due"))}</li>')
            md.append(f"- {c.get('title')}: due {c.get('due')}")
        parts.append("</ul>")

    parts.append(f'<p>All open cases and recent changes: <a href="{BASE_URL}/developing/{UTM}">Developing</a>. '
                 f'How we check: <a href="{BASE_URL}/about/{UTM}">How we verify</a>. '
                 "Spotted an error? Reply to this email.</p>")
    return subject, preview, "\n".join(parts), "\n".join(md)


def kit_post(payload, key):
    r = requests.post(f"{KIT_API}/broadcasts", json=payload, timeout=30,
                      headers={"X-Kit-Api-Key": key, "Content-Type": "application/json", "Accept": "application/json"})
    return r.status_code, r.text


def create_in_kit(subject, preview, body, mode, now):
    key = os.environ.get("KIT_API_KEY", "").strip()
    if not key:
        print("::error::The KIT_API_KEY secret is missing. Add it in Settings > Secrets and variables > Actions.")
        return None
    payload = {"subject": subject, "preview_text": preview, "content": body,
               "description": f"ColdCase Weekly {now.strftime('%Y-%m-%d')} (created automatically)",
               "public": False, "published_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
               "send_at": (now + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ") if mode == "send" else None}
    tag = os.environ.get("KIT_TAG_ID", "").strip()
    if tag:  # optional: send only to subscribers with this tag
        payload["subscriber_filter"] = [{"all": [{"type": "tag", "ids": [int(tag)]}], "any": None, "none": None}]
    code, text = kit_post(payload, key)
    if code == 422 and "subscriber_filter" not in payload:
        # Kit's documentation lists subscriber_filter as required but also says it defaults to all subscribers
        payload["subscriber_filter"] = []
        code, text = kit_post(payload, key)
    if code not in (200, 201):
        hint = {401: "the API key is wrong or was reset (create a new V4 key and update the KIT_API_KEY secret)",
                403: "Kit says this account may not create broadcasts through the API",
                422: "Kit rejected a field"}.get(code, "Kit returned an unexpected answer")
        print(f"::error::Kit did not accept the email ({code}): {hint}. Kit said: {text[:400]}")
        return None
    try:
        b = json.loads(text).get("broadcast", {})
    except Exception:
        b = {}
    print(f"Kit accepted the email: broadcast id {b.get('id')}, status '{b.get('status')}', "
          f"recipients: {'tag ' + tag if tag else 'all subscribers'}.")
    return b


def main(mode):
    now = datetime.now(timezone.utc)
    led = load_ledger()
    sent = set(led.get("sent", []))
    verdicts, new_cases, other, watching, keys = collect(cases.load_cases(), sent, now)
    if not (verdicts or new_cases or other):
        print("Nothing new since the last email: no email this week. (This is expected in a quiet week.)")
        return 0
    subject, preview, body, md = build(verdicts, new_cases, other, watching, now)
    print(f"Subject: {subject}\nPreview: {preview}\n\n{md}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"## ColdCase Weekly ({mode})\n\n**Subject:** {subject}\n\n{md}\n")
    if mode == "preview":
        print("\nPreview only: nothing was sent to Kit.")
        return 0
    b = create_in_kit(subject, preview, body, mode, now)
    if not b:
        return 1
    led["sent"] = sorted(sent | set(keys))
    led.setdefault("emails", []).append({"date": now.strftime("%Y-%m-%d"), "mode": mode, "subject": subject,
                                         "broadcast_id": b.get("id"), "items": len(keys)})
    save_ledger(led, now)
    print("Draft created: open Kit > Send > Broadcasts, check it, then press Send." if mode == "draft"
          else "Scheduled: Kit sends it in about 15 minutes.")
    return 0


if __name__ == "__main__":
    m = (sys.argv[1] if len(sys.argv) > 1 else "preview").strip().lower()
    if m not in ("preview", "draft", "send"):
        print("Usage: weekly_email.py preview|draft|send")
        sys.exit(2)
    sys.exit(main(m))
