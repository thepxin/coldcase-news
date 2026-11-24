---
title: "PHP phpAfterShell flaw rated 9.2 critical, fixed the day it was disclosed"
date: "2026-11-24T08:55:17Z"
description: "PHP fixed the phpAfterShell flaw, rated 9.2 under CVSS 4.0, on November 19, 2026, and Cloudflare said its WAF blocks known attack patterns."
tags: ["Tech", "Software"]
desk: "tech"
verdict: ""
status: "report"
then: "On November 19, 2026, security firm depthfirst disclosed phpAfterShell (CVE-2026-126714), a PHP session handler flaw that can lead to remote code execution, and the PHP project fixed it the same day, according to Cloudflare."
now: "Cloudflare said its WAF blocks known phpAfterShell attack patterns on every plan, and that no source it reviewed reports exploitation in the wild."
verified: "2026-11-24"
toolkit: "general"
checked: "2026-11-24"
sourcing: "approved"
models: ["claude-haiku-5-5", "claude-sonnet-5-5"]

sources:
  - outlet: "Cloudflare"
    tier: "A"
    kind: "official"
    date: "2026-11-20"
    title: "How Cloudflare WAF helps protect against phpAfterShell and other critical PHP flaws"
    url: "https://blog.cloudflare.com/phpaftershell-waf-protection/"
social:
  hook: "The PHP fix for phpAfterShell arrived the day it was disclosed. So did 16 other security fixes."
  x: "The PHP fix for phpAfterShell arrived the day it was disclosed. So did 16 other security fixes.\n\nEvery line sourced: https://coldcasetech.com/posts/2026-11-24-php-aftershell-critical-flaw-fixed-same-day/\n\n#PHP #phpAfterShell"
  instagram: "The PHP fix for phpAfterShell arrived the day it was disclosed. So did 16 other security fixes.\n\nPHP fixed the phpAfterShell flaw, rated 9.2 under CVSS 4.0, on November 19, 2026, and Cloudflare said its WAF blocks known attack patterns.\n\nFull story and every source: link in bio.\n\nColdCaseTech · An independent record of technology's promises\n\n#coldcasetech #php #phpaftershell #software #technews #tech"
  tags: ["PHP", "phpAfterShell"]
  replies: ["The same PHP releases fixed 16 other security flaws on November 19. Six of them are also rated critical, according to Cloudflare.", "phpAfterShell is rated 9.2 out of 10 under CVSS 4.0. PHP fixed it in 8.2.36, 8.3.37, 8.4.28, 8.5.13 and 8.6.0. Cloudflare says only a PHP upgrade and worker restart fully fixes it.", "Cloudflare says none of the 17 PHP flaws was in CISA's exploited catalog as of November 19. Has your team already moved to a fixed PHP release?"]
  reel: ["PHP fixed a 9.2-rated flaw on Nov. 19, the day depthfirst disclosed it.", "Cloudflare said its firewall blocks known attack patterns, even on the Free plan.", "The same PHP releases fix 16 other flaws. Six are also rated critical."]
cover:
  image: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80"
  alt: "PHP phpAfterShell flaw rated 9.2 critical, fixed the day it was disclosed"
  relative: false
draft: false
---

On November 19, 2026, the security research company depthfirst disclosed phpAfterShell (CVE-2026-126714), a vulnerability in PHP's default file-based session handler that can lead to remote code execution ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)). The flaw scores 9.2 out of 10 (Critical) under CVSS 4.0 ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)). PHP fixed it the same day in versions 8.2.36, 8.3.37, 8.4.28, 8.5.13 and 8.6.0 ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)).

The company confirmed that its WAF blocks known phpAfterShell attack patterns, including for customers on the Free plan ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)).

## Key Facts

| Item | Detail | Source |
|---|---|---|
| Flaw | phpAfterShell, CVE-2026-126714, in PHP's file-based session handler | [Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/) |
| Severity | 9.2 out of 10 (Critical) under CVSS 4.0 | [Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/) |
| Fixed in | PHP 8.2.36, 8.3.37, 8.4.28, 8.5.13 and 8.6.0 | [Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/) |
| Other fixes | 16 other security vulnerabilities, six of them also rated critical | [Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/) |
| Exploitation | None of the 17 listed in CISA's Known Exploited Vulnerabilities catalog as of November 19, 2026 | [Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/) |

## Timeline

- **2026-10-21**: Cloudflare released its original PHP remote code execution rules in an emergency release ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)).
- **2026-11-19**: depthfirst disclosed phpAfterShell, PHP issued the fixes, and Cloudflare updated its rule's detection logic to cover the flaw ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)).
- **2026-11-20**: Cloudflare published its blog post on WAF protection against phpAfterShell and the other critical PHP flaws ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)).

## Details (as Reported)

PHP stores session data in files by default, and session_start() deserializes the file's content into the $_SESSION array ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)). The flaw is triggered when the write at the end of a request is interrupted, leaving the beginning of the new session data followed by the end of the old one ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)). PHP's advisory names two ways to place controlled data in the session: session upload progress, and applications that store large user-controlled strings in the session ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)). Code execution also depends on an interruption at a useful point in the write and a suitable deserialization gadget chain in the application, according to PHP ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)).

The WAF protection comes from a PHP remote code execution rule first deployed in October 2026 for the php2shell vulnerabilities ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)). The rule is part of both the Cloudflare Free Managed Ruleset and the Cloudflare Managed Ruleset, is enabled by default, and its default action is Block ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)). The company also added three rules to the Cloudflare Managed Ruleset for paid plans, covering CVE-2026-129289 in PHP-FPM and CVE-2026-15353 and CVE-2026-129506 in PHP's SOAP extension ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)). They default to the Log action because the request patterns can also appear in legitimate traffic ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)).

Cloudflare described the WAF as an additional layer of defense rather than a replacement for the patch, and noted that the only complete fix is to upgrade PHP and restart every worker ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)). The vulnerable versions are PHP 8.2 before 8.2.36, 8.3 before 8.3.37, 8.4 before 8.4.28, 8.5 before 8.5.13, and the 8.6.0 release candidates ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)). Linux distributions often backport fixes without changing the PHP version number, so the full package version should be checked against the distribution's advisory ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)).

Each of the other six critical flaws needs a specific configuration to be exploitable ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)). Leo Lin and Asahi are credited as reporters in the CVE record ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)).

{{< recommend >}}


## What Is Not Yet Confirmed

- depthfirst reports it reached code execution without an application gadget by chaining a second, undisclosed memory-corruption bug in a PHP-native class, but the sources Cloudflare reviewed do not establish whether that bug is fixed in the November 19 releases ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)).
- PHP 8.1 and earlier have reached end-of-life, and PHP says CVE-2026-129289 was introduced in PHP 5.6.0, while releases older than 8.2 may also be affected by CVE-2026-115560 ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)).
- So far, there appears to be no indication that the vulnerabilities have been exploited, and its analysts will update the rules as new techniques and variations appear, Cloudflare notes ([Cloudflare](https://blog.cloudflare.com/phpaftershell-waf-protection/)).

