---
title: "DeepSeek V4 and Kimi K3 weights match Nvidia Blackwell chips, researchers allege"
date: "2026-11-15T22:13:56Z"
description: "Unemployment Labs says DeepSeek V4, Kimi K3 and other open-weight Chinese models bear fingerprints of training on export-banned Nvidia Blackwell chips."
tags: ["Tech", "AI"]
desk: "tech"
verdict: ""
status: "report"
then: "Unemployment Labs, a nonprofit research group led by former OpenAI researcher Will DePue, reported evidence that open-weight Chinese AI models were trained on Nvidia Blackwell chips."
now: "The researchers state their method does not reveal where the chips were, how they were accessed, or prove that export controls were broken."
verified: "2026-11-15"
toolkit: "ai"
checked: "2026-11-15"
sourcing: "approved"
models: ["claude-sonnet-5-5"]

sources:
  - outlet: "TechCrunch"
    tier: "B"
    kind: "newsroom"
    date: "2026-11-13"
    title: "Export-banned Nvidia chips are behind China's most powerful AI models — uh-oh, Jensen! | TechCrunch"
    url: "https://techcrunch.com/2026/11/13/export-banned-nvidia-chips-are-behind-chinas-most-powerful-ai-models-uh-oh-jensen/"
  - outlet: "Tom's Hardware"
    tier: "B"
    kind: "newsroom"
    date: "2026-11-14"
    title: "Researchers allege DeepSeek, Kimi, and other Chinese AI models were trained using banned Nvidia Blackwell GPUs — Researchers use new GPU 'fingerprinting' technique to identify the GPUs used to train o"
    url: "https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware"
social:
  hook: "Unemployment Labs found Blackwell fingerprints in DeepSeek V4 weights. It cannot say where the chips sat."
  x: "Unemployment Labs found Blackwell fingerprints in DeepSeek V4 weights. It cannot say where the chips sat.\n\nEvery line sourced: https://coldcasetech.com/posts/2026-11-15-deepseek-kimi-weights-nvidia-blackwell-fingerprint/\n\n#DeepSeek #DeepSeekV4"
  instagram: "Unemployment Labs found Blackwell fingerprints in DeepSeek V4 weights. It cannot say where the chips sat.\n\nUnemployment Labs says DeepSeek V4, Kimi K3 and other open-weight Chinese models bear fingerprints of training on export-banned Nvidia Blackwell chips.\n\nFull story and every source: link in bio.\n\nColdCaseTech · An independent record of technology's promises\n\n#coldcasetech #deepseek #deepseekv4 #nvidia #blackwell #kimik3 #ai #technews #tech"
  tags: ["DeepSeek", "DeepSeekV4", "Nvidia", "Blackwell", "KimiK3"]
  replies: ["Blackwell B chips have 148 shader modules, GB chips 152. Researchers matched that to DeepSeek V4 weights. Changing the counts broke the match.", "The method works only on open-weight models. Tom's Hardware notes that renting Blackwell hardware abroad is not currently illegal for Chinese companies, as far as it can tell.", "Epoch AI estimates about two million advanced chips entered China in 2024 and 2025. Do you think weight fingerprints will be accepted as proof of where models were trained?"]
cover:
  image: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=1200&q=80"
  alt: "DeepSeek V4 and Kimi K3 weights match Nvidia Blackwell chips, researchers allege"
  relative: false
draft: false
---

Unemployment Labs, a nonprofit research group, analyzed open-weight models from DeepSeek, Moonshot AI, MiniMax and Ant Group, and found compelling evidence that the most closely watched models, including Moonshot's Kimi K3 releases and DeepSeek's V4 models, bear fingerprints from training on Blackwell chips ([TechCrunch](https://techcrunch.com/2026/11/13/export-banned-nvidia-chips-are-behind-chinas-most-powerful-ai-models-uh-oh-jensen/)). The group is led by Will DePue, a former OpenAI researcher, who analyzed the weights of the released models ([TechCrunch](https://techcrunch.com/2026/11/13/export-banned-nvidia-chips-are-behind-chinas-most-powerful-ai-models-uh-oh-jensen/)). The researchers hedge their findings, noting that the analysis does not reveal where the chips were or how they were accessed ([Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware)).

## Key Facts

| Item | Detail | Source |
|---|---|---|
| Researcher | Unemployment Labs, led by Will DePue | [TechCrunch](https://techcrunch.com/2026/11/13/export-banned-nvidia-chips-are-behind-chinas-most-powerful-ai-models-uh-oh-jensen/) |
| Models named | DeepSeek V4, Kimi K3.1, MiniMax-M3, Ling-3.1-Flash | [Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware) |
| Method | Statistical match of weight initialization to chip layouts | [Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware) |
| Export status | Blackwell GPUs are banned from export to China or Chinese-owned firms | [TechCrunch](https://techcrunch.com/2026/11/13/export-banned-nvidia-chips-are-behind-chinas-most-powerful-ai-models-uh-oh-jensen/) |
| Limit | Works only on models with open weights | [Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware) |

## Timeline

- **2026-11-13**: TechCrunch reports the Unemployment Labs findings on DeepSeek, Moonshot AI, MiniMax and Ant Group models ([TechCrunch](https://techcrunch.com/2026/11/13/export-banned-nvidia-chips-are-behind-chinas-most-powerful-ai-models-uh-oh-jensen/)).
- **2026-11-14**: Tom's Hardware details the fingerprinting technique and the models it names ([Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware)).

## Details (as Reported)

Nvidia's Hopper chips have 132 shader modules, Blackwell B series chips have 148, and Blackwell GB chips have 152 ([Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware)). Training begins by initializing weights with pseudo-random adjustments through cuRAND, a process spread across the shader modules and their threads ([Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware)).

The researchers repeated that initialization with the same chips, software and thread counts, and their weight distribution matched that of DeepSeek, Kimi and others ([Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware)). When they changed the shader module and thread counts, the correlation broke down ([Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware)). The method identifies chip families and an approximate card count, but cannot pinpoint the exact card variant ([Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware)). For DeepSeek V4, the researchers also analyzed the weight values and ruled out AMD cards ([Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware)).

White House technology adviser Michael Kratsios said earlier this year that Moonshot had used export-banned Nvidia chips, citing U.S. intelligence sources ([TechCrunch](https://techcrunch.com/2026/11/13/export-banned-nvidia-chips-are-behind-chinas-most-powerful-ai-models-uh-oh-jensen/)). Epoch AI estimates that about two million advanced chips entered China in 2024 and 2025 through schemes designed to hide their final destination ([TechCrunch](https://techcrunch.com/2026/11/13/export-banned-nvidia-chips-are-behind-chinas-most-powerful-ai-models-uh-oh-jensen/)). Epoch also estimates that 275,000 Nvidia AI accelerators were imported to Malaysia in 2024 and 2025 ([TechCrunch](https://techcrunch.com/2026/11/13/export-banned-nvidia-chips-are-behind-chinas-most-powerful-ai-models-uh-oh-jensen/)).

{{< recommend >}}


## What Is Not Yet Confirmed

- Whether export control laws were violated is not established, since the chips could have been in an offshore data center ([TechCrunch](https://techcrunch.com/2026/11/13/export-banned-nvidia-chips-are-behind-chinas-most-powerful-ai-models-uh-oh-jensen/)).
- Where the chips were located and how they were accessed are not revealed by the analysis ([Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware)).
- The models were not necessarily trained entirely on Nvidia chips ([TechCrunch](https://techcrunch.com/2026/11/13/export-banned-nvidia-chips-are-behind-chinas-most-powerful-ai-models-uh-oh-jensen/)).
- As far as Tom's Hardware can tell, it is not currently illegal for Chinese companies to rent Blackwell hardware abroad ([Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/researchers-allege-deepseek-kimi-and-other-chinese-ai-models-were-trained-on-export-controlled-nvidia-blackwell-chips-statistical-analysis-on-model-weights-reveals-high-correlation-to-nvidia-hardware)).

