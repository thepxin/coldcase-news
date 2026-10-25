"""Ready-to-post social text for one article, cut to each platform's limits.

Every post is built from parts that already passed the fact-check (headline, the hook, the summary, Then/Now),
so nothing here can add a new claim. Limits (October 2026):
  X          280 characters for standard accounts; every link counts as 23; emoji and CJK count as 2.
  Instagram  2,200-character caption, at most 30 hashtags; links in captions are not clickable ("link in bio").
"""
import re
import unicodedata

X_LIMIT, X_URL = 280, 23
INSTAGRAM_LIMIT = 2200
URL_RE = re.compile(r"https?://\S+")

FIELD_TAGS = {"ai": "AI", "chips and silicon": "Semiconductors", "devices": "Gadgets", "software": "Software",
              "platforms": "BigTech", "policy and privacy": "Privacy", "crypto": "Crypto", "evs": "EV",
              "space": "Space", "quantum": "QuantumComputing", "robotics": "Robotics", "energy": "Energy",
              "telecom": "Telecom", "gaming": "Gaming", "cloud and infrastructure": "Cloud"}


def x_length(text: str) -> int:
    """Length as X counts it: each link is 23; Latin text 1 per character; emoji, CJK and other wide characters 2."""
    n = 0
    for part in URL_RE.split(text):
        for ch in unicodedata.normalize("NFC", part):
            o = ord(ch)
            n += 1 if (o <= 4351 or 8192 <= o <= 8205 or 8208 <= o <= 8223 or 8242 <= o <= 8247) else 2
    return n + X_URL * len(URL_RE.findall(text))


def _trim(text: str, room: int, measure=len) -> str:
    """Cut at a word boundary so measure(text) <= room, ending with an ellipsis."""
    if measure(text) <= room:
        return text
    words = text.split()
    while words and measure(" ".join(words) + "…") > room:
        words.pop()
    return (" ".join(words).rstrip(",;:") + "…") if words else ""


def _status_line(status: str, verdict: str, due: str) -> str:
    if status == "open":
        return f"Open case: due {due}. We check every day." if due else "Open case: we check every day."
    if status == "closed" and verdict:
        return f"Verdict: {verdict}."
    return ""


def compose(*, headline: str, hook: str, summary: str, then: str, now: str, labels: tuple[str, str],
            status: str, verdict: str, due: str, url: str, field_key: str, field_label: str,
            sources: list[dict]) -> dict:
    hook = (hook or summary or headline).strip()
    status_line = _status_line(status, verdict, due)
    field_tag = "#" + FIELD_TAGS.get(field_key, re.sub(r"[^A-Za-z0-9]", "", field_label or "Tech"))
    officials = sorted({(s.get("outlet") or "").split(" (")[0] for s in sources or [] if s.get("tier") == "A"} - {""})
    n_src = len(sources or [])
    if n_src == 1 and officials:
        checked = f"Checked against the official source ({officials[0]})."
    else:
        checked = (f"Checked against {n_src} source{'s' if n_src != 1 else ''}"
                   + (f", including {', '.join(officials)} (official)" if officials else "") + ".")

    # X: hook, status, link, one hashtag. Shrink in a fixed order until it fits.
    def x_post(h, with_status=True, with_tag=True):
        parts = [h]
        if with_status and status_line:
            parts.append(status_line)
        parts.append(f"Every line sourced: {url}")
        text = "\n\n".join(parts)
        return text + (f"\n\n{field_tag} #TechNews" if with_tag else "")
    x = x_post(hook)
    for args in ((True, False), (False, False)):
        if x_length(x) <= X_LIMIT:
            break
        x = x_post(hook, *args)
    if x_length(x) > X_LIMIT:
        fixed = x_length(x_post("", False, False))
        x = x_post(_trim(hook, X_LIMIT - fixed, x_length), False, False)

    ledger = f"{labels[0]}: {then}\n{labels[1]}: {now}" if then and now else ""
    words = lambda t: set(re.findall(r"[a-z0-9]+", (t or "").lower()))
    if summary and (summary.strip() == (then or "").strip() or
                    len(words(summary) & words(hook)) > 0.6 * max(1, len(words(summary)))):
        summary = ""   # never say (nearly) the same sentence twice
    tags = ["#coldcasetech", "#technews", "#tech", field_tag.lower()]
    instagram = "\n\n".join(p for p in [
        hook, summary if summary and summary != hook else "", status_line,
        "Full story and every source: link in bio.",
        "ColdCaseTech · An independent record of technology's promises",
        " ".join(dict.fromkeys(tags))] if p)
    if len(instagram) > INSTAGRAM_LIMIT:
        instagram = instagram[:INSTAGRAM_LIMIT - 1] + "…"

    return {
        "hook": hook,
        "x": x, "x_chars": x_length(x),
        "instagram": instagram,
    }


def as_text(article_title: str, kit: dict, url: str, share_url: str) -> str:
    """The plain-text version written to scripts/latest_social_teaser.txt after each daily run."""
    line = "=" * 64
    return f"""{line}
{article_title}
Share kit with buttons and the Instagram image: {share_url}
(Bluesky and Telegram post automatically.)
{line}

X ({kit['x_chars']}/280):
{kit['x']}

INSTAGRAM (post this caption with the image from the share kit):
{kit['instagram']}
"""
