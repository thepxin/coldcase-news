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
# Raise this when the site's own checks are fixed: every held draft is then tried once more without being edited.
RULES = 5
BYLINE = "Rishit K."
DRAFT_EXT = (".md", ".txt")
SKIP_NAMES = {"readme.md", "master_prompt.md"}
MAX_LINKS = 20                # links read per draft (the first 20 in the draft)
EXTRA_PATH = os.path.join("data", "draft_sources.json")   # extra outlets accepted for drafts only
MARKET_DATA = "market data (prices only)"
MIN_WORDS = 60                # shorter drafts are held without spending an AI request
EXCERPT_CHARS = 20000   # about 3,000 words: the whole article text of almost any page

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
    no_ext = "." not in low   # "AA3" created on GitHub without ".md" still counts
    return ((low.endswith(DRAFT_EXT) or no_ext) and low not in SKIP_NAMES and not low.endswith(".note.md")
            and not low.startswith((".", "_")) and low not in ("readme", "license"))


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
        if entry.get("status") == "held" and entry.get("hash") == digest(text) and entry.get("rules") == RULES:
            continue   # held and unchanged; a fix to the site's checks (a new RULES) gives it one more try
        out.append(path)
    return sorted(out, key=lambda p: (log[key(p)]["first_seen"], os.path.basename(p)))


HTML_CITE = re.compile(r"<\s*(sup|a|span)\b", re.I)

DOCS_ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|>~<])")


def unmangle(text: str) -> str:
    """Undo what Google Docs' "Download as Markdown" (and similar editors) do to a pasted article: every line made a
    "# " heading, and Markdown signs escaped with a backslash (\\[Meta](...), \\*\\*bold\\*\\*, \\- list). The words
    themselves are not changed."""
    lines = text.splitlines()
    filled = [l for l in lines if l.strip()]
    headed = bool(filled) and sum(1 for l in filled if re.match(r"^#\s", l) or l.strip() == "#") >= 0.6 * len(filled)
    if headed:
        lines = [re.sub(r"^#(\s|$)", "", l, count=1) for l in lines]
    out = "\n".join(lines)
    if not (headed or DOCS_ESCAPE.search(out)):
        return text
    out = DOCS_ESCAPE.sub(r"\1", out)
    out = re.sub(r"(?m)^([ \t]*\|.*\|)[ \t]*\n(?:[ \t]*\n)+(?=[ \t]*\|)", r"\1\n", out)   # table rows back together
    return re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", out)   # Docs' extra empty paragraphs


# Page-data lines the chat desk writes under the type line. When present they are used exactly as written (and checked
# like the article); when absent the site writes them. "verdict" is closed only; "due" and "due date" are open only.
FIELD_KEYS = {"verdict": "verdict_score", "then": "original_claim", "now": "current_reality",
              "summary": "summary_description", "due": "due_text", "due date": "due_date"}
FIELD_LINE = re.compile(r"^(verdict|then|now|summary|due date|due_date|due)\s*:\s*(\S.*)$", re.I)
VERDICTS = {"delivered": "Delivered", "partially delivered": "Partially Delivered", "not delivered": "Not Delivered"}


def parse_ready(text: str) -> dict:
    """An approved article from the chat desk: first line "# Headline", then "type: closed|open|report" (optional),
    then the body with inline [Outlet](URL) citations. Code-fence lines (```) and any "## Sources" section are
    ignored, so the chat's code block can be pasted as it is. Text that went through Google Docs is repaired."""
    text = unmangle(text)
    lines = [l for l in text.strip().splitlines() if not l.strip().startswith("```")]
    headline, kind = "", ""
    while lines and not headline:
        headline = lines.pop(0).strip().lstrip("#").strip()
    headline = re.sub(r"^(title|headline)\s*:\s*", "", headline, flags=re.I)
    fields = {}
    while lines:   # the type line and the optional page-data lines, in any order, before the article itself
        line = lines[0].strip()
        m = re.match(r"^type\s*:\s*(closed|open|report)\b", line, re.I)
        f = FIELD_LINE.match(line)
        if not line:
            lines.pop(0)
        elif m:
            kind = m.group(1).lower()
            lines.pop(0)
        elif f:
            fields[FIELD_KEYS[f.group(1).lower().replace("_", " ")]] = f.group(2).strip()
            lines.pop(0)
        else:
            break
    body = "\n".join(lines).strip()
    body = re.split(r"(?mi)^#{1,3}\s*sources\s*$", body)[0].strip()
    links = []
    for u in URL_RE.findall(body):
        u = u.rstrip(".,;:!?*_")
        if u not in links:
            links.append(u)
    return {"headline": headline, "type": kind, "fields": fields, "body": body, "links": links,
            "words": len(re.sub(URL_RE, " ", body).split()), "html": bool(HTML_CITE.search(body))}


def parse(text: str) -> dict:
    """Title = the first non-empty line (a leading # is fine). Body = the rest. Links = every http(s) address
    in the draft, in order, without duplicates. Text that went through Google Docs is repaired."""
    text = unmangle(text)
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


# Website names that are never a company's own site, even when the word appears in a headline.
NOT_A_COMPANY = {"news", "blog", "blogs", "tech", "daily", "times", "post", "review", "reviews", "report", "wiki",
                 "wikipedia", "medium", "substack", "reddit", "twitter", "youtube", "facebook", "instagram", "linkedin",
                 "github", "google", "wordpress", "blogspot", "yahoo", "msn", "forbes", "motley", "seekingalpha",
                 "the", "new", "now", "app", "web", "get", "top", "big", "all", "one", "out", "who", "how", "why",
                 "abc", "cbs", "nbc", "fox", "aol", "ign"}
_TWO_PART_ENDINGS = {"co.uk", "co.jp", "com.au", "co.in", "com.br", "co.kr", "com.cn", "co.nz", "com.sg", "com.hk",
                     "co.za", "com.tw", "co.il"}


def company_label(host: str) -> str:
    """'decart' for decart.ai or www.decart.ai, 'sony' for sony.co.jp."""
    parts = (host or "").lower().split(".")
    if len(parts) < 2:
        return ""
    if ".".join(parts[-2:]) in _TWO_PART_ENDINGS and len(parts) >= 3:
        return parts[-3]
    return parts[-2]


def own_site(url: str, headline: str, host_of) -> str:
    """The company's name as written in the headline when the link is that company's own website (for example
    decart.ai in a headline that names Decart). Returns "" otherwise. Only plain names of 3+ letters count."""
    label = company_label(host_of(url))
    if len(label) < 3 or not label.isalpha() or label in NOT_A_COMPANY:   # 3 letters: NIO, AMD, IBM, BYD
        return ""
    m = re.search(r"\b" + re.escape(label) + r"\b", headline or "", re.I)
    return m.group(0) if m else ""


def gather(links: list[str], cfg, fetch_html, extract, outlet_for, host_of, parse_date, iso, strip_tracking, extra=None,
           headline: str = ""):
    """Open each link. Returns (sources, notes). Outlets on the approved list (data/sources.json) keep their tier;
    the extra draft-only outlets (data/draft_sources.json) count as Tier B newsrooms, as market data that may be
    cited for share prices only, or (kind "company") as a company's own website. A company's own website also counts
    when the headline names that company (decart.ai for a story about Decart): an official, Tier A source.
    The helpers are passed in from source_discovery so tests can replace the network."""
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
            if x and x.get("kind") == "company":
                o, kind = {"name": x["name"], "tier": "A"}, "official"
            elif x:
                o = {"name": x["name"], "tier": "B"}
                kind = MARKET_DATA if x.get("kind") == "market data" else "newsroom"
            else:
                own = own_site(url, headline, host_of)
                if own:
                    o, kind = {"name": own, "tier": "A"}, "official"
        if not o:
            notes.append(f"Not used: {url} ({host_of(url)} is not on the approved or newsroom lists, and it is not "
                         "the own website of a company named in the headline. To accept it, add it to "
                         "data/draft_sources.json; a company's own site uses \"kind\": \"company\").")
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
    entry.update({"status": "held", "hash": digest(text), "rules": RULES, "checked": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
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


def write_changes(target: str, article_file: str, fixes: list) -> str:
    """List every line the site changed in an approved article, next to the published draft."""
    path = os.path.splitext(target)[0] + ".CHANGES.md"
    out = [f"# Lines the site changed before publishing", "",
           f"Published as `{article_file}`. Your approved text is `{os.path.basename(target)}`.",
           "Because lines were changed, the page says \"Written by Rishit K. · edited with AI assistance\".", ""]
    for i, (old, new) in enumerate(fixes, 1):
        out += [f"## {i}", "", "Was:", "", f"> {old}", "", "Now:", "", f"> {new}" if new else "> (deleted)", ""]
    out += ["If a change is wrong, edit the article file in `content/posts/` (and tell the checker why next time)."]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"[drafts] the site changed {len(fixes)} line(s); the list is in {path}")
    return path


def forget_missing(log: dict, folder=DRAFTS_DIR):
    """Drop log entries for drafts that were deleted (published ones are kept as the record)."""
    for k in list(log):
        if log[k].get("status") != "published" and not os.path.exists(os.path.join(folder, k)):
            log.pop(k)
