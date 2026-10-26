"""Find stories ONLY from approved sources (data/sources.json) and enforce the source rules.

How a story is found:
  1. Read the feeds of every approved outlet (official bodies and established newsrooms).
  2. Rank recent items by how HOT they are right now (see heat(): how many approved outlets cover the same story,
     how fresh it is, whether its names are trending on Google or Hacker News, and whether it is a famous name),
     across all tech fields, and try the hottest first (one article per field per day).
  3. For each candidate, collect sources about the SAME incident:
     - other approved feed items that share the incident's distinctive name or CVE ID, and
     - pages linked from those articles, but only on approved domains, or on the affected
       organisation's own website (its official statement, counted as Tier A).
  4. Every source must mention the incident's name or CVE ID, have readable text, and come
     from an approved place. Anything else is dropped.
  5. The story is used only if ALL rules pass (see "rules" in data/sources.json):
     - at least 2 different outlets, at least 1 Tier A source,
     - a real then-vs-now gap between the oldest and newest dated source,
     - a recent newest source, and
     - if the headline is about an attacker's CLAIM, the organisation's own statement is required.
If no story passes, nothing is published that day.
"""
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests

try:
    import feedparser
except ImportError:  # the workflow installs it; keeps imports safe for tests
    feedparser = None
try:
    import trafilatura
except ImportError:
    trafilatura = None

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "..", "data", "sources.json")
UA = "Mozilla/5.0 (compatible; ColdCaseTech-research/1.0; +https://coldcasetech.com/about/)"
MAX_ARTICLE_FETCHES = 300      # per desk per run (was 70: too low, later topics were never tried)
MAX_RELATED_FETCHES = 4        # per story: other approved outlets covering the same incident
MAX_LINK_FETCHES = 6           # per story: linked official / own-statement pages
FETCH_TIMEOUT = "15"

SECURITY_TOPICS = {
    "data breach": ["breach", "data leak", "leaked", "exposed data", "stolen data", "exfiltration", "exfiltrated"],
    "ransomware attack": ["ransomware", "extortion"],
    "cloud outage": ["outage", "disruption", "degraded", "experiencing issues", "unavailable", "post-incident", "postmortem", "post-mortem"],
    "zero day vulnerability": ["zero-day", "zero day", "0-day", "actively exploited", "exploited in the wild"],
    "linux vulnerability": ["linux", "kernel"],
    "crypto hack": ["crypto hack", "exchange hack", "wallet drain", "drained", "defi exploit", "bridge exploit"],
    "security incident": ["security incident", "cyberattack", "cyber attack", "hacked", "compromise", "intrusion"],
    "supply chain attack": ["supply chain attack", "supply-chain attack", "malicious package", "malicious packages", "poisoned"],
    "authentication bypass": ["authentication bypass", "auth bypass", "bypass authentication", "mfa bypass", "login bypass"],
    "firewall vulnerability": ["firewall", "vpn", "fortinet", "palo alto", "ivanti", "sonicwall", "citrix", "gateway"],
}
TECH_AREAS = {
    "ai": ["ai", "artificial intelligence", "openai", "chatgpt", "gemini", "claude", "llm", "copilot", "anthropic", "agent", "agents", "model", "models"],
    "devices": ["iphone", "pixel", "galaxy", "smartphone", "phone", "laptop", "macbook", "tablet", "ipad", "headset", "glasses", "smartwatch", "watch", "console", "playstation", "xbox", "nintendo", "switch", "wearable"],
    "chips and silicon": ["chip", "chips", "gpu", "gpus", "cpu", "silicon", "semiconductor", "processor", "rtx", "geforce", "radeon", "snapdragon", "tsmc", "wafer", "nm"],
    "software": ["software", "ios", "android", "windows", "macos", "app", "apps", "browser", "chrome", "firmware", "feature", "features"],
    "platforms": ["platform", "youtube", "spotify", "netflix", "instagram", "facebook", "whatsapp", "tiktok", "steam", "subscription", "app store", "play store"],
    "policy and privacy": ["regulation", "regulator", "law", "ban", "antitrust", "fcc", "commission", "court", "ruling", "privacy", "gdpr", "dma", "fine", "fined"],
    "crypto": ["bitcoin", "ethereum", "crypto", "etf", "etfs", "stablecoin", "stablecoins", "token", "blockchain", "solana"],
    "evs": ["ev", "evs", "electric vehicle", "electric vehicles", "tesla", "rivian", "battery", "batteries", "charging", "robotaxi", "self-driving", "autonomous"],
    "space": ["space", "nasa", "spacex", "starship", "rocket", "satellite", "satellites", "starlink", "moon", "lunar", "mars", "orbit", "esa", "isro"],
    "quantum": ["quantum", "qubit", "qubits", "quantum computer", "quantum computing"],
    "robotics": ["robot", "robots", "robotics", "humanoid", "drone", "drones", "automation"],
    "energy": ["solar", "fusion", "nuclear", "reactor", "grid", "wind power", "hydrogen", "energy storage", "power plant"],
    "telecom": ["5g", "6g", "broadband", "fiber", "wi-fi", "wifi", "telecom", "spectrum", "jio", "airtel", "verizon", "t-mobile"],
    "gaming": ["game", "games", "gaming", "console", "playstation", "xbox", "nintendo", "steam", "gpu"],
    "cloud and infrastructure": ["cloud", "data center", "datacenter", "aws", "azure", "google cloud", "server", "servers", "supercomputer"],
}
# A tech story must be about a promise/claim or its outcome, not just any news.
OUTCOME_WORDS = ["promised", "promise", "promises", "pledged", "pledge", "announced", "unveiled", "unveils", "launch", "launches", "launched",
                 "release", "released", "releases", "ships", "shipping", "shipped", "available", "rollout", "rolls out", "rolled out",
                 "delayed", "delay", "delays", "postponed", "pushed back", "cancel", "canceled", "cancelled", "scrapped", "roadmap",
                 "benchmark", "benchmarks", "performance", "tested", "review", "specs", "price", "pricing", "price cut", "target",
                 "deadline", "goal", "finally", "arrives", "missed", "falls short", "exceeds", "claims", "claimed", "update", "updates",
                 "approved", "approval", "rejected", "fined", "ruling", "deployed", "milestone",
                 "breakthrough", "record", "world's first", "first-ever", "achieves", "achieved", "introduces", "debuts",
                 "reveals", "demonstrates", "beats", "surpasses", "opens", "expands", "partners", "acquires", "raises"]

# Words that never identify a specific incident (so two unrelated stories are never merged).
GENERIC = set("""
about above across actively affected affecting after again against agency alert alerts allegedly also amid among announce announces
another attack attacked attacker attackers attacks authentication authorities available back become before being between billion
breach breached breaches bypass campaign cause caused claim claimed claims cloud company companies compromise compromised confirm
confirmed confirms critical customer customers cyber cyberattack cyberattacks damage data days devices disclose discloses disclosed
disruption down during email emails employees exploit exploited exploits expose exposed exposes failure files fixes flaw flaws following
from gang global government group groups hack hacked hacker hackers hacking hits impact impacted impacts incident incidents information
into investigation issue issues just last latest leak leaked leaks lessons linked links malicious malware many massive million millions
more most months multiple network networks new news newly next notifies notify notification officials outage outages over patch patched
patches people personal phishing platform police possible potential privacy probe questions ransom ransomware records related report
reported reports researchers response result reveals risk says security sensitive server servers service services sites software some
state stolen still such systems takes than that their them then there these they this those threat threats through time tool tools update
updates urges used user users using vulnerabilities vulnerability warn warning warns week what when where which while with without
worldwide year years zero-day after-hours review reviews tested hands-on finally first launch launches launched release
released announce announced announces unveils unveiled available price prices pricing cheaper faster better best biggest bigger
short falls falling rise rises rising drops drop gets getting coming comes here why how what's it's you your our now today week's
apps app phone phones feature features model models chip chips plan plans deal deals report reports sales market markets chinese russian iranian korean north american british indian european federal hacking-group
""".split())
SECOND_LEVEL_SUFFIXES = {"co.uk", "co.jp", "com.au", "co.in", "com.br", "co.kr", "com.cn", "co.nz", "com.sg", "com.hk", "co.za", "com.tw", "gov.uk", "org.uk", "ac.uk"}
CLAIM_PATTERN = re.compile(r"\b(claims?|claimed|allegedly|alleged|leak site|threatens to leak|says it (hacked|breached))\b", re.I)
CVE_PATTERN = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I)
DEAL_TITLE = re.compile(r"(\bsave (up to )?\$|\bdeals?\b|\d+% off|lowest price|all-time low|discount|coupon|best .* to buy|gift guide)", re.I)
JUNK_PATH = re.compile(r"^/?$|/(docs?|guides?|help|support|pricing|plans|careers|jobs|legal|privacy|terms|cookies?|login|signin|signup|register|download|contact|about/?$|products?/?$|store|shop|cart|account)(/|$)", re.I)
INCIDENT_WORDS = re.compile(r"(security|incident|breach|outage|advisory|bulletin|status|statement|update|notice|post-?mortem|postmortem|disclosure|announce|press|news|blog|investor|filing|release|launch|recall|vulnerab|cve)", re.I)
EXTORTION_PAGE = re.compile(r"(\.onion\b|will be (published|leaked|released)|pay (the )?ransom|before the deadline|data leak site|tox id|our (blog|site) will publish)", re.I)
SKIP_LINK = re.compile(r"(/tag/|/tags/|/author/|/category/|/topics?/|/search|/login|/subscribe|/newsletter|/feed|\.(jpg|jpeg|png|gif|svg|pdf|zip|mp4)$|#)", re.I)


# ---------------------------------------------------------------- helpers

def load_config(path=CONFIG_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def host_of(url):
    h = (urlparse(url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def outlet_for(url, cfg):
    h = host_of(url)
    for o in cfg["outlets"]:
        for d in o["domains"]:
            if h == d or h.endswith("." + d):
                return o
    return None


def org_label(url):
    """'capcom' for capcom.co.jp, 'railway' for blog.railway.com."""
    parts = host_of(url).split(".")
    if len(parts) < 2:
        return ""
    if ".".join(parts[-2:]) in SECOND_LEVEL_SUFFIXES and len(parts) >= 3:
        return parts[-3]
    return parts[-2]


def tokens(text):
    return [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", text or "")]


def iso(dt):
    return dt.strftime("%Y-%m-%d") if dt else ""


def parse_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            d = datetime.strptime(str(value)[:25], fmt)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


# ---------------------------------------------------------------- network (replaceable in tests)

def http_get(url):
    r = requests.get(url, headers={"User-Agent": UA, "Accept": "*/*"}, timeout=20)
    r.raise_for_status()
    return r.content


_TRAF_CONFIG = None


def fetch_html(url):
    global _TRAF_CONFIG
    if trafilatura is None:
        return None
    if _TRAF_CONFIG is None:
        try:
            from trafilatura.settings import use_config
            _TRAF_CONFIG = use_config()
            _TRAF_CONFIG.set("DEFAULT", "DOWNLOAD_TIMEOUT", FETCH_TIMEOUT)
        except Exception:
            _TRAF_CONFIG = False
    return trafilatura.fetch_url(url, config=_TRAF_CONFIG) if _TRAF_CONFIG else trafilatura.fetch_url(url)


def extract(html, url):
    """Readable text + publication date + title, using trafilatura's JSON output."""
    if trafilatura is None or not html:
        return None
    try:
        raw = trafilatura.extract(html, url=url, output_format="json", with_metadata=True,
                                  include_comments=False, include_tables=True)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def links_in(html, base_url):
    out = []
    for href in re.findall(r'href=["\']([^"\'#]+)["\']', html or "", re.I):
        u = urljoin(base_url, href.strip())
        if u.startswith("http") and not SKIP_LINK.search(u) and u not in out:
            out.append(u)
    return out


# ---------------------------------------------------------------- discovery

def read_feeds(cfg, log=print, desk=None):
    items = []
    if feedparser is None:
        log("feedparser is not installed; cannot read feeds.")
        return items
    for o in cfg["outlets"]:
        if desk and desk not in o.get("desks", ["security"]):
            continue
        for feed_url in o.get("feeds", []):
            try:
                parsed = feedparser.parse(http_get(feed_url))
            except Exception as e:
                log(f"Feed failed ({o['name']}): {feed_url}: {str(e)[:120]}")
                continue
            n = 0
            for e in parsed.entries:
                link = e.get("link") or ""
                title = (e.get("title") or "").strip()
                t = e.get("published_parsed") or e.get("updated_parsed")
                if not link or not title or not t:
                    continue
                items.append({"outlet": o, "title": title, "url": link,
                              "summary": re.sub(r"<[^>]+>", " ", e.get("summary") or "")[:800],
                              "date": datetime(*t[:6], tzinfo=timezone.utc)})
                n += 1
            log(f"Feed OK ({o['name']}): {n} items")
    return items


def _has_any(text, words):
    return any(re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", text) for w in words)


def matches_topic(item, topic, desk="security"):
    text = (item["title"] + " " + item["summary"]).lower()
    if desk == "tech":
        return _has_any(text, TECH_AREAS.get(topic, [topic])) and _has_any(text, OUTCOME_WORDS)
    return _has_any(text, SECURITY_TOPICS.get(topic, [topic]))


KEY_MAX_DF = 3
# Names in a big story appear in many feed items (8 outlets covering one launch). Story keys may appear in up to this
# many items, so the hottest stories keep their names; truly common words are in GENERIC or appear far more often.
HOT_KEY_MAX_DF = 12


def subject_keys(title, df, max_df=KEY_MAX_DF):
    keys = {t for t in tokens(title) if len(t) >= 4 and t not in GENERIC and not t.isdigit() and df.get(t, 0) <= max_df}
    return keys | {c.upper() for c in CVE_PATTERN.findall(title)}


def key_hits(text, keys):
    """How many of the story's keywords a page mentions. A matching CVE ID counts as 2 (it is unique)."""
    low = (text or "").lower()
    n = 0
    for k in keys:
        if k.startswith("CVE-"):
            n += 2 if k.lower() in low else 0
        elif re.search(r"\b" + re.escape(k) + r"\b", low):
            n += 1
    return n


def mentions_story(text, keys):
    """Strict check for OTHER pages (related coverage, linked pages): at least 2 of the story's keywords, so that
    e.g. 'Gemini' the AI model and 'Gemini' the crypto exchange are never treated as the same story."""
    return key_hits(text, keys) >= (1 if len(keys) <= 1 else 2)


def mentions(text, keys):
    low = (text or "").lower()
    for k in keys:
        if k.startswith("CVE-"):
            if k.lower() in low:
                return True
        elif re.search(r"\b" + re.escape(k) + r"\b", low):
            return True
    return False


def evaluate(sources, rules, needs_own_statement=False, now=None):
    """Return (ok, reasons). Pure function: the rule check, kept separate so it can be tested."""
    now = now or datetime.now(timezone.utc)
    reasons = []
    outlets = {s["outlet"] for s in sources}
    tier_a = [s for s in sources if s["tier"] == "A"]
    dated = sorted(d for d in (parse_date(s["date"]) for s in sources) if d)
    if rules.get("relaxed"):
        # tech: one official source, OR two different outlets, is enough; a time gap is only needed for a verdict
        if not (tier_a or len(outlets) >= 2):
            reasons.append("needs one official source or two different outlets")
        if not dated:
            reasons.append("no dated source")
        elif (now - dated[-1]).days > rules["max_age_days_newest"]:
            reasons.append("newest source is too old")
        return (not reasons), reasons
    if len(outlets) < rules["min_outlets"]:
        reasons.append(f"only {len(outlets)} outlet(s), need {rules['min_outlets']}")
    if len(tier_a) < rules["min_tier_a"]:
        reasons.append("no Tier A (official or the organisation's own) source")
    if needs_own_statement and not any(s["kind"] == "own statement" for s in sources):
        reasons.append("headline is about an attacker's claim and the organisation has not confirmed it")
    if len(dated) < 2:
        reasons.append("fewer than 2 dated sources, so then-vs-now cannot be shown")
    else:
        spread = (dated[-1] - dated[0]).days
        if spread < rules["min_spread_days"]:
            reasons.append(f"sources span only {spread} day(s), need {rules['min_spread_days']}")
        if (now - dated[-1]).days > rules["max_age_days_newest"]:
            reasons.append("newest source is too old")
    return (not reasons), reasons


class Finder:
    """Reads one desk's approved feeds once, then gathers verified sources for stories or case updates."""

    def __init__(self, cfg=None, desk="security", log=print, now=None):
        self.cfg = cfg or load_config()
        self.desk, self.log = desk, log
        self.rules = self.cfg["rules"][desk]
        self.now = now or datetime.now(timezone.utc)
        self.items = [i for i in read_feeds(self.cfg, log, desk) if (self.now - i["date"]).days <= self.rules["max_age_days_newest"]]
        self.df = {}
        for i in self.items:
            for t in set(tokens(i["title"] + " " + i["summary"])):
                self.df[t] = self.df.get(t, 0) + 1
        self.fetches, self.cache, self.why = 0, {}, {}

    def get_source(self, url, tier_override=None, kind=None, outlet_name=None, feed_date=None, keys=frozenset(),
                   strict=False):
        cfg, rules = self.cfg, self.rules
        if url in self.cache:  # each page is downloaded once per run; the checks below run for every story
            html, data = self.cache[url]
        elif self.fetches >= MAX_ARTICLE_FETCHES:
            self.why[url] = f"page limit for this run reached ({MAX_ARTICLE_FETCHES})"
            return None
        else:
            self.fetches += 1
            try:
                html = fetch_html(url)
            except Exception:
                html = None
            data = extract(html, url) if html else None
            self.cache[url] = (html, data)
        text = (data or {}).get("text") or ""
        result = None
        if not html:
            self.why[url] = "the site did not return the page (blocked, timed out or not found)"
        elif len(text) < 400:
            self.why[url] = "too little readable text on the page"
        elif not (mentions_story if strict else mentions)(text, keys):
            self.why[url] = "the page does not mention this story"
        if kind == "own statement" and text:
            if EXTORTION_PAGE.search(text) or ".onion" in url:
                text = ""  # never treat an attacker's page as the organisation's statement
            else:
                title = (data or {}).get("title") or ""
                plain_keys = {k for k in keys if not k.startswith("CVE-") and k != org_label(url)}
                hits = sum(1 for k in plain_keys if mentions(text, {k}))
                if not (INCIDENT_WORDS.search(title + " " + urlparse(url).path) or hits >= 2):
                    text = ""
                    self.why[url] = "organisation page is not about this story"
        if len(text) >= 400 and (mentions_story if strict else mentions)(text, keys):
            o = outlet_for(url, cfg)
            result = {
                "outlet": outlet_name or (o["name"] if o else host_of(url)),
                "tier": tier_override or (o["tier"] if o else "B"),
                "kind": kind or ("official" if o and o["tier"] == "A" else "newsroom"),
                "title": (data or {}).get("title") or url,
                "url": url,
                "date": iso(feed_date) or iso(parse_date((data or {}).get("date"))),
                "excerpt": text[: rules["excerpt_chars"]],
                "_html": html,
            }
        return result

    def related_items(self, seed, keys):
        return [i for i in self.items if i is not seed and (keys & (set(tokens(i["title"])) | {c.upper() for c in CVE_PATTERN.findall(i["title"])}))]

    def gather(self, seed, keys, related, org_names, skip_urls=frozenset()):
        """Seed article + related approved coverage + linked approved/official pages."""
        cfg, rules = self.cfg, self.rules
        first = self.get_source(seed["url"], feed_date=seed["date"], keys=keys)
        if not first:
            return None, self.why.get(seed["url"], "unknown reason")
        sources = [first]
        for r in sorted(related, key=lambda r: r["outlet"]["id"] == seed["outlet"]["id"])[:MAX_RELATED_FETCHES]:
            if r["url"] in skip_urls:
                continue
            src = self.get_source(r["url"], feed_date=r["date"], keys=keys, strict=True)
            if src and all(src["url"] != x["url"] for x in sources):
                sources.append(src)
        candidates = []
        for src in list(sources):
            for u in links_in(src.get("_html"), src["url"]):
                if (any(u == x["url"] for x in sources) or u in candidates or u in skip_urls
                        or JUNK_PATH.search(urlparse(u).path or "/")):
                    continue
                o = outlet_for(u, cfg)
                own = (not o) and not host_of(u).endswith(".onion") and org_label(u) in org_names
                if o or own:
                    candidates.append(u)
        candidates.sort(key=lambda u: (0 if not outlet_for(u, cfg) else 1 if outlet_for(u, cfg)["tier"] == "A" else 2))
        for u in candidates[:MAX_LINK_FETCHES]:
            if len(sources) >= rules["max_sources"]:
                break
            o = outlet_for(u, cfg)
            if o:
                src = self.get_source(u, keys=keys, strict=True)
            elif rules.get("own_statement_counts_as_tier_a", True):
                src = self.get_source(u, tier_override="A", kind="own statement",
                                      outlet_name=f"{org_label(u).capitalize()} (official statement)", keys=keys)
            else:
                src = None
            if src and all(src["url"] != x["url"] for x in sources):
                sources.append(src)
        return sources, ""


def clean(sources, limit):
    """Tier A first, then oldest to newest; strip internal fields."""
    sources = sorted(sources, key=lambda s: (s["tier"] != "A", s["date"] or "9999"))
    return [{k: v for k, v in s.items() if not k.startswith("_")} for s in sources[:limit]]


# ColdCaseTech is tech-only: security bulletins and incidents (CVE IDs, patches, exploits, breaches) are skipped
SECURITY_TITLE = re.compile(r"\bCVE-\d{4}-\d+|security (bulletin|advisory|update)|vulnerabilit|exploit|ransomware|"
                            r"malware|zero-day|\bpatch(es|ed)?\b|\bbreach|hacker|hacked|cyberattack", re.I)


def can_give_verdict(sources, rules):
    """A verdict (then vs now) needs at least 2 dated sources that are min_spread_days apart."""
    dated = sorted(d for d in (parse_date(s["date"]) for s in sources) if d)
    return len(dated) >= 2 and (dated[-1] - dated[0]).days >= rules["min_spread_days"]


def best_topic(item, topics, desk="tech"):
    """The field a story belongs to: the one with the most matching words (ties go to the earlier field)."""
    text = (item["title"] + " " + item["summary"]).lower()
    best, hits = None, 0
    for t in topics:
        words = TECH_AREAS.get(t, [t]) if desk == "tech" else SECURITY_TOPICS.get(t, [t])
        n = sum(1 for w in words if _has_any(text, [w]))
        if n > hits:
            best, hits = t, n
    return best


def heat(seed, keys, f, hot=None):
    """How hot a story is right now. Returns (score, details).
    coverage: different approved outlets covering the SAME story in the last 4 days (3 points each, up to 6 outlets)
    fresh:    newest coverage within 24 h = 4, 48 h = 2, 72 h = 1
    trend:    its names are in Google Trends or on the Hacker News front page (up to 6)
    famous:   a company or product people search for constantly (2)"""
    need = 1 if len(keys) <= 1 else 2
    cluster = [i for i in f.items if i is not seed and abs((i["date"] - seed["date"]).days) <= 4
               and key_hits(i["title"] + " " + i["summary"], keys) >= need]
    outlets = {seed["outlet"]["id"]} | {i["outlet"]["id"] for i in cluster}
    newest = max([seed["date"]] + [i["date"] for i in cluster])
    age_h = (f.now - newest).total_seconds() / 3600
    fresh = 4 if age_h <= 24 else 2 if age_h <= 48 else 1 if age_h <= 72 else 0
    words = {t for t in tokens(seed["title"]) if t not in GENERIC}
    trend = hot.score(words) if hot else 0
    famous = 2 if (hot and hot.famous(words)) else 0
    score = 3 * min(len(outlets), 6) + fresh + trend + famous
    return score, {"outlets": len(outlets), "fresh": fresh, "trend": trend, "famous": famous, "cluster": cluster}


MAX_TRIES = 24   # stories fully checked per run, hottest first


def discover(topics, used_urls, cfg=None, log=print, now=None, desk="tech", finder=None, known=(), skip_fields=(), hot=None):
    """Yield (topic, sources, mode) for candidate stories that pass the source rules, HOTTEST FIRST across all fields.
    known: keyword sets of existing cases (see case_keys); a story about one of them is left to the update desk.
    skip_fields: fields that already have an article today (read live, so it can grow while this runs).
    hot: trends.Hot (what people search for right now); None = rank by coverage and freshness only.
    mode "case":   the sources span enough time for a then-vs-now verdict (the writer may still choose a report or
                   an open case if that fits the sources better).
    mode "report": fresh news without a time gap: only a report (no verdict) or an open case (dated promise)."""
    f = finder or Finder(cfg, desk, log, now)
    if not f.items:
        log("No feed items available; nothing to write today.")
        return
    rules, now = f.rules, f.now
    scored = []
    for s in f.items:
        if s["url"] in used_urls or DEAL_TITLE.search(s["title"]) or SECURITY_TITLE.search(s["title"]):
            continue
        topic = best_topic(s, topics, desk)
        if not topic or (desk == "tech" and not _has_any((s["title"] + " " + s["summary"]).lower(), OUTCOME_WORDS)):
            continue
        keys = subject_keys(s["title"], f.df, HOT_KEY_MAX_DF)
        if not keys:
            continue
        score, d = heat(s, keys, f, hot)
        scored.append((score, s["date"], topics.index(topic), s, keys, topic, d))
    scored.sort(key=lambda x: (-x[0], -x[1].timestamp(), x[2]))
    log(f"[{desk}] {len(scored)} candidate stories from approved feeds. Hottest first:")
    shown, seen = 0, set()
    for score, _, _, s, _, topic, d in scored:
        if shown >= 10:
            break
        if s["url"] in seen:
            continue  # another outlet's version of a story already listed
        seen.update([s["url"]] + [i["url"] for i in d["cluster"]])
        shown += 1
        log(f"  {score:>2} pts  [{topic}] {s['title'][:80]}  (outlets {d['outlets']}, fresh +{d['fresh']}, "
            f"trending +{d['trend']}, famous +{d['famous']})")
    tried, tries, attempted = set(), 0, []
    for score, _, _, seed, keys, topic, d in scored:
        if tries >= MAX_TRIES:
            log(f"  stopped after checking the {MAX_TRIES} hottest stories")
            break
        if topic in skip_fields or seed["url"] in tried:
            continue
        label = seed["title"][:90]
        if any(same_case(case_keys(seed["title"]), k) for k in known):
            log(f"  skip '{label}': already an existing case or today's article (the update desk follows it)")
            tried.add(seed["url"])
            continue
        ck = case_keys(seed["title"])
        if sum(1 for a in attempted if same_case(ck, a)) >= 2:
            continue  # this story already failed twice from other outlets' versions
        attempted.append(ck)
        tries += 1
        # the same story from other approved outlets first, then anything sharing a name (gather checks each page)
        related = d["cluster"] + [r for r in f.related_items(seed, keys) if r not in d["cluster"]]
        org_names = {t for t in tokens(seed["title"]) if len(t) >= 3 and t not in GENERIC}
        sources, reason = f.gather(seed, keys, related, org_names)
        if not sources:
            log(f"  skip '{label}': could not use the article: {reason}")
            continue
        ok, reasons = evaluate(sources, rules, False, now)
        outlets = sorted({f"{s['outlet']} ({s['tier']})" for s in sources})
        if not ok:
            log(f"  skip '{label}': " + "; ".join(reasons) + f" [sources: {', '.join(outlets)}]")
            continue
        if can_give_verdict(sources, rules):
            mode = "case"
        else:
            newest = max(dd for dd in (parse_date(s["date"]) for s in sources) if dd)
            if (now - newest).days > rules.get("report_max_age_days", 3):
                log(f"  skip '{label}': no time gap for a verdict, and too old for a news report [sources: {', '.join(outlets)}]")
                continue
            mode = "report"
        tried.update(x["url"] for x in sources)
        tried.update(i["url"] for i in d["cluster"])
        log(f"  PASS ({mode}, {score} pts) [{topic}] '{label}' with {len(sources)} sources: {', '.join(outlets)}")
        yield topic, clean(sources, rules["max_sources"]), mode


CASE_STOP = set("""
about after again ahead also amid and announced announces are back before being both brings but can cheaper could
date dates day days deliveries delivery did does double early faster fewer first for from gets had has have higher how
into its just later less lower many measured month months more most much new news next not now off one only our out over
percent plan plans promised promises really reported reports review said says schedule set sets shipped ships slower some
still than that the their them then they this three time times twice two under unit units update updated updates was week
weeks were what when which while who why will with within without year years you your
january february march april may june july august september october november december
""".split()) | {w for w in OUTCOME_WORDS if " " not in w}
MODEL_NUMBER = re.compile(r"(?<![\d.,$A-Za-z])(\d{2,5})(?![\d.,%A-Za-z]|\s*(?:percent|per cent|x\b|times|gb|tb|mph|km|hours|days))", re.I)


def case_keys(title):
    """Name-like words (and model numbers such as 5090) of a case headline, to recognise later coverage of the SAME case."""
    words = {t for t in tokens(title) if t not in GENERIC and t not in CASE_STOP}
    nums = {n for n in MODEL_NUMBER.findall(title or "") if not re.fullmatch(r"(19|20)\d\d", n)}
    return words | nums


def _words(text):
    return set(tokens(text)) | set(MODEL_NUMBER.findall(text or ""))


def same_case(keys_a, keys_b):
    shared = len(keys_a & keys_b)
    return shared >= 2 and shared >= 0.6 * min(len(keys_a), len(keys_b))


def find_update(case, finder, log=print):
    """New, verified developments for an existing case, from approved feeds only.
    case: dict with title, since (datetime of the last update or publication) and urls (every URL already used).
    Returns (sources, reason). Every new source is dated AFTER 'since', is about the same case, and together they
    include at least one Tier A source or two different outlets."""
    f = finder
    keys = case_keys(case["title"])
    if not keys:
        return None, "headline has no distinctive names to search for"
    need = 3 if len(keys) >= 4 else min(2, len(keys))  # a one-name case must have that name in the headline
    since = case["since"]
    fresh = []
    for i in f.items:
        if i["date"] <= since or i["url"] in case["urls"] or DEAL_TITLE.search(i["title"]):
            continue
        hits = len(keys & _words(i["title"] + ("" if len(keys) == 1 else " " + i.get("summary", ""))))
        if hits >= need:
            fresh.append((hits, i))
    if not fresh:
        return None, "no new coverage in approved feeds"
    fresh = [i for _, i in sorted(fresh, key=lambda x: (x[0], x[1]["date"]), reverse=True)]
    org_names = {t for t in tokens(case["title"]) if len(t) >= 3 and t not in GENERIC}
    reason = "new coverage could not be read"
    for seed in fresh[:3]:
        sources, why = f.gather(seed, keys, [i for i in fresh if i is not seed], org_names, skip_urls=set(case["urls"]))
        if not sources:
            reason = why
            continue
        new = [s for s in sources if s["url"] not in case["urls"]
               and (parse_date(s["date"]) is not None and parse_date(s["date"]) > since)]
        if not new:
            reason = "no new source is dated after the last check"
            continue
        outlets = {s["outlet"] for s in new}
        if not (any(s["tier"] == "A" for s in new) or len(outlets) >= 2):
            reason = f"new coverage only from {', '.join(sorted(outlets))}: needs an official source or a second outlet"
            continue
        return clean(new, f.rules["max_sources"]), ""
    return None, reason
