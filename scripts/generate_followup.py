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

# --- AFFILIATE CONFIGURATION ---
ELEVENLABS_LINK = "https://try.elevenlabs.io/cy22d10gen9g"
AMAZON_TAG = "coldcasetech-21"

TOPICS = [
    "data breach investigation",
    "ransomware attack aftermath",
    "cloud outage post-mortem",
    "cybersecurity vulnerability patch",
    "AI startup shutdown",
    "fintech regulation enforcement",
    "crypto exchange hack recovery"
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
    url = "https://hn.algolia.com/api/v1/search_by_date"
    params = {"query": query, "tags": "story", "hitsPerPage": 15}
    try:
        response = requests.get(url, params=params, timeout=15)
        hits = response.json().get("hits", [])
    except Exception as e:
        print(f"Algolia fetch error: {e}")
        return []

    sources = []
    for hit in hits:
        article_url = hit.get("url")
        title = hit.get("title")
        created_at = hit.get("created_at", "")
        if not article_url or not title or article_url in used_urls:
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
        if len(sources) >= max_items:
            break
    return sources

def generate_article(topic: str, sources: list[dict]) -> FollowUpArticle | None:
    prompt = f"""
    You are an investigative tech and security follow-up editor analyzing: '{topic}'.
    Below are verified source extracts with their URLs and dates:
    {json.dumps(sources, indent=2)}

    INSTRUCTIONS:
    1. Set has_meaningful_update to true if there is enough factual substance here to write a compelling follow-up report.
    2. Write markdown_body using clean, standard Markdown. Do NOT use raw HTML tags or curly braces. Include:
        - A direct opening paragraph explaining the initial incident vs. reality today.
        - A Markdown comparison table comparing Early Headlines vs. Current Reality.
        - A chronological bulleted timeline with dates.
        - Outbound Markdown links citing the exact source URLs provided above.
        - Zero robotic AI filler words.
    3. Write a 3-sentence reddit_teaser summarizing the main takeaway.
    """

    # Retry up to 3 times if the model is in high demand (HTTP 503 / rate limits)
    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
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
            print(f"Gemini API attempt {attempt}/3 failed: {e}")
            if attempt < 3:
                wait_time = attempt * 15
                print(f"Waiting {wait_time}s before retrying...")
                time.sleep(wait_time)
    return None

def save_hugo_post(article: FollowUpArticle):
    os.makedirs("content/posts", exist_ok=True)
    os.makedirs("scripts", exist_ok=True)

    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    safe_slug = re.sub(r"[^a-z0-9-]", "-", article.slug.lower()).strip("-")[:55]
    safe_slug = re.sub(r"-+", "-", safe_slug)
    filename = f"content/posts/{today_str}-{safe_slug}.md"

    safe_title = json.dumps(article.headline)
    safe_desc = json.dumps(article.summary_description)
    cover_image = f"https://picsum.photos/seed/{safe_slug}/1200/630"

    t_lower = (article.headline + " " + article.markdown_body).lower()

    if any(k in t_lower for k in ["breach", "leak", "ransomware", "credential", "password"]):
        affiliate_block = f"""
---
### Verified Security & Incident Toolkit
* **Physical MFA Security:** Block phishing and credential stuffing with hardware FIDO2 keys — [Explore YubiKey 5 Series](https://www.amazon.in/dp/B07HBD7135?tag={AMAZON_TAG})
* **Air-Gapped Encrypted Storage:** Isolate critical backups offline on hardware-encrypted drives — [View Encrypted SSDs](https://www.amazon.in/s?k=hardware+encrypted+ssd&tag={AMAZON_TAG})
* **AI Audio & Narration Stack:** Power your automated media pipeline with lifelike synthesis — [Try ElevenLabs]({ELEVENLABS_LINK})

*Disclosure: As an Amazon Associate, ColdCaseTech earns from qualifying purchases.*
"""
    elif any(k in t_lower for k in ["cloud", "outage", "infrastructure", "server", "architecture", "ai"]):
        affiliate_block = f"""
---
### Infrastructure & AI Production Toolkit
* **Hardware Firewall & Isolated Lab:** Secure internal lab networks with dedicated security appliances — [Explore Network Firewalls](https://www.amazon.in/s?k=hardware+firewall+router&tag={AMAZON_TAG})
* **AI Voice Generation:** Build lifelike virtual narrators and automated audio briefings — [Explore ElevenLabs]({ELEVENLABS_LINK})
* **Uninterruptible Power & Uptime:** Protect local servers and routers against sudden power drops — [Check UPS Backup Systems](https://www.amazon.in/s?k=ups+power+backup+router&tag={AMAZON_TAG})

*Disclosure: As an Amazon Associate, ColdCaseTech earns from qualifying purchases.*
"""
    else:
        affiliate_block = f"""
---
### Recommended Privacy & Research Tools
* **Hardware Security Keys:** Lock down cloud and exchange accounts with physical FIDO2 authentication — [Explore YubiKey Security Keys](https://www.amazon.in/dp/B07HBD7135?tag={AMAZON_TAG})
* **AI Voice Synthesis:** Create high-retention multimedia and audio content — [Try ElevenLabs]({ELEVENLABS_LINK})
* **Data Backup & Redundancy:** Maintain immutable offsite snapshots — [Hardware Backup Solutions](https://www.amazon.in/s?k=encrypted+external+ssd&tag={AMAZON_TAG})

*Disclosure: As an Amazon Associate, ColdCaseTech earns from qualifying purchases.*
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

    with open("scripts/latest_social_teaser.txt", "w", encoding="utf-8") as f:
        f.write(f"HEADLINE: {article.headline}\n\n{article.reddit_teaser}\n")

    print(f"SUCCESS: Created clean article at {filename}")

if __name__ == "__main__":
    os.makedirs("content/posts", exist_ok=True)
    used_urls = get_previously_used_urls("content/posts")
    day_of_year = datetime.now(timezone.utc).timetuple().tm_yday

    for offset in range(len(TOPICS)):
        topic = TOPICS[(day_of_year + offset) % len(TOPICS)]
        print(f"Searching fresh sources for topic: {topic}...")
        sources = fetch_clean_sources(topic, used_urls)
        if len(sources) >= 2:
            article = generate_article(topic, sources)
            if article and article.has_meaningful_update:
                save_hugo_post(article)
                break
        time.sleep(2)