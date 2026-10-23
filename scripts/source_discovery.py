"""Find stories ONLY from approved sources (data/sources.json) and enforce the source rules.

How a story is found:
  1. Read the feeds of every approved outlet (official bodies and established newsrooms).
  2. Pick recent items that match today's topic.
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
from datetime import datetime, timedelta, timezone
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
MAX_ARTICLE_FETCHES = 70

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
}
# A tech story must be about a promise/claim or its outcome, not just any news.
OUTCOME_WORDS = ["promised", "promise", "promises", "pledged", "pledge", "announced", "unveiled", "unveils", "launch", "launches", "launched",
                 "release", "released", "releases", "ships", "shipping", "shipped", "available", "rollout", "rolls out", "rolled out",
                 "delayed", "delay", "delays", "postponed", "pushed back", "cancel", "canceled", "cancelled", "scrapped", "roadmap",
                 "benchmark", "benchmarks", "performance", "tested", "review", "specs", "price", "pricing", "price cut", "target",
                 "deadline", "goal", "finally", "arrives", "missed", "falls short", "exceeds", "claims", "claimed", "update", "updates",
                 "approved", "approval", "rejected", "fined", "ruling", "deployed", "milestone"]

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


def fetch_html(url):
    if trafilatura is None:
        return None
    return trafilatura.fetch_url(url)


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


def subject_keys(title, df):
    keys = {t for t in tokens(title) if len(t) >= 4 and t not in GENERIC and not t.isdigit() and df.get(t, 0) <= KEY_MAX_DF}
    return keys | {c.upper() for c in CVE_PATTERN.findall(title)}


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


def discover(topics, used_urls, cfg=None, log=print, now=None, desk="security"):
    """Yield (topic, sources) for every candidate story on this desk that passes ALL rules, best first."""
    cfg = cfg or load_config()
    rules = cfg["rules"][desk]
    now = now or datetime.now(timezone.utc)
    items = [i for i in read_feeds(cfg, log, desk) if (now - i["date"]).days <= rules["max_age_days_newest"]]
    if not items:
        log("No feed items available; nothing to write today.")
        return
    df = {}
    for i in items:
        for t in set(tokens(i["title"] + " " + i["summary"])):
            df[t] = df.get(t, 0) + 1
    fetches = {"n": 0}
    cache = {}

    def get_source(url, tier_override=None, kind=None, outlet_name=None, feed_date=None, keys=frozenset()):
        if url in cache:
            return cache[url]
        if fetches["n"] >= MAX_ARTICLE_FETCHES:
            return None
        fetches["n"] += 1
        html = None
        try:
            html = fetch_html(url)
        except Exception:
            html = None
        data = extract(html, url) if html else None
        text = (data or {}).get("text") or ""
        result = None
        if kind == "own statement" and (EXTORTION_PAGE.search(text) or ".onion" in url):
            text = ""  # never treat an attacker's page as the organisation's statement
        if len(text) >= 400 and mentions(text, keys):
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
        cache[url] = result
        return result

    tried = set()  # URLs of stories already offered, so the same incident is never written twice in one run
    for topic in topics:
        seeds = [i for i in items if matches_topic(i, topic, desk) and i["url"] not in used_urls and i["url"] not in tried]
        scored = []
        for s in seeds:
            keys = subject_keys(s["title"], df)
            if not keys:
                continue
            related = [i for i in items if i is not s and (keys & (set(tokens(i["title"])) | {c.upper() for c in CVE_PATTERN.findall(i["title"])}))]
            scored.append((len({r["outlet"]["id"] for r in related}), s["date"], s, keys, related))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        log(f"[{desk}] Topic '{topic}': {len(scored)} candidate stories from approved feeds.")
        for _, _, seed, keys, related in scored[:5]:
            if seed["url"] in tried:
                continue
            label = seed["title"][:90]
            first = get_source(seed["url"], feed_date=seed["date"], keys=keys)
            if not first:
                log(f"  skip '{label}': could not read the article")
                continue
            sources = [first]
            for r in related:
                src = get_source(r["url"], feed_date=r["date"], keys=keys)
                if src and all(src["url"] != x["url"] for x in sources):
                    sources.append(src)
            # follow links from approved articles: approved domains, or the organisation's own site
            org_names = {t for t in tokens(seed["title"]) if len(t) >= 3 and t not in GENERIC}
            candidates = []
            for src in list(sources):
                for u in links_in(src.get("_html"), src["url"]):
                    if any(u == x["url"] for x in sources) or u in candidates:
                        continue
                    o = outlet_for(u, cfg)
                    own = (not o) and not host_of(u).endswith(".onion") and org_label(u) in org_names
                    if o or own:
                        candidates.append(u)
            candidates.sort(key=lambda u: (0 if not outlet_for(u, cfg) else 1 if outlet_for(u, cfg)["tier"] == "A" else 2))
            for u in candidates[:8]:
                if len(sources) >= rules["max_sources"]:
                    break
                o = outlet_for(u, cfg)
                if o:
                    src = get_source(u, keys=keys)
                elif rules.get("own_statement_counts_as_tier_a", True):
                    src = get_source(u, tier_override="A", kind="own statement",
                                     outlet_name=f"{org_label(u).capitalize()} (official statement)", keys=keys)
                else:
                    src = None
                if src and all(src["url"] != x["url"] for x in sources):
                    sources.append(src)
            needs_own = desk == "security" and bool(CLAIM_PATTERN.search(seed["title"]))
            ok, reasons = evaluate(sources, rules, needs_own, now)
            outlets = sorted({f"{s['outlet']} ({s['tier']})" for s in sources})
            if not ok:
                log(f"  skip '{label}': " + "; ".join(reasons) + f" [sources: {', '.join(outlets)}]")
                continue
            tried.update(x["url"] for x in sources)
            log(f"  PASS '{label}' with {len(sources)} sources: {', '.join(outlets)}")
            # Tier A first, then oldest to newest, and strip internal fields
            sources.sort(key=lambda s: (s["tier"] != "A", s["date"] or "9999"))
            yield topic, [{k: v for k, v in s.items() if not k.startswith("_")} for s in sources[: rules["max_sources"]]]
