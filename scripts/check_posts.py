"""Check that every case still cites its sources with working links.

Runs automatically on every push that changes content/posts (see .github/workflows/check_posts.yml),
for example after you edit a post in a document editor and paste it back.
It reads the post's own source list (the 'sources:' section at the top of the file) and reports:
  - any paragraph, bullet or table row that no longer has a [text](link) citation,
  - any source that is no longer cited anywhere,
  - any [text] left without its (link),
  - any link that is not one of the post's sources.
Usage: python scripts/check_posts.py [post.md ...]   (no arguments = every post)
Exit code 1 when a problem is found, so the check shows a red X on GitHub.
"""
import glob
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guards  # noqa: E402

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def split_post(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, text, 0
    fm = yaml.safe_load(m.group(1)) or {}
    body_start_line = m.group(1).count("\n") + 3
    return fm, m.group(2), body_start_line


def check_file(path):
    """Return a list of (line_number, message). Empty list = the post is fine."""
    try:
        fm, body, offset = split_post(path)
    except Exception as e:
        return [(1, f"the top section (front matter) cannot be read: {e}")]
    if fm is None:
        return [(1, "missing the top section (front matter) between --- lines")]
    sources = fm.get("sources") or []
    if not sources:
        return []  # older posts without a stored source list are not checked
    problems = []
    for s in sources:
        if not isinstance(s, dict) or not s.get("url"):
            problems.append((1, "a source in the 'sources:' list has no url"))
    sources = [s for s in sources if isinstance(s, dict) and s.get("url")]
    for n, t in guards.uncited_lines(body):
        problems.append((offset + n - 1, f"no source link on this line: '{t}'"))
    cited = {guards._norm_url(u) for u in guards.MD_LINK.findall(body)}
    for s in sources:
        if guards._norm_url(s["url"]) not in cited:
            problems.append((1, f"source no longer cited anywhere: {s.get('outlet', '')} {s['url']}"))
    allowed = {guards._norm_url(s["url"]) for s in sources}
    names = sorted({str(s.get("outlet", "")).strip() for s in sources if s.get("outlet")}, key=len, reverse=True)
    for i, line in enumerate(body.splitlines(), 1):
        for m in re.finditer(r"\[([^\]]+)\](?!\()", line):
            problems.append((offset + i - 1, f"'[{m.group(1)[:60]}]' has lost its (link)"))
        plain = guards.MD_LINK.sub(" ", line.replace("](", "]\x00("))
        for name in names:
            short = name.split(" (")[0]
            if re.search(r"\(\s*" + re.escape(short) + r"[^()]{0,20}\)", plain):
                problems.append((offset + i - 1, f"'({short})' is plain text: its source link is missing"))
        for u in guards.MD_LINK.findall(line):
            if guards._norm_url(u) not in allowed:
                problems.append((offset + i - 1, f"link is not one of this post's sources: {u}"))
    return problems


def main(paths):
    paths = paths or sorted(glob.glob(os.path.join(REPO, "content", "posts", "*.md")))
    bad = 0
    for p in paths:
        if not p.endswith(".md") or not os.path.exists(p):
            continue
        rel = os.path.relpath(p, REPO)
        problems = check_file(p)
        if problems:
            bad += 1
            print(f"\nPROBLEMS in {rel}:")
            for line, msg in problems:
                print(f"  line {line}: {msg}")
                if os.environ.get("GITHUB_ACTIONS"):
                    print(f"::error file={rel},line={line}::{msg}")
        else:
            print(f"OK  {rel}")
    if bad:
        print(f"\n{bad} post(s) need fixing. Open each one on GitHub (pencil icon) and restore the missing links; "
              "the correct links are listed in the post's own 'sources:' section at the top.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
