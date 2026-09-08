---
name: outreach-analyze
description: "Read the results of a campaign and say what to change. Pulls campaign statistics and the activity feed from Emelia, recomputes the rates with the right denominators, separates the numbers that mean something from the ones broken by open tracking, breaks results down per step and per A/B version, reads the replies, and diagnoses whether the problem is deliverability, targeting, the offer or the message. Writes outreach/report.md ending with one recommendation. Triggers on: analyze, analytics, results, stats, statistics, report, campaign performance, reply rate, open rate, bounce rate, unsubscribe rate, benchmark, A/B results, why no replies, why so many bounces, what should I change."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Analyze a campaign

## What this does

Pulls what a campaign actually did, recomputes the rates that Emelia precomputes with
denominators that are not always the ones you want, reads the replies, and turns all of
it into a diagnosis: deliverability, targeting, offer, or message. Writes
`outreach/report.md` and ends with a single recommendation.

## When to use it

Use it at the read points of a running campaign (day 3, day 7, day 14 of a pilot),
after a campaign finishes, when someone asks "why is nobody replying", or when you
have two variants and want to know if either is winning.

Do not use it to triage and answer individual replies: that is
[`outreach-inbox`](../outreach-inbox/SKILL.md). Do not
use it to debug SPF, DKIM, DMARC or warmup: this skill tells you delivery is the
problem, [`outreach-deliverability`](../outreach-deliverability/SKILL.md) fixes it.

## Inputs

| Input | Required | If missing |
|---|---|---|
| A campaign name or id | yes | list the campaigns and ask which one |
| `EMELIA_API_KEY` in the environment | yes | there is no offline mode here, say so and stop |
| The Emelia MCP server | no, but it changes the method | without it, `get_campaign_stats` is unavailable and you rebuild the numbers from the activity feed (see below), and you say in the report that you did |
| `outreach/campaign.json` from the launch | no | it saves you the id lookup and carries the sequence intent |
| A date range | no | analyze the whole campaign |
| How many meetings were booked | no | ask, it is not in the API and it is the only number the user really cares about |

## How to do it

### 1. Resolve the campaign

MCP: `list_campaigns`, match on name, take `_id`.
REST: `GET https://api.emelia.io/advanced/campaigns` with header `Authorization: <key>`.

Then `get_campaign` (MCP) or read `outreach/campaign.json` for the shape you need:
`status`, `steps`, `schedule.trackOpens`, `schedule.trackLinks`, and
`recipients.lists`.

Two things to establish before any number means anything:

- **Status.** `DRAFT` means it never started and every count is zero, so stop and say
  that. `PAUSED` means the clock stopped, so "day 14" is not day 14 of sending.
  `RUNNING` means late steps have not fired yet. `FINISHED` and `ARCHIVED` are the only
  states where the numbers are final.
- **`schedule.trackOpens`.** If it is off there is no open data at all, and a 0% open
  rate is a configuration fact, not a deliverability finding. Check this before you
  diagnose anything from opens.

### 2. Pull the numbers

**With MCP**, `get_campaign_stats` with `campaignId` and `detailed: true` (optional
`start` and `end` as ISO dates). It returns `{ global, steps }`.

**Without MCP**, there is no statistics endpoint on the REST API. Rebuild the counts
from the activity feed instead:

```
GET /advanced/campaigns/{campaignId}/activities?type=SENT&page=0
GET /advanced/campaigns/{campaignId}/activities?type=BOUNCED&page=0
GET /advanced/campaigns/{campaignId}/activities?type=MAIL_REPLIED&page=0
GET /advanced/campaigns/{campaignId}/activities?type=UNSUBSCRIBED&page=0
```

`page` starts at 0 and the feed returns about 30 activities per page, newest first, so
page until a page comes back short. Count unique contacts by `contact._id` for replies,
raw events for the rest. Tell the user how many pages you are about to pull before you
pull hundreds, and say in the report that the numbers were rebuilt from the feed. One
thing this path cannot give you is a unique open count, so do not substitute the raw
`OPENED` count for it: say unique opens are unavailable.

### 3. The field map, and the denominators to distrust

`global` carries counts, not rates, except for the `_percent` fields:

| Field | Counts |
|---|---|
| `contacts` | contacts attached to the campaign |
| `contacted` | unique contacts reached on any channel |
| `sent` | email send events |
| `opened` | open events, every open, not unique |
| `clicked` | click events |
| `mail_replied`, `linkedin_replied` | reply events per channel |
| `replied` | **unique contacts** who replied on any channel |
| `bounced`, `unsubscribed` | events |
| `visited`, `invited`, `accepted`, `message_sent`, `inmail_sent`, `liked` | LinkedIn steps |
| `progress_percent` | how far through the flow the campaign is |

There is no `delivered` field. Delivered is `sent - bounced`.

The `_percent` fields are computed for you, and three of them use a denominator you
probably did not expect:

| Precomputed field | Divided by | What to use instead |
|---|---|---|
| `bounced_percent` | `contacts` (the whole attached list) | `bounced / sent` |
| `unsubscribed_percent` | `contacts` | `unsubscribed / (sent - bounced)` |
| `clicked_percent` | opens when open tracking is on | `clicked / (sent - bounced)` |
| `opened_percent` | `sent`, on raw opens | step level `first_open`, see below |
| `mail_replied_percent` | `sent`, on reply events | `replied / contacted` |
| `linkedin_replied_percent` | `message_sent + inmail_sent` | usable as is |
| `accepted_percent` | `invited` | usable as is |

`bounced_percent` is the dangerous one. On a campaign still sending, `contacts` is much
larger than `sent`, so the bounce rate reads low and calm while the real rate on what
has actually gone out is several times higher. Recompute it every single time.

All `_percent` values are capped at 100 before you receive them, so a field sitting at
exactly 100 may be a clipped number rather than a real one.

`steps` is an **array of arrays**: one entry per action step, in flow order, and inside
each entry one row per A/B version for email steps (a single row for everything else).

Email version rows carry `_id` (the version id), `stepId`, `stepType: "EMAIL"`,
`disabled`, then `sent`, `first_open`, `opened`, `clicked`, `replied`, `bounced`,
`unsubscribed`, and the matching `_percent` fields, all divided by that version's own
`sent`. Non-email rows carry `stepType` plus `visited`, `invited`, `accepted`,
`message_sent`, `inmail_sent`, `replied`, `liked`, `followed`, `task_completed`.

**`first_open` is the honest open number** (unique first opens) and it exists only on
the step rows, never in `global`. That alone is a reason to work from `steps`.

### 4. The rates that count

Compute these yourself and put them in the report with their denominators named:

1. **Bounce rate** = `bounced / sent`. Under 1% healthy, 1 to 3% watch, over 3% pause
   the campaign, over 5% stop everything and fix the list.
2. **Reply rate** = `replied / contacted`, unique people over unique people. This is
   the metric.
3. **Positive reply share** = positive replies / all replies, which requires reading
   them (step 6). This measures the offer.
4. **Unsubscribe rate** = `unsubscribed / (sent - bounced)`.
5. **Reply rate per step and per version** = `replied / sent` on each step row.
6. **Meetings booked**, which no API knows. Ask the user and write down the answer.

Below roughly 100 sends, report raw counts and not percentages. "3 replies out of 74"
is honest. "4.1%" pretends to a precision that a single event would move by more than a
point.

### 5. The rates that lie

**The open rate is not a measurement of human attention.** Apple Mail Privacy
Protection, which shipped with iOS 15 in September 2021 and with macOS Monterey shortly
after, preloads remote images through Apple's proxy for every user who turned it on, so
the tracking pixel fires whether or not anyone read the message. Gmail has served
images through its own proxy since 2013. Corporate security gateways fetch every image
and follow every link before delivering. What an "open" proves is that a machine or a
person fetched an image.

What to do about it:

- Never run an A/B test on opens, and never promote a variant because it opened better.
- Never report an open rate without saying it is inflated.
- Use `first_open` from the step rows, not `opened` from `global`, and treat even that
  as an upper bound.
- A **low** open rate is still informative. Under about 20% usually means delivery, not
  disinterest, because the machines alone normally push it higher than that.
- Check the timing. Pull `OPENED` activities and compare their `date` against the
  matching `SENT`. Opens arriving within seconds, in a burst, across many contacts, are
  scanners. If most of your opens look like that, you have no open data.
- Clicks are less polluted but not clean: scanners click too. With open tracking on, a
  click that arrives with no matching open, or one second after the send, is a machine.
  And many good cold emails carry no
  link at all because links cost deliverability, so a 0% click rate can mean nothing
  went wrong.

### 6. Read the replies

MCP: `get_campaign_activities` with `campaignId` and `type: "MAIL_REPLIED"` (then
`"LINKEDIN_REPLIED"`). Note this tool exposes `type`, `contactId` and `versionId` but
**not** `page`, so it gives you the first page only. Past 30 replies, use REST:

```
GET /advanced/campaigns/{campaignId}/activities?type=MAIL_REPLIED&page=0
```

Each activity carries `_id`, `contact`, `event`, `date`, `customData`, `step` (its
position in the flow, counting from 0 at the first action step), `version` (the index
of the A/B version, `-1` when the step has only one) and `sender` (the mailbox that
sent it). Reply activities also carry `reply` with `text`, `content`, `subject` and
`senderName`. The published schema lists `stepId` and `versionId`; what the feed
actually returns is `step` and `version`, so read the keys that are present rather than
the keys you expected.

Classify every reply, by hand, into: interested, meeting requested, not now, wrong
person, not interested, unsubscribe request, out of office, auto-reply. Out of office
and auto-replies are not replies: exclude them from the reply rate and say how many you
excluded. The split between "wrong person" and "not interested" is the single most
diagnostic thing in the whole report, because one is a targeting failure and the other
is an offer failure.

### 7. Per step and per version

For each step row: `sent`, `replied`, `unsubscribed`, and `replied / sent`.

- The step that carries the campaign is usually not step 1. Say which one it is.
- A step whose unsubscribes exceed its replies is costing more than it returns. Name it
  and recommend cutting it.
- For A/B versions, compare `replied / sent`, never opens. And check the sample: at 100
  sends per version, a gap under roughly a factor of two is noise. Detecting a 3%
  against 6% difference with normal confidence needs around 750 contacts per version
  (standard two proportion sample size, a rule of thumb). Below that, say "no
  conclusion yet" instead of picking a winner.
- If one version has `disabled: true`, it stopped receiving traffic partway through, so
  its rate is not comparable to the other one.

### 8. Benchmarks, honestly

These are rules of thumb from common cold B2B email practice, not measurements from
your account or from Emelia's. Your own previous campaign is a better benchmark than
any of them, so use it when you have it and say which one you used.

| Metric | Weak | Usual | Strong |
|---|---|---|---|
| Bounce, `bounced / sent` | over 5% | 1 to 3% | under 1% |
| Reply rate, unique repliers / contacted | under 1% | 2 to 5% | over 8% |
| Positive share of replies | under 10% | 20 to 40% | over 50% |
| Unsubscribe / delivered | over 2% | under 1% | under 0.3% |
| Reported open rate | under 20% (suspect delivery) | 30 to 60% | not a target, do not optimize it |
| Click rate when there is a link | under 0.5% | 1 to 3% | over 5% |

A reply rate above 10% almost always means a small, tightly targeted list or a warm
audience. On a broad list it means someone is counting auto-replies.

### 9. Differential diagnosis

Match the shape of the numbers, not one number at a time:

| What you see | Most likely cause | Check first | Do |
|---|---|---|---|
| Bounce over 5%, few opens | list never verified, or stale source | what share of the list verified `valid` | pause, verify the remainder, drop the rest, expect to re-warm |
| Almost no opens, bounce under 2%, no replies | spam foldering, or open tracking is simply off | `schedule.trackOpens` **before anything else** | if tracking is off you have no open data, judge on replies. If it is on, run the deliverability skill |
| Opens above 50%, zero replies over 100+ sends | message or offer, not delivery | what the first email actually asks for | rewrite the ask, not the subject, the subject already worked |
| Replies present, mostly "wrong person", "not my department" | targeting | the job titles present in the list, not the ones in the ICP | back to the ICP, tighten titles and headcount |
| Replies present, mostly "not now", "we already use X" | timing or competition, targeting is fine | which competitor comes up and how often | keep the list, change the trigger and the angle |
| Step 1 fine, later steps near zero, unsubscribes rising | sequence too long | unsubscribes per step on the step rows | cut the last step |
| Unsubscribes above 2% of delivered | wrong list or wrong tone | which step they come from | step 1: the list. Later steps: the follow ups are pushy |
| Everything fine except one mailbox | that mailbox is burned | group `SENT` and `BOUNCED` activities by `sender` | remove it from the campaign, check its warmup score, re-warm it |
| Numbers identical to the last read | campaign stopped, or you are reading cache | `status`, then the date of the newest activity | statistics are cached server side and lag an active campaign by minutes, longer on a finished one. Wait rather than re-polling |
| `opened` much larger than `sent` | repeat opens and machine fetches | `first_open` against `opened` on the step rows | report `first_open` and stop quoting the global open number |

### 10. Write the report

One file, `outreach/report.md`. Numbers with their denominators, the diagnosis, then
**one** recommendation. Not three options: the one you would do.

## Output

`outreach/report.md`. Real example:

```markdown
# Q4 SaaS founders, day 14

Campaign `66f1c0a2e4b0a1d3f9c2ab77`, status FINISHED, email only, 3 steps.
Source: get_campaign_stats (MCP), detailed, pulled 2026-09-08 10:12.

## What happened

| Metric | Count | Rate | Denominator |
|---|---|---|---|
| Contacts attached | 104 | | |
| Contacted (unique) | 98 | 94.2% | of attached |
| Sent (events) | 241 | | 3 steps |
| Bounced | 4 | 1.7% | of sent |
| Delivered | 237 | | sent minus bounced |
| Unique first opens (steps) | 61 | 25.7% | of delivered, inflated, see below |
| Clicked | 3 | 1.3% | of delivered |
| Replied (unique people) | 7 | 7.1% | of contacted |
| Unsubscribed | 1 | 0.4% | of delivered |
| Meetings booked | 2 | | reported by you |

Emelia reports `bounced_percent` at 3.8% because it divides by the attached list.
On what actually went out the bounce rate is 1.7%, which is healthy.

## Replies, read one by one

7 replies, plus 3 out of office that are excluded from the rate above.
- Interested / wants a call: 2
- Not now, ask again in Q1: 3
- Wrong person, forwarded internally: 1
- Not interested: 1
Positive share: 2 of 7, 29%, inside the usual band.

## Per step

| Step | Sent | First opens | Replies | Unsub | Reply / sent |
|---|---|---|---|---|---|
| 1 | 98 | 34 | 2 | 0 | 2.0% |
| 2 | 91 | 19 | 4 | 0 | 4.4% |
| 3 | 52 | 8 | 1 | 1 | 1.9% |

Step 2 carries the campaign: 4 of the 7 replies. Step 3 returned one reply and one
unsubscribe on 52 sends, so it roughly breaks even and is not worth its risk.

Single version per step, so there is no A/B result to report.

## Diagnosis

Deliverability is fine (bounce 1.7%, no provider anomaly, all 4 bounces on the same
two dead domains). Targeting is fine: only one "wrong person" out of 7. The offer
lands: 2 of 7 asked for a call on a 98 person list.

The 25.7% open figure is below the reply rate it should support, which here means the
opens are undercounting (plain text emails, images blocked) rather than that people
did not read. Another reason not to steer on this number.

## Recommendation

Scale this sequence to 500 contacts on the same ICP, cutting step 3. Ramp from 20 to
50 emails a day over two weeks and keep verifying every address before it enters the
list.
```

## Checks before finishing

- Every rate in the report names its denominator, and none of them is a raw
  `_percent` field copied over without checking what it divides by.
- Bounce rate was recomputed as `bounced / sent`.
- Auto-replies and out of office were excluded from the reply count, and the number
  excluded is stated.
- Open figures are labelled as inflated wherever they appear.
- If the sample is under about 100 sends, counts are reported instead of percentages.
- The campaign `status` and the pull time are in the report, so the reader knows how
  final the numbers are.
- The report says whether the numbers came from `get_campaign_stats` or were rebuilt
  from the activity feed.
- The report ends with exactly one recommendation.

## Failure modes

**A 401 with "Campaign not found".** That status code is misleading: it means the
campaign id does not belong to this API key, not that the key is bad. Re-list the
campaigns and check the id.

**Everything reads zero.** Look at `status` first. A campaign in `DRAFT` was created
but never started in the app, and no amount of analysis will find numbers that do not
exist.

**The numbers did not move since your last read.** Statistics are cached server side,
for minutes on an active campaign and longer on a paused or finished one. Re-polling
every minute changes nothing. Compare the newest activity `date` instead.

**An open rate near zero, or above 90%.** Near zero: check `schedule.trackOpens`
before writing a word about deliverability, half of these are tracking turned off.
Above 90%: machines. Compare `first_open` with `opened`, look at the delay between
`SENT` and `OPENED`, and report the campaign as having no usable open data.

**Only 30 activities came back.** The MCP activities tool does not expose pagination.
Switch to REST with `page`, starting at 0.

**Two variants, 60 sends each, one has twice the replies.** That is four replies
against two. Say there is no conclusion. Promoting a variant on that evidence is how
teams talk themselves into a worse email.

## Limits

This skill reads what Emelia recorded. It cannot tell you whether a message went to
spam (no inbox placement data), cannot attribute revenue, cannot see replies that
landed in a mailbox Emelia does not watch, and cannot measure opens that Apple, Gmail
or a security gateway faked for you. It does not rewrite the copy, fix authentication
records, or change the list: it tells you which of those to go and do.
