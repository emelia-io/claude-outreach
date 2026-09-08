---
name: outreach-verify
description: "Verify the deliverability of every email address on a list before you send to it, with Emelia's verifier, one at a time or in bulk. Sorts each address into send, drop or hold, detects catch-all domains with a control test, keeps the projected bounce rate under the threshold that protects sender reputation, and writes the verdicts into outreach/leads.csv and outreach/enrichment.json. Triggers on: verify email, email verification, email verifier, check emails, validate emails, bounce rate, hard bounce, catch-all, clean my list, list hygiene, deliverability check, is this email valid."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Verify before you send

## What this does

Checks each address on a list against Emelia's verifier and turns the answer into a
decision: send it, drop it, or hold it for a small separate batch. It measures the
bounce rate you are about to inflict on your sending domain and stops you when that
number is too high. A bounce costs a fraction of a credit to avoid and weeks of
sender reputation to survive.

## When to use it

Always, on any list, before any campaign. Specifically:

- After `outreach-find-email`, on anything the finder marked `risky` and on anything
  built from an address pattern.
- On any list you did not build yourself: a purchase, an old CRM export, a conference
  file, a scrape.
- On any list older than 60 to 90 days. People change jobs, and a verification is a
  photograph, not a guarantee.
- Before restarting a campaign that was paused for more than a month.

Skip it only on addresses that replied to you recently, or that someone on your team
confirmed by hand this week.

Use a different skill when you have no addresses at all (`outreach-find-email`), or
when you want the whole waterfall under one budget (`outreach-enrich`).

## Inputs

| Field | Required | Notes |
|-------|----------|-------|
| `email` | yes | One address per call. Trim it. Lowercase the domain. |

Files: `outreach/leads.csv` in, `outreach/leads.csv` and
`outreach/enrichment.json` out.

Access: `EMELIA_API_KEY` exported in the shell. The REST API is the documented path
and this skill assumes it. If the Emelia MCP server is also configured, its
`verify_email` tool wraps the same two calls and polls for you. With neither, run in
dry run: report how many addresses would be checked and what it would cost, and
refuse to declare the list safe to send.

Before you start, clean the obvious without spending a credit:

- Rows with no `@`, a double `@`, spaces, or a domain with no dot: drop, no
  verification needed.
- Duplicate addresses: keep one, or pay twice for the same answer.
- Role mailboxes (`contact@`, `info@`, `sales@`, `support@`, `no-reply@`): flag them.
  They usually verify as valid and still ruin a campaign, because nobody answers a
  shared inbox and complaints are higher. Ask before paying to verify them.
- Free consumer domains in a B2B campaign (gmail.com, orange.fr): keep them if the
  ICP includes sole traders, drop them otherwise. Decide before verifying.

## How to do it

### 1. Count, quote, wait for a yes

At the time of writing, Emelia bills the verifier **0.25 credit per address checked**,
so 1 credit covers 4 addresses. Unlike the finders, this is charged whatever the
answer: a verification that comes back invalid costs the same as one that comes back
valid. That is the whole reason you clean the list before you verify it, not after.
Confirm the current rate on your plan page before a large run.

Print this and stop:

```
Verification on outreach/leads.csv

  Rows with an address        341
  Malformed, dropped free       7
  Duplicates, dropped free     12
  Role mailboxes               19   keep them? they verify valid and rarely reply
  To verify                   303

  Cost: 0.25 credit per address, charged whatever the answer.
  Total 75.75 credits. Your balance: 1,009 credits.

Run it? (yes / no / verify without the role mailboxes)
```

### 2. One verification

Two REST calls: create the job, then poll it.

```bash
curl -s -X POST https://api.emelia.io/tools/verify/email \
  -H "Authorization: $EMELIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"marie@emelia.io"}'
# {"success":true,"jobId":"66f0e7..."}

curl -s https://api.emelia.io/tools/verify/email/66f0e7... \
  -H "Authorization: $EMELIA_API_KEY"
# {"success":true,"data":{"email":"marie@emelia.io","qualification":"valid",
#   "status":"done","date":"..."}}
```

Poll every 2 to 3 seconds. A verification is usually quick, but the job can end in
`status: "error"` after about a minute if the mail server never answers. Treat that
as `unknown`, not as valid.

If the MCP server is configured, one call does both:

```
verify_email
  email: "marie@emelia.io"
```

Same field in, same `data` object out.

### 3. The four categories, and what you do with each

Emelia returns one field, `qualification`. The documented values are `valid` and
`invalid`. The finder can also hand you `risky`. Everything else you need comes from
combining that field with the domain level test in step 4. These are the four
buckets you actually act on:

| Bucket | How you get it | What it means | What you do |
|--------|----------------|---------------|-------------|
| **Valid** | `qualification: "valid"` on a domain that is not catch-all | The mailbox exists and accepts mail | **Send.** This is your sending list. |
| **Invalid** | `qualification: "invalid"` | The mailbox does not exist or the domain does not accept mail | **Drop.** Never send. Never "try it anyway to see". This is exactly what a hard bounce is. |
| **Catch-all or risky** | `qualification: "valid"` on a domain that answers yes to everything, or `qualification: "risky"` from the finder | Unproven. It may be a real mailbox, it may be a black hole that accepts then bounces later | **Hold.** Send in a separate small batch, described below. |
| **Unknown** | `status: "error"`, a timeout, or a server that refused to answer | No verdict | Retry once, at least an hour later. Still nothing: treat it as catch-all, or drop it if you are being careful. |

Two rules that are not negotiable. Invalid never gets sent: not on the first step,
not on a follow-up, not "because it is a big account". And a bucket is a decision,
not a label to admire: every row leaves this skill with a `send_decision` of `send`,
`hold` or `drop`.

### 4. The catch-all problem, honestly

A catch-all domain accepts mail for every address that exists under it, real or not.
`marie@acme.com`, `zzz@acme.com` and `nobody@acme.com` all get the same yes. No
verifier on earth can prove a specific mailbox exists behind a catch-all, because the
mail server refuses to tell anyone. Any tool that claims otherwise is guessing.

Emelia's API does not hand you a separate catch-all label, so detect it yourself, per
domain, at a cost of one extra verification:

1. Group your addresses by domain. Do the test once per domain, not once per row.
2. Build a control address that cannot exist: a random string of 12 characters plus
   the domain, for example `qv7hd2lk9wpz@acme.com`.
3. Verify the control address (0.25 credit).
4. If the control comes back `valid`, the domain is catch-all. Mark every address on
   that domain `catch_all`, whatever their own verification said.
5. If the control comes back `invalid`, the domain answers honestly, so a `valid` on
   that domain means the mailbox really exists.

Only test domains where you have at least one address you intend to send to. On 300
addresses over 180 domains this adds about 45 credits, which is cheap for knowing
which half of your "valid" rows are real.

**What to do with catch-all rows.** They are not worthless, they are unproven:

- Put them in their own batch, sent after the proven list, never mixed into it.
- Cap the batch at roughly 10% of your daily volume for that mailbox.
- Watch the bounce rate on that batch specifically. Under 3%, keep going. Above,
  stop and drop the rest of the catch-all rows.
- Never use catch-all rows to warm up a new domain, and never send them from a
  mailbox you cannot afford to lose.

### 5. The threshold that decides whether you send at all

Compute the projected hard bounce rate before the campaign starts:

```
projected bounce rate = (invalid + unknown) / (rows you are about to send to)
```

Rules of thumb, widely used across senders rather than an Emelia measurement:

| Projected bounce rate | Verdict |
|-----------------------|---------|
| under 2% | Healthy. Go. |
| 2 to 3% | Marginal. Send only the proven valid rows and drop the rest. |
| over 3% | Stop. Do not send this list. Fix it. |
| over 5% | The list is not a list, it is a liability. Rebuild it. |

Why it matters: mailbox providers read bounces as a signal that you do not know who
you are writing to, which is the profile of a spammer. The penalty lands on your
domain and your mailboxes, not on the campaign, and it takes weeks of clean sending
to undo. The credits saved by skipping verification are not worth a week of a burnt
domain.

Watch one neighbouring number at the same time, published by Google for bulk senders
since 2024: keep the spam complaint rate under 0.3%, and aim under 0.1%. Complaints
and bounces have the same root cause, which is writing to people who never expected
you.

If the projected rate is over 3% and the user wants to send anyway, this is a refusal,
not a warning. Say what would happen, and offer the proven subset instead.

### 6. Bulk: the loop

There is no bulk endpoint. Bulk means the single verification repeated.

1. Sort by domain. Verify one address per domain first, plus its control address.
   Domains that turn out to be catch-all can then be decided in one move instead of
   row by row.
2. Run one verification at a time, or at most five in parallel. Verifications are
   fast, but your plan's ceiling is 100 requests per minute on Start, 300 on Grow,
   1,000 on Scale, and 30 with no subscription, and each verification is at least two
   requests.
3. Write each verdict to `outreach/enrichment.json` as it arrives. You are paying per
   answer, so never lose one.
4. Progress line every 50 rows: verified, valid, invalid, catch-all, unknown, credits
   spent.
5. On HTTP 402 or a credit error, stop and report the resume point. On 429, wait 60
   seconds and resume from the same row.
6. At the end, recompute the projected bounce rate and apply the table in step 5
   before you say the list is ready.

Record the verification date on every row. A verdict older than 60 to 90 days should
be treated as stale and checked again before a new campaign.

## Output

`outreach/leads.csv` keeps every original column and gains five:

```csv
first_name,last_name,company_name,email,source,email_verification,email_domain_type,email_verified_at,send_decision,verification_note
Marie,Dupont,Emelia,marie@emelia.io,finder,valid,standard,2026-09-08,send,
Paul,Martin,Emelia,paul@emelia.io,finder,invalid,standard,2026-09-08,drop,mailbox does not exist
Sofia,Neri,Kotive,sofia.neri@kotive.fr,finder,valid,catch_all,2026-09-08,hold,domain accepts every address
Luc,Bernard,Vantia,contact@vantia.fr,csv,valid,standard,2026-09-08,hold,role mailbox
Ana,Costa,Delor,ana@delor.pt,csv,unknown,standard,2026-09-08,drop,server did not answer twice
```

`outreach/enrichment.json`, the slice this skill owns:

```json
{
  "run": {
    "id": "2026-09-08-1210",
    "step": "verify_email",
    "list": "outreach/leads.csv",
    "started_at": "2026-09-08T12:10:03Z",
    "finished_at": "2026-09-08T12:31:57Z"
  },
  "cost": {
    "rate_at_run_time": "0.25 credit per address, charged whatever the answer",
    "addresses_checked": 303,
    "control_addresses_checked": 47,
    "credits_spent": 87.5,
    "credits_before": 1009,
    "credits_after": 921.5
  },
  "counts": {
    "rows_with_address": 341,
    "dropped_before_spend": 38,
    "verified": 303,
    "valid": 214,
    "invalid": 31,
    "catch_all": 51,
    "unknown": 7,
    "role_mailboxes": 19
  },
  "domains": {
    "tested": 47,
    "catch_all": 12,
    "catch_all_list": ["kotive.fr", "grandgroupe.com"]
  },
  "decisions": { "send": 214, "hold": 58, "drop": 69 },
  "bounce_projection": {
    "if_you_send_only_valid": 0.0,
    "if_you_send_valid_plus_catch_all": 0.019,
    "if_you_send_everything": 0.125,
    "verdict": "Send the 214 valid rows. The 51 catch-all rows go in a second batch of at most 20 a day. Do not send the 31 invalid rows."
  },
  "notes": [
    "12 of 47 domains are catch-all, which is why 51 rows are on hold.",
    "7 addresses got no answer twice and were dropped rather than risked."
  ]
}
```

Then say it in words, with the decision at the end:

```
303 addresses verified for 87.5 credits.
  214 valid          send these
   51 catch-all      unproven, second batch, 20 a day maximum
   31 invalid        dropped, they would have bounced
    7 unknown        no answer twice, dropped

Sending the 214 valid rows projects a bounce rate near zero. Sending everything
projects 12.5%, which would damage the domain. The list is ready for the first
number, not the second.
```

## Checks before finishing

- The cost was stated and the user said yes before the first paid call.
- Malformed rows and duplicates were removed **before** paying to verify them.
- Every row that will be sent to has a `send_decision` and an `email_verified_at`.
- Every domain holding a row you intend to send to was tested for catch-all, or the
  summary says which domains were not tested and why.
- The projected bounce rate was computed and compared against the table, and the
  verdict was stated to the user in words.
- No row marked `invalid` is in the sending list. Check this explicitly, it is the
  one mistake with a lasting cost.
- Catch-all rows are in a separate batch with a volume cap, not merged into the main
  list.
- `leads.csv` keeps every original column, in order, unchanged.

## Failure modes

**Everything comes back valid, control addresses included.** Either every domain is
catch-all or you tested the control on the wrong domain. Recheck one by hand: a list
where 100% verifies valid is suspicious, not clean.

**A verdict of `invalid` on an address you know works.** Greylisting, a server that
blocks probes, a temporary outage. Retry once an hour later. If it still says invalid
and a human has genuinely had a reply from that address, trust the human, keep the
row, and note the override in `verification_note`. Never rewrite verdicts in bulk.

**`status: "error"` on a whole domain.** The mail server is refusing probes. Treat the
whole domain as unknown, and decide once for the domain rather than paying per row.

**402 or a credit error.** The balance ran out mid run. Stop, and report that the
rest is unverified, so the list is not ready to send. A partially verified list is not
a verified list, and saying so is the point of this skill.

**429.** Over the plan ceiling. Wait 60 seconds and resume from the same row.

**The user asks to send anyway on a list projecting 6% bounces.** Refuse, explain what
it costs, and offer the proven subset. This is the one place where the right answer
is no.

**A list verified three months ago.** Stale. Between 5 and 10% of B2B addresses go
bad every quarter as a rule of thumb, because people change jobs. Re-verify.

## Limits

Verification proves that a mailbox accepts mail today. It does not prove the person
still works there, that they will read it, or that they want to hear from you.

It cannot prove anything on a catch-all domain. That is how those servers answer, not
a shortcoming of Emelia, and no vendor gets around it. This skill tells you which
domains those are instead of pretending.

It does not check spam traps or blocklists, does not measure your domain reputation,
and does not tell you whether SPF, DKIM and DMARC are right: that is
`outreach-deliverability`, the other half of not landing in spam. It does not send
anything and does not add anyone to a campaign.
