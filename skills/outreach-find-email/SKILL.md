---
name: outreach-find-email
description: "Find professional email addresses for the people on a lead list, one at a time or in bulk, with Emelia's email finder. Takes a full name plus a company name or domain, states the credit cost before spending anything, polls each job to completion, and records what was found and what was not in outreach/enrichment.json and outreach/leads.csv. Never guesses an address pattern and calls it found. Triggers on: find email, email finder, find emails, find the email of, email address, email lookup, email enrichment, enrich emails, missing emails, bulk email finder, get emails for my list."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Find professional emails

## What this does

Turns rows that have a name and a company into rows that have a professional email
address, using Emelia's email finder. It counts the rows and states the credit cost
before spending anything, runs the lookups, and reports the discovery rate honestly:
found, not found, still running. It does not invent addresses: when the finder
returns nothing, the row is marked `not_found`, not filled with a guess.

## When to use it

Use it when you have a list with names and companies but no email addresses, or when
a list has holes you want filled before writing a sequence.

Use a different skill when:

- The list is not filtered yet. Run `outreach-filter` first: every credit spent on a
  row you are about to exclude is wasted, and this is the most common way people burn
  their balance.
- You already have addresses and want to know whether they will bounce
  (`outreach-verify`).
- You want the whole waterfall under one budget (`outreach-enrich`, which calls this
  skill).
- You want a mobile number (`outreach-find-phone`, which costs far more).

## Inputs

Per row, the finder needs two things:

| Field | Required | Notes |
|-------|----------|-------|
| `fullname` | yes | First and last name in one string, as the person writes it. `"Marie Dupont"`, not `"MARIE DUPONT"` and not `"Dupont, Marie"`. |
| `companyName` | yes | The trading name, not the legal name. `"Emelia"`, not `"EMELIA SAS"`. |
| `companyWebsite` | no, but send it | The company domain or site. This is the single biggest accuracy lever. `"emelia.io"` or `"https://emelia.io"` both work. |
| `country` | send it always | ISO 2 letter code (`FR`, `US`, `DE`). See the trap below. |

**The country trap.** The published request schema marks `country` as optional, and
the API validator requires it: a call without it comes back as a 400 and no job is
created. Always send it. If you do not know the country, infer it from the domain
extension or the company address, and say in your summary which rows you inferred.

Files: `outreach/leads.csv` in (ask for a CSV path or run `outreach-leads` first if
it is missing), `outreach/leads.csv` and `outreach/enrichment.json` out.

Access: `EMELIA_API_KEY` exported in the shell. The REST API is the documented path
and this skill assumes it. If the Emelia MCP server is also configured, its
`find_email` tool wraps the same two calls and does the polling for you. With
neither, say so and run in dry run: you still produce the row count and the cost
estimate, and you spend nothing.

If you only have a LinkedIn URL for a person, this finder cannot use it. It needs a
name and a company. Take them from the list row, and if they are not there, ask the
user rather than deriving a name from a profile slug.

## How to do it

### 1. Count, then quote the cost, then wait

Never start a bulk run without this step.

At the time of writing, Emelia bills the email finder **1 credit per address
actually found**. The credit is taken when the job starts and given back when the
job ends with nothing, so a miss is free and a hit costs one. Confirm the current
rate on your plan page in the Emelia app before a large run, since pricing can
change.

Print this and stop:

```
Email finder on outreach/leads.csv

  Rows in the file            412
  Already have an email        71   skipped
  Missing name or company      18   skipped, listed below
  To look up                  323

  Cost: 1 credit per address found, nothing for a miss.
  Worst case 323 credits, realistic range 180 to 240 at a 55 to 75% hit rate.
  Your balance: 1,250 credits.

Run it? (yes / no / a smaller sample)
```

Offer a 25 row sample when the list is above 200 rows and has never been run. The
sample buys you the real hit rate on this data for about 15 credits, and that number
drives every later estimate.

### 2. One lookup

Two REST calls: create the job, then poll it.

```bash
curl -s -X POST https://api.emelia.io/tools/find/email \
  -H "Authorization: $EMELIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fullname":"Marie Dupont","companyName":"Emelia","companyWebsite":"emelia.io","country":"FR"}'
# {"success":true,"jobId":"66f0c3..."}

curl -s https://api.emelia.io/tools/find/email/66f0c3... \
  -H "Authorization: $EMELIA_API_KEY"
# {"success":true,"data":{"fullname":"Marie Dupont","companyName":"Emelia",
#   "email":"marie@emelia.io","qualification":"valid","status":"done","date":"..."}}
```

Poll the GET every 2 to 3 seconds. Do not poll faster: it burns your request quota
without making the job finish sooner.

If the MCP server is configured, one call does both:

```
find_email
  fullname: "Marie Dupont"
  companyName: "Emelia"
  companyWebsite: "emelia.io"
  country: "FR"
```

It posts the job, polls it every 2 seconds for up to 90 seconds, and returns the same
`data` object. Same fields in, same fields out, one call instead of a loop.

### 3. Read the result properly

The result carries two different fields and people confuse them constantly.

`status` is about the job:

| status | Meaning | What to do |
|--------|---------|------------|
| `running` | Not finished | Keep polling. Emelia queries one source, and when that source returns nothing usable it tries a second one, so a single lookup can legitimately run for two to four minutes. |
| `done` | Finished | Read `email` and `qualification`. |
| `error` | The job failed | No address. Retry once, then mark the row `error` and move on. Do not loop. |

`qualification` is about the address:

| qualification | Meaning | Treat as |
|---------------|---------|----------|
| `valid` | The address checks out | Found |
| `risky` | Returned by the second source when its confidence is below "sure" | Found but unproven. Verify it with `outreach-verify` before sending. |
| `invalid` | No usable address | Not found |

Two more cases that are not qualifications:

- `status: "done"` with no `email` field: not found. This is the common miss.
- The MCP tool returns `{"jobId": "...", "status": "running", "note": "..."}`: the
  job outlived its 90 second wait. It is still running on Emelia's side. Keep the
  `jobId` and come back to it later, with a plain `GET /tools/find/email/{jobId}` or
  with the MCP tool built for it:

```
get_enrichment_result
  type: "find_email"
  jobId: "66f0c3..."
```

Never restart a lookup because it timed out in your client. You would pay twice for
the same person.

### 4. Bulk: the loop

There is no bulk endpoint. Bulk means running the single lookup once per row, so
the loop is where the discipline lives.

1. Build the work list: rows that passed the filter, have a name and a company, and
   have no email yet. Nothing else.
2. Deduplicate on name plus domain. The same person appearing twice costs twice.
3. Sort by company so all rows for one domain sit together. That makes the pattern
   check in step 5 possible and partial results readable.
4. Run one lookup at a time, or at most three in parallel, at roughly one new job per
   second. Your plan's ceiling is 100 requests per minute on Start, 300 on Grow,
   1,000 on Scale, 30 with no subscription, and each lookup is a POST plus several
   GETs.
5. Append each result to `outreach/enrichment.json` as it lands, so an interrupted
   run keeps everything already paid for.
6. Every 50 rows, print one progress line: done, found, not found, credits spent.
7. On a credit error (HTTP 402, or a message containing "credits"), stop the loop, do
   not retry, and say where the run stopped.
8. On HTTP 429, wait 60 seconds and resume from the same row. Do not drop the row.

Jobs still `running` at the end of the loop go into a `pending` array with their
`jobId`. Collect them with `get_enrichment_result` before you write the summary.

### 5. What to do with the misses

A miss is information, not a failure. Report it, do not hide it.

**Never do this:** see `marie@emelia.io` and `paul@emelia.io` in the results and
write `julien@emelia.io` into `leads.csv` as if the finder returned it. A guessed
address that bounces costs you sender reputation, which is worth far more than the
credit you saved.

**You may do this, with the user's agreement.** When a domain has at least five found
addresses and at least four share the same shape (`first@`, `first.last@`, `f.last@`,
`firstlast@`), you have an observed pattern for that domain. For a missing person on
that same domain:

1. Build the candidate address from the pattern.
2. Verify it with `outreach-verify` (a quarter of a credit, charged either way).
3. Accept it only when the verification says `valid` **and** the domain is not
   catch-all. On a catch-all domain the verification proves nothing, so the candidate
   stays a guess and is dropped.
4. Write it with `email_source: pattern_verified`, never `finder`, so the user can
   filter those rows out later if a reply comes back wrong.

Show the pattern and the candidates, and ask before verifying. Rows where the pattern
is unclear stay `not_found`.

### 6. Realistic hit rates

Rules of thumb, not measured Emelia figures. Use them to sanity check a run, not to
promise a number to a client.

| Input quality | Expect |
|---------------|--------|
| Full name plus company domain, company has 10 or more people and its own mail domain | 55 to 75% |
| Full name plus company name only, no domain | 15 to 20 points lower |
| Micro companies, sole traders, generic mailboxes (gmail, orange, free) | under 40% |
| Names from a scrape with initials, accents stripped, or the company field holding a legal name | much lower, and the input is the problem |

If a 200 row run comes back under 30%, stop and look at the input before spending
more. Nine times out of ten it is a bad `companyName` column (legal names, holding
companies, agency names) or a country you did not send.

## Output

Two files. `outreach/leads.csv` gains columns and keeps every original column in its
original order. `outreach/enrichment.json` holds the detail and the cost.

`leads.csv`, after the run:

```csv
first_name,last_name,company_name,company_domain,job_title,source,email,email_status,email_source,email_job_id
Marie,Dupont,Emelia,emelia.io,Head of Growth,basile,marie@emelia.io,valid,finder,66f0c3a1
Paul,Martin,Emelia,emelia.io,CTO,basile,paul@emelia.io,valid,finder,66f0c3a2
Julien,Roche,Emelia,emelia.io,VP Sales,basile,,not_found,,66f0c3a3
Sofia,Neri,Kotive,kotive.fr,CEO,basile,sofia.neri@kotive.fr,risky,finder,66f0c3a4
```

`outreach/enrichment.json`, the slice this skill owns:

```json
{
  "run": {
    "id": "2026-09-08-1042",
    "step": "find_email",
    "list": "outreach/leads.csv",
    "started_at": "2026-09-08T10:42:11Z",
    "finished_at": "2026-09-08T11:09:44Z"
  },
  "cost": {
    "rate_at_run_time": "1 credit per address found, refunded on a miss",
    "credits_spent": 241,
    "credits_before": 1250,
    "credits_after": 1009
  },
  "counts": {
    "rows_in": 412,
    "skipped_already_had_email": 71,
    "skipped_missing_input": 18,
    "looked_up": 323,
    "found_valid": 218,
    "found_risky": 23,
    "not_found": 78,
    "error": 4,
    "pending": 0
  },
  "rates": { "discovery": 0.746, "note": "241 of 323 looked up" },
  "not_found_rows": [12, 19, 44, 51],
  "pattern_candidates": [
    { "domain": "emelia.io", "pattern": "first@", "observed_on": 6, "rows": [51] }
  ],
  "notes": [
    "18 rows had no company name and were never sent to the finder.",
    "4 jobs ended in error and were not retried a second time."
  ]
}
```

When `outreach-enrich` runs the waterfall it owns this file, and this skill writes
into its `find_email` section instead of replacing it. Then say it in words:

```
323 rows looked up, 241 addresses found (74.6%), 78 not found, 4 errors.
241 credits spent. 23 of the 241 came back risky and are not safe to send until
verified.
```

## Checks before finishing

- The cost was stated and the user said yes before the first paid call.
- Every row of `leads.csv` still has its original columns, in their original order,
  with their original values. Nothing was reordered or dropped.
- No address in the file came from a pattern unless it was verified and marked
  `email_source: pattern_verified`.
- Found plus not found plus errors plus pending equals the number of rows looked up.
  If it does not, a result was lost, so go and fetch it by `jobId`.
- No job is left in `running`. Every `jobId` was either resolved or listed as pending
  with instructions to collect it.
- The summary states the discovery rate as a percentage, not as "the list is
  enriched".
- `credits_spent` in the JSON matches the difference in the account balance, or the
  gap is explained.

## Failure modes

**400 with a validation message.** Almost always the missing `country`, sometimes an
empty `fullname` or `companyName` after trimming. Fix the input and retry; no credit
was taken because no job was created.

**401.** The API key is wrong or disabled. Generate a new one in the Emelia app under
Settings then API. Nothing else in this skill will work until this is fixed.

**402, or an error mentioning credits.** The balance is empty. Stop the loop, report
how many rows were done and where to resume. Do not retry: the balance will not refill
by itself.

**429.** Over your plan's request ceiling. Wait 60 seconds, resume from the same row,
slow the loop down.

**Job stuck in `running`.** Normal beyond 90 seconds because of the second source.
Keep the `jobId` and come back to it. Still running after 15 minutes: record it as
pending and tell the user, do not resubmit.

**A high not-found rate on one domain.** Usually the domain is wrong (a redirect, a
holding company, an agency site). Check one company by hand before spending more.

**A role mailbox comes back** (`contact@`, `info@`, `sales@`). Keep it, mark it, and
do not treat it as a personal address in the copy: a first name variable on a shared
mailbox is what makes cold email look automated.

**Names with particles or two surnames** (`de la Fuente`, `Van den Berg`). Send the
name exactly as it appears in the source: do not normalise it, do not strip accents.

## Limits

This skill finds business addresses. It does not confirm the person still works
there, and a leaver's address can stay technically valid for months, so `valid` is
not a promise that anyone will read it.

It cannot use a LinkedIn URL as input: the finder takes a name and a company. It does
not find personal addresses and should not be pointed at consumer domains. It cannot
tell you whether a domain is catch-all, which is the verifier's job, and until you
run it a found address on a catch-all domain is unproven.

It does not send anything, does not add anyone to a campaign, and does not decide who
is worth contacting.
