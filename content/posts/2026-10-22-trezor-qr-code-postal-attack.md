---
title: "Trezor customers targeted with malicious QR code letters after shipping breach"
date: "2026-10-22T19:51:00Z"
description: "Trezor users receive phishing letters with QR codes after a shipping partner data breach."
tags: ["Follow-Up", "Investigation", "Security & Tech"]
verdict: "Escalated"
then: "Trezor disclosed a customer data breach in one of its shipping partners."
now: "Some Trezor customers are now receiving postal letters containing malicious QR codes that redirect to phishing sites to steal seed phrases."
verified: "2026-10-22"
toolkit: "breach"
model: "groq/openai/gpt-oss-120b"
cover:
  image: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80"
  alt: "Trezor customers targeted with malicious QR code letters after shipping breach"
  relative: false
draft: false
---

Trezor initially reported that a breach at one of its shipping partners exposed customer addresses, raising concerns about physical‑mail attacks on crypto users. Today, the breach has evolved: victims are receiving postal letters that contain QR codes linking to phishing sites designed to capture seed phrases, a clear escalation of the threat vector.

## Early Headlines vs. Current Reality
| Topic | Early Headlines | Current Reality | Source |
|---|---|---|---|
| Trezor breach | Trezor disclosed a shipping partner data breach | Victims receive malicious QR code letters | Domainsure |
| Nvidia GPU VRAM hack | Nvidia crypto mining GPUs hacked to unlock locked VRAM | Mod unlocks 64 GB VRAM on CMP 170HX as reported | Tom's Hardware |
| BlindLock feature | BlindLock hides passwords and crypto addresses inside images | Feature remains as described, no new changes | BlindLock |
| Crypto firm logistics breach | Crypto firm breached via logistics partner ShipMonk | Details remain speculative, no new evidence | IT Security Awareness |

## Timeline
- **2026-08-18**: How to Hack a Crypto Currency Company article published describing a logistics‑partner breach scenario (IT Security Awareness). 
- **2026-09-03**: Tom's Hardware reports a software mod that unlocks hidden VRAM on Nvidia CMP mining GPUs (Tom's Hardware). 
- **2026-09-09**: Domainsure details postal letters with malicious QR codes sent to Trezor customers after the shipping breach (Domainsure). 
- **2026-09-10**: BlindLock launches a photo‑based password vault that can store crypto balances without private keys (BlindLock).

## Root Cause and Lessons
The Trezor incident stems from a data leak at a third‑party shipping provider, which exposed customer home addresses. Attackers leveraged the exposed addresses to send physical letters that appear to come from Trezor, each containing a QR code that redirects to a domain unrelated to the official site. Scanning the code leads victims to a page that prompts for their seed phrase, resulting in wallet drainage. Using [hardware security keys](/go/yubikey.html) for two‑factor authentication can mitigate credential theft, but does not protect against address exposure.

Nvidia's CMP VRAM hack is rooted in firmware that disables memory stacks on GA100 silicon to create lower‑spec SKUs. Modders reverse‑engineered the firmware and re‑enabled the hidden stacks, expanding memory capacity dramatically. This underscores the importance of secure firmware signing and verification to prevent unauthorized hardware modifications.

BlindLock’s approach stores encrypted crypto balances inside ordinary‑looking images, relying on local encryption and TPM/SE chips. While the concept remains unchanged, users should still back up vaults offline and verify image integrity, as the security model assumes the device remains uncompromised.

The speculative ShipMonk breach narrative illustrates how supply‑chain phishing can cascade from a logistics partner to a crypto firm. Organizations should enforce strict email authentication, train staff to verify unexpected requests, and limit trust in third‑party communications.

{{< recommend >}}


## Sources
- [Domainsure, 2026-09-09](https://domainsure.com/crypto/trezor-supply-chain-hack-moves-to-postal-mail-attack/)
- [Tom's Hardware, 2026-09-03](https://www.tomshardware.com/pc-components/gpus/nvidia-crypto-mining-gpus-hacked-to-restore-locked-away-vram-in-order-to-feed-ai-boom-software-mod-unlocks-64gb-of-vram-on-usd250-cmp-170hx)
- [BlindLock, 2026-09-10](https://blindlock.app/en/)
- [IT Security Awareness, 2026-08-18](https://www.itsecurityawareness.ie/news/88/how-to-hack-a-crypto-currency-company-)

