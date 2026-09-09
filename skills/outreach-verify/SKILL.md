---
name: outreach-verify
description: "Verify the email addresses you brought yourself before you send to them: a CSV, an export from another tool, an old CRM extract, a contact base that has been sitting for a year. Sorts each address into send, drop or hold, detects catch-all domains with a control test, keeps the projected bounce rate under the threshold that protects sender reputation, and writes the verdicts into outreach/leads.csv and outreach/enrichment.json. Not for addresses Emelia's email finder returned, which come back verified already, so paying to check them again buys nothing. Triggers on: verify email, email verification, email verifier, check emails, validate emails, bounce rate, hard bounce, catch-all, clean my list, list hygiene, old list, stale contacts, deliverability check, is this email valid."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Verify the addresses you did not find at Emelia

## What this does

Checks addresses whose provenance you do not control against Emelia's verifier and
turns the answer into a decision: send it, drop it, or hold it for a small separate
batch. It measures the bounce rate you are about to inflict on your sending domain
and stops you when that number is too high. A bounce costs a fraction of a credit to
avoid and weeks of sender reputation to survive.

It deliberately does not re-check what Emelia's email finder just returned. That
address already carries a verification verdict, so paying for a second one buys you
nothing.

## When to use it

**The rule: verify what you did not find at Emelia.**

Emelia's email finder returns an address together with a `qualification` field, and
that field is a verdict from the source that checked the mailbox, not a guess. An
address the finder returned as `valid` is verified. Sending it through this skill
costs 0.25 credit per row and changes nothing. On a 3,000 row list that is 750
credits for an answer you already had.

So use it on:

- **Any list you did not build with the finder.** A CSV a colleague sent you, a CRM
  export, a conference attendee file, a scrape, a purchased file, the output of
  another enrichment tool.
- **Addresses the finder flagged `risky`.** Those come from Emelia's secondary source
  below its "sure" confidence threshold, so they are the one finder output that was
  not proven. Verifying them is a real choice, and dropping them is the other one.
- **Addresses you built from a pattern**, per `outreach-find-email` section 5. A
  pattern is a guess until a verifier says otherwise.
- **Anything old**, see the freshness table below.

Do not use it on:

- Addresses `outreach-find-email` just returned as `valid`. Send them.
- Addresses that replied to you in the last few weeks. A reply is the strongest proof
  a mailbox exists, and it is free.

### Freshness: how old is too old

A verification is a photograph, not a guarantee. As a rule of thumb, 5 to 10% of B2B
addresses go bad every quarter because people change jobs, so a year old verdict is
worth about as much as no verdict at all.

| Age of the verdict, or of the find | Before a large campaign |
|---|---|
| Under 30 days | Do not re-verify. You would be paying for the same answer. |
| 1 to 3 months | Re-verify only if the list is your main sending list for the quarter, or if the last campaign on it bounced more than usual. |
| 3 to 12 months | Re-verify. Expect 5 to 20% to have gone bad. |
| Over 12 months | Re-verify, and expect 20 to 30% losses. Budget for it before you promise a volume. |

Same table for a paused campaign you are about to restart: under a month, restart;
over three months, re-verify first.

Use a different skill when you have no addresses at all (`outreach-find-email`), or
when you want the whole waterfall under one budget (`outreach-enrich`, which applies
this rule for you and only sends the right rows here).

## Inputs

| Field | Required | Notes |
|-------|----------|-------|
| `email` | yes | One address per call. Trim it. Lowercase the domain. |

Files: `outreach/leads.csv` in, `outreach/leads.csv` and
`outreach/enrichment.json` out.

The work list is not the whole file. Build it explicitly, and say so in the summary:

```
work list = rows with an address
            minus rows whose email_source is "finder" and whose email_status is "valid"
            minus rows already verified in the last 30 days
            plus  rows whose email_source is "finder" and whose email_status is "risky", if the user wants them
```

If the file has no `email_source` column, you do not know where the addresses came
from. Ask the user before assuming: "did these come out of Emelia's finder, or from
somewhere else?" One question saves the whole spend when the answer is the finder.

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
valid. That is the whole reason you clean the list before you verify it, not after,
and the reason the work list excludes what the finder already proved.

Print this and stop:

```
Verification on outreach/leads.csv

  Rows with an address                 341
  From Emelia's finder, valid          168   already verified, not re-checked
  Verified in the last 30 days          12   still fresh, not re-checked
  Malformed or duplicate, dropped free  12
  To verify (addresses you brought)    126   including 11 role mailboxes
  Flagged risky by the finder           23   verify these too? (0.25 each)

  Cost: 0.25 credit per address, charged whatever the answer.
  126 addresses plus about 40 catch-all controls = 41.5 credits.
  Add the 23 risky rows: 47.25 credits. Your balance: 1,009 credits.

Run it? (yes / yes with the risky rows / no / verify without the role mailboxes)
```

Two lines of that quote matter more than the rest: the 168 rows you are **not**
paying to check, and the reason. Say it out loud, because the reflex of verifying
everything is exactly what this skill exists to break.

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
| **Valid** | `qualification: "valid"` on a domain that is not catch-all, from the verifier or from the finder | The mailbox exists and accepts mail | **Send.** This is your sending list. |
| **Invalid** | `qualification: "invalid"` | The mailbox does not exist or the domain does not accept mail | **Drop.** Never send. Never "try it anyway to see". This is exactly what a hard bounce is. |
| **Catch-all or risky** | `qualification: "valid"` on a domain that answers yes to everything, or `qualification: "risky"` from the finder and never verified | Unproven. It may be a real mailbox, it may be a black hole that accepts then bounces later | **Hold.** Send in a separate small batch, described below. |
| **Unknown** | `status: "error"`, a timeout, or a server that refused to answer | No verdict | Retry once, at least an hour later. Still nothing: treat it as catch-all, or drop it if you are being careful. |

Two rules that are not negotiable. Invalid never gets sent: not on the first step,
not on a follow-up, not "because it is a big account". And a bucket is a decision,
not a label to admire: every row leaves this skill with a `send_decision` of `send`,
`hold` or `drop`.

A row that arrives already `valid` from the finder lands in the first bucket without
a call and without a credit. Give it `email_verified_at` equal to its find date and
`verification_source: finder`, so the freshness table above can act on it later.

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

Only test domains holding an address **you are verifying**. Domains that only carry
finder results do not need a control: you are not deciding those rows here, the
finder already did. On 126 addresses over 40 domains this adds about 10 credits,
which is cheap for knowing which of your "valid" rows are real.

**What to do with catch-all rows.** They are not worthless, they are unproven:

- Put them in their own batch, sent after the proven list, never mixed into it.
- Cap the batch at roughly 10% of your daily volume for that mailbox.
- Watch the bounce rate on that batch specifically. Under 3%, keep going. Above,
  stop and drop the rest of the catch-all rows.
- Never use catch-all rows to warm up a new domain, and never send them from a
  mailbox you cannot afford to lose.

### 5. The threshold that decides whether you send at all

Compute the projected hard bounce rate before the campaign starts, over the whole
sending list, finder rows included:

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
to undo. The credits saved by skipping a **needed** verification are not worth a week
of a burnt domain. The credits spent on an unneeded one are simply gone.

Watch one neighbouring number at the same time, published by Google for bulk senders
since 2024: keep the spam complaint rate under 0.3%, and aim under 0.1%. Complaints
and bounces have the same root cause, which is writing to people who never expected
you.

If the projected rate is over 3% and the user wants to send anyway, this is a refusal,
not a warning. Say what would happen, and offer the proven subset instead.

### 6. Bulk: the loop

There is no bulk endpoint. Bulk means the single verification repeated.

1. Build the work list from the rule in Inputs. Print how many rows it excluded and
   why before the first call.
2. Sort by domain. Verify one address per domain first, plus its control address.
   Domains that turn out to be catch-all can then be decided in one move instead of
   row by row.
3. Run one verification at a time, or at most five in parallel. Verifications are
   fast, but your plan's ceiling is 100 requests per minute on Start, 300 on Grow,
   1,000 on Scale, and 30 with no subscription, and each verification is at least two
   requests.
4. Write each verdict to `outreach/enrichment.json` as it arrives. You are paying per
   answer, so never lose one.
5. Progress line every 50 rows: verified, valid, invalid, catch-all, unknown, credits
   spent.
6. On HTTP 402 or a credit error, stop and report the resume point. On 429, wait 60
   seconds and resume from the same row.
7. At the end, recompute the projected bounce rate over the whole sending list and
   apply the table in step 5 before you say the list is ready.

Record the verification date on every row, including the rows you did not pay for.
That date is what the freshness table reads next quarter.

## Output

`outreach/leads.csv` keeps every original column and gains six:

```csv
first_name,last_name,company_name,email,email_source,email_verification,verification_source,email_domain_type,email_verified_at,send_decision,verification_note
Marie,Dupont,Emelia,marie@emelia.io,finder,valid,finder,standard,2026-09-08,send,returned verified by the finder, not re-checked
Paul,Martin,Kavia,p.martin@kavia.fr,csv,invalid,verifier,standard,2026-09-09,drop,mailbox does not exist
Sofia,Neri,Kotive,sofia.neri@kotive.fr,csv,valid,verifier,catch_all,2026-09-09,hold,domain accepts every address
Luc,Bernard,Vantia,contact@vantia.fr,csv,valid,verifier,standard,2026-09-09,hold,role mailbox
Ana,Costa,Delor,ana@delor.pt,csv,unknown,verifier,standard,2026-09-09,drop,server did not answer twice
Tom,Weiss,Sorel,t.weiss@sorel.com,finder,valid,verifier,standard,2026-09-09,send,flagged risky by the finder then verified valid
```

`outreach/enrichment.json`, the slice this skill owns:

```json
{
  "run": {
    "id": "2026-09-09-1210",
    "step": "verify_email",
    "list": "outreach/leads.csv",
    "started_at": "2026-09-09T12:10:03Z",
    "finished_at": "2026-09-09T12:24:11Z"
  },
  "scope": {
    "rule": "verify what did not come from Emelia's finder",
    "rows_with_address": 341,
    "excluded_finder_valid": 168,
    "excluded_verified_under_30_days": 12,
    "excluded_malformed_or_duplicate": 12,
    "checked_carried_in": 126,
    "checked_risky_from_finder": 23,
    "credits_not_spent_by_excluding_finder_rows": 42.0
  },
  "cost": {
    "rate_at_run_time": "0.25 credit per address, charged whatever the answer",
    "addresses_checked": 149,
    "control_addresses_checked": 40,
    "credits_spent": 47.25,
    "credits_before": 1009,
    "credits_after": 961.75
  },
  "counts": {
    "valid": 98,
    "invalid": 27,
    "catch_all": 20,
    "unknown": 4,
    "role_mailboxes": 11
  },
  "domains": {
    "tested": 40,
    "catch_all": 9,
    "catch_all_list": ["kotive.fr", "grandgroupe.com"]
  },
  "decisions": { "send": 267, "hold": 31, "drop": 43 },
  "bounce_projection": {
    "sending_list_rows": 267,
    "if_you_send_the_send_group": 0.0,
    "if_you_send_the_hold_group_too": 0.02,
    "if_you_send_all_329_deliverable_rows": 0.094,
    "verdict": "Send the 267 rows marked send. The 20 catch-all rows go in a second batch of at most 20 a day. Do not send the 27 invalid rows."
  },
  "notes": [
    "168 finder rows were not re-verified. They came back with a verdict already, and re-checking them would have cost 42 credits for the same answer.",
    "9 of 40 tested domains are catch-all, which is why 20 rows are on hold.",
    "4 addresses got no answer twice and were dropped rather than risked."
  ]
}
```

Then say it in words, with the decision at the end:

```
149 addresses verified for 47.25 credits. 168 more were left alone: the finder
returned them verified, so re-checking them would have cost 42 credits for the
same answer.

  267 send        87 verified in this run, 180 already verified before it
   31 hold        20 catch-all, 11 role mailboxes, second batch, 20 a day maximum
   43 drop        27 invalid, 4 with no verdict after two tries, 12 malformed

Sending the 267 projects a bounce rate near zero. Sending all 329 deliverable
rows projects 9.4%, which would damage the domain. The list is ready for the
first number, not the second.
```

## Checks before finishing

- The cost was stated and the user said yes before the first paid call.
- **No address that Emelia's finder returned as `valid` was sent to the verifier.**
  Check this explicitly and report the count you skipped and the credits it saved.
  This is the check people forget, and it is the expensive one.
- Malformed rows and duplicates were removed **before** paying to verify them.
- Every row that will be sent to has a `send_decision` and an `email_verified_at`,
  including rows whose verdict came from the finder.
- Every domain holding a row **you verified here** was tested for catch-all, or the
  summary says which domains were not tested and why.
- The projected bounce rate was computed over the whole sending list, not only over
  the rows checked in this run, and the verdict was stated in words.
- No row marked `invalid` is in the sending list. Check this explicitly, it is the
  one mistake with a lasting cost.
- Catch-all rows are in a separate batch with a volume cap, not merged into the main
  list.
- `leads.csv` keeps every original column, in order, unchanged.

## Failure modes

**You verified the finder's output.** The single most expensive mistake this skill
can make, and it looks like diligence. Symptom: `addresses_checked` is close to the
number of rows with an address, and almost everything comes back valid. Stop, do not
re-run, and tell the user how many credits went on it so the next run does not repeat
it.

**No `email_source` column, so you cannot tell provenance.** Ask. Do not assume the
addresses are the user's own just because the column is missing, and do not assume
they came from the finder either. One question, then decide.

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

**A carried-in address verifies `invalid` and the person is still worth reaching.**
The address is dead, the lead is not. Send that row to `outreach-find-email` with the
name and the company: 1 credit for a fresh address, and the finder returns it
verified.

## Limits

Verification proves that a mailbox accepts mail today. It does not prove the person
still works there, that they will read it, or that they want to hear from you.

It is not a second opinion on Emelia's finder. The finder returns a verdict with the
address, and this skill has no better source than the one that produced it, so
running it over finder output spends credits and changes no decision.

It cannot prove anything on a catch-all domain. That is how those servers answer, not
a shortcoming of Emelia, and no vendor gets around it. This skill tells you which
domains those are instead of pretending.

It does not check spam traps or blocklists, does not measure your domain reputation,
and does not tell you whether SPF, DKIM and DMARC are right: that is
`outreach-deliverability`, the other half of not landing in spam. It does not send
anything and does not add anyone to a campaign.
