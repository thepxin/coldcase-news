---
title: "Cloudflare DNS Zone Builder cuts peak memory 85% and halves build delay"
date: "2026-11-02T18:50:43Z"
description: "Cloudflare says a targeted build planner and new scheduler cut peak memory in its DNS Zone Builder by 85% and halved the delay before DNS data reaches Quicksilver."
tags: ["Tech", "Cloud and Infrastructure"]
desk: "tech"
verdict: ""
status: "report"
then: "Cloudflare announced on 2026-11-02 that a targeted build planner and a new scheduler for its DNS Zone Builder cut peak memory by 85% and halved the time from a DNS change to its data being written to Quicksilver."
now: "Cloudflare states that zone setting changes no longer rebuild zones with tens of millions of records, while timestamp-only updates still cause a full build until the caller and its purpose can be identified."
verified: "2026-11-02"
toolkit: "infra"
checked: "2026-11-02"
sourcing: "approved"
models: ["claude-sonnet-5-5"]

sources:
  - outlet: "Cloudflare"
    tier: "A"
    kind: "official"
    date: "2026-11-02"
    title: "How we halved DNS build delay and cut memory use by 85%"
    url: "https://blog.cloudflare.com/dns-targeted-zone-builds/"
social:
  hook: "Cloudflare says its DNS builds now use 85% less peak memory. Zone setting changes no longer rebuild zones with tens of millions of records."
  x: "Cloudflare says its DNS builds now use 85% less peak memory. Zone setting changes no longer rebuild zones with tens of millions of records.\n\nEvery line sourced: https://coldcasetech.com/posts/2026-11-02-cloudflare-dns-zone-builder-memory-cut/\n\n#Cloud #TechNews"
  instagram: "Cloudflare says its DNS builds now use 85% less peak memory. Zone setting changes no longer rebuild zones with tens of millions of records.\n\nCloudflare says a targeted build planner and new scheduler cut peak memory in its DNS Zone Builder by 85% and halved the delay before DNS data reaches Quicksilver.\n\nFull story and every source: link in bio.\n\nColdCaseTech · An independent record of technology's promises\n\n#coldcasetech #technews #tech #cloud"
cover:
  image: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80"
  alt: "Cloudflare DNS Zone Builder cuts peak memory 85% and halves build delay"
  relative: false
draft: false
---

Cloudflare reported on November 2, 2026 that a targeted build planner and a new scheduler for its DNS Zone Builder cut peak memory by 85% and halved the time from a DNS change to its data being written to Quicksilver ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)). The company set out the work in a blog post that follows its 2022 description of the DNS propagation pipeline ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)).

The Zone Builder now receives about 700 DNS record changes per second, up from about 250 in 2022, plus about 100 other events such as zone setting changes ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)). Some zones hold more than 20 million records, and the company expects them to keep growing toward hundreds of millions ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)).

## Key Facts

| Item | Detail | Source |
|---|---|---|
| Peak memory | Cut by 85% | [Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/) |
| Change-to-Quicksilver time | Halved | [Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/) |
| Record changes per second | About 700 now, about 250 in 2022 | [Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/) |
| Largest zones | More than 20 million records | [Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/) |
| Build types | Five, from resources only to full zone | [Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/) |

## Timeline

- **2026-11-02**: Cloudflare published its account of the targeted build planner and scheduler for DNS builds ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)).

## Details (as Reported)

A build reads the current database state, converts it into the format used at the edge, and writes any changes to Quicksilver ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)). According to the company, the original Zone Builder rebuilt the desired state from the current database state and did not need to know why a zone changed ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)). A full build still reads, encodes and compares every record and holds the whole zone in memory, and for the largest zones the zone does not fit in memory at all ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)).

The new planner chooses the smallest build the company can prove is safe, and the scheduler combines work for the same zone ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)). Builds come in five types: resources only, resources and metadata, apex and metadata, purge, and full zone ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)). The rule is that every key a targeted build writes must be byte-for-byte identical to what a full build would write, and if that cannot be proven the system does a full build ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)).

To support targeting, the company changed the event producer to include changed zone fields and settings, with previous and new values when available ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)). Cloudflare stated that the extra memory headroom let it safely shorten waits the pipeline has always needed for resilience ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)). In 2022, per-record builds were 150 times faster than full builds on average, and 4,250 times faster on a test zone with one million records ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)).

{{< recommend >}}


## What Is Not Yet Confirmed

- Some database functions only update a timestamp, and Cloudflare stated that such an update still causes a full build until it can identify the caller and its purpose ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)).
- Missing details, unknown events, or any change that may affect records anywhere in the zone also lead to a full build, according to Cloudflare ([Cloudflare](https://blog.cloudflare.com/dns-targeted-zone-builds/)).

