"""Fetch the live side-panel data and write it to data/feeds/*.json for Hugo.

Runs in GitHub Actions every 3 hours (see .github/workflows/feeds.yml).
Hugo reads these files at build time, so visitors' browsers never contact these sources.

Rules:
- Each feed is independent. One failing source never stops the others.
- A file is only rewritten when its data actually changed.
- If a source fails, the last good data is kept for up to STALE_HOURS.
  After that the file says "unavailable" and the panel hides itself.
- The script always exits 0, so a feed problem never fails the workflow.

Sources (all free):
  wire    newest headlines from the approved tech outlets in data/sources.json (their public RSS feeds)
  crypto  Bitcoin, Ethereum and Solana prices in USD and INR from CoinGecko's free public API (credit shown)
  launches  the next rocket launches from The Space Devs' Launch Library 2 (free: 15 requests an hour without a key;
            we use 8 a day; they ask sites to keep a copy instead of sending visitors to them, which is what we do)
  support   when phones, Windows and Macs stop getting updates, from endoflife.date (free, open source, no key)
These two feed the Stakeout page (/stakeout/). Its outage board is live instead: functions/api/status.js.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUT_DIR = os.environ.get("FEEDS_OUT_DIR", "data/feeds")
STALE_HOURS = int(os.environ.get("FEEDS_STALE_HOURS", "48"))
TIMEOUT = 30
UA = "ColdCaseTech-feeds/1.0 (+https://coldcasetech.com/)"
COINGECKO_URL = ("https://api.coingecko.com/api/v3/simple/price"
                 "?ids=bitcoin,ethereum,solana&vs_currencies=usd,inr&include_24hr_change=true")
COINS = [("bitcoin", "BTC"), ("ethereum", "ETH"), ("solana", "SOL")]
LAUNCHES_URL = "https://ll.thespacedevs.com/2.3.0/launches/upcoming/?limit=12&mode=normal"
LAUNCHES_SHOWN = 6
EOL_URL = "https://endoflife.date/api/v1/products/{}"
WIRE_ITEMS = 8
WIRE_PER_OUTLET = 2
def now_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_json(url, **kw):
    headers = {"User-Agent": UA, "Accept": "application/json"}
    headers.update(kw.pop("headers", {}))
    r = requests.get(url, headers=headers, timeout=TIMEOUT, **kw)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------- sources

def fetch_wire():
    """Newest headlines from approved tech outlets (no deal posts), at most 2 per outlet."""
    import source_discovery as D
    cfg = D.load_config()
    items = [i for i in D.read_feeds(cfg, log=lambda *_: None, desk="tech")
             if not D.DEAL_TITLE.search(i["title"]) and not D.SECURITY_TITLE.search(i["title"])]
    if not items:
        raise RuntimeError("no feed items")
    items.sort(key=lambda i: i["date"], reverse=True)
    out, per = [], {}
    for i in items:
        name = i["outlet"]["name"]
        if per.get(name, 0) >= WIRE_PER_OUTLET:
            continue
        per[name] = per.get(name, 0) + 1
        out.append({"title": i["title"][:140], "url": i["url"], "outlet": name, "date": iso(i["date"])})
        if len(out) >= WIRE_ITEMS:
            break
    return {"items": out}


def fetch_crypto():
    key = os.environ.get("COINGECKO_API_KEY", "").strip()  # optional free "Demo" key from coingecko.com
    d = get_json(COINGECKO_URL, headers={"x-cg-demo-api-key": key} if key else {})
    items = []
    for cid, sym in COINS:
        c = d.get(cid) or {}
        if "usd" not in c:
            continue
        items.append({"symbol": sym, "usd": c["usd"], "inr": c.get("inr"),
                      "change_24h": round(float(c.get("usd_24h_change") or 0), 2)})
    if not items:
        raise RuntimeError("no prices returned")
    return {"items": items, "source": "CoinGecko", "source_url": "https://www.coingecko.com/"}


SHORT_PROVIDER = {
    "China Aerospace Science and Technology Corporation": "CASC (China)",
    "China Aerospace Science and Industry Corporation": "CASIC (China)",
    "Russian Federal Space Agency (ROSCOSMOS)": "Roscosmos",
    "United Launch Alliance": "ULA",
    "Indian Space Research Organization": "ISRO",
    "National Aeronautics and Space Administration": "NASA",
    "Japan Aerospace Exploration Agency": "JAXA",
    "Mitsubishi Heavy Industries": "Mitsubishi (Japan)",
}
SHORT_PLACE = {", People's Republic of China": ", China", ", Republic of Kazakhstan": ", Kazakhstan",
               ", Russian Federation": ", Russia"}


def _parse_iso(v):
    try:
        return datetime.strptime(v[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def fetch_launches():
    """Next rocket launches. Only what the page shows is kept: rocket, mission, time and how exact it is, status."""
    d = get_json(LAUNCHES_URL)
    out = []
    for l in d.get("results") or []:
        net = _parse_iso(l.get("net") or "")
        if not net or net < now_utc() - timedelta(hours=1):
            continue   # already launched
        name = l.get("name") or ""
        parts = name.split(" | ", 1)
        rocket = (((l.get("rocket") or {}).get("configuration") or {}).get("name") or parts[0]).strip()
        mission = ((l.get("mission") or {}).get("name") or (parts[1] if len(parts) > 1 else "")).strip()
        rocket = re.sub(r" Block \d+$", "", rocket)   # "Falcon 9 Block 5" -> "Falcon 9"
        mission = mission.replace(" TBD?", "").strip()
        provider = ((l.get("launch_service_provider") or {}).get("name") or "").strip()
        place = (((l.get("pad") or {}).get("location") or {}).get("name") or "").strip()
        for long, short in SHORT_PLACE.items():
            place = place.replace(long, short)
        status = ((l.get("status") or {}).get("abbrev") or "").strip()
        precision = ((l.get("net_precision") or {}).get("name") or "").strip()
        if not rocket:
            continue
        out.append({"rocket": rocket, "mission": mission, "net": iso(net), "status": status,
                    "precision": precision or "Day", "provider": SHORT_PROVIDER.get(provider, provider), "pad": place})
        if len(out) >= LAUNCHES_SHOWN:
            break
    if not out:
        raise RuntimeError("no upcoming launches returned")
    return {"items": out, "source": "The Space Devs (Launch Library 2)", "source_url": "https://thespacedevs.com/llapi"}


# Support clock: one card per product. "prefix" is put in front of the API's model labels; dates for Pixel are months.
SUPPORT = [
    {"id": "pixel", "name": "Google Pixel", "prefix": "", "month": True,
     "note": "Google publishes an end date for every Pixel."},
    {"id": "windows", "name": "Windows", "prefix": "Windows ", "only": "-w",
     "note": "Home and Pro editions. Each yearly update gets about 2 years of fixes."},
    {"id": "iphone", "name": "iPhone", "prefix": "iPhone ", "still": True,
     "note": "Apple doesn't announce end dates; it drops models when a new iOS comes out."},
    {"id": "macos", "name": "Mac", "prefix": "", "still": True,
     "note": "Apple doesn't announce end dates; older macOS versions stop getting fixes."},
]


def _label(rel, cfg):
    lab = (rel.get("label") or rel.get("name") or "").strip()
    lab = lab.replace(" (W)", "")
    if lab.startswith("macOS ") and "(" in lab:   # "macOS 14 (Sonoma)" -> "macOS 14 Sonoma"
        lab = lab.replace("(", "").replace(")", "")
    return cfg["prefix"] + lab


def _join(labels, prefix_word):
    """["Pixel 7", "Pixel 7 Pro"] -> "Pixel 7 and 7 Pro" (the shared first word is said once)."""
    if not labels:
        return ""
    first, rest = labels[0], labels[1:]
    rest = [x[len(prefix_word):] if prefix_word and x.startswith(prefix_word) else x for x in rest]
    allx = [first] + rest
    return allx[0] if len(allx) == 1 else ", ".join(allx[:-1]) + " and " + allx[-1]


def support_card(cfg, releases, today):
    rels = [r for r in releases if not cfg.get("only") or str(r.get("name", "")).endswith(cfg["only"])]
    word = (cfg["prefix"] or (_label(rels[0], cfg).split(" ")[0] + " ")) if rels else ""

    def group(rs):
        rs = sorted(rs, key=lambda r: (r.get("releaseDate") or "", len(_label(r, cfg))))
        return _join([_label(r, cfg) for r in rs], word)

    by_date = {}
    for r in rels:
        e = r.get("eolFrom")
        if isinstance(e, str) and len(e) >= 10:
            by_date.setdefault(e[:10], []).append(r)
    card = {"name": cfg["name"], "note": cfg["note"], "link": f"https://endoflife.date/{cfg['id']}"}
    if cfg.get("month"):
        card["month"] = True
    ended = sorted(d for d in by_date if d <= today)
    future = sorted(d for d in by_date if d > today)
    if ended:
        card["ended"] = {"what": group(by_date[ended[-1]]), "date": ended[-1]}
    if future:
        card["next"] = [{"what": group(by_date[d]), "date": d} for d in future[:2]]
    if cfg.get("still"):
        live = [r for r in rels if r.get("isMaintained") and not r.get("isEol")]
        live.sort(key=lambda r: r.get("releaseDate") or "")
        if live and cfg["id"] == "iphone":
            oldest = live[0]
            card["still"] = f"{_label(oldest, cfg)} ({(oldest.get('releaseDate') or '')[:4]}) and newer"
        elif live:
            card["still"] = _join([_label(r, cfg) for r in live], word)
    if not (card.get("ended") or card.get("next") or card.get("still")):
        return None
    return card


def fetch_support():
    today = now_utc().strftime("%Y-%m-%d")
    items = []
    for cfg in SUPPORT:
        try:
            d = get_json(EOL_URL.format(cfg["id"]))
            releases = (d.get("result") or {}).get("releases") or []
            card = support_card(cfg, releases, today)
            if card:
                items.append(card)
        except Exception as e:   # one product failing never hides the others
            print(f"support: {cfg['id']} failed ({e})")
    if not items:
        raise RuntimeError("no product data returned")
    return {"items": items, "source": "endoflife.date", "source_url": "https://endoflife.date/"}


# ---------------------------------------------------------------- writing

def load(name):
    try:
        with open(os.path.join(OUT_DIR, f"{name}.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def comparable(d):
    return {k: v for k, v in (d or {}).items() if k not in ("updated", "checked")}


def save(name, payload):
    """Write only if the data changed. Returns True when the file changed."""
    payload = {k: v for k, v in payload.items() if not k.startswith("_")}
    old = load(name)
    new = {"status": "ok", **payload}
    if old and old.get("status") == "ok" and comparable(old) == comparable(new):
        print(f"{name}: unchanged")
        return False
    new["updated"] = iso(now_utc())
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(new, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print(f"{name}: updated ({len(new.get('items', []))} items)")
    return True


def mark_failed(name, err):
    old = load(name)
    if old and old.get("status") == "ok":
        try:
            age = now_utc() - datetime.strptime(old["updated"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except Exception:
            age = timedelta(days=999)
        if age < timedelta(hours=STALE_HOURS):
            print(f"{name}: FAILED ({err}); keeping last good data from {old['updated']}")
            return False
    if old and old.get("status") == "unavailable":
        print(f"{name}: still unavailable ({err})")
        return False
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump({"status": "unavailable", "updated": iso(now_utc())}, f, indent=1)
        f.write("\n")
    print(f"{name}: FAILED ({err}); marked unavailable, panel will hide")
    return True


def run(name, fn, *args):
    try:
        return fn(*args)
    except Exception as e:
        mark_failed(name, e)
        return None


def main():
    for name, fn in (("wire", fetch_wire), ("crypto", fetch_crypto), ("launches", fetch_launches),
                     ("support", fetch_support)):
        data = run(name, fn)
        if data:
            save(name, data)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never fail the workflow
        print(f"fetch_feeds: unexpected error: {e}")
    sys.exit(0)
