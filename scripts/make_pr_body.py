"""Write pr_body.md (your Security Friday review checklist, readable on your phone) from post_meta_security.json.
Prints the pull request title. Used by .github/workflows/daily_news.yml."""
import json
import sys

if sys.argv[1:] == ["update"]:
    # A dated update to an existing Security Friday case: it also needs your review.
    try:
        u = json.load(open("post_meta_update.json", encoding="utf-8"))
    except Exception:
        print("Security case update for review")
        open("pr_body.md", "w", encoding="utf-8").write("A security case got a dated update. Open **Files changed** to read it.\n")
        sys.exit(0)
    e = u.get("entry", {})
    moved = ""
    if e.get("verdict_from") != e.get("verdict_to"):
        moved = f"**Verdict change:** {e.get('verdict_from') or 'none'} -> {e.get('verdict_to')}"
    out = ["## Security Friday: update to an existing case", "",
           "The original case text is unchanged. One dated update was added to its `updates:` list (top of the file), "
           "and the case's status lines (`verdict`, `now`) were set to the newest state. It passed the source rules, "
           "the hard checks and a clean AI fact-check. **Nothing is live until you merge.**", "",
           f"**Case:** {u.get('title', '')}", f"**Update ({e.get('date', '')}):** {e.get('summary', '')}", "",
           e.get("text", ""), ""]
    if moved:
        out += [moved, ""]
    out += [f"**Automated result:** {u.get('report', '')}", "", "### New sources"]
    for x in e.get("sources", []):
        out.append(f"- **{x.get('outlet', '')}** (Tier {x.get('tier', '')}, {x.get('date', '') or 'undated'}): [{x.get('title', 'source')}]({x.get('url', '')})")
    out += ["", "### Your check (about 5 minutes)",
            "- [ ] The new sources are about the same incident",
            "- [ ] Every number, name and date in the update matches its cited source",
            "- [ ] A verdict change (if any) matches what the sources say", "",
            "**Publish:** Merge pull request. **Reject:** Close pull request (the case stays as it was).", "",
            f"File: `{u.get('file', '')}`"]
    open("pr_body.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(("Security case update: " + u.get("title", "case"))[:240])
    sys.exit(0)

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
