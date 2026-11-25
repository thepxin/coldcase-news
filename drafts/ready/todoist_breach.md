# Todoist confirms breach exposing data of approximately 6 per cent of its users
type: report
then: Todoist stated that it stopped using salted SHA1 password hashing over a decade ago, although some accounts whose passwords had not changed in over a decade still kept such hashes [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU).
now: Todoist confirmed that an attacker downloaded those hashes, along with email addresses and account creation dates, for approximately 6 per cent of its users, and that it has now retired support for the method [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU).
summary: Todoist confirmed that an attacker downloaded email addresses and older password hashes for approximately 6 per cent of its users.

Todoist confirmed on November 24, 2026, that an attacker had gained unauthorized access to its production systems on November 23, 2026, and downloaded customer records [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU). Approximately 6 per cent of its users had their email addresses, account creation dates and older salted SHA1 password hashes taken, while smaller groups lost tokens, mailbox content or text resembling credentials [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU).

According to the company, the intrusion began between November 22 and 23, when an attacker used a stolen credential associated with its version control system to modify automated workflows in three repositories [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU). The attacker obtained additional credentials and used one of them to take over an employee's work account and gain access to the company's cloud infrastructure [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU). It could also read source code, although the investigation found no changes to application code [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU).

The company reported that the affected accounts used an older password hashing method, salted SHA1, which it stopped using over a decade ago [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU). It has now retired support for that method and found no indication that the attacker signed in to those accounts [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU).

The notice stated that, for approximately 0.003 per cent of users, the attacker retrieved Todoist application programming interface tokens and Slack integration tokens [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU). For approximately 0.001 per cent of users, the attacker searched tasks, comments and attachment names for content resembling credentials, and some matching text was returned [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU).

A separate group of approximately 0.001 per cent of users had connected Outlook mailboxes accessed, according to the company, including email subjects, sender information and the beginning of messages, up to 255 characters [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU). The attacker searched those mailboxes for terms associated with developer tools, credentials, cryptocurrency and file sharing [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU).

The company stated that it had blocked the access paths used in the attack, protected affected accounts and notified affected users [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU). Affected passwords were disabled, and those users were asked to reset them [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU).

## Key Facts

| Item | Detail | Source |
| --- | --- | --- |
| Point of entry | A stolen version control credential, used to modify workflows in three repositories | [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU) |
| Wider access | An employee's work account and the company's cloud infrastructure | [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU) |
| Password data taken | Approximately 6 per cent of users, with email addresses, creation dates and salted SHA1 hashes | [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU) |
| Tokens taken | Approximately 0.003 per cent of users | [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU) |
| Stored content returned | Approximately 0.001 per cent of users, with text resembling credentials | [TechCrunch](https://techcrunch.com/2026/11/25/todoist-confirms-6-of-customers-details-were-stolen-in-data-breach/) |
| Outlook mailboxes | Approximately 0.001 per cent of users, with subjects, senders and up to 255 characters of each message | [Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU) |

## Timeline

- **2026-11-23**: An attacker gained unauthorized access to Todoist's production systems and downloaded account records ([Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU)).
- **2026-11-24**: Todoist disabled the affected Todoist for Outlook email add-in, began notifying affected users and published its security incident notice ([Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU)).
- **2026-11-25**: TechCrunch reported that around 6 per cent of the company's customers were affected ([TechCrunch](https://techcrunch.com/2026/11/25/todoist-confirms-6-of-customers-details-were-stolen-in-data-breach/)).

## Details (as Reported)

- Todoist stated that older password hashes can be vulnerable to password guessing ([Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU)).
- Todoist stated that the user figures are approximate, with a minimal overlap between groups ([Todoist](https://www.todoist.com/help/todoist/get-started/security-incident-in-november-2026-cG0EIACNU)).
- TechCrunch reported that the company blamed stolen credentials and named Uber and Klue among other companies hit by such attacks this year ([TechCrunch](https://techcrunch.com/2026/11/25/todoist-confirms-6-of-customers-details-were-stolen-in-data-breach/)).

## What Is Not Yet Confirmed

The sources do not list open questions.
