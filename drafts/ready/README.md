# Approved articles

Put articles here that you have already checked with the chat desk (`drafts/MASTER_PROMPT.md`) and approved.
They are published **word for word**, before any plain draft, one per publishing slot.

1. In the chat, wait for **READY FOR THE EDITOR**, read the article, and fix anything you want changed.
2. Here: **Add file → Create new file**, name it e.g. `nvidia-huang-reinstated.md`.
3. Paste the chat's code block (from `# Headline` to the end; the ``` lines can stay or go). **Commit changes.**
   Copy it with the code block's copy button and paste it **straight here**. Going through Google Docs or Word turns
   every line into a heading and adds backslashes; the site repairs that, but a straight paste is safest.

**The shape of the file** (the chat writes all of it; paste it as it is):

```
# Headline
type: closed
verdict: Not Delivered
then: The earlier promise, who made it and when ([Outlet](URL)).
now: What happened ([Outlet](URL)).
summary: One factual sentence for search results and social posts.

The article body...
```

The `verdict`, `then`, `now` and `summary` lines are optional (older files without them still work; the site then
writes them itself), but with them nothing on the page comes from anyone except you and the chat.

**Sourcing rule:** at least one official source (the company's own page, an SEC filing, a regulator) or articles
from two different newsrooms. Two TechCrunch articles count as one newsroom.

Before publishing, the site adds the page data and social posts, then runs its own independent claim-by-claim check.
Every link must be an accepted, readable source. If anything fails, nothing is published and a
`<name>.NOTE.md` appears here saying what to fix. Edit and commit again to retry.

Published articles carry the byline "Written and edited by Rishit K. with AI assistance".
