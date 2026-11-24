# Your drafts

**Two ways to publish your own articles:**
- **Chat desk (recommended):** check and polish your draft in a Claude chat with `MASTER_PROMPT.md`, approve it,
  then put it in `drafts/ready/` (see the README there). Published word for word, byline "Written and edited by
  Rishit K. with AI assistance". About half the AI cost.
- **Plain draft (below):** put your draft here and the pipeline polishes it for you, byline "Written by Rishit K. ·
  edited with AI assistance". Approved articles in `drafts/ready/` always go first.

Put the articles you write here, one file per article. Each daily run publishes your oldest waiting draft first,
one per publishing slot (8:11 am, 2:11 pm, 8:11 pm IST, plus the 11:17 pm catch-up). When no draft is waiting, the AI
finds a story as before.

## How to add a draft (phone or computer)

1. Open this folder on GitHub and tap **Add file → Create new file**.
2. Name it anything ending in `.md`, for example `nvidia-ceo.md`.
3. Write it like this:

```
Jensen Huang resigns as Nvidia CEO; Colette Kress steps in

Write the story in your own words: what happened, who said it, when, and why it matters to readers.
Plain notes are fine. The pipeline turns it into the ColdCaseTech voice and format.

Paste the link to every source you used, anywhere in the text:
https://nvidianews.nvidia.com/...
https://www.reuters.com/...
```

4. Tap **Commit changes**.

## The rules your draft must meet

- **First line = the title.** At least 60 words below it.
- **Links:** at least one link to the company's own announcement or an official body, **or** links to two different
  newsrooms. Accepted: the approved list (`data/sources.json`) plus the newsroom list for your drafts
  (`data/draft_sources.json`: The Guardian, BBC, CNBC, Bloomberg, NYT, Times of India and more). Other links are
  ignored. Up to 15 links are read, in the order they appear.
- **Price tables** (Stock Analysis, Nasdaq) can back share prices and percentage changes only.
- **Paywalls:** the checker can't read most paywalled pages (Bloomberg, NYT, WSJ, FT). A line that rests only on one
  is held, so give each line a readable source too.
- **Every fact must be in one of your linked sources.** Names, numbers, dates, quotes, who said what.
- **No opinions, advice or predictions.** ColdCaseTech reports what sources state.

## What happens next

- **Published:** the article goes live with your byline ("Written by Rishit K. · edited with AI assistance"), and the
  draft moves to `drafts/published/`.
- **Held:** nothing is published. A file named `<your-draft>.NOTE.md` appears next to your draft, listing exactly
  which lines to fix. Edit your draft and commit; the next run tries it again. (A held draft you don't change is
  never retried, so it costs nothing.)

To publish a draft right away instead of waiting for the next slot: **Actions → Daily Cold-Case News Generator →
Run workflow**, set "What to run" to **tech**, then **Run workflow**. This publishes one extra article, using your
oldest waiting draft.
