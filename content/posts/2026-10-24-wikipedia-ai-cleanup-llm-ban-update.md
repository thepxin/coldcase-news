---
title: "Wikipedia bars LLM-written articles since March 2026 as AI cleanup continues"
date: "2026-10-24T17:35:49Z"
description: "Wikipedia has prohibited LLM-generated article content since March 2026; a founding cleanup editor says Pangram flagged 15 or 16 percent of new pages in early 2026."
tags: ["Tech", "AI"]
desk: "tech"
verdict: ""
status: "report"
then: "WikiProject AI Cleanup states that the Wikipedia guideline WP:LLM has prohibited using LLMs to generate or rewrite article content since March 2026, with limited exceptions for translation and basic copyediting."
now: "Founding member Ellia Lebleu told IEEE Spectrum that Pangram flagged perhaps 20 percent of new articles and drafts as AI-generated in late 2025 and 15 or 16 percent in early 2026, and that it is too early to tell whether the rule is working."
verified: "2026-10-24"
toolkit: "infra"
checked: "2026-10-24"
sourcing: "approved"
models: ["claude-sonnet-5-5"]

sources:
  - outlet: "Wikipedia (official statement)"
    tier: "A"
    kind: "own statement"
    date: "2026-10-24"
    title: "Wikipedia:WikiProject AI Cleanup - Wikipedia"
    url: "https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup"
  - outlet: "IEEE Spectrum"
    tier: "B"
    kind: "newsroom"
    date: "2026-10-21"
    title: "Inside Wikipedia’s Cleanup Effort Against AI Text"
    url: "https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup"
social:
  hook: "Wikipedia has prohibited LLM-generated article content since March 2026; a founding cleanup editor says Pangram flagged 15 or 16 percent of new pages in early 2026."
  x: "Wikipedia has prohibited LLM-generated article content since March 2026; a founding cleanup editor says Pangram flagged 15 or 16 percent of new pages in early 2026.\n\nEvery line sourced: https://coldcasetech.com/posts/2026-10-24-wikipedia-ai-cleanup-llm-ban-update/\n\n#AI #TechNews"
  threads: "Wikipedia has prohibited LLM-generated article content since March 2026; a founding cleanup editor says Pangram flagged 15 or 16 percent of new pages in early 2026.\n\nEvery line sourced: https://coldcasetech.com/posts/2026-10-24-wikipedia-ai-cleanup-llm-ban-update/"
  instagram: "Wikipedia has prohibited LLM-generated article content since March 2026; a founding cleanup editor says Pangram flagged 15 or 16 percent of new pages in early 2026.\n\nFull story and every source: link in bio.\n\nColdCaseTech · An independent record of technology's promises\n\n#coldcasetech #technews #tech #ai"
  reddit_title: "Wikipedia bars LLM-written articles since March 2026 as AI cleanup continues"
  reddit_comment: "Checked against 2 sources, including Wikipedia (official). The article links each line to its source, so you can read the originals."
  subreddits: ["artificial", "singularity", "technology"]
cover:
  image: "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1200&q=80"
  alt: "Wikipedia bars LLM-written articles since March 2026 as AI cleanup continues"
  relative: false
draft: false
---

WikiProject AI Cleanup, the volunteer effort to find and remove AI-generated material from Wikipedia, states that the guideline WP:LLM has prohibited the use of large language models to generate or rewrite article content since March 2026, with limited exceptions for translation and basic copyediting ([Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup)). In an interview published on 2026-10-21, founding member Ellia Lebleu told IEEE Spectrum that the detection company Pangram flagged perhaps 20 percent of new articles and drafts as AI-generated in late 2025, and 15 or 16 percent in early 2026 ([IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup)).

## Key Facts

| Item | Detail | Source |
| --- | --- | --- |
| Policy | WP:LLM prohibits LLMs to generate or rewrite article content since March 2026 | [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup) |
| Exceptions | Translation and basic copyediting | [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup) |
| Late 2025 estimate | Pangram flagged perhaps 20 percent of new articles and drafts | [IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup) |
| Early 2026 estimate | Pangram flagged 15 or 16 percent | [IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup) |
| Tool in development | Wikimedia Foundation is working on Paste Check | [IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup) |

## Timeline

- **2022-11-30**: ChatGPT was released, the date before which article text is very unlikely to be AI-generated ([Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup)).
- **2023-12-04**: The first founding members added their names to the project participant list ([Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup)).
- **2026-10-21**: IEEE Spectrum published its interview with Lebleu ([IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup)).

## Details (as Reported)

The project's stated goals include identifying AI-written text, identifying AI-generated images, keeping track of AI-using editors, educating editors, and protecting against disruption from AI agents ([Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup)). A lot of LLM-generated text inserted from 2022 to 2026 remains on the site, according to the project page, and pages clearly entirely LLM-generated can be nominated for speedy deletion under WP:G15 ([Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup)).

Early articles repeated phrases such as "stands as a testament" or "rich cultural heritage", while by 2025 the signs had become subtler and more structural ([IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup)). Lebleu called fake or misleading citations a major worry, adding that AI more often finds a real source but gets its content completely wrong ([IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup)).

Lebleu explained that Pangram was tested on Wikipedia content from before ChatGPT and found no false positives, so its results provide a very conservative lower bound ([IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup)). The vast majority of AI-generated content is submitted by beginner editors, Lebleu added, and the rule has been made visible in welcome messages, editing help and advice ([IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup)).

On tooling, another Wikipedia editor has built an AI source verifier that checks whether the sources on a page match the claims, and the Wikimedia Foundation is developing Paste Check to flag text pasted directly from some AI chatbots ([IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup)). The Foundation is also working on an attribution framework that could show AI users when an article was last edited, how comprehensive it is and whether editors have flagged problems ([IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup)).

{{< recommend >}}


## What Is Not Yet Confirmed

- Lebleu stated that it is still a little early to tell whether the rule prohibiting AI writing is working ([IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup)).
- It is not yet known whether the drop in flagged content reflects the recent policies or models getting more powerful before Pangram has had time to adapt, according to Lebleu ([IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup)).
- Because the AI source verifier is itself an AI model, there is no guarantee it will be correct every time, Lebleu stated ([IEEE Spectrum](https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup)).

