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

def fetch_clean_sources(query: str, max_items: int = 4) -> list[dict]:
    url = "https://hn.algolia.com/api/v1/search_by_date"
    params = {"query": query, "tags": "story", "hitsPerPage": 12}
    response = requests.get(url, params=params, timeout=15)
    hits = response.json().get("hits", [])

    sources = []
    for hit in hits:
        article_url = hit.get("url")
        title = hit.get("title")
        created_at = hit.get("created_at", "")
        if not article_url or not title:
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

def generate_article(topic: str, sources: list[dict]) -> FollowUpArticle:
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

def save_hugo_post(article: FollowUpArticle):
    os.makedirs("content/posts", exist_ok=True)
    os.makedirs("scripts", exist_ok=True)

    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    safe_slug = re.sub(r"[^a-z0-9-]", "-", article.slug.lower()).strip("-")[:55]
    safe_slug = re.sub(r"-+", "-", safe_slug)
    filename = f"content/posts/{today_str}-{safe_slug}.md"

    # json.dumps guarantees 100% valid YAML escaping for quotes and colons
    safe_title = json.dumps(article.headline)
    safe_desc = json.dumps(article.summary_description)
    cover_image = f"https://picsum.photos/seed/{safe_slug}/1200/630"

    affiliate_block = """
---
### Recommended Security & Privacy Toolkit
* **Credential Protection:** Isolate passwords in an encrypted vault with **1Password** or **Bitwarden** [Check Offer](https://example.com/affiliate).
* **Encrypted Network Traffic:** Protect traffic on untrusted networks with **Proton VPN** or **NordVPN** [Check Offer](https://example.com/affiliate).
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
    existing_files = " ".join(os.listdir("content/posts"))
    day_of_year = datetime.now(timezone.utc).timetuple().tm_yday

    for offset in range(len(TOPICS)):
        topic = TOPICS[(day_of_year + offset) % len(TOPICS)]
        print(f"Searching sources for topic: {topic}...")
        sources = fetch_clean_sources(topic)
        if len(sources) >= 2:
            article = generate_article(topic, sources)
            if article.has_meaningful_update:
                save_hugo_post(article)
                break
        time.sleep(2)