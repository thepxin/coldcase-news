---
title: "NVIDIA releases cuDSS GPU solver library, citing up to 10x sparse solve speedups"
date: "2026-10-24T17:38:19Z"
description: "NVIDIA announced general availability of cuDSS, a CUDA-X library that moves sparse solving in engineering simulations onto GPUs."
tags: ["Tech", "Chips and Silicon"]
desk: "tech"
verdict: ""
status: "report"
then: "NVIDIA announced the general availability of cuDSS, a CUDA-X library that shifts a critical part of engineering and scientific simulations onto GPUs."
now: "NVIDIA stated that cuDSS launched in general availability on 2026-10-21 and can be used through C, C++, Python and Fortran interfaces."
verified: "2026-10-24"
toolkit: "gaming"
checked: "2026-10-24"
sourcing: "approved"
models: ["claude-sonnet-5-5"]

sources:
  - outlet: "NVIDIA"
    tier: "A"
    kind: "official"
    date: "2026-10-21"
    title: "NVIDIA cuDSS Now Generally Available to Accelerate Engineering and Scientific Simulations"
    url: "https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/"
social:
  hook: "NVIDIA announced general availability of cuDSS, a CUDA-X library that moves sparse solving in engineering simulations onto GPUs."
  x: "NVIDIA announced general availability of cuDSS, a CUDA-X library that moves sparse solving in engineering simulations onto GPUs.\n\nEvery line sourced: https://coldcasetech.com/posts/2026-10-24-nvidia-cudss-generally-available-simulation-library/\n\n#Semiconductors #TechNews"
  instagram: "NVIDIA announced general availability of cuDSS, a CUDA-X library that moves sparse solving in engineering simulations onto GPUs.\n\nFull story and every source: link in bio.\n\nColdCaseTech · An independent record of technology's promises\n\n#coldcasetech #technews #tech #semiconductors"
  reddit_title: "NVIDIA releases cuDSS GPU solver library, citing up to 10x sparse solve speedups"
  reddit_comment: "Checked against the official source (NVIDIA). The article links each line to its source, so you can read the originals."
  subreddits: ["nvidia", "hardware", "technology"]
cover:
  image: "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=1200&q=80"
  alt: "NVIDIA releases cuDSS GPU solver library, citing up to 10x sparse solve speedups"
  relative: false
draft: false
---

NVIDIA announced the general availability of cuDSS on 2026-10-21, describing it as a CUDA-X library that shifts a critical part of engineering and scientific simulations onto GPUs ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)). The library targets the solving of large sparse systems, the math-heavy step that repeats throughout such simulations and often limits how many designs a team can test ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)). The company named Applied Materials, COMSOL, Cadence, Dassault Systèmes, Siemens and Synopsys as industry leaders already integrating it into their tools ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)).

## Key Facts

| Item | Detail | Source |
|---|---|---|
| Product | NVIDIA cuDSS, a CUDA-X library | [NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/) |
| Status | Generally available from 2026-10-21 | [NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/) |
| Applied Materials result | Up to 10x faster sparse solves in Ginestra versus CPU-only approaches | [NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/) |
| ZEISS SMT result | Measured 4x speedup in an EUV lithography plasma simulation benchmark | [NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/) |
| Dassault Systèmes result | 8-10x speedup within Abaqus and electromagnetic solvers | [NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/) |
| Interfaces | C, C++, Python and Fortran | [NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/) |

## Timeline

- **2026-10-21**: NVIDIA announced that cuDSS launched in general availability ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)).

## Details (as Reported)

NVIDIA said that engineering feats from advanced chips to aircraft to industrial systems depend on simulation to predict how designs will perform before they are built ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)). As designs become more complex, simulations take longer to run, which raises computing demands and limits the number of ideas teams can test ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)). By tapping into GPUs, cuDSS is meant to reduce time to results and increase simulation throughput, letting end users explore larger models, more accurate representations and a wider design space at a reduced cost ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)).

The company reported that Applied Materials accelerated sparse solves in Ginestra, its physics-based, defect-centric simulation platform, speeding exploration of semiconductor materials and device reliability ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)). Using COMSOL Multiphysics with cuDSS, ZEISS SMT completed the full EUV lithography plasma simulation benchmark in six days and 14 hours ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)). Cadence uses cuDSS in its Celsius software to simulate heat, structural stress and warpage in advanced chips and 3D chip designs, helping customers including Nokia analyze complex designs faster ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)).

Siemens uses cuDSS in Simcenter STAR-CCM+ to accelerate simulations of structures in fluid-structure interaction workflows ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)). Synopsys applies it in its Sentaurus Device simulator for advanced logic, memory and power chips, helping Infineon model increasingly complex devices faster ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)).

According to NVIDIA, cuDSS can scale out of the box from individual workstations to large computing clusters ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)). Developers can integrate it into existing engineering, scientific and optimization software, bringing GPU acceleration to tools already used by engineers and researchers ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)). NVIDIA invited attendees of GTC Berlin to learn more at its demo booth and the Dassault Systèmes booth ([NVIDIA](https://blogs.nvidia.com/blog/cudss-generally-available-engineering-scientific-simulation/)).

{{< recommend >}}


## What Is Not Yet Confirmed

The sources do not list open questions.

