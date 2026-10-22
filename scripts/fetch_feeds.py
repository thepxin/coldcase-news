"""Fetch public security feeds and write them to data/feeds/*.json for Hugo.

Runs in GitHub Actions every 3 hours (see .github/workflows/feeds.yml).
Hugo reads these files at build time, so no key ever reaches a browser.

Rules:
- Each feed is independent. One failing source never stops the others.
- A file is only rewritten when its data actually changed, so the workflow
  commits (and Cloudflare rebuilds) only when there is something new.
- If a source fails, the last good data is kept for up to STALE_HOURS.
  After that the file says "unavailable" and the panel hides itself.
- The script always exits 0, so a feed problem never fails the workflow.

Sources (all free):
  kev        CISA Known Exploited Vulnerabilities (no key; GitHub mirror as backup)
  epss       FIRST EPSS exploit-probability scores (no key)
  breaches   Have I Been Pwned breach list (no key, CC BY 4.0: credit required)
  advisories GitHub Advisory Database (GITHUB_TOKEN optional, CC BY 4.0)
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

import requests

OUT_DIR = os.environ.get("FEEDS_OUT_DIR", "data/feeds")
STALE_HOURS = int(os.environ.get("FEEDS_STALE_HOURS", "48"))
TIMEOUT = 30
UA = "ColdCaseTech-feeds/1.0 (+https://coldcasetech.com/radar/)"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

KEV_URLS = [
    "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    "https://raw.githubusercontent.com/cisagov/kev-data/main/known_exploited_vulnerabilities.json",
]
EPSS_URL = "https://api.first.org/data/v1/epss"
HIBP_URL = "https://haveibeenpwned.com/api/v3/breaches"
HIBP_PAGE = "https://haveibeenpwned.com/PwnedWebsites#{name}"
GITHUB_ADV_URL = "https://api.github.com/advisories"


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

def fetch_kev():
    last_err = None
    for url in KEV_URLS:
        try:
            d = get_json(url)
            vulns = d["vulnerabilities"]
            break
        except Exception as e:  # try the mirror next
            last_err = e
            print(f"KEV: {url} failed: {e}")
    else:
        raise RuntimeError(f"all KEV sources failed: {last_err}")

    vulns = sorted(vulns, key=lambda v: (v.get("dateAdded", ""), v.get("cveID", "")), reverse=True)
    cutoff = (now_utc() - timedelta(days=30)).strftime("%Y-%m-%d")
    recent30 = [v for v in vulns if v.get("dateAdded", "") >= cutoff]
    vendors = Counter(v.get("vendorProject", "Unknown") for v in recent30).most_common(5)
    latest = [{
        "cve": v.get("cveID", ""),
        "vendor": v.get("vendorProject", ""),
        "product": v.get("product", ""),
        "name": v.get("vulnerabilityName", ""),
        "added": v.get("dateAdded", ""),
        "due": v.get("dueDate", ""),
        "ransomware": v.get("knownRansomwareCampaignUse", "") == "Known",
    } for v in vulns[:25]]
    return {
        "source": "CISA Known Exploited Vulnerabilities Catalog",
        "source_url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
        "catalog_version": d.get("catalogVersion", ""),
        "count": len(vulns),
        "added_30d": len(recent30),
        "vendors_30d": [{"vendor": n, "count": c} for n, c in vendors],
        "items": latest,
        "_recent_cves": [v.get("cveID") for v in vulns[:100] if v.get("cveID")],
    }


def fetch_epss(cves):
    """EPSS scores for recently added KEV entries: exploited now, and how likely next."""
    if not cves:
        raise RuntimeError("no CVEs to score (KEV unavailable)")
    scores = {}
    for i in range(0, len(cves), 50):
        batch = cves[i:i + 50]
        d = get_json(EPSS_URL, params={"cve": ",".join(batch), "limit": 100})
        for row in d.get("data", []):
            try:
                scores[row["cve"]] = (float(row["epss"]), float(row.get("percentile", 0)), row.get("date", ""))
            except (KeyError, ValueError):
                continue
    if not scores:
        raise RuntimeError("EPSS returned no scores")
    ranked = sorted(scores.items(), key=lambda kv: kv[1][0], reverse=True)
    score_date = max(s[2] for _, s in ranked)
    return {
        "source": "FIRST Exploit Prediction Scoring System (EPSS)",
        "source_url": "https://www.first.org/epss",
        "score_date": score_date,
        "items": [{"cve": c, "epss": round(s[0], 4), "percentile": round(s[1], 4)} for c, s in ranked[:10]],
        "scores": {c: round(s[0], 4) for c, s in ranked},
    }


def fetch_breaches():
    d = get_json(HIBP_URL)
    good = [b for b in d if b.get("IsVerified") and not any(
        b.get(k) for k in ("IsFabricated", "IsSensitive", "IsRetired", "IsSpamList", "IsMalware"))]
    good.sort(key=lambda b: b.get("AddedDate", ""), reverse=True)
    items = [{
        "name": b.get("Name", ""),
        "title": b.get("Title", ""),
        "domain": b.get("Domain", ""),
        "breach_date": b.get("BreachDate", ""),
        "added": (b.get("AddedDate", "") or "")[:10],
        "accounts": int(b.get("PwnCount", 0) or 0),
        "data": (b.get("DataClasses") or [])[:4],
        "url": HIBP_PAGE.format(name=b.get("Name", "")),
    } for b in good[:20]]
    if not items:
        raise RuntimeError("HIBP returned no usable breaches")
    return {
        "source": "Have I Been Pwned",
        "source_url": "https://haveibeenpwned.com/",
        "license": "CC BY 4.0",
        "items": items,
    }


def fetch_advisories():
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    items = []
    for sev in ("critical", "high"):
        d = get_json(GITHUB_ADV_URL, headers=headers, params={
            "type": "reviewed", "severity": sev, "sort": "published", "direction": "desc", "per_page": 20})
        for a in d:
            pkg = ((a.get("vulnerabilities") or [{}])[0] or {}).get("package") or {}
            items.append({
                "ghsa": a.get("ghsa_id", ""),
                "cve": a.get("cve_id") or "",
                "summary": (a.get("summary") or "").strip()[:140],
                "severity": a.get("severity", sev),
                "published": (a.get("published_at") or "")[:10],
                "ecosystem": pkg.get("ecosystem", ""),
                "package": pkg.get("name", ""),
                "url": a.get("html_url", ""),
            })
    items.sort(key=lambda x: (x["published"], x["severity"] == "critical"), reverse=True)
    if not items:
        raise RuntimeError("GitHub returned no advisories")
    return {
        "source": "GitHub Advisory Database",
        "source_url": "https://github.com/advisories",
        "license": "CC BY 4.0",
        "items": items[:15],
    }


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
    kev = run("kev", fetch_kev)
    if kev:
        save("kev", kev)
    epss = run("epss", fetch_epss, (kev or {}).get("_recent_cves", []))
    if epss:
        save("epss", epss)
    breaches = run("breaches", fetch_breaches)
    if breaches:
        save("breaches", breaches)
    adv = run("advisories", fetch_advisories)
    if adv:
        save("advisories", adv)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never fail the workflow
        print(f"fetch_feeds: unexpected error: {e}")
    sys.exit(0)
