"""Read existing cases and append dated updates to them, without rewriting the original case.

A case is a post in content/posts/. Its original text (the body) is never changed by the robot.
An update is appended to the post's 'updates:' list in the top section (front matter), and the case's
current status lines (status, verdict, now, lastmod) are set to the newest state. Git keeps every earlier version.
"""
import glob
import json
import os
import re
from datetime import datetime, timedelta, timezone

import yaml

POSTS = "content/posts"
CHECKS_FILE = "data/case_checks.json"
FM = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


def read_case(path):
    text = open(path, encoding="utf-8").read()
    m = FM.match(text)
    if not m:
        return None
    fm = yaml.safe_load(m.group(1)) or {}
    fm["_path"] = path
    fm["_slug"] = os.path.splitext(os.path.basename(path))[0]
    return fm


def _day(value):
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def last_activity(case):
    """Date of the newest update, or the publication date."""
    ups = case.get("updates") or []
    return _day(ups[-1].get("date")) if ups else _day(case.get("date"))


def all_urls(case):
    urls = {s.get("url") for s in case.get("sources") or [] if isinstance(s, dict)}
    for u in case.get("updates") or []:
        urls |= {s.get("url") for s in u.get("sources") or [] if isinstance(s, dict)}
    return {u for u in urls if u}


def load_cases(posts_dir=POSTS):
    out = []
    for p in sorted(glob.glob(os.path.join(posts_dir, "*.md"))):
        try:
            c = read_case(p)
        except Exception:
            c = None
        if c and c.get("sources") and c.get("desk") in ("tech", "security") and not c.get("draft"):
            out.append(c)
    return out


def update_candidates(cases, now=None, recent_days=60, limit=25):
    """Which cases the update desk looks at, most urgent first:
    1. open cases whose due date has passed, 2. other open cases (soonest due first),
    3. closed cases with activity in the last `recent_days` days (newest first)."""
    now = now or datetime.now(timezone.utc)
    open_cases = [c for c in cases if c.get("status") == "open"]
    due = lambda c: _day(c.get("due_by")) or now + timedelta(days=3650)
    past_due = sorted([c for c in open_cases if due(c) <= now], key=due)
    upcoming = sorted([c for c in open_cases if due(c) > now], key=due)
    recent = sorted([c for c in cases if c.get("status") != "open" and last_activity(c)
                     and (now - last_activity(c)).days <= recent_days], key=last_activity, reverse=True)
    return (past_due + upcoming + recent)[:limit]


def _q(v):
    return json.dumps(v if v is not None else "", ensure_ascii=False)


def _set_scalar(fm_text, key, value):
    line = f"{key}: {_q(value)}"
    if re.search(rf"^{key}:.*$", fm_text, re.M):
        return re.sub(rf"^{key}:.*$", lambda _: line, fm_text, count=1, flags=re.M)
    return re.sub(r"^cover:", lambda _: line + "\ncover:", fm_text, count=1, flags=re.M) if re.search(r"^cover:", fm_text, re.M) \
        else fm_text.rstrip("\n") + "\n" + line


def source_yaml(sources, indent):
    pad = " " * indent
    return "".join(
        f"{pad}- outlet: {_q(x.get('outlet', ''))}\n"
        f"{pad}  tier: {_q(x.get('tier', ''))}\n"
        f"{pad}  kind: {_q(x.get('kind', ''))}\n"
        f"{pad}  date: {_q(x.get('date', ''))}\n"
        f"{pad}  title: {_q((x.get('title') or '')[:200])}\n"
        f"{pad}  url: {_q(x.get('url', ''))}\n" for x in sources)


def append_update(path, entry, new_status, new_verdict, new_now):
    """Append one update to the case file. entry: date, summary, text, sources, verdict_from, verdict_to,
    status_from, status_to. The original body is copied through unchanged. Returns the new file text."""
    text = open(path, encoding="utf-8").read()
    m = FM.match(text)
    fm_text, body = m.group(1), m.group(2)
    block = (f"  - date: {_q(entry['date'])}\n"
             f"    summary: {_q(entry['summary'])}\n"
             f"    status_from: {_q(entry['status_from'])}\n"
             f"    status_to: {_q(entry['status_to'])}\n"
             f"    verdict_from: {_q(entry['verdict_from'])}\n"
             f"    verdict_to: {_q(entry['verdict_to'])}\n"
             f"    now_before: {_q(entry['now_before'])}\n"
             f"    text: {_q(entry['text'])}\n"
             f"    sources:\n" + source_yaml(entry["sources"], 6))
    lines = fm_text.split("\n")
    if "updates:" in lines:
        i = lines.index("updates:") + 1
        while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("-")):
            i += 1
        lines[i:i] = block.rstrip("\n").split("\n")
        fm_text = "\n".join(lines)
    else:
        insert = "updates:\n" + block.rstrip("\n")
        if re.search(r"^cover:", fm_text, re.M):
            fm_text = re.sub(r"^cover:", lambda _: insert + "\ncover:", fm_text, count=1, flags=re.M)
        else:
            fm_text = fm_text.rstrip("\n") + "\n" + insert
    fm_text = _set_scalar(fm_text, "status", new_status)
    fm_text = _set_scalar(fm_text, "verdict", new_verdict)
    fm_text = _set_scalar(fm_text, "now", new_now)
    fm_text = _set_scalar(fm_text, "lastmod", entry["date"] + "T00:00:00Z")
    fm_text = _set_scalar(fm_text, "checked", entry["date"])
    new_text = f"---\n{fm_text}\n---\n{body}"
    # safety: the result must still be readable, keep the original body, and contain the new update
    check = yaml.safe_load(fm_text)
    assert check["updates"][-1]["text"] == entry["text"], "update did not round-trip"
    assert FM.match(new_text).group(2) == body, "original body changed"
    return new_text


def record_checks(results, path=CHECKS_FILE):
    """results: {slug: {"checked": "YYYY-MM-DD", "result": "..."}}. Kept for open cases only (the 'last checked' line)."""
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception:
        data = {}
    data.update(results)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(data.items())), f, ensure_ascii=False, indent=1)
        f.write("\n")
