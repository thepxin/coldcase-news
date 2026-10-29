---
title: "CodeRabbit uses OpenAI GPT-6.1 Sol as primary model in its security agent"
date: "2026-10-29T15:35:41Z"
description: "OpenAI announced that CodeRabbit uses GPT-6.1 Sol as the primary model in its security agent to review risks across complex codebases."
tags: ["Tech", "AI"]
desk: "tech"
verdict: ""
status: "report"
then: "OpenAI announced on 2026-10-26 that CodeRabbit is using GPT-6.1 Sol as the primary model in its security agent."
now: "OpenAI stated that CodeRabbit reports using GPT-6.1 Sol to flag security-related issues across thousands of repositories and organizations, with human reviewers deciding which changes ship."
verified: "2026-10-29"
toolkit: "ai"
checked: "2026-10-29"
sourcing: "approved"
models: ["claude-sonnet-5-5"]

sources:
  - outlet: "Coderabbit (official statement)"
    tier: "A"
    kind: "own statement"
    date: "2026-02-09"
    title: "CodeRabbit Security | AI Security Reviews & Deep Scans"
    url: "https://www.coderabbit.ai/security"
  - outlet: "OpenAI"
    tier: "A"
    kind: "official"
    date: "2026-10-26"
    title: "GPT-6.1 Sol helps CodeRabbit strengthen security across complex codebases"
    url: "https://openai.com/index/gpt-6-1-sol-coderabbit-code-security"
social:
  hook: "OpenAI says CodeRabbit now runs GPT-6.1 Sol as the primary model in its security agent. A person still approves each proposed fix."
  x: "OpenAI says CodeRabbit now runs GPT-6.1 Sol as the primary model in its security agent. A person still approves each proposed fix.\n\nEvery line sourced: https://coldcasetech.com/posts/2026-10-29-coderabbit-openai-gpt-6-1-sol-security-agent/\n\n#AI #TechNews"
  instagram: "OpenAI says CodeRabbit now runs GPT-6.1 Sol as the primary model in its security agent. A person still approves each proposed fix.\n\nFull story and every source: link in bio.\n\nColdCaseTech · An independent record of technology's promises\n\n#coldcasetech #technews #tech #ai"
cover:
  image: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80"
  alt: "CodeRabbit uses OpenAI GPT-6.1 Sol as primary model in its security agent"
  relative: false
draft: false
---

OpenAI announced on 2026-10-26 that CodeRabbit is using GPT-6.1 Sol as the primary model in its security agent, extending review beyond individual code changes to risks across complex codebases ([OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security)). CodeRabbit's system also uses other frontier models and security tooling, according to the announcement ([OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security)).

## Key Facts

| Item | Detail | Source |
|---|---|---|
| Model role | GPT-6.1 Sol is the primary model in CodeRabbit's security agent | [OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security) |
| Scale | CodeRabbit reports flagging issues across thousands of repositories and organizations | [OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security) |
| Deep Scan | Investigation across repositories, including dependencies and how components interact | [OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security) |
| Remediation | For supported issues, a drafted pull request for a person to review and approve | [OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security) |
| Billing | Deep Scan is billed separately | [CodeRabbit](https://www.coderabbit.ai/security) |

## Timeline

- **2026-02-09**: CodeRabbit described CodeRabbit Secure as security agents that trace exploitable paths across files, services and trust boundaries ([Coderabbit (official statement)](https://www.coderabbit.ai/security)).
- **2026-10-26**: OpenAI announced that CodeRabbit uses GPT-6.1 Sol as the primary model in its security agent ([OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security)).

## Details (as Reported)

OpenAI explained that a pull request can affect shared libraries, dependencies and safeguards elsewhere in an application, and that GPT-6.1 Sol helps CodeRabbit connect behavior across files and components to surface potential security issues ([OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security)). During pull-request review, the model helps analyze changes as developers work ([OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security)). CodeRabbit Secure extends the investigation to linked repositories, such as a shared authentication library ([OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security)).

The announcement states that CodeRabbit's review is independent of the agent that wrote the code and complements established scanners ([OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security)). For user-selected findings, CodeRabbit Secure can attempt exploit verification in an isolated sandbox without testing production systems ([OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security)). OpenAI added that human reviewers remain responsible for deciding which changes to ship ([OpenAI](https://openai.com/index/gpt-6-1-sol-coderabbit-code-security)).

CodeRabbit's own page states that every finding goes through reachability, exploitability and blast radius analyses, and that findings no attacker can reach are capped at low severity ([Coderabbit (official statement)](https://www.coderabbit.ai/security)). It also states that a verification pass rejects findings that are extremely hard to exploit ([Coderabbit (official statement)](https://www.coderabbit.ai/security)). Fix with AI drafts a fix in a pull request, and a person on the customer's team reviews and merges each fix, as CodeRabbit never merges one on its own ([Coderabbit (official statement)](https://www.coderabbit.ai/security)).

On data handling, CodeRabbit states that it never trains models on customer code and shares it with OpenAI, Anthropic or both only for reviews ([Coderabbit (official statement)](https://www.coderabbit.ai/security)). Cached data for private repositories is encrypted and expires within seven days, according to the company ([Coderabbit (official statement)](https://www.coderabbit.ai/security)). PR Security Review, Blast Radius, Security Architecture Review and the Attack Surface Map come with the Advanced and current Enterprise plans, and new organizations get a 14-day Advanced trial ([Coderabbit (official statement)](https://www.coderabbit.ai/security)).

{{< recommend >}}


## What Is Not Yet Confirmed

The sources do not list open questions.

