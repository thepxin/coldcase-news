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
"""
import json
import os
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
    items = [i for i in D.read_feeds(cfg, log=lambda *_: None, desk="tech") if not D.DEAL_TITLE.search(i["title"])]
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
    for name, fn in (("wire", fetch_wire), ("crypto", fetch_crypto)):
        data = run(name, fn)
        if data:
            save(name, data)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never fail the workflow
        print(f"fetch_feeds: unexpected error: {e}")
    sys.exit(0)
