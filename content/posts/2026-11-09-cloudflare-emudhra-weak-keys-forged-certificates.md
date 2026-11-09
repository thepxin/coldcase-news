---
title: "Cloudflare eMudhra weak keys: forged certificates appeared within hours of disclosure"
date: "2026-11-09T23:41:39Z"
description: "Cloudflare reported about 22,000 handshakes using eMudhra's weak keys and said it has seen no evidence of interception of its own connections so far."
tags: ["Tech", "Software"]
desk: "tech"
verdict: ""
status: "report"
then: "Cloudflare reported on October 30, 2026 that it learned of eMudhra's eight weak keys on October 19, patched its high-priority systems, and tracked exploitation attempts through logging added to Pingora."
now: "Cloudflare said all high-priority systems are patched, it has seen about 22,000 attempted handshakes with the weak keys, and it has no evidence so far of the keys being used to intercept its connections."
verified: "2026-11-09"
toolkit: "infra"
checked: "2026-11-09"
sourcing: "approved"
models: ["claude-sonnet-5-5"]

sources:
  - outlet: "Cloudflare"
    tier: "A"
    kind: "official"
    date: "2026-10-30"
    title: "4 real? Tracking exploitation and patching of eMudhra’s weak keys"
    url: "https://blog.cloudflare.com/emudhra-patching/"
social:
  hook: "eMudhra picked the number 4 as a key. Cloudflare logged about 22,000 attempted handshakes with the weak keys."
  x: "eMudhra picked the number 4 as a key. Cloudflare logged about 22,000 attempted handshakes with the weak keys.\n\nEvery line sourced: https://coldcasetech.com/posts/2026-11-09-cloudflare-emudhra-weak-keys-forged-certificates/\n\n#Software #TechNews"
  instagram: "eMudhra picked the number 4 as a key. Cloudflare logged about 22,000 attempted handshakes with the weak keys.\n\nCloudflare reported about 22,000 handshakes using eMudhra's weak keys and said it has seen no evidence of interception of its own connections so far.\n\nFull story and every source: link in bio.\n\nColdCaseTech · An independent record of technology's promises\n\n#coldcasetech #technews #tech #software"
cover:
  image: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=1200&q=80"
  alt: "Cloudflare eMudhra weak keys: forged certificates appeared within hours of disclosure"
  relative: false
draft: false
---

Cloudflare published a follow-up on October 30, 2026 detailing exploitation and patching after it learned on October 19 of eight weak keys belonging to the certificate authority eMudhra ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)). The company reported about 22,000 attempted handshakes using the keys and found no evidence so far of them being used to intercept its connections ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)). It also reported that at least one forged certificate appeared within hours of the weakness becoming public ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).

## Key Facts

| Item | Detail | Source |
|---|---|---|
| Weak keys | Eight keys, using the numbers 4, 56, 66, 115, 155, 156, 230 and 237 | [Cloudflare](https://blog.cloudflare.com/emudhra-patching/) |
| Handshakes logged | About 22,000 attempts with the weak keys | [Cloudflare](https://blog.cloudflare.com/emudhra-patching/) |
| Unusual certificates | About 160 handshakes named unrelated domains | [Cloudflare](https://blog.cloudflare.com/emudhra-patching/) |
| Cloudflare patching | All high-priority systems patched | [Cloudflare](https://blog.cloudflare.com/emudhra-patching/) |
| eMudhra status | Exiting the public CA business | [Cloudflare](https://blog.cloudflare.com/emudhra-patching/) |

## Timeline

- **2026-10-19**: Cloudflare learned of the weak keys and began patching high-impact systems ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).
- **2026-10-20**: A forged certificate was dated 18:19 UTC, less than an hour after Mozilla's bug report was made public ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).
- **2026-10-21**: Logging for eMudhra-signed certificates finished rolling out in Pingora ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).
- **2026-10-23**: Cloudflare changed its control endpoint to also serve an eMudhra certificate, this time without signed certificate timestamps ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).
- **2026-10-30**: Cloudflare published its follow-up on exploitation and patching ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).

## Details (as Reported)

Cloudflare described the weakness as unprecedented for a certificate authority, because the affected intermediate private keys could be recovered almost instantly by anyone from the public certificates themselves ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)). Where eMudhra was trusted to pick a 115-digit number, it picked the number 4 ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)). Any unpatched client that does not enforce Certificate Transparency would accept certificates for any domain created with the recovered keys ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).

On its own systems, Cloudflare patched customer origin-facing proxies using Pingora within hours to reject the vulnerable keys ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)). An AI-assisted analysis of its source code found all other systems trusting the weak keys within four hours, and lower-impact remediation was due at the end of last week ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)). A small number of confirmed low-impact tickets are still being worked on ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).

Two-thirds of the logged handshakes were fetches of test sites, and almost all of the rest went to origins that appeared to have set up a certificate for themselves using the weak intermediate ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)). Every handshake configured to verify the certificate was refused ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)). About 160 handshakes carried certificates naming other organizations' domains, some related to consumer IoT devices, and some were valid for over two years, longer than any public CA may issue ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)). Cloudflare judged that these looked like the servers' own default certificates and would have failed hostname verification anyway ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).

To gauge how many visitors still trust the weak keys, Cloudflare sent two probe connections on a fraction of its challenge pages and recorded 50 million probes over a week ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)). It cautioned that the traffic is skewed, contains many unconfirmed bots, and only includes clients that run JavaScript ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).

eMudhra announced it is exiting the public CA business and attributed the problem to a mistake in a key generation script ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)). It signed a certificate revocation list with what might have been a correctly generated key, then corrected it to be signed with the weak key ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).

{{< recommend >}}


## What Is Not Yet Confirmed

- eMudhra has not yet shared the key generation script ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).
- The role of the auditors and cross signers remains to be cleared up ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).
- Cloudflare noted that the absence of evidence does not exclude carefully targeted interception ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).
- Cloudflare cannot directly test whether a visitor still trusts the weak keys without breaking connections ([Cloudflare](https://blog.cloudflare.com/emudhra-patching/)).

