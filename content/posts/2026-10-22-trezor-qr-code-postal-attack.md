---
title: "Trezor customers targeted with malicious QR code letters after shipping breach"
date: "2026-10-22T19:51:00Z"
description: "Trezor users receive phishing letters with QR codes after a shipping partner data breach."
tags: ["Follow-Up", "Investigation", "Security & Tech"]
verdict: "Escalated"
then: "Trezor disclosed on August 13, 2026 that a breach at its shipping partner ShipMonk exposed customer names, addresses, phone numbers and emails."
now: "Some Trezor customers have received postal letters urging them to 'migrate their wallets' via QR codes that redirect to phishing sites built to steal seed phrases, and the breach's scope has grown to roughly 81,000 customers."
verified: "2026-10-22"
toolkit: "breach"
model: "groq/openai/gpt-oss-120b"
cover:
  image: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80"
  alt: "Trezor customers targeted with malicious QR code letters after shipping breach"
  relative: false
draft: false
---

Trezor initially reported on August 13, 2026 that a breach at its shipping partner ShipMonk exposed the names, shipping addresses, phone numbers and email addresses of 13,689 customers (11,742 with full exposure, 1,947 with partial exposure), raising concerns about physical-mail and "wrench" attacks on crypto users. In early September, Trezor said the impact had grown to roughly 81,000 customers after older U.S. order records that ShipMonk was supposed to have deleted were also found exposed. By September 9, victims were reporting postal letters with QR codes linking to phishing sites designed to capture seed phrases, a clear escalation of the threat vector.

## Early Headlines vs. Current Reality
| Topic | Early Headlines | Current Reality | Source |
|---|---|---|---|
| Trezor breach | Trezor disclosed a shipping partner data breach | Victims receive letters urging a wallet "migration" via malicious QR codes; breach scope expanded to ~81,000 customers | Domainsure |
| Nvidia GPU VRAM hack | Nvidia crypto mining GPUs hacked to unlock locked VRAM | Software-only "CMP Unlocker" can theoretically unlock up to 64 GB on the CMP 170HX, but only 40 GB is confirmed working by users | Tom's Hardware |
| BlindLock feature | BlindLock hides passwords and crypto addresses inside images | Passwords, notes and 2FA codes are hidden in an encrypted PNG; the crypto feature (WalletLink, read-only balances and addresses) is still listed as "coming soon" | BlindLock |
| Crypto firm logistics breach | Crypto firm breached via logistics partner ShipMonk | Confirmed: this is the Trezor breach itself; attackers reportedly exploited a Metabase vulnerability, and ShipMonk received extortion emails from ShinyHunters | IT Security Awareness; Trezor; BleepingComputer |

## Timeline
- **2026-08-13**: Trezor publicly discloses the ShipMonk breach and notifies 13,689 affected customers by email (Trezor).
- **2026-08-18**: Tom's Hardware reports a software mod that unlocks hidden VRAM on Nvidia CMP mining GPUs (Tom's Hardware).
- **2026-08-18**: How to Hack a Crypto Currency Company article published on the logistics-partner breach (IT Security Awareness).
- **2026-09-09**: Domainsure details postal letters with malicious QR codes sent to Trezor customers after the shipping breach (Domainsure).
- **2026-09-10**: BlindLock's photo-based password vault cited; its planned WalletLink feature, which would display crypto balances and addresses without private keys, is listed as coming soon (BlindLock).

## Root Cause and Lessons
The Trezor incident stems from a data breach at third-party shipping provider ShipMonk, which exposed customer names, home addresses, phone numbers and email addresses; Trezor says its own systems, devices, private keys and wallet backups were not compromised. Attackers leveraged the exposed addresses to send physical letters that appear to come from Trezor, advising recipients to "migrate their wallets." Each letter contains a QR code that routes through an io-qr.cc redirector to a "qr-trezor" lookalike domain registered on September 3, unrelated to the official site. Scanning the code leads victims to a page that prompts for their seed phrase, resulting in wallet drainage. [Hardware security keys](/go/yubikey.html) protect account logins, but they offer no protection here: anyone who obtains a seed phrase can restore the wallet without any second factor. The only defense is never entering a seed phrase on any website or device other than the hardware wallet itself, and treating unsolicited mail claiming to be from Trezor as hostile.

Nvidia's CMP VRAM hack is rooted in firmware that disables memory stacks on GA100 silicon to create lower-spec SKUs. The CMP Unlocker tool, built on Jon Pry's research into defeating stack protection in Nvidia's Falcon security coprocessor, re-enables the hidden stacks entirely in software, with no physical modification, expanding memory capacity dramatically. Results vary, since some of the locked memory may have been disabled because it is defective. This underscores the importance of hardened secure coprocessors and firmware verification to prevent unauthorized hardware modifications.

BlindLock's approach stores passwords, notes and 2FA codes inside ordinary-looking PNG images, encrypted in two layers (AES-256-GCM and XChaCha20-Poly1305) and bound to the device's TPM or Secure Enclave. Its crypto feature, WalletLink, is not yet available and would only read public balances and addresses, not hold keys or assets. Users should still keep BlindLock's encrypted backup file and twelve recovery words offline and separate, since a copied image alone cannot restore access on a new device, and the security model assumes the device remains uncompromised.

The ShipMonk breach shows how a logistics partner that holds no crypto and touches no private keys can still become the weak link for a crypto firm. Notification emails indicated attackers exploited a vulnerability in the Metabase analytics platform, and ShipMonk also failed to delete older Trezor customer records as required by contract, which widened the exposure. Organizations should enforce strict data-retention and deletion audits for vendors, minimize the customer data shared with third parties, enforce strict email authentication, and train staff to verify unexpected requests.

{{< recommend >}}


## Sources
- [Domainsure, 2026-09-09](https://domainsure.com/crypto/trezor-supply-chain-hack-moves-to-postal-mail-attack/)
- [Tom's Hardware, 2026-08-18](https://www.tomshardware.com/pc-components/gpus/nvidia-crypto-mining-gpus-hacked-to-restore-locked-away-vram-in-order-to-feed-ai-boom-software-mod-unlocks-64gb-of-vram-on-usd250-cmp-170hx)
- [BlindLock, 2026-09-10](https://blindlock.app/en/)
- [IT Security Awareness, 2026-08-18](https://www.itsecurityawareness.ie/news/88/how-to-hack-a-crypto-currency-company-)
- [Trezor, 2026-08-13](https://trezor.io/blog/news/recent-customer-data-exposed-in-shipping-provider-incident)
- [BleepingComputer](https://www.bleepingcomputer.com/news/security/trezor-data-breach-impact-now-reaches-81-000-customers/amp/)
