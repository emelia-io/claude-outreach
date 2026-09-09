---
name: outreach-enrich
description: "The full enrichment waterfall on a lead list: filter first, find the missing emails, verify only the addresses that came from somewhere other than Emelia's finder, find mobile numbers only where they are worth 50 credits, then decide row by row who is sendable, who is on hold and who is dropped. Runs under a credit budget fixed before the first call and stops when it is reached. Writes outreach/enrichment.json with every counter and updates outreach/leads.csv without losing a single original column, then fills the custom fields your sequence needs. Triggers on: enrich, enrichment, enrich my list, waterfall, find and verify, clean and enrich, contact data, credits budget, how much will this cost, prepare my list, custom fields."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# The enrichment waterfall

## What this does

Runs the whole contact data chain on a filtered list, in the order that costs the
least: find the missing addresses, verify the ones whose provenance you do not
control, decide, then phone numbers for the small group that deserves a call. It runs
under a credit budget you set before the first call and stops when it hits it. At the
end every row carries a decision (`send`, `hold`, `drop`) and the file says why.
Nothing is quietly dropped, nothing is quietly guessed, and nothing is verified twice.

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

The waterfall is not a single chain. After the filter it splits in two, because the
finder and the verifier work on **disjoint sets of rows**:

```
filter
  |
  +-- rows with no address ------> find email --> valid: send as returned
  |                                           \-> risky: verify, or drop
  |
  +-- rows with an address you -> verify ------> invalid: back to the finder,
  |   brought yourself                            1 credit for a fresh address
  |
  +-- both branches ------------> decide ------> find phone (chosen subset only)
```

- **Filter before anything.** A found email on a row you exclude is a credit burnt.
- **Never verify what the finder returned.** Emelia's finder hands back an address
  together with its `qualification`, which is a verification verdict from the source
  that checked the mailbox. `valid` means verified. Running it through the verifier
  costs 0.25 credit per row and returns the same word. This is the single biggest
  waste in a naive waterfall: on 3,000 found addresses it is 750 credits for nothing.
- **Verify what you brought.** Addresses from a CSV, a CRM export, another tool or a
  file older than a few months have no verdict, and those are exactly the rows that
  bounce. That is the verifier's job.
- **`risky` is the one grey zone.** The finder returns it when its secondary source
  was below "sure". Verify those rows (0.25 each) or drop them, and ask the user
  which, because on a large list the two answers cost very differently.
- **Decide before phone.** A mobile costs about 50 times an email, so you buy them
  for a chosen segment after you know who is worth calling, never for a whole list.

A useful consequence of the split: a carried-in address that verifies `invalid` is
not a dead row, it is a live lead with a dead address. Send it to the finder with its
name and company. One credit, and the address comes back verified.

### 2. Plan the run and quote it, before anything is spent

Count the rows in each bucket, apply the rates, and present one plan. Rates at the
time of writing, to confirm on the user's plan page: 1 credit per email found (a miss
is refunded), 0.25 credit per verification (charged whatever the answer), 50 credits
per mobile found (a miss is refunded).

```
Enrichment plan for outreach/leads.csv, 412 rows

  Split:  71 rows already carry an address (from your CSV)
         323 rows have a name and a company but no address
          18 rows have neither, never looked up

  1  Find email    323 rows, expect 180 to 240 found at 55 to 75%   180 to 240 cr
                   what comes back valid is verified, it does not
                   go through step 2
  2  Verify         71 addresses you brought, plus about 34
                   catch-all controls on their domains              about 27 cr
                   plus the risky finds if you want them (~23)      about 6 cr
  3  Find phone    only the segment you choose, nothing by default
                   the 40 priority rows would cost                  500 to 800 cr

  Total without phones   210 to 275 credits
  Total with the 40      710 to 1,075 credits
  Your balance           1,250 credits
  Time: about 30 minutes on Start, 10 on Grow. Request quota, not a slow API.

Not in this plan: verifying the 180 to 240 addresses the finder will return.
They come back verified. That pass would have added 45 to 60 credits and
changed no decision.

Budget for this run? Suggested cap: 300 credits without phones.
(yes 300 / another number / verify the risky finds too / no phones / no)
```

Wait for a real answer. This is the single confirmation that protects the user's
money, and it is required by the rules of this repository.

### 3. Run the steps, writing as you go

**Find email**, per `outreach-find-email`. Work list: filtered rows with a name and
a company and no email. Send `country` on every call, the API rejects it without one.
Write each result to `outreach/enrichment.json` as it lands. Results marked `valid`
are done: they are verified and they go straight to the decision step.

**Verify**, per `outreach-verify`. Work list, and this is where the money is:

```
verify  =  rows whose address was in the file before this run
        +  rows the finder returned as risky, if the user said yes
        +  candidates built from an observed domain pattern
verify  =/= everything that has an address
```

Group those rows by domain, run the catch-all control test once per domain holding a
row you would send to, then verify. Do not run controls on domains that only carry
finder results: you are not deciding those rows here.

Print the exclusion before the first paid call, in one line: "218 finder results are
not going through verification, which saves 54.5 credits." The user should see the
saving, not just the spend.

**Decide.** No API calls. Apply the rule in step 4 to every row.

**Find phone**, per `outreach-find-phone`, on the subset the user names after seeing
the decisions, and only on rows with a LinkedIn profile URL. Quote the cost again for
that subset: the number changed since the plan, because you now know who survived.

After every step, print a two line summary and the running credit total. Never batch
three steps and report once: the user must be able to stop between them.

### 4. The decision rule, per row

Apply in order, first match wins. The `verdict` column says where the answer came
from, so you can see at a glance that no row was paid for twice:

| Row state | Verdict from | Decision | Written reason |
|-----------|--------------|----------|----------------|
| No email, no LinkedIn URL | nothing | `drop` | `no reachable channel` |
| Email `invalid` | verifier, or the finder's own answer | `drop` | `would hard bounce` |
| Email `unknown` after two attempts | verifier | `drop` | `no verdict, not worth the reputation` |
| Email is a role mailbox (`contact@`, `info@`) | any | `hold` | `role mailbox, not a person` |
| Email `valid`, domain known catch-all | verifier | `hold` | `catch-all domain, unproven` |
| Email `valid`, returned by the finder | finder | `send` | `found and verified by Emelia` |
| Email `risky` from the finder, then verified `valid` on a domain that is not catch-all | verifier | `send` | `risky find, verified` |
| Email `risky` from the finder, not verified | nothing | `hold` | `unproven, verify it or drop it` |
| Email `valid`, carried in, domain not catch-all | verifier | `send` | `verified` |
| No email, LinkedIn URL present, in the priority segment | nothing | `hold` | `phone or LinkedIn channel only` |
| No email, LinkedIn URL present, not priority | nothing | `drop` | `no email, not worth a 50 credit lookup` |

The order of the rows matters: the drops and the holds come first on purpose, so a
role mailbox that verifies valid is held rather than sent.

The two `send` lines that come from the finder are the point of the whole rewrite.
A finder `valid` sends on the finder's own verdict, with no verification call behind
it. Nothing about the row is less proven than a carried-in address you paid to check:
the same kind of check produced both, one of them was just included in the price of
the find.

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
Budget cap of 300 credits reached after 268 of 323 finder rows.

  Done      268 looked up, 201 found (183 valid, 18 risky)
            71 carried-in addresses verified, 34 controls
  Not done   55 rows never looked up, listed in enrichment.json
            the 18 risky finds are not verified yet
  Spent     300.0 credits, balance 950

Finishing the remaining 55 rows would cost about 40 credits for the finder. The
18 risky finds would cost 4.5 more if you want them verified. The 183 valid finds
need nothing. Continue? (yes / no / stop here)
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
- Tell the user the wall clock time up front. On Start, 300 finds is roughly 22
  minutes. The verification pass adds only a few minutes now that it runs on the
  carried-in rows instead of the whole list. That is the quota, not the API.

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
first_name,last_name,company_name,company_domain,linkedin_url,source,email,email_source,email_status,email_verification,verification_source,email_domain_type,email_verified_at,phone,phone_country,phone_type,send_decision,decision_reason
Marie,Dupont,Emelia,emelia.io,https://www.linkedin.com/in/marie-dupont-1a2b3c,basile,marie@emelia.io,finder,valid,valid,finder,standard,2026-09-09,+33612345678,FR,mobile,send,found and verified by Emelia
Paul,Martin,Kavia,kavia.fr,https://www.linkedin.com/in/paul-martin-9z8y7x,csv,p.martin@kavia.fr,csv,,invalid,verifier,standard,2026-09-09,,,,drop,would hard bounce
Sofia,Neri,Kotive,kotive.fr,https://www.linkedin.com/in/sofia-neri,basile,sofia.neri@kotive.fr,finder,risky,valid,verifier,standard,2026-09-09,,,,send,risky find verified
Luc,Bernard,Vantia,vantia.fr,,csv,contact@vantia.fr,csv,,valid,verifier,standard,2026-09-09,,,,hold,role mailbox not a person
Julien,Roche,Emelia,emelia.io,,basile,,,not_found,,,,2026-09-09,,,,drop,no reachable channel
```

`verification_source` is the column that proves the rule held: every row that reads
`finder` there is a row you did not pay to check twice.

### `outreach/enrichment.json`

The canonical shape. When a single skill runs alone it writes its own section at the
top level; when the waterfall runs, the sections live under `steps`.

```json
{
  "run": {
    "id": "2026-09-09-1042", "list": "outreach/leads.csv",
    "started_at": "2026-09-09T10:42:11Z", "finished_at": "2026-09-09T11:38:02Z",
    "order": ["find_email", "verify_email", "decide", "find_phone"],
    "note": "find_email and verify_email ran on disjoint sets of rows",
    "stopped_early": false, "stop_reason": null
  },
  "budget": {
    "cap_credits": 300, "spent_credits": 273.0, "remaining_in_cap": 27.0,
    "credits_before": 1250, "credits_after": 977,
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
      "scope": "addresses carried in with the file, plus the risky finds",
      "checked_carried_in": 71, "checked_risky_from_finder": 23,
      "not_checked_because_the_finder_verified_them": 218,
      "credits_not_spent_on_those": 54.5,
      "control_domains_tested": 34,
      "valid": 62, "invalid": 18, "catch_all": 12, "unknown": 2,
      "role_mailboxes": 11, "credits": 32.0
    },
    "find_phone": {
      "eligible": 269, "looked_up": 0, "found": 0, "credits": 0,
      "note": "user declined phones on this run"
    }
  },
  "totals": {
    "rows_in": 412, "rows_never_looked_up": 18, "rows_sent_to_finder": 323,
    "rows_with_a_carried_in_address": 71, "with_email": 312,
    "verified_in_this_run": 94, "verified_by_the_finder": 218,
    "sendable": 269, "on_hold": 23, "dropped": 120, "credits_spent": 273.0
  },
  "decisions": {
    "send": 269, "hold": 23, "drop": 120,
    "send_sources": {
      "found and verified by Emelia": 218,
      "carried in, verified here": 37,
      "risky find, verified": 14
    },
    "hold_reasons": { "catch-all domain unproven": 12, "role mailbox": 11 },
    "drop_reasons": {
      "would hard bounce": 18, "no email found, no reachable channel": 62,
      "no email found, LinkedIn only, not priority": 16,
      "no verdict, not worth the reputation": 2,
      "finder error, not retried": 4,
      "no name or company, never looked up": 18
    }
  },
  "bounce_projection": { "send_group": 0.0, "verdict": "safe to send" },
  "pending_jobs": [],
  "notes": [
    "218 finder results went straight to the send group. Verifying them would have cost 54.5 credits and returned the same verdict.",
    "18 rows had no name or company and were never sent to the finder.",
    "9 of 34 tested domains are catch-all, which is why 12 rows are on hold.",
    "No phone lookups ran. The 269 sendable rows have a LinkedIn URL if you want them."
  ]
}
```

### The spoken summary

```
412 rows in, 269 ready to send (65%), 23 on hold, 120 dropped. 273 credits spent
of a 300 cap, 977 left.

Of the 269: 218 came from the finder already verified, 37 were addresses you
brought that I verified here, 14 were risky finds that verified clean.

The verification pass cost 32 credits instead of 90, because the 218 finder
results were not checked twice. That is 54.5 credits kept.

The 120 dropped are not lost data: 62 had no findable email and no other channel,
18 would have bounced, 18 had no name or company to search on, 16 had a LinkedIn
URL but were not worth a 50 credit lookup, 4 errored, 2 got no verdict. They are
still in leads.csv with their reason.

Bounce projection on the 269: near zero. Ready for outreach-write.
```

Say the percentage. Say what the discipline saved. Never say "the list is enriched".

## Checks before finishing

- A budget cap was set and confirmed before the first paid call, and the run stayed
  under it or stopped and asked.
- The order held: filter, then find and verify on disjoint sets, then decide, then
  phone. No phone lookup ran on a row before its email verdict existed.
- **No address the finder returned as `valid` was sent to the verifier.** Check it in
  the file: no row may have `email_source: finder`, `email_status: valid` and
  `verification_source: verifier` at the same time. Report the count you skipped and
  the credits it saved, in the summary the user reads.
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

**The verifier ran over the whole list.** The classic waterfall reflex, and it looks
like care. Symptom: `verify_email.checked_carried_in` plus
`checked_risky_from_finder` is close to `with_email`, and almost every verdict comes
back valid. It costs 0.25 credit per finder result for an answer you already had.
Stop, do not re-run, and tell the user what it cost so the next run does not repeat
it.

**A step silently produced nothing**, for instance the verifier finding zero rows to
work on because the file has no `email_source` column and every address looks like a
finder result. Zero verifications on a list that carries 71 addresses from a CSV is a
finding, not a clean run. The counters catch it: `checked_carried_in` should equal
`rows_with_a_carried_in_address` minus the malformed and the duplicates.

**No `email_source` column at all**, so you cannot tell a finder result from a
carried-in address. Ask the user where the addresses came from before spending
anything. Do not verify everything "to be safe": that is the expensive assumption.

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
