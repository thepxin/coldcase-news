"""Write pr_body.md (your Security Friday review checklist, readable on your phone) from post_meta_security.json.
Prints the pull request title. Used by .github/workflows/daily_news.yml."""
import json
import sys

try:
    m = json.load(open("post_meta_security.json", encoding="utf-8"))
except Exception:
    print("Security Friday: case for review")
    open("pr_body.md", "w", encoding="utf-8").write(
        "Security Friday case generated. Open **Files changed** to read it, then **Merge** to publish or **Close** to reject.\n")
    sys.exit(0)

fence = "`" * 3
lines = [
    "## Security Friday: case ready for your review",
    "",
    "This case already passed every automated step: approved sources only, the source rules, the hard checks and a clean "
    "AI fact-check. **Nothing is live until you merge.**",
    "",
    f"**Headline:** {m.get('headline', '')}",
    f"**Verdict:** {m.get('verdict', '')}",
    f"**Automated result:** {m.get('report', '')}",
    "",
    f"**Then:** {m.get('then', '')}",
    "",
    f"**Now:** {m.get('now', '')}",
    "",
    "### Sources it was written from",
]
for s in m.get("sources", []):
    lines.append(f"- **{s.get('outlet', '')}** (Tier {s.get('tier', '')}, {s.get('kind', '')}, {s.get('date', '') or 'undated'}): "
                 f"[{s.get('title', 'source')}]({s.get('url', '')})")
lines += [
    "",
    "### Your check (about 10 minutes)",
    "- [ ] Open every Tier A source: it is really the company's or official body's own page",
    "- [ ] The verdict matches what the sources say",
    "- [ ] Every number, name and date in the article matches its cited source",
    "- [ ] Nothing names or blames a company or person beyond what the sources state",
    "- [ ] No sentence draws a conclusion or gives advice",
    "",
    "### How to decide (GitHub phone app works)",
    "- **Publish:** tap **Merge pull request**, then **Confirm merge**. It goes live in about 2 minutes; Dev.to and Hashnode copies follow on a later daily run.",
    "- **Reject:** tap **Close pull request**. Nothing is published.",
    "- **Fix first:** in a browser, open **Files changed**, tap **...** on the file, **Edit file**, commit to this branch, then merge.",
    "",
    f"File: `{m.get('file', '')}`",
]
if m.get("social"):
    lines += ["", "### Ready-to-copy social posts (share after you merge)", "", fence + "text",
              m["social"].replace(fence, "'" * 3), fence]
open("pr_body.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(("Security Friday review: " + m.get("headline", "case"))[:240])
