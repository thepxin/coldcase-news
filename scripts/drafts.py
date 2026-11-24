"""The editor's drafts desk: articles Rishit K. writes himself, in the folder drafts/.

How it works (each daily run, before the AI looks for stories of its own):
1. The oldest waiting draft in drafts/ is picked first. One draft fills one publishing slot; when no draft is ready,
   the AI fills the slot as before.
2. Every link in the draft is opened. Only links to approved outlets (data/sources.json) are used as sources;
   other links are listed in the note and ignored.
3. generate_followup.py rewrites the draft into the house voice and the site's format, keeping the editor's facts,
   angle and order, then runs the usual claim-by-claim check.
4. Published: the draft moves to drafts/published/ and the article carries the byline "Rishit K.".
   Held: nothing is published. A note next to the draft (<name>.NOTE.md) lists what to fix. Edit the draft and save
   it: a changed draft is tried again in the next run. An unchanged held draft is never retried (no cost).

This file has no AI calls and no network calls of its own except reading the draft's links (fetch below), so it can
be tested on its own.
"""
import hashlib
import json
import os
import re
from datetime import datetime, timezone

DRAFTS_DIR = "drafts"
PUBLISHED_DIR = os.path.join(DRAFTS_DIR, "published")
READY_DIR = os.path.join(DRAFTS_DIR, "ready")   # articles the editor already approved (from the chat desk)
LOG_PATH = os.path.join("data", "drafts_log.json")
BYLINE = "Rishit K."
DRAFT_EXT = (".md", ".txt")
SKIP_NAMES = {"readme.md", "master_prompt.md"}
MAX_LINKS = 20                # links read per draft (the first 20 in the draft)
EXTRA_PATH = os.path.join("data", "draft_sources.json")   # extra outlets accepted for drafts only
MARKET_DATA = "market data (prices only)"
MIN_WORDS = 60                # shorter drafts are held without spending an AI request
EXCERPT_CHARS = 7000

URL_RE = re.compile(r"https?://[^\s<>()\[\]\"']+")


def _now():
    return datetime.now(timezone.utc)


def load_log(path=LOG_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_log(log: dict, path=LOG_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def digest(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()[:16]


def is_draft_file(name: str) -> bool:
    low = name.lower()
    return (low.endswith(DRAFT_EXT) and low not in SKIP_NAMES and not low.endswith(".note.md")
            and not low.startswith((".", "_")))


def key(path: str) -> str:
    """The log key: the path inside drafts/ ("nvidia.md" or "ready/nvidia.md")."""
    return os.path.relpath(path, DRAFTS_DIR).replace(os.sep, "/")


def is_ready(path: str) -> bool:
    return key(path).startswith("ready/")


def note_path(path: str) -> str:
    return os.path.splitext(path)[0] + ".NOTE.md"


def pending(log: dict, folder=DRAFTS_DIR, now=None) -> list[str]:
    """Drafts ready to try, oldest first (the day they were first seen, then the file name).
    A held draft is skipped until its text changes."""
    now = now or _now()
    out = []
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return []
    for name in names:
        path = os.path.join(folder, name)
        if not os.path.isfile(path) or not is_draft_file(name):
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        if not text.strip():
            continue
        entry = log.setdefault(key(path), {})
        entry.setdefault("first_seen", now.strftime("%Y-%m-%dT%H:%M:%SZ"))
        if entry.get("status") == "held" and entry.get("hash") == digest(text):
            continue
        out.append(path)
    return sorted(out, key=lambda p: (log[key(p)]["first_seen"], os.path.basename(p)))


HTML_CITE = re.compile(r"<\s*(sup|a|span)\b", re.I)


def parse_ready(text: str) -> dict:
    """An approved article from the chat desk: first line "# Headline", then "type: closed|open|report" (optional),
    then the body with inline [Outlet](URL) citations. Code-fence lines (```) and any "## Sources" section are
    ignored, so the chat's code block can be pasted as it is."""
    lines = [l for l in text.strip().splitlines() if not l.strip().startswith("```")]
    headline, kind = "", ""
    while lines and not headline:
        headline = lines.pop(0).strip().lstrip("#").strip()
    headline = re.sub(r"^(title|headline)\s*:\s*", "", headline, flags=re.I)
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines:
        m = re.match(r"^\s*type\s*:\s*(closed|open|report)\b", lines[0], re.I)
        if m:
            kind = m.group(1).lower()
            lines.pop(0)
    body = "\n".join(lines).strip()
    body = re.split(r"(?mi)^#{1,3}\s*sources\s*$", body)[0].strip()
    links = []
    for u in URL_RE.findall(body):
        u = u.rstrip(".,;:!?*_")
        if u not in links:
            links.append(u)
    return {"headline": headline, "type": kind, "body": body, "links": links,
            "words": len(re.sub(URL_RE, " ", body).split()), "html": bool(HTML_CITE.search(body))}


def parse(text: str) -> dict:
    """Title = the first non-empty line (a leading # is fine). Body = the rest. Links = every http(s) address
    in the draft, in order, without duplicates."""
    lines = text.strip().splitlines()
    title = ""
    while lines and not title:
        title = lines.pop(0).strip().lstrip("#").strip()
    title = re.sub(r"^(title|headline)\s*:\s*", "", title, flags=re.I)
    body = "\n".join(lines).strip()
    links = []
    for u in URL_RE.findall(text):
        u = u.rstrip(".,;:!?*_")
        if u not in links:
            links.append(u)
    return {"title": title, "body": body, "links": links, "words": len(re.sub(URL_RE, " ", body).split())}


def load_extra(path=EXTRA_PATH) -> list[dict]:
    """The extra outlets accepted for drafts only (data/draft_sources.json)."""
    try:
        with open(path, encoding="utf-8") as f:
            return [o for o in json.load(f).get("outlets", []) if o.get("name") and o.get("domains")]
    except (OSError, ValueError, AttributeError):
        return []


def extra_outlet(url: str, extra: list[dict], host_of):
    host = host_of(url)
    for o in extra:
        if any(host == d or host.endswith("." + d) for d in o["domains"]):
            return o
    return None


def gather(links: list[str], cfg, fetch_html, extract, outlet_for, host_of, parse_date, iso, strip_tracking, extra=None):
    """Open each link. Returns (sources, notes). Outlets on the approved list (data/sources.json) keep their tier;
    the extra draft-only outlets (data/draft_sources.json) count as Tier B newsrooms, or as market data that may be
    cited for share prices only. The helpers are passed in from source_discovery so tests can replace the network."""
    sources, notes = [], []
    extra = load_extra() if extra is None else extra
    for raw in links[:MAX_LINKS]:
        url = strip_tracking(raw)
        o = outlet_for(url, cfg)
        kind = None
        if o:
            kind = "official" if o["tier"] == "A" else "newsroom"
        else:
            x = extra_outlet(url, extra, host_of)
            if x:
                o = {"name": x["name"], "tier": "B"}
                kind = MARKET_DATA if x.get("kind") == "market data" else "newsroom"
        if not o:
            notes.append(f"Not used: {url} ({host_of(url)} is not on the approved or newsroom lists: "
                         f"data/sources.json, data/draft_sources.json).")
            continue
        try:
            html = fetch_html(url)
        except Exception:
            html = None
        data = extract(html, url) if html else None
        text = (data or {}).get("text") or ""
        if not html:
            notes.append(f"Not used: {url} (the page did not open: blocked, moved or timed out).")
            continue
        if len(text) < 300:
            notes.append(f"Not used: {url} (too little readable text on the page, often a paywall).")
            continue
        if any(s["url"] == url for s in sources):
            continue
        sources.append({
            "outlet": o["name"],
            "tier": o["tier"],
            "kind": kind,
            "title": (data or {}).get("title") or url,
            "url": url,
            "date": iso(parse_date((data or {}).get("date"))),
            "excerpt": text[:EXCERPT_CHARS],
        })
    if len(links) > MAX_LINKS:
        notes.append(f"Only the first {MAX_LINKS} links were read.")
    sources.sort(key=lambda s: (s["tier"] != "A", s["date"] or "9999"))
    return sources, notes


def enough_sources(sources: list[dict]) -> str:
    """The site's sourcing rule for tech: one official source, or two different outlets. Returns "" when met."""
    counted = [s for s in sources if s.get("kind") != MARKET_DATA]
    if any(s["tier"] == "A" for s in counted) or len({s["outlet"] for s in counted}) >= 2:
        return ""
    if not counted:
        return "No approved source or newsroom could be read (price tables alone do not count)."
    return (f"Only one newsroom ({counted[0]['outlet']}) could be read; the rule is one official source or two "
            "different outlets.")


def hold(path: str, log: dict, text: str, reasons: list[str], notes=(), now=None):
    """Mark a draft as held and write the note next to it."""
    now = now or _now()
    name = os.path.basename(path)
    entry = log.setdefault(key(path), {})
    entry.update({"status": "held", "hash": digest(text), "checked": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "reasons": list(reasons)[:12]})
    lines = [f"# Not published yet: {name}", "",
             f"Checked {now.strftime('%d %b %Y, %H:%M')} UTC. Nothing was published.", "",
             "## What to fix", ""]
    lines += [f"- {r}" for r in reasons] or ["- (no reason recorded)"]
    if notes:
        lines += ["", "## Links", ""] + [f"- {n}" for n in notes]
    lines += ["", "## Then", "",
              f"Edit `{name}` and save it (Commit changes). A changed draft is tried again in the next run.",
              "This note is replaced or removed automatically. Lines you are unsure of can simply be deleted.", ""]
    with open(note_path(path), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[drafts] HELD {name}: " + " | ".join(reasons[:4]))


def published(path: str, log: dict, text: str, article_file: str, now=None) -> str:
    """Move the draft to drafts/published/ (with the date), remove its note and record the article."""
    now = now or _now()
    name = os.path.basename(path)
    k = key(path)
    os.makedirs(PUBLISHED_DIR, exist_ok=True)
    target = os.path.join(PUBLISHED_DIR, f"{now:%Y-%m-%d}-{name}")
    n = 2
    while os.path.exists(target):
        base, ext = os.path.splitext(name)
        target = os.path.join(PUBLISHED_DIR, f"{now:%Y-%m-%d}-{base}-{n}{ext}")
        n += 1
    os.replace(path, target)
    if os.path.exists(note_path(path)):
        os.remove(note_path(path))
    entry = log.pop(k, {})
    log[key(target)] = {"status": "published", "hash": digest(text), "article": article_file,
                                     "first_seen": entry.get("first_seen", ""),
                                     "published": now.strftime("%Y-%m-%dT%H:%M:%SZ")}
    print(f"[drafts] PUBLISHED {name} as {article_file}; the draft is now {target}")
    return target


def forget_missing(log: dict, folder=DRAFTS_DIR):
    """Drop log entries for drafts that were deleted (published ones are kept as the record)."""
    for k in list(log):
        if log[k].get("status") != "published" and not os.path.exists(os.path.join(folder, k)):
            log.pop(k)
