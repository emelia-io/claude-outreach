---
name: outreach-enrich
description: "The full enrichment waterfall on a lead list: filter first, find the missing emails, verify what was found, find mobile numbers only where they are worth 50 credits, then decide row by row who is sendable, who is on hold and who is dropped. Runs under a credit budget fixed before the first call and stops when it is reached. Writes outreach/enrichment.json with every counter and updates outreach/leads.csv without losing a single original column, then fills the custom fields your sequence needs. Triggers on: enrich, enrichment, enrich my list, waterfall, find and verify, clean and enrich, contact data, credits budget, how much will this cost, prepare my list, custom fields."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# The enrichment waterfall

## What this does

Runs the whole contact data chain on a filtered list, in the order that costs the
least: find, verify, decide, then phone numbers for the small group that deserves a
call. It runs under a credit budget you set before the first call and stops when it
hits it. At the end every row carries a decision (`send`, `hold`, `drop`) and the
file says why. Nothing is quietly dropped, nothing is quietly guessed.

## When to use it

Use it as the default enrichment step of a campaign, when you want one budget, one
report and one pass over the list.

Use the single skills instead when you want one thing only: `outreach-find-email`,
`outreach-find-phone`, `outreach-verify`. This skill calls all three, so read them
for the field level detail; it owns the order, the budget, the decision rule and the
files.

Never run it on an unfiltered list. `outreach-filter` first: exclusions, duplicates,
existing customers, the blacklist, rows with no usable company. Credits spent on a
row you delete ten minutes later are gone.

## Inputs

- `outreach/leads.csv`, filtered. Required. Every original column is preserved.
- `outreach/icp.json`, optional. Used to decide which segment is worth a phone
  number, and which rows can be dropped rather than held.
- A **credit budget** for the run. Ask for it if the user did not give one. This is
  not optional: a waterfall without a ceiling is how people spend 12,000 credits on a
  Tuesday.
- `EMELIA_API_KEY` exported in the shell. The REST API is the documented path and
  this skill assumes it. The Emelia MCP server, if configured, wraps the same calls
  and adds the list management tools used at the end.

Columns the waterfall reads: `first_name`, `last_name` (or `fullname`), `company_name`,
`company_domain` (or `website`), `country`, `linkedin_url`, `email` if some rows already have
one. Map the user's real column names once, at the start, and say what you mapped.

Missing key, no budget, or no filtered list: say which one is missing and stop. In
dry run, produce the plan and the cost estimate and spend nothing.

## How to do it

### 1. Fix the order, and never change it

```
filter  ->  find email  ->  verify  ->  decide  ->  find phone (subset only)
```

- **Filter before find.** A found email on a row you exclude is a credit burnt.
- **Find before verify.** Verifying an address you just found costs a quarter of a
  credit and turns a maybe into a yes.
- **Verify before decide.** The decision needs the verdict, not the address.
- **Decide before phone.** A mobile costs about 50 times an email, so you buy them
  for a chosen segment after you know who is worth calling, never for a whole list.

One exception: rows that already have an email skip the finder and go straight to
verification.

### 2. Plan the run and quote it, before anything is spent

Count the rows in each bucket, apply the rates, and present one plan. Rates at the
time of writing, to confirm on the user's plan page: 1 credit per email found (a miss
is refunded), 0.25 credit per verification (charged whatever the answer), 50 credits
per mobile found (a miss is refunded).

```
Enrichment plan for outreach/leads.csv, 412 rows

  1  Find email   323 rows, expect 180 to 240 found at 55 to 75%   180 to 240 cr
  2  Verify       about 310 addresses plus 45 catch-all controls   about 89 cr
  3  Find phone   only the segment you choose, nothing by default
                  the 40 priority rows would cost                  500 to 800 cr

  Total without phones   270 to 330 credits
  Total with the 40      770 to 1,130 credits
  Your balance           1,250 credits
  Time: about 45 minutes on Start, 15 on Grow. Request quota, not a slow API.

Budget for this run? Suggested cap: 400 credits without phones.
(yes 400 / another number / no phones / no)
```

Wait for a real answer. This is the single confirmation that protects the user's
money, and it is required by the rules of this repository.

### 3. Run the steps, writing as you go

**Find email**, per `outreach-find-email`. Work list: filtered rows with a name and
a company and no email. Send `country` on every call, the API rejects it without one.
Write each result to `outreach/enrichment.json` as it lands.

**Verify**, per `outreach-verify`. Work list: every row that now has an address,
whether the finder brought it or it was already in the file. Group by domain, run the
catch-all control test once per domain holding a row you would send to, then verify.

**Decide.** No API calls. Apply the rule in step 4 to every row.

**Find phone**, per `outreach-find-phone`, on the subset the user names after seeing
the decisions, and only on rows with a LinkedIn profile URL. Quote the cost again for
that subset: the number changed since the plan, because you now know who survived.

After every step, print a two line summary and the running credit total. Never batch
three steps and report once: the user must be able to stop between them.

### 4. The decision rule, per row

Apply in order, first match wins:

| Row state | Decision | Written reason |
|-----------|----------|----------------|
| No email, no LinkedIn URL | `drop` | `no reachable channel` |
| Email verified `invalid` | `drop` | `would hard bounce` |
| Email `unknown` after two attempts | `drop` | `no verdict, not worth the reputation` |
| Email is a role mailbox (`contact@`, `info@`) | `hold` | `role mailbox, not a person` |
| Email verified `valid`, domain catch-all | `hold` | `catch-all domain, unproven` |
| Email verified `valid`, domain not catch-all | `send` | `verified` |
| No email, LinkedIn URL present, in the priority segment | `hold` | `phone or LinkedIn channel only` |
| No email, LinkedIn URL present, not priority | `drop` | `no email, not worth a 50 credit lookup` |

The order of the rows matters: the drops and the holds come first on purpose, so a
role mailbox that verifies valid is held rather than sent. An address the finder
marked `risky` gets no special rule, it is decided by its verification like any
other: verified valid on a domain that is not catch-all, it sends.

`send` rows go into the campaign. `hold` rows go into a second, smaller batch or into
a different channel, never mixed into the first send. `drop` rows stay in the file
with their reason, so the user can see the cost of their data quality instead of
watching rows disappear.

Then check the aggregate before declaring anything ready: projected bounce rate on
the `send` group must be under 2%, per `outreach-verify`. If it is not, the run is
not finished, whatever the counters say.

### 5. The budget, and what happens when it runs out

Track credits spent continuously, not at the end. Before starting a job, check that
the budget can still absorb its worst case (1 credit for a find, 0.25 for a
verification, 50 for a phone); if it cannot, do not start it. When the cap is
reached, stop cleanly: no new job, collect the jobs already running since they are
already paid for, write the file, report. Never go over the cap because "there were
only 20 rows left". Ask.

The stop report, which is a normal outcome and not an error:

```
Budget cap of 400 credits reached after 268 of 323 rows.

  Done      268 looked up, 201 found, 189 verified valid
  Not done   55 rows never looked up, listed in enrichment.json
  Spent     400.0 credits, balance 850

Finishing the remaining 55 rows would cost about 55 credits for the finder plus
14 for verification. Continue? (yes / no / stop here)
```

Two other hard stops, both of which end the run rather than retry it:

- HTTP 402 or a message mentioning credits: the account balance is empty. Stop, write
  the file, report the resume point.
- The user says stop. Write the file first, then stop.

### 6. Bulk without tripping the quota

The rate limit is per API key, per minute: **30 with no subscription, 100 on Start,
300 on Grow, 1,000 on Scale**. Every enrichment costs more than one request: a find
is one POST plus several GETs while you poll, a verification is one POST plus one or
two GETs.

Budget about 6 requests per find and 3 per verification, then pace to stay under the
ceiling with headroom:

| Plan | Requests per minute | Rows per minute, finding | Rows per minute, verifying |
|------|---------------------|--------------------------|----------------------------|
| No subscription | 30 | 4 | 8 |
| Start | 100 | 14 | 28 |
| Grow | 300 | 45 | 90 |
| Scale | 1,000 | 150 | 300 |

- Poll a job every 2 to 3 seconds, never faster. Faster polling does not make a job
  finish sooner, it only spends quota.
- At most three finds in flight at once, five verifications.
- Never run two enrichment loops against the same key at the same time, including
  from another terminal or another agent. The quota is shared and you will 429 both.
- On 429: wait 60 seconds, resume from the same row, halve the pace.
- Tell the user the wall clock time up front. On Start, 300 rows of find plus verify
  is roughly 40 minutes. That is the quota, not the API.

### 7. Fill the custom fields the sequence needs

Enrichment is only useful if the values reach the campaign, so do this last, once
the decisions exist. Push contacts with their fields into the list attached to the
campaign, which is how a contact enters a running campaign:

```bash
curl -s -X POST https://api.emelia.io/advanced/lists/contacts \
  -H "Authorization: $EMELIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"id":"<listId>","contact":{"email":"marie@emelia.io","firstName":"Marie",
       "lastName":"Dupont","linkedinUrlProfile":"https://www.linkedin.com/in/marie-dupont-1a2b3c",
       "company":"Emelia","icebreaker":"your post on outbound benchmarks"}}'
```

Any key that is not a known contact field becomes a custom variable, so `icebreaker`
above is usable as a variable in the sequence. To set one field on a contact already
in a campaign:

```bash
curl -s -X PATCH https://api.emelia.io/advanced/contacts \
  -H "Authorization: $EMELIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"campaignId":"<campaignId>","email":"marie@emelia.io",
       "fieldName":"icebreaker","fieldValue":"your post on outbound benchmarks"}'
```

With the MCP server, `add_contacts_to_list_bulk` takes up to 100 flat contacts per
call and reports created, duplicate, updated and failed per row, with `updateIfExists`
to re-run without creating duplicates.

Three rules on custom fields. Every variable used in `sequence.md` must exist on every
`send` row, because a missing variable is what produces "Hi ," in a real inbox. Give
every variable a fallback that reads naturally in the sentence. And never write a
value you inferred rather than found: an icebreaker about a funding round that did not
happen is worse than no icebreaker.

## Output

### `outreach/leads.csv`

Every original column, in its original order, untouched. Enrichment columns are
appended to the right:

```csv
first_name,last_name,company_name,company_domain,linkedin_url,source,email,email_status,email_source,email_verification,email_domain_type,email_verified_at,phone,phone_country,phone_type,send_decision,decision_reason
Marie,Dupont,Emelia,emelia.io,https://www.linkedin.com/in/marie-dupont-1a2b3c,basile,marie@emelia.io,valid,finder,valid,standard,2026-09-08,+33612345678,FR,mobile,send,verified
Paul,Martin,Emelia,emelia.io,https://www.linkedin.com/in/paul-martin-9z8y7x,basile,paul@emelia.io,valid,finder,invalid,standard,2026-09-08,,,,drop,would hard bounce
Sofia,Neri,Kotive,kotive.fr,https://www.linkedin.com/in/sofia-neri,basile,sofia.neri@kotive.fr,risky,finder,valid,catch_all,2026-09-08,,,,hold,catch-all domain unproven
Julien,Roche,Emelia,emelia.io,,basile,,not_found,,,,2026-09-08,,,,drop,no reachable channel
```

### `outreach/enrichment.json`

The canonical shape. When a single skill runs alone it writes its own section at the
top level; when the waterfall runs, the sections live under `steps`.

```json
{
  "run": {
    "id": "2026-09-08-1042", "list": "outreach/leads.csv",
    "started_at": "2026-09-08T10:42:11Z", "finished_at": "2026-09-08T12:34:02Z",
    "order": ["find_email", "verify_email", "decide", "find_phone"],
    "stopped_early": false, "stop_reason": null
  },
  "budget": {
    "cap_credits": 400, "spent_credits": 328.5, "remaining_in_cap": 71.5,
    "credits_before": 1250, "credits_after": 921.5,
    "rates_at_run_time": {
      "find_email": "1 per address found, refunded on a miss",
      "verify_email": "0.25 per address checked, always charged",
      "find_phone": "50 per number found, refunded on a miss"
    }
  },
  "steps": {
    "find_email": {
      "looked_up": 323, "found_valid": 218, "found_risky": 23,
      "not_found": 78, "error": 4, "credits": 241, "discovery_rate": 0.746
    },
    "verify_email": {
      "checked": 303, "control_domains_tested": 47, "valid": 214,
      "invalid": 31, "catch_all": 51, "unknown": 7, "credits": 87.5
    },
    "find_phone": {
      "eligible": 214, "looked_up": 0, "found": 0, "credits": 0,
      "note": "user declined phones on this run"
    }
  },
  "totals": {
    "rows_in": 412, "rows_skipped_before_spend": 89, "rows_processed": 323,
    "with_email": 289, "verified": 303, "sendable": 214, "on_hold": 58,
    "dropped": 140, "credits_spent": 328.5
  },
  "decisions": {
    "send": 214, "hold": 58, "drop": 140,
    "hold_reasons": { "catch-all domain unproven": 39, "role mailbox": 19 },
    "drop_reasons": {
      "would hard bounce": 31, "no reachable channel": 78,
      "no verdict, not worth the reputation": 7,
      "no email, not worth a 50 credit lookup": 24
    }
  },
  "bounce_projection": { "send_group": 0.0, "verdict": "safe to send" },
  "pending_jobs": [],
  "notes": [
    "89 rows skipped before any spend: 71 already had an address, 18 had no company.",
    "12 of 47 domains are catch-all, which is why 39 rows are on hold.",
    "No phone lookups ran. The 214 sendable rows have a LinkedIn URL if you want them."
  ]
}
```

### The spoken summary

```
412 rows in, 214 ready to send (52%), 58 on hold, 140 dropped. 328.5 credits spent
of a 400 cap, 921.5 left.

The 140 dropped are not lost data: 78 had no findable email, 31 would have bounced,
24 had no email and were not worth a 50 credit lookup, 7 got no verdict. They are
still in leads.csv with their reason.

Bounce projection on the 214: near zero. Ready for outreach-write.
```

Say the percentage. Never say "the list is enriched".

## Checks before finishing

- A budget cap was set and confirmed before the first paid call, and the run stayed
  under it or stopped and asked.
- The order was filter, find, verify, decide, phone. No phone lookup ran on a row
  before its email verdict existed.
- Every row in `leads.csv` has a `send_decision` and a `decision_reason`.
- Every original column survived, in order, unchanged. Diff the header against the
  input file and confirm the first N columns are identical.
- The row count out equals the row count in. Nothing was deleted, only decided.
- `credits_spent` matches the account balance movement, or the gap is explained.
- No `pending_jobs` left unresolved without being listed.
- Every variable used by the planned sequence exists on every `send` row, with a
  fallback.
- The summary gives percentages and names what was not done.

## Failure modes

**The user gives no budget.** Do not invent one and do not start. Propose a cap based
on the row count and the rates, and wait.

**The list was never filtered.** You find out when 30% of the rows are duplicates or
existing customers. Stop, run `outreach-filter`, restart. Credits spent before that
point are unrecoverable, so check first.

**Column mapping wrong**: `company_name` holding a legal name (`EMELIA SAS`), `company_domain`
holding a full URL with a path, names in capitals. The hit rate collapses and it looks
like the API is bad. Check ten rows by hand before running 300.

**Credits run out mid run.** Stop, write the file, report the resume point. Nothing is
lost as long as the file was written row by row.

**429 storms.** Two loops on one key, or polling every 200 milliseconds. One loop, one
key, poll every 2 to 3 seconds.

**A step silently produced nothing**, for instance verification running on zero rows
because the finder wrote to a column the verifier did not read. The counters catch it:
`verified` should be close to `with_email`. A counter at zero where it should not be
is a finding to report, not a clean run.

**The user asks to send to the `hold` group anyway.** Explain the batch and the cap,
per `outreach-verify`. Never merge hold rows into the main send.

**Re-running the waterfall on the same file.** Skip every row that already has a
verdict. Re-running a find or a phone lookup on a row you already paid for is charged
again, including when Emelia serves it from its own cache. The file on disk is your
protection against paying twice.

## Limits

This skill spends money on the user's behalf, so it does nothing without an explicit
yes and a cap. It cannot recover credits already spent, and it cannot tell you a row
was worth enriching before it enriched it.

It does not build the list, does not filter it, does not write the copy, does not
check your sending setup and does not launch anything. Those are `outreach-leads`,
`outreach-filter`, `outreach-write`, `outreach-deliverability` and
`outreach-campaign`.

It cannot make a bad list good. If 60% of the rows drop out, the problem is upstream:
the targeting, the source, or the column mapping. Say that instead of running the
waterfall twice.
