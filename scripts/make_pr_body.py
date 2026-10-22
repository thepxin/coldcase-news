"""Write pr_body.md (the review checklist you read on your phone) from post_meta.json.
Prints the PR title. Used by .github/workflows/daily_news.yml."""
import json
import sys

try:
    m = json.load(open("post_meta.json", encoding="utf-8"))
except Exception:
    print("New ColdCaseTech case for review")
    open("pr_body.md", "w", encoding="utf-8").write("New case generated. Open **Files changed** to read it, then Merge to publish or Close to reject.\n")
    sys.exit(0)

fallback = not str(m.get("model", "")).startswith("gemini")
lines = ["## New case ready for review", ""]
if fallback:
    lines += [f"> **Written by the fallback model ({m.get('model') or 'unknown'}).** Gemini was unavailable. "
              "Check the facts extra carefully before publishing.", ""]
lines += [
    f"**Headline:** {m.get('headline', '')}",
    f"**Verdict:** {m.get('verdict', '')}  ·  **Topic:** {m.get('topic', '')}  ·  **Words:** {m.get('words', '?')}  ·  **Model:** {m.get('model', '')}",
    "",
    f"**Then:** {m.get('then', '')}",
    "",
    f"**Now:** {m.get('now', '')}",
    "",
    "### Sources the article was allowed to use",
]
for s in m.get("sources", []):
    lines.append(f"- [{s.get('title', 'source')}]({s.get('url', '')}) ({s.get('date', '')})")
lines += [
    "",
    "### Your 5-minute check",
    "- [ ] The headline and verdict match what the sources actually say",
    "- [ ] Open 2 sources: numbers, names and dates in the article match them",
    "- [ ] No claim appears that is not in the sources",
    "- [ ] Nothing accuses a company or person of more than the sources support",
    "",
    "### How to decide (works in the GitHub phone app)",
    "- **Publish:** tap **Merge pull request**, then **Confirm merge**. The case goes live in about 2 minutes, then is shared to Dev.to and Hashnode automatically.",
    "- **Reject:** tap **Close pull request**. Nothing is published.",
    "- **Read it:** open **Files changed** and tap the post file.",
    "- **Fix a typo first:** in a browser, open **Files changed**, tap **...** on the file, choose **Edit file**, commit, then merge.",
    "",
    f"File: `{m.get('file', '')}`",
]
try:
    social = open("scripts/latest_social_teaser.txt", encoding="utf-8").read().strip()
except Exception:
    social = ""
if social:
    fence = "`" * 3
    lines += ["", "### Ready-to-copy social posts (share after you merge)", "", fence + "text",
              social.replace(fence, "'" * 3), fence]
open("pr_body.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
prefix = "Review (fallback model): " if fallback else "Review: "
print((prefix + m.get("headline", "new case"))[:240])
