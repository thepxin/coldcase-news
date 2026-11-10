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


# ---------------------------------------------------------------- hashtags that name the story
# Generic tags (#TechNews, #Software) are used by thousands of posts an hour and searched by nobody. People search and
# follow NAMES: #Waymo, #GTA6, #Pixel10. story_tags() takes the names from the article's own headline, so a tag can
# never be about something the article is not about. Names that are trending right now go first.
TAG_PHRASES = {   # well-known names that are written as several words
    "grand theft auto vi": "GTA6", "grand theft auto 6": "GTA6", "gta vi": "GTA6", "gta 6": "GTA6",
    "call of duty": "CallOfDuty", "world of warcraft": "WorldOfWarcraft", "geforce now": "GeForceNOW",
    "black friday": "BlackFriday", "cyber monday": "CyberMonday", "apple intelligence": "AppleIntelligence",
    "blue origin": "BlueOrigin", "new glenn": "NewGlenn", "apple arcade": "AppleArcade", "apple watch": "AppleWatch",
    "vision pro": "VisionPro", "macbook pro": "MacBookPro", "macbook air": "MacBookAir", "ipad mini": "iPadMini",
    "ipad pro": "iPadPro", "ipad air": "iPadAir", "fire tv": "FireTV", "game pass": "GamePass",
    "steam deck": "SteamDeck", "legend of zelda": "Zelda", "ray-ban meta": "RayBanMeta", "google cloud": "GoogleCloud",
    "open ai": "OpenAI", "hacker news": "HackerNews", "tp-link": "TPLink", "wi-fi": "WiFi",
}
# product lines whose number is part of the name: "Pixel 10" -> #Pixel10
TAG_NUMBERED = set("pixel iphone ipad galaxy switch windows playstation ps xbox ios macos android rtx ryzen snapdragon "
                   "gpt gemini starship wifi quest homepod surface".split())
TAG_STOP = set("""
january february march april may june july august september october november december monday tuesday wednesday
thursday friday saturday sunday jan feb mar apr jun jul aug sep sept oct nov dec ai us usa uk eu un ceo cfo cto coo gb
tb mb kb pt et utc gmt rom ram cpu gpu ssd usb pdf api os tv ev evs pc pcs vpn dns llm llms faq ipo q1 q2 q3 q4 am pm
the a an and or but for nor so yet with from into over after before about this that these those what when where why
how who which its it's their there here now then new first last next more most less only also still just every all
no not yes one two three four five six seven eight nine ten million billion percent inc corp ltd llc co mr ms dr
promised delivered measured verdict status sources update updated claim claimed reported report details timeline
oled led lcd hdr xdr uhd nfc gps sdk ide cli sms sim esim lte iot saas url html css json sql ui ux qa hr pr it id
""".split())
TAG_HOT_NAMES = set()   # filled from trends.HOT_NAMES when that module is available (famous names always qualify)
try:
    import trends as _trends
    TAG_HOT_NAMES = set(_trends.HOT_NAMES)
except Exception:
    pass
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[-'][A-Za-z][A-Za-z0-9]*)*")
_NUM_AFTER = re.compile(r" (\d{1,3})(?![\d.,%-]|\s?(?:GB|TB|MB|inch|percent|million|billion|days?|hours?|years?|p\.m|a\.m))")


def _name_kind(word: str, body: str, sentence_start: bool) -> str:
    """'strong' for a certain name (famous, or written like NHTSA / iPad / GeForce), 'plain' for an ordinary
    capitalised name (Waymo, Roadster), '' for a word that is not a name."""
    low = word.lower()
    if low in TAG_STOP or len(word) < 2 or not any(c.isupper() for c in word) or sum(c.isdigit() for c in word) > 4:
        return ""
    if low in TAG_HOT_NAMES or any(c.isupper() for c in word[1:]):
        return "strong"
    if not body:                                    # nothing to check against: only accept it mid-sentence
        return "" if sentence_start else "plain"
    # A name is always written with its capital. An ordinary word that only starts a sentence also appears in lower case.
    # (a web address such as "waymo.com" does not count as lower-case use)
    if re.search(r"(?<![A-Za-z0-9./@_-])" + re.escape(low) + r"(?![A-Za-z0-9_]|[.-][a-z])", body):
        return ""
    return "plain"


def story_tags(headline: str, body: str = "", hot=None, limit: int = 6, skip=()) -> list[str]:
    """Hashtags (without '#') made from the names in the headline. Best first: certain names (companies, products,
    agencies), then longer names, then single ordinary names; names trending right now move to the front of their group.
    hot: optional {word: weight} of what is trending (trends.Hot.weight). skip: words never to use (news outlets)."""
    headline = (headline or "").replace("’", "'")
    body = re.sub(r"https?://\S+|\]\([^)]*\)", " ", body or "")
    skip = {w.lower() for w in skip}
    low_head, items, covered = headline.lower(), [], []
    mid_caps = ordinary_caps = 0
    for phrase, tag in TAG_PHRASES.items():
        for m in re.finditer(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", low_head):
            items.append({"pos": m.start(), "end": m.end(), "tag": tag, "kind": "strong", "words": phrase.replace("-", " ").split()})
            covered.append((m.start(), m.end()))
    for m in _WORD.finditer(headline):
        if any(a <= m.start() < b for a, b in covered):
            continue
        word = re.sub(r"'s$", "", m.group(0))
        if "-" in word and any(part[:1].islower() for part in word.split("-")[1:]):
            word = word.split("-")[0]               # "LLM-written" is about "LLM", not a name of its own
        before = headline[:m.start()].rstrip()
        starts = not before or before[-1] in ".!?:"
        kind = "" if word.lower() in skip else _name_kind(word, body, starts)
        if word[:1].isupper() and not starts and word.lower() not in TAG_STOP:
            mid_caps += 1
            ordinary_caps += (not kind and bool(body))   # capitalised in the headline, lower case in the article
        if not kind:
            continue
        tag, end = re.sub(r"[^A-Za-z0-9]", "", word), m.start() + len(word)
        num = _NUM_AFTER.match(headline[m.end():])
        if num and word.lower() in TAG_NUMBERED:
            tag, end = tag + num.group(1), m.end() + num.end()
        if len(tag) >= 2:
            items.append({"pos": m.start(), "end": end, "tag": tag, "kind": kind, "words": [word.lower()]})
    items.sort(key=lambda i: i["pos"])

    def mentions(i):
        return len(re.findall(r"(?<![A-Za-z0-9])" + re.escape(headline[i["pos"]:i["pos"] + len(i["words"][0])]) + r"(?![A-Za-z0-9])", body))

    # Join names written as several plain words ("Modern Warfare", "Jensen Huang"); attach a single plain word to the
    # certain name right before it ("Tesla Roadster" -> #TeslaRoadster, next to #Tesla).
    # A Title Case Headline capitalises ordinary words too, so capitals prove nothing there: be strict.
    title_case = ordinary_caps >= 3 and ordinary_caps >= 0.4 * max(1, mid_caps)
    out, k = [], 0
    while k < len(items):
        it = items[k]
        if it["kind"] != "plain":
            out.append(dict(it, tier=0)); k += 1
            continue
        run = [it]
        if title_case:
            if mentions(it) >= 2:
                out.append(dict(it, tier=0))
            k += 1
            continue
        while k + len(run) < len(items) and items[k + len(run)]["kind"] == "plain" \
                and headline[run[-1]["end"]:items[k + len(run)]["pos"]] == " ":
            run.append(items[k + len(run)])
        prev = items[k - 1] if k and headline[items[k - 1]["end"]:it["pos"]] == " " else None
        if 2 <= len(run) <= 3:
            out.append({"pos": it["pos"], "tag": "".join(r["tag"] for r in run), "tier": 1, "words": [w for r in run for w in r["words"]]})
        elif len(run) == 1 and prev and prev["kind"] == "strong":
            out.append({"pos": it["pos"], "tag": prev["tag"] + it["tag"], "tier": 0, "words": prev["words"] + it["words"]})
        elif len(run) == 1:
            # The first name in a headline is its subject. A later single word must be a real subject of the article,
            # and not a piece of a longer title ("Zone Builder", "Conditional Approval").
            around = (headline[:it["pos"]].split() or [""])[-1], (headline[it["end"]:].split() or [""])[0]
            piece = (around[0][:1].isupper() and headline[it["pos"] - 1:it["pos"]] == " " and not (prev and prev["end"] + 1 == it["pos"])
                     and around[0].rstrip(":,.").lower() not in TAG_STOP and around[0][-1:] not in ":,.") \
                or (around[1][:1].isupper() and around[1].rstrip(":,.").lower() not in TAG_STOP
                    and not (k + 1 < len(items) and items[k + 1]["pos"] == it["end"] + 1))
            subject = not out and (it["pos"] == 0 or mentions(it) >= 2)
            out.append(dict(it, tier=2 if piece else (0 if (subject or mentions(it) >= 3) else 2)))
        k += len(run)
    for i in out:   # an unknown abbreviation the article barely uses (a unit, a code name) is not what people search
        w = i["words"][0]
        if i["tier"] == 0 and len(i["words"]) == 1 and i["tag"].isupper() and w not in TAG_HOT_NAMES and i is not out[0] \
                and body and mentions(i) < 2:
            i["tier"] = 2
    weight = hot or {}
    out.sort(key=lambda i: (i["tier"], -max((weight.get(w, 0) for w in i["words"]), default=0), i["pos"]))
    tags = []
    for i in out:
        if i["tier"] == 2:
            break                                    # weak candidates are left out: the field tag is the better fill-in
        if i["tag"].lower() not in {t.lower() for t in tags} and len(i["tag"]) <= 30:
            tags.append(i["tag"])
    return tags[:limit]


def outlet_words(sources) -> set:
    """Words of the news outlets an article cites ("Wired", "Verge"): the outlet is not the story, so never a tag."""
    out = set()
    for s in sources or []:
        if s.get("tier") != "A":
            out |= {w.lower() for w in re.findall(r"[A-Za-z0-9]+", (s.get("outlet") or "").split(" (")[0])}
    return out - {"the"}


def field_tag_for(field_key: str, field_label: str = "") -> str:
    return FIELD_TAGS.get((field_key or "").lower(), re.sub(r"[^A-Za-z0-9]", "", field_label or field_key or "Tech")) or "Tech"


def tag_line(tags, field: str, specific: int = 2, brand: bool = False, lower: bool = False) -> str:
    """The hashtag line for one platform: up to `specific` story names, then the field tag when there is room for it.
    With no story names it falls back to the field tag and #TechNews."""
    names = list(tags or [])[:specific]
    out = (["coldcasetech"] if brand else []) + names
    if len(names) < specific or brand:
        out.append(field)
    if not names or brand:
        out.append("TechNews")
    if brand:
        out.append("Tech")
    seen, line = set(), []
    for t in out:
        if t and t.lower() not in seen:
            seen.add(t.lower())
            line.append("#" + (t.lower() if lower else t))
    return " ".join(line)


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
            sources: list[dict], body: str = "", hot=None) -> dict:
    hook = (hook or summary or headline).strip()
    status_line = _status_line(status, verdict, due)
    field = field_tag_for(field_key, field_label)
    tags = story_tags(headline, body, hot, skip=outlet_words(sources))   # names from the headline: ["Waymo", "NHTSA"]
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
        return text + (f"\n\n{tag_line(tags, field, 2)}" if with_tag else "")
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
    instagram = "\n\n".join(p for p in [
        hook, summary if summary and summary != hook else "", status_line,
        "Full story and every source: link in bio.",
        "ColdCaseTech · An independent record of technology's promises",
        tag_line(tags, field, 5, brand=True, lower=True)] if p)
    if len(instagram) > INSTAGRAM_LIMIT:
        instagram = instagram[:INSTAGRAM_LIMIT - 1] + "…"

    return {
        "hook": hook,
        "x": x, "x_chars": x_length(x),
        "instagram": instagram,
        "tags": tags,
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
