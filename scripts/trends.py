"""What people are searching for and talking about right now, used ONLY to rank stories (never as a source).

Signals (all public, no keys, each fails safely to nothing):
  - Google Trends daily trending searches (US and India) and the news headlines attached to them.
  - The Hacker News front page (the most-read tech community).
  - HOT_NAMES: companies and products that people search for constantly.
A story still needs approved sources and must pass every check; trends only decide which good story goes first.
"""
import re
import xml.etree.ElementTree as ET

import requests

UA = "Mozilla/5.0 (compatible; ColdCaseTech-research/1.0; +https://coldcasetech.com/about/)"
GOOGLE_TRENDS = ["https://trends.google.com/trending/rss?geo=US", "https://trends.google.com/trending/rss?geo=IN"]
HACKER_NEWS = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=40"
HT = "{https://trends.google.com/trending/rss}"

HOT_NAMES = set("""
openai chatgpt sora anthropic claude gemini deepmind google pixel android chrome youtube apple iphone ipad macbook
airpods vision siri nvidia geforce rtx blackwell amd ryzen radeon intel qualcomm snapdragon arm tsmc microsoft windows
copilot xbox azure meta instagram whatsapp facebook quest llama tesla cybertruck robotaxi optimus spacex starship
starlink samsung galaxy sony playstation nintendo switch amazon alexa kindle aws netflix spotify tiktok bytedance
bitcoin ethereum deepseek grok perplexity mistral huawei xiaomi oneplus jio airtel reddit discord steam valve
""".split())

# words too common to say anything about a story
_STOP = set("""
about after also amid and announced announces are back been best biggest but can could day days does for from game games
gets has have here how into its just launch launches launched more most new news next not now off one only over part
people release released says show shows than that the their them they this time today top update updates video videos
watch what when where which while who why will with world year years your
""".split())


def _tokens(text):
    return {t for t in re.findall(r"[a-z][a-z0-9\-]{2,}", (text or "").lower()) if t not in _STOP}


def _get(url, timeout=12):
    r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
    r.raise_for_status()
    return r


def google_trends(log=print):
    """Trending searches and their news headlines, as one text block per trend."""
    out = []
    for url in GOOGLE_TRENDS:
        try:
            root = ET.fromstring(_get(url).content)
            n = 0
            for item in root.iter("item"):
                parts = [item.findtext("title") or ""]
                parts += [ni.findtext(HT + "news_item_title") or "" for ni in item.iter(HT + "news_item")]
                out.append(" ".join(parts))
                n += 1
            log(f"Trends OK (Google Trends {url.rsplit('=', 1)[-1]}): {n} trending searches")
        except Exception as e:
            log(f"Trends skipped (Google Trends {url.rsplit('=', 1)[-1]}): {str(e)[:100]}")
    return out


def hacker_news(log=print):
    try:
        hits = _get(HACKER_NEWS).json().get("hits", [])
        log(f"Trends OK (Hacker News front page): {len(hits)} stories")
        return [h.get("title") or "" for h in hits]
    except Exception as e:
        log(f"Trends skipped (Hacker News): {str(e)[:100]}")
        return []


class Hot:
    """Word weights for 'what is hot right now'. Google Trends words weigh 2, Hacker News words 1."""

    def __init__(self, google=(), hn=()):
        self.weight = {}
        for text in hn:
            for t in _tokens(text):
                self.weight[t] = max(self.weight.get(t, 0), 1)
        for text in google:
            for t in _tokens(text):
                self.weight[t] = 2

    @classmethod
    def fetch(cls, log=print):
        return cls(google_trends(log), hacker_news(log))

    def score(self, words):
        """Trend points for a story's name words (max 6)."""
        return min(6, sum(self.weight.get(w, 0) for w in set(words)))

    @staticmethod
    def famous(words):
        return bool(set(words) & HOT_NAMES)
