---
name: outreach-deliverability
description: "Audits the sending setup before a campaign goes out: SPF, DKIM, DMARC and MX records read with dig, domain and tracking domain age, warmup state per mailbox, blacklist and health flags from Emelia, safe daily volume per mailbox and a week by week ramp plan, mailbox rotation, and the content patterns that push a cold email into spam. Returns one verdict, READY, READY WITH LIMITS or BLOCKED, with the exact list of things to fix, and writes outreach/deliverability.md. This skill is a gate: it is expected to say no. Triggers on: deliverability, spam, SPF, DKIM, DMARC, DNS, warmup, warm up, sender reputation, bounce, blacklist, inbox placement, landing in spam, daily limit, sending volume, ramp up, tracking domain, mailbox rotation, email health."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Deliverability audit and launch gate

## What this does

Checks whether the mailboxes and domains you are about to send from can carry the
campaign, and refuses the launch when they cannot. It reads the DNS records with
`dig`, the warmup and health of every mailbox from Emelia, and the volume you are
planning, then writes one verdict and a ramp plan to `outreach/deliverability.md`.

It is the step that saves the domain. A burnt domain is not repaired by better copy.

## When to use it

Run it before every launch. `outreach-campaign` reads its verdict and stops when the
verdict is BLOCKED, so run this first, not after. Run it again when opens collapse, when
replies stop, when a mailbox stops sending, when you add a mailbox or a domain, or before
raising the daily volume.

Use a different skill when the question is not infrastructure: `outreach-verify` checks
whether the addresses on your list exist, `outreach-write` checks the copy for spam
patterns and subject length, `outreach-audit` tells you whether a low reply rate is
deliverability or the offer.

## Inputs

- **The sending domains.** Take them from the mailboxes returned by Emelia. If Emelia
  is not connected, ask the user for the list of sending addresses and work from the
  part after the `@`.
- **`EMELIA_API_KEY`** in the environment, or the Emelia MCP server configured. Without
  either, do the DNS half and report the warmup half as `unknown`, never as OK.
- **`dig`**, part of `bind-utils` or `dnsutils`. If it is missing, use `nslookup -type=TXT`
  or `host -t TXT`. If none of them exist, ask the user to paste the records rather than
  guessing.
- **`outreach/campaign.json`** when it exists, for the planned contact count and the
  number of mailboxes. Without it, ask how many contacts and over how many days.
- **`whois`** for domain age. If it is missing, ask the user when the domain was
  registered. Do not skip the question: a domain under 30 days is the single most
  common reason a first campaign dies.

## How to do it

### 1. Inventory the mailboxes

MCP: `list_email_providers` with no argument, then again with `disconnectedOnly: true`.
REST has no documented equivalent, so without MCP ask the user to list the mailboxes
connected in the app.

Each provider carries `_id`, `senderEmail`, `senderName`, `emailType` (`GOOGLE`,
`OFFICE`, `SMTP`, `GOOGLEIMAP`), `disabled`, `disconnected`, `customDomain`, `warmup`
and `health`. Passwords come back masked as `********`, that is normal.

A provider with `disconnected: true` or `disabled: true` sends nothing. Reconnecting it
is the user's job in the app, not yours. Record it as a blocker.

Group the mailboxes by domain. Everything below is per domain for DNS, per mailbox for
warmup and volume.

### 2. Read the DNS records, with these exact commands

Run every check against the sending domain, and once more with `@8.8.8.8` when an
answer looks stale. A record you changed an hour ago may still be cached locally.

**SPF**

```bash
dig +short TXT example.com | grep -i "v=spf1"
```

- Exactly one record must start with `v=spf1`. Two SPF records is a PermError and both
  are ignored, so SPF fails entirely. This is a blocker, and it is common after adding
  a second sending tool.
- It must authorise the service that actually sends. Google Workspace:
  `include:_spf.google.com`. Microsoft 365: `include:spf.protection.outlook.com`. A
  custom SMTP relay: whatever that provider documents.
- It must end with `-all` (hard fail) or `~all` (soft fail). `?all` and `+all` authorise
  the world and are worth nothing.
- Count the DNS lookups: every `include`, `a`, `mx`, `ptr`, `exists` and `redirect`
  counts. More than 10 is a PermError. Expand nested includes to count them:
  `dig +short TXT _spf.google.com`.

**DKIM**

```bash
dig +short TXT google._domainkey.example.com
dig +short TXT selector1._domainkey.example.com
dig +short TXT selector2._domainkey.example.com
```

- `google` is the Google Workspace default selector. Microsoft 365 publishes
  `selector1` and `selector2` as CNAMEs, so follow them:
  `dig +short CNAME selector1._domainkey.example.com`.
- When the selector is unknown, do not guess more than three times. Ask the user to send
  one email from that mailbox to themselves, open the raw source, and read the
  `DKIM-Signature` header: the selector is the `s=` tag, the signing domain is `d=`.
  If there is no `DKIM-Signature` header at all, DKIM is not enabled. That is a blocker.
- A valid record contains `v=DKIM1` and a non empty `p=` public key. A record with an
  empty `p=` is a revoked key: treat it exactly like a missing record.
- Check that `d=` in the header matches the domain in the From address. A signature from
  a different domain does not align, and DMARC then relies on SPF alone.

**DMARC**

```bash
dig +short TXT _dmarc.example.com
```

- Must start with `v=DMARC1` and carry a `p=` policy: `none`, `quarantine` or `reject`.
- `p=none` is acceptable to start and is what most senders should launch with. Move to
  `quarantine` once the aggregate reports are clean, not before.
- `rua=mailto:...` is how you get those reports. Without it you are blind. Not a blocker,
  but say it.
- Google's sender requirements, in force since February 2024, ask every sender for SPF
  or DKIM, and ask senders above 5,000 messages a day to Gmail for SPF, DKIM, DMARC, a
  one click unsubscribe and a spam complaint rate kept under 0.3%. Microsoft applied
  comparable requirements to high volume senders in 2025. Cold outreach sits below those
  volumes, but the records are checked at any volume, so publish all three.

**MX**

```bash
dig +short MX example.com
```

A sending domain with no MX cannot receive replies, and receivers read that as a
throwaway domain. Blocker.

**Tracking domain**

```bash
dig +short CNAME track.example.com
```

Emelia rewrites tracked links and the unsubscribe link through a shared tracking server
unless the mailbox has a custom tracking domain whose status is OK, in which case links
become `https://<your-domain>/<token>`. A shared tracking domain means your links carry
the reputation of everyone else using it. Set one custom tracking domain per sending
domain in the app, and check here that it resolves.

### 3. Domain age

```bash
whois example.com | grep -iE "creation date|created|registered on"
```

Rule of thumb, not a measured threshold:

| Age of the domain | What it can carry |
|---|---|
| Under 30 days | Warmup only. No campaign. This is a blocker. |
| 30 to 90 days | Half volume, one mailbox, watch the bounce rate daily |
| Over 90 days with warmup running | Normal ramp |

Run the same check on the tracking domain. A brand new tracking domain in an email from
an old domain is a mismatch that filters notice.

### 4. Warmup, per mailbox

MCP: `get_warmup_status`. It returns 10 mailboxes per page, so loop `page: 1`, `page: 2`
until the list is empty. There is no documented REST equivalent, so without MCP read the
warmup screen in the app and record the numbers by hand.

Each entry carries `email`, `provider` (the mailbox id, which is what `set_warmup` wants),
`running`, `startDate`, `emailsSent`, `emailsReceived`, `spamCount`,
`conversationsCount`, `score`, `step`, `disabledReason`, and a `health` block with `spf`,
`dkim`, `dmarc`, `mx` (each `OK` or `MISSING`), `sendAbility` (`OK`, `NOT_RECEIVED` or
`SENDING_ERROR`), `blacklistCount` and `lastCheck`.

How to read it:

- `running: false` is a blocker. Turn it on with `set_warmup` and
  `{ providerId: "<the provider field of this entry, or the _id from
  list_email_providers>", enabled: true }`, then wait. Warmup that started today does not
  make a mailbox ready today.
- `disabledReason` tells you why it stopped. Read it out loud to the user rather than
  silently re-enabling.
- `spamCount` climbing is the real alarm, well before the score moves. Compare it to
  `emailsReceived`: warmup mail landing in spam means campaign mail is landing there too.
- Emelia does not publish a pass mark for `score`, so use it comparatively: rank your
  mailboxes by score and treat the outlier as suspect. Do not invent a threshold.
- `health` is a snapshot from the last diagnostic, and `lastCheck` tells you how old it
  is. When it disagrees with your `dig` output, trust `dig` and say the health block is
  stale.
- `blacklistCount` above zero means the sending IP or domain is listed somewhere. On
  Google and Microsoft mailboxes the IP is shared and you cannot fix it, so the answer is
  volume, not delisting.

### 5. Volume the mailboxes can carry, and the ramp

Rules of thumb from cold email practice, not measurements from your account:

- 30 to 50 cold emails per mailbox per day at cruising speed. Emelia lets a campaign go
  to 500 a day per mailbox, which is a product ceiling, not a safe number.
- Keep warmup running permanently, not only during the ramp. It is what keeps the
  positive engagement ratio up when the campaign adds cold, unanswered mail.
- New domain and new mailbox, week by week:

| Week | Campaign emails per mailbox per day |
|---|---|
| 1 and 2 | 0, warmup only |
| 3 | 10 |
| 4 | 20 |
| 5 | 30 |
| 6 and after | 40 to 50 |

Compute what the user actually needs: `mailboxes = ceil(contacts / (days x per mailbox
cap))`. If the answer is more mailboxes than they have, say so now. The fix is more
mailboxes or more days, never a higher cap.

Rotation: spread the campaign across every connected mailbox rather than draining one.
Mailboxes on the same domain share that domain's reputation, so one burnt mailbox drags
its siblings down. Two or three sending domains, three to five mailboxes each, is a
common shape. Never send cold campaigns from the company's primary domain: use a
separate lookalike domain so that a mistake costs you outbound, not your invoices.

### 6. What flips a message into spam

Check these against `outreach/sequence.md` and report each one that is present:

- **Attachments.** Never in a first touch. Send the link on a later step, once they replied.
- **Shortened links.** `bit.ly` and friends sit on blocklists because everyone abuses them.
  Use the full URL or your own tracking domain.
- **Images.** One at most, never an image only message. Mostly image with a short caption
  is the newsletter shape, and cold mail should not look like a newsletter.
- **Link count.** One call to action plus the unsubscribe link. Three or more links in a
  first cold email is a strong spam signal.
- **HTML weight.** Tables, buttons, background colors and web fonts read as marketing.
  Plain paragraphs with one link read like a person wrote them.
- **Link tracking.** `trackLinks` rewrites every URL through the tracking domain, adding a
  redirect that filters dislike. On a cold first touch, off is worth more than the clicks.
- **Open tracking.** `trackOpens` adds a pixel that Apple Mail Privacy Protection fires
  for a large share of recipients anyway, so it costs reputation and returns a bad number.
- **Shared tracking domain.** Covered above: fix it with a custom tracking domain.
- **Missing unsubscribe.** `{{unsubscribe_link}}` must be in the copy. It is a legal
  requirement in most markets and it feeds the `List-Unsubscribe` header, which is what
  stops an annoyed reader from pressing the spam button instead.
- **A From name that hides the sender**, a reply-to on a different domain, or a domain
  with no website. Each one is a reason to be filtered, and none of them is worth it.

### 7. The verdict

Write one of three words, and mean it.

**BLOCKED** when any of these is true. Do not soften it, do not offer to continue anyway:

- SPF missing, duplicated, or over the 10 lookup limit
- DKIM missing, or the key is revoked
- DMARC missing
- No MX on the sending domain
- The mailbox is `disconnected` or `disabled`
- Warmup `running: false`
- `health.sendAbility` is not `OK`
- The sending domain is under 30 days old
- The list has not been verified (`outreach-verify` has not run)
- The planned daily volume is above what the ramp allows for the age of the setup

**READY WITH LIMITS** when everything is present but the setup is young: warmup started
under 14 days ago, domain under 90 days, `blacklistCount` above zero, or a single mailbox
for the volume requested. State the reduced daily cap explicitly, in numbers.

**READY** otherwise.

## Output

`outreach/deliverability.md`. The `## Verdict` section is read by `outreach-campaign`, so
keep the single word on its own line.

```markdown
# Deliverability audit, 2026-03-12

## Verdict

READY WITH LIMITS

Send at most 20 emails per mailbox per day until 2026-03-26, then re-run this audit.
Two mailboxes, so 40 a day, so the 1,180 contact list takes 30 working days.

## Mailboxes

| Mailbox | Type | Warmup | Days warm | Spam | Health | Custom tracking |
|---|---|---|---|---|---|---|
| paul@get-acme.com | GOOGLE | running | 21 | 0 | OK | track.get-acme.com |
| lea@get-acme.com | GOOGLE | running | 9 | 2 | OK | track.get-acme.com |

lea@ has been warming for 9 days and has 2 warmup mails in spam. It carries half the
volume of paul@ until that count stops moving.

## DNS, get-acme.com

| Record | Value found | Verdict |
|---|---|---|
| SPF | `v=spf1 include:_spf.google.com ~all` | OK, 1 record, 4 lookups |
| DKIM | `google._domainkey`, `v=DKIM1; k=rsa; p=MIIBIjANBg...` | OK, 2048 bit |
| DMARC | `v=DMARC1; p=none; rua=mailto:dmarc@get-acme.com` | OK, reports on |
| MX | `1 aspmx.l.google.com.` | OK |
| Tracking | `track.get-acme.com` CNAME resolves | OK, not shared |

Domain created 2025-11-04, 128 days old. Tracking domain same age.

## Ramp plan

| Until | Per mailbox per day | Total per day |
|---|---|---|
| 2026-03-26 | 20 | 40 |
| 2026-04-09 | 30 | 60 |
| after | 40 | 80 |

## Fix before the next audit

1. Move DMARC to `p=quarantine` once two weeks of reports are clean.
2. Step 1 of the sequence carries a 210 KB image. Replace it with a line of text.
3. `trackLinks` is on. Turn it off for step 1.
```

## Checks before finishing

- Every connected mailbox has a row, including the disconnected ones.
- Every sending domain has four DNS answers recorded verbatim, not summarised as OK.
- Nothing is marked OK that you did not actually query. Unknown is a valid value and it
  is the honest one when Emelia is not connected.
- The verdict is one of the three words, on its own line, under `## Verdict`.
- The ramp plan has real dates and real numbers, not "increase gradually".
- If the verdict is BLOCKED, the fix list is ordered by what unblocks the launch first.

## Failure modes

- **`dig` prints nothing.** The record does not exist, or the domain is wrong. Confirm the
  domain with `dig +short A example.com` before concluding the record is missing.
- **The record you just added is not visible.** DNS caches. Re-query with `@8.8.8.8` and
  `@1.1.1.1`, and check the TTL of the old record before telling the user it failed.
- **DKIM selector not found.** Do not conclude DKIM is missing after three guesses. Get
  the `DKIM-Signature` header from a real message, as described above.
- **`get_warmup_status` returns an empty list.** No mailbox is connected to the account.
  That is a blocker, not an empty result to ignore.
- **`health` says SPF is OK and `dig` says it is missing.** `lastCheck` is old. Trust
  `dig`, report the disagreement.
- **`Invalid or disabled Emelia API key`.** The key was revoked or was never valid.
  Generate a new one in the app under Settings then API.
- **`Emelia API rate limit reached`.** 30 requests a minute without a subscription, 100 on
  Start, 300 on Grow, 1000 on Scale. Pause and resume; do not retry in a loop.
- **The user asks you to launch anyway.** Restate the specific blocker and what it costs,
  offer the reduced volume that would be safe, and leave the decision written down. Do
  not change the verdict to make it pass.

## Limits

This audit sees your side only. It cannot see how Google or Microsoft actually score your
domain, it cannot read Postmaster Tools or SNDS, and it does not run a seed test to
measure inbox placement. It reports `blacklistCount` from Emelia but does not query
blocklists directly, and it cannot delist a shared provider IP. It does not repair a
burnt domain: at that point the answer is a new domain and eight weeks of patience. And a
green verdict is not a promise of the inbox, only the absence of the known reasons to be
filtered.
