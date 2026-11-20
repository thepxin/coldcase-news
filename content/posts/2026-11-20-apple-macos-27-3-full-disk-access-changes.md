---
title: "Apple macOS 27.3 beta 2 splits Mac Device Control and Data Access in two"
date: "2026-11-20T08:58:00Z"
description: "Apple macOS 27.3 beta 2 splits Device Control and Data Access into two settings and adds more granular Full Disk Access options for Mac users."
tags: ["Tech", "Software"]
desk: "tech"
verdict: ""
status: "report"
then: "Apple announced on November 16, 2026 that macOS 27.3 beta 2 introduces increased transparency and more granular options for the Device Control and Data Access and Full Disk Access APIs."
now: "Apple said all app permissions previously granted by users remain in effect, and 9to5Mac reported that macOS 27.3 public beta 2 is now available ahead of next month's official release."
verified: "2026-11-20"
toolkit: "desktop"
checked: "2026-11-20"
sourcing: "approved"
models: ["claude-sonnet-5-5"]

sources:
  - outlet: "Apple"
    tier: "A"
    kind: "official"
    date: "2026-11-16"
    title: "Updates to Device Control and Data Access, and Full Disk Access in macOS - Latest News - Apple Developer"
    url: "https://developer.apple.com/news/?id=oqng0zjk"
  - outlet: "TechCrunch"
    tier: "B"
    kind: "newsroom"
    date: "2026-11-16"
    title: "Apple reveals new Mac security controls as AI agents raise privacy risks | TechCrunch"
    url: "https://techcrunch.com/2026/11/16/apple-reveals-new-mac-security-controls-as-ai-agents-raise-privacy-risks/"
  - outlet: "9to5Mac"
    tier: "B"
    kind: "newsroom"
    date: "2026-11-19"
    title: "macOS 27.3 public beta 2 now available, here’s everything new - 9to5Mac"
    url: "https://9to5mac.com/2026/11/19/macos-27-3-public-beta-2-now-available-heres-everything-new/"
social:
  hook: "Apple's macOS 27.3 beta 2 adds an option for apps to ask every time. Permissions already granted stay in effect."
  x: "Apple's macOS 27.3 beta 2 adds an option for apps to ask every time. Permissions already granted stay in effect.\n\nEvery line sourced: https://coldcasetech.com/posts/2026-11-20-apple-macos-27-3-full-disk-access-changes/\n\n#Apple #macOS"
  instagram: "Apple's macOS 27.3 beta 2 adds an option for apps to ask every time. Permissions already granted stay in effect.\n\nApple macOS 27.3 beta 2 splits Device Control and Data Access into two settings and adds more granular Full Disk Access options for Mac users.\n\nFull story and every source: link in bio.\n\nColdCaseTech · An independent record of technology's promises\n\n#coldcasetech #apple #macos #mac #device #software #technews #tech"
  tags: ["Apple", "macOS", "Mac", "Device"]
  replies: ["Apple's note says all permissions users already granted remain in effect. The new rules apply when approving new app permission requests.", "In macOS 27.3 beta 2, Apple split Device Control and Data Access into System & App Protection Override and Accessibility.", "Apple will let users set apps to ask for access every time. TechCrunch called it arguably tedious for automation. Would you switch it on?"]
  reel: ["Apple announced new Mac privacy controls in macOS 27.3 beta 2 on November 16.", "Device Control and Data Access is now split into two settings.", "Apple says users can set apps to ask every time they need access."]
cover:
  image: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80"
  alt: "Apple macOS 27.3 beta 2 splits Mac Device Control and Data Access in two"
  relative: false
draft: false
---

Apple announced on November 16, 2026 that macOS 27.3 beta 2 brings increased transparency and more granular options to two Mac APIs: Device Control and Data Access, and Full Disk Access ([Apple](https://developer.apple.com/news/?id=oqng0zjk)). The company wrote that users should understand that granting an app such access puts all of the data on their Mac at risk ([Apple](https://developer.apple.com/news/?id=oqng0zjk)). TechCrunch reported that the changes arrive as AI agents and their apps demand full disk access ([TechCrunch](https://techcrunch.com/2026/11/16/apple-reveals-new-mac-security-controls-as-ai-agents-raise-privacy-risks/)).

## Key Facts

| Item | Detail | Source |
| --- | --- | --- |
| Build | macOS 27.3 beta 2, announced November 16, 2026 | [Apple](https://developer.apple.com/news/?id=oqng0zjk) |
| Split | Device Control and Data Access becomes System & App Protection Override and Accessibility | [Apple](https://developer.apple.com/news/?id=oqng0zjk) |
| Granting access | A single method: select the requesting app from a list | [Apple](https://developer.apple.com/news/?id=oqng0zjk) |
| Ask every time | Users can configure apps to ask each time they need access | [Apple](https://developer.apple.com/news/?id=oqng0zjk) |
| Existing permissions | All permissions previously granted remain in effect | [Apple](https://developer.apple.com/news/?id=oqng0zjk) |
| Entitlements | Backup and assistive technology apps can request them | [Apple](https://developer.apple.com/news/?id=oqng0zjk) |

## Timeline

- **2026-11-16**: Apple announced the changes to Device Control and Data Access and to Full Disk Access in macOS 27.3 beta 2 ([Apple](https://developer.apple.com/news/?id=oqng0zjk)).
- **2026-11-19**: 9to5Mac reported that macOS 27.3 public beta 2 is available, with a build that matches the developer build ([9to5Mac](https://9to5mac.com/2026/11/19/macos-27-3-public-beta-2-now-available-heres-everything-new/)).

## Details (as Reported)

Beyond the split into two settings and the single list-based method, it is adding guidance that encourages users to grant access to just the specific apps (for System & App Protection Override) or folders (for Full Disk Access) their workflows require ([Apple](https://developer.apple.com/news/?id=oqng0zjk)). Users also get increased visibility into the wide range of data apps will receive access to or control over if full permissions are granted ([Apple](https://developer.apple.com/news/?id=oqng0zjk)). A transparency indicator will appear when an app is controlling another app using System & App Protection Override ([Apple](https://developer.apple.com/news/?id=oqng0zjk)).

For developers, Apple advised adjusting how they onboard users and making sure their apps can gracefully handle access to only a limited set of folders or apps ([Apple](https://developer.apple.com/news/?id=oqng0zjk)). Apps that use Full Disk Access for disk backup, or the new Accessibility settings to provide assistive technologies, can request entitlements to deliver the same experience for new installations that they offered before macOS 27.3 ([Apple](https://developer.apple.com/news/?id=oqng0zjk)). Apple stated that known apps are not currently affected and keep the same experience without an entitlement ([Apple](https://developer.apple.com/news/?id=oqng0zjk)).

TechCrunch reported that Apple said in October it would revise some security settings around Mac apps, after two incidents involving AI agents ([TechCrunch](https://techcrunch.com/2026/11/16/apple-reveals-new-mac-security-controls-as-ai-agents-raise-privacy-risks/)). In one, a journalist claimed that Meta's Muse app read their private messages without consent; in the other, a Wired report cited a flaw in ChatGPT's Mac app that could have allowed hackers to access sensitive data ([TechCrunch](https://techcrunch.com/2026/11/16/apple-reveals-new-mac-security-controls-as-ai-agents-raise-privacy-risks/)). The newsroom also reported that the changes do not appear to prevent Mac users from installing and running AI agents or other apps that ask for higher levels of access ([TechCrunch](https://techcrunch.com/2026/11/16/apple-reveals-new-mac-security-controls-as-ai-agents-raise-privacy-risks/)).

9to5Mac reported that Apple is rolling out the public beta ahead of next month's official release ([9to5Mac](https://9to5mac.com/2026/11/19/macos-27-3-public-beta-2-now-available-heres-everything-new/)). It described macOS 27.3 as shaping up to be the biggest update since the release of macOS 27 ([9to5Mac](https://9to5mac.com/2026/11/19/macos-27-3-public-beta-2-now-available-heres-everything-new/)).

{{< recommend >}}


## What Is Not Yet Confirmed

- Apple stated that additional entitlement details will be available soon ([Apple](https://developer.apple.com/news/?id=oqng0zjk)).
- Apple stated that known apps are not currently affected, with no further detail on which apps are covered ([Apple](https://developer.apple.com/news/?id=oqng0zjk)).

