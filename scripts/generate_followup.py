import os
import re
import json
import time
import requests
import trafilatura
from datetime import datetime, timezone
from pydantic import BaseModel
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

DEVTO_API_KEY = os.environ.get("DEVTO_API_KEY", "")
HASHNODE_TOKEN = os.environ.get("HASHNODE_TOKEN", "")
HASHNODE_PUB_ID = os.environ.get("HASHNODE_PUB_ID", "")
INDEXNOW_KEY = "cctindexnow2026key8941"

BASE_URL = "https://coldcasetech.com"

FTC_DISCLOSURE = (
    "*Disclosure: ColdCaseTech is reader-supported. We may earn an affiliate "
    "commission when you purchase through our partner links (including Contabo, Surfshark, "
    "GearUP, ElevenLabs, and as an Amazon Associate) at no extra cost to you.*"
)

CYBER_COVER_IMAGES = [
    "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1510511459019-5dda7724fd87?auto=format&fit=crop&w=1200&q=80",
]

TOPICS = [
    "data breach",
    "ransomware attack",
    "cloud outage",
    "zero day vulnerability",
    "linux vulnerability",
    "crypto hack",
    "security incident",
    "supply chain attack",
    "authentication bypass",
    "firewall vulnerability"
]

class FollowUpArticle(BaseModel):
    has_meaningful_update: bool
    headline: str
    slug: str
    summary_description: str
    original_claim: str
    current_reality: str
    verdict_score: str
    markdown_body: str
    reddit_teaser: str

def get_previously_used_urls(posts_dir: str = "content/posts") -> set[str]:
    used_urls = set()
    if not os.path.exists(posts_dir):
        return used_urls
    for fname in os.listdir(posts_dir):
        if fname.endswith(".md"):
            fpath = os.path.join(posts_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                    urls = re.findall(r'https?://[^\s\)\]]+', content)
                    used_urls.update(urls)
            except Exception:
                continue
    return used_urls

def fetch_clean_sources(query: str, used_urls: set[str], max_items: int = 4) -> list[dict]:
    sources = []
    endpoints = [
        "https://hn.algolia.com/api/v1/search_by_date",
        "https://hn.algolia.com/api/v1/search"
    ]
    for endpoint in endpoints:
        params = {"query": query, "tags": "story", "hitsPerPage": 40}
        try:
            response = requests.get(endpoint, params=params, timeout=15)
            hits = response.json().get("hits", [])
        except Exception as e:
            print(f"Algolia fetch error on {endpoint}: {e}")
            continue

        for hit in hits:
            article_url = hit.get("url")
            title = hit.get("title")
            created_at = hit.get("created_at", "")
            if not article_url or not title or article_url in used_urls:
                continue
            if any(s["url"] == article_url for s in sources):
                continue

            try:
                downloaded = trafilatura.fetch_url(article_url)
                extracted_text = trafilatura.extract(downloaded) if downloaded else ""
            except Exception:
                extracted_text = ""

            if extracted_text and len(extracted_text) > 300:
                sources.append({
                    "title": title,
                    "date": created_at[:10],
                    "url": article_url,
                    "excerpt": extracted_text[:1800]
                })
                used_urls.add(article_url)
            if len(sources) >= max_items:
                return sources
    return sources

def generate_article(topic: str, sources: list[dict]) -> FollowUpArticle | None:
    prompt = f"""
    You are an investigative tech and security follow-up editor at ColdCaseTech analyzing: '{topic}'.
    Below are verified source extracts with their URLs and dates:
    {json.dumps(sources, indent=2)}

    INSTRUCTIONS:
    1. Set has_meaningful_update to true if there is factual substance here to write a compelling follow-up report.
    2. Write markdown_body using clean, standard Markdown. Do NOT use raw HTML tags or curly braces. Include:
        - A direct opening paragraph explaining the initial incident vs. reality today.
        - A Markdown comparison table comparing Early Headlines vs. Current Reality.
        - A chronological bulleted timeline with dates.
        - Outbound Markdown links citing the exact source URLs provided above.
        - Exactly ONE natural, in-text contextual anchor link woven into the root-cause or infrastructure section choosing the most relevant:
          * For breach/ransomware recovery: [immutable off-site storage](/go/contabo-storage.html) or [hardware security keys](/go/yubikey.html)
          * For infrastructure/outage/architecture: [bare-metal dedicated servers](/go/contabo-dedicated.html) or [isolated compute nodes](/go/contabo-vps6.html)
          * For surveillance/traffic monitoring: [encrypted tunnel routing](/go/surfshark-vpn.html)
        - Zero robotic AI filler words.
    3. Write a 3-sentence reddit_teaser summarizing the main takeaway.
    """

    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FollowUpArticle,
                    temperature=0.4,
                ),
            )
            article = FollowUpArticle.model_validate_json(response.text)
            article.markdown_body = article.markdown_body.replace("{", "(").replace("}", ")")
            return article
        except Exception as e:
            print(f"Gemini API (gemini-3.8-flash) attempt {attempt}/3 failed: {e}")
            if attempt < 3:
                wait_time = attempt * 15
                print(f"Waiting {wait_time}s before retrying...")
                time.sleep(wait_time)
    return None

def syndicate_article(article: FollowUpArticle, canonical_url: str, cover_image: str):
    syndication_body = f"""> **Originally published on [ColdCaseTech]({canonical_url}):** *Then vs. Now Verdict ({article.verdict_score}):* {article.original_claim} — **Reality:** {article.current_reality}

{article.markdown_body}

---
*Track real-time breach telemetry and CISA KEV advisories on the [ColdCaseTech Live CVE Radar]({BASE_URL}/radar/) or follow us on [X (@coldcasetech)](https://x.com/coldcasetech).*
"""

    if DEVTO_API_KEY:
        try:
            res = requests.post(
                "https://dev.to/api/articles",
                headers={"api-key": DEVTO_API_KEY, "Content-Type": "application/json"},
                json={
                    "article": {
                        "title": article.headline,
                        "published": True,
                        "body_markdown": syndication_body,
                        "canonical_url": canonical_url,
                        "main_image": cover_image,
                        "tags": ["security", "cybersecurity", "cloud", "devops"]
                    }
                },
                timeout=15
            )
            if res.status_code in [200, 201]:
                print(f"SUCCESS: Syndicated to Dev.to -> {res.json().get('url')}")
            else:
                print(f"Dev.to warning: {res.status_code} - {res.text[:200]}")
        except Exception as e:
            print(f"Dev.to error: {e}")

    if HASHNODE_TOKEN and HASHNODE_PUB_ID:
        clean_pub_id = HASHNODE_PUB_ID.replace("dashboards/", "").strip("/")
        query = """
        mutation PublishPost($input: PublishPostInput!) {
          publishPost(input: $input) {
            post { url }
          }
        }
        """
        variables = {
            "input": {
                "title": article.headline,
                "publicationId": clean_pub_id,
                "contentMarkdown": syndication_body,
                "originalArticleURL": canonical_url,
                "coverImageOptions": {"coverImageURL": cover_image},
                "tags": [
                    {"slug": "cybersecurity", "name": "Cybersecurity"},
                    {"slug": "security", "name": "Security"},
                    {"slug": "cloud", "name": "Cloud"}
                ]
            }
        }
        try:
            h_res = requests.post(
                "https://gql.hashnode.com",
                headers={"Authorization": HASHNODE_TOKEN, "Content-Type": "application/json"},
                json={"query": query, "variables": variables},
                timeout=15
            )
            if h_res.status_code == 200 and "errors" not in h_res.json():
                post_url = h_res.json().get("data", {}).get("publishPost", {}).get("post", {}).get("url")
                print(f"SUCCESS: Syndicated to Hashnode -> {post_url}")
            else:
                print(f"Hashnode warning: {h_res.text[:200]}")
        except Exception as e:
            print(f"Hashnode error: {e}")

    try:
        ping_url = f"https://api.indexnow.org/indexnow?url={canonical_url}&key={INDEXNOW_KEY}"
        requests.get(ping_url, timeout=10)
        print(f"SUCCESS: Pinged Bing IndexNow for {canonical_url}")
    except Exception as e:
        print(f"IndexNow ping warning: {e}")

def save_hugo_post(article: FollowUpArticle):
    os.makedirs("content/posts", exist_ok=True)
    os.makedirs("scripts", exist_ok=True)

    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    safe_slug = re.sub(r"[^a-z0-9-]", "-", article.slug.lower()).strip("-")[:55]
    safe_slug = re.sub(r"-+", "-", safe_slug)
    filename = f"content/posts/{today_str}-{safe_slug}.md"
    canonical_url = f"{BASE_URL}/posts/{today_str}-{safe_slug}/"

    safe_title = json.dumps(article.headline)
    safe_desc = json.dumps(article.summary_description)
    img_index = sum(ord(c) for c in safe_slug) % len(CYBER_COVER_IMAGES)
    cover_image = CYBER_COVER_IMAGES[img_index]

    t_lower = (article.headline + " " + article.markdown_body).lower()

    if any(k in t_lower for k in ["breach", "leak", "ransomware", "credential", "password"]):
        affiliate_block = f"""
---
### Verified Security & Incident Toolkit
- **Air-Gapped Cloud Backups:** Prevent ransomware encryption from destroying local archives — [Deploy Contabo Storage VPS]({BASE_URL}/go/contabo-storage.html)
- **Identity & Metadata Masking:** Shield primary emails and personal PII from credential dumps and data brokers — [Activate Surfshark Alternative ID]({BASE_URL}/go/surfshark-id.html)
- **Encrypted Network Tunneling:** Lock down exposed traffic and remote endpoints against session hijacking — [Get Surfshark VPN]({BASE_URL}/go/surfshark-vpn.html)
- **Physical MFA Security:** Block phishing and credential stuffing with hardware FIDO2 keys — [Explore YubiKey 5 Series]({BASE_URL}/go/yubikey.html)
- **Air-Gapped Encrypted Storage:** Isolate critical backups offline on hardware-encrypted drives — [View Encrypted SSDs]({BASE_URL}/go/encrypted-ssd.html)
- **AI Audio & Narration Stack:** Power your automated media pipeline with lifelike synthesis — [Try ElevenLabs]({BASE_URL}/go/elevenlabs.html)

{FTC_DISCLOSURE}
"""
    elif any(k in t_lower for k in ["cloud", "outage", "infrastructure", "server", "architecture", "ai"]):
        affiliate_block = f"""
---
### Infrastructure & Network Resilience Toolkit
- **High-Availability Failover:** Migrate mission-critical databases to isolated bare-metal hardware — [Deploy Contabo Dedicated Servers]({BASE_URL}/go/contabo-dedicated.html)
- **Full-Stack Endpoint & Perimeter Defense:** Deploy integrated antivirus, breach alerts, and zero-trust tunneling — [Explore Surfshark Security Suite]({BASE_URL}/go/surfshark-suite.html)
- **Low-Latency Network & Packet Routing:** Mitigate ISP throttling, jitter, and unstable cross-region hops — [Optimize Routing with GearUP]({BASE_URL}/go/gearup.html)
- **Hardware Firewall & Isolated Lab:** Secure internal lab networks with dedicated security appliances — [Explore Network Firewalls]({BASE_URL}/go/firewall.html)
- **AI Voice Generation:** Build lifelike virtual narrators and automated audio briefings — [Explore ElevenLabs]({BASE_URL}/go/elevenlabs.html)
- **Uninterruptible Power & Uptime:** Protect local servers and routers against sudden power drops — [Check UPS Backup Systems]({BASE_URL}/go/ups-backup.html)

{FTC_DISCLOSURE}
"""
    else:
        affiliate_block = f"""
---
### Recommended Privacy & Research Tools
- **Isolated Cloud Sandbox:** Spin up disposable Linux environments for malware analysis and secure routing — [Deploy Contabo Core VPS]({BASE_URL}/go/contabo-vps.html)
- **Encrypted Client & Traffic Protection:** Secure workstation and mobile connections with a hardened VPN client — [Download Surfshark VPN]({BASE_URL}/go/surfshark-download.html)
- **Identity & Email Aliasing:** Prevent targeted spear-phishing on exchange and financial accounts — [Explore Surfshark Alternative ID]({BASE_URL}/go/surfshark-id.html)
- **Low-Jitter Connection Optimizer:** Stabilize high-traffic network routes and eliminate packet loss — [Try GearUP]({BASE_URL}/go/gearup.html)
- **Hardware Security Keys:** Lock down cloud and exchange accounts with physical FIDO2 authentication — [Explore YubiKey Security Keys]({BASE_URL}/go/yubikey.html)
- **AI Voice Synthesis:** Create high-retention multimedia and audio content — [Try ElevenLabs]({BASE_URL}/go/elevenlabs.html)

{FTC_DISCLOSURE}
"""

    markdown_content = f"""---
title: {safe_title}
date: "{now.strftime('%Y-%m-%dT%H:%M:%SZ')}"
description: {safe_desc}
tags: ["Follow-Up", "Investigation", "Security & Tech"]
cover:
  image: "{cover_image}"
  alt: {safe_title}
  relative: false
draft: false
---

> **Then vs. Now Verdict ({article.verdict_score}):** **Originally:** {article.original_claim} — **Reality Now:** {article.current_reality}

{article.markdown_body}
{affiliate_block}
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    social_kit = f"""================================================================
1. REDDIT / HACKER NEWS DROP (r/cybersecurity, r/sysadmin, r/devops)
================================================================
TITLE: {article.headline} [Forensic Post-Mortem]

BODY:
{article.reddit_teaser}

- Early Claim: {article.original_claim}
- Current Reality ({article.verdict_score}): {article.current_reality}

Full timeline & source breakdown: {canonical_url}

================================================================
2. X / TWITTER POST (https://x.com/coldcasetech)
================================================================
🚨 ColdCaseTech Post-Mortem: {article.headline}

Then: {article.original_claim}
Now ({article.verdict_score}): {article.current_reality}

Full technical breakdown & hardening playbook 👇
{canonical_url}

#CyberSecurity #InfoSec #SecOps #CloudSecurity #DFIR

================================================================
3. INSTAGRAM CAPTION (https://www.instagram.com/coldcasetech/)
================================================================
🔍 CASE FILE UPDATE: {article.headline}

Mainstream tech media moves on after 48 hours. Here is what the forensic post-mortem actually revealed:

📌 Early Headline: {article.original_claim}
⚡ Current Reality ({article.verdict_score}): {article.current_reality}

{article.reddit_teaser}

🔗 Read the full root-cause investigation and live CVE radar via the link in our bio (@coldcasetech) -> {BASE_URL}

#cybersecurity #infosec #ethicalhacking #cloudsecurity #socanalyst #technews #dfir #devsecops

================================================================
4. LINKEDIN POST (https://www.linkedin.com/in/coldcase-tech-29102a446/)
================================================================
🔍 Forensic Post-Mortem: {article.headline}

Initial incident disclosures rarely tell the full story. Here is how the technical reality shifted once the forensic dust settled:

• Initial Claim: {article.original_claim}
• Verified Reality ({article.verdict_score}): {article.current_reality}

{article.reddit_teaser}

Read the full timeline, source citations, and hardening playbook:
👉 {canonical_url}

#CyberSecurity #InfoSec #CloudSecurity #DFIR #IncidentResponse #SecOps
"""

    with open("scripts/latest_social_teaser.txt", "w", encoding="utf-8") as f:
        f.write(social_kit)

    print(f"SUCCESS: Created clean article at {filename}")
    syndicate_article(article, canonical_url, cover_image)

if __name__ == "__main__":
    os.makedirs("content/posts", exist_ok=True)
    used_urls = get_previously_used_urls("content/posts")
    day_of_year = datetime.now(timezone.utc).timetuple().tm_yday

    for offset in range(len(TOPICS)):
        topic = TOPICS[(day_of_year + offset) % len(TOPICS)]
        print(f"Searching fresh sources for topic: {topic}...")
        sources = fetch_clean_sources(topic, used_urls)
        print(f"Found {len(sources)} clean sources for '{topic}'.")
        if len(sources) >= 2:
            article = generate_article(topic, sources)
            if article and article.has_meaningful_update:
                save_hugo_post(article)
                break
        time.sleep(2)