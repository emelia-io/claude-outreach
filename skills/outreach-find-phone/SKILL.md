---
name: outreach-find-phone
description: "Find direct mobile numbers for the people on a lead list with Emelia's phone finder, from their LinkedIn profile URL, one at a time or in bulk. States the credit cost before spending, polls each job to completion, handles found and not found honestly, and writes the numbers into outreach/leads.csv and outreach/enrichment.json. Emelia does not place the calls: the number goes to your phone or your CRM. Triggers on: find phone, phone finder, find mobile, mobile number, direct dial, phone number, cell number, find the number of, phone enrichment, cold call list, get phone numbers."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Find direct mobile numbers

## What this does

Turns a LinkedIn profile URL into a direct mobile number, using Emelia's phone
finder. It counts the rows, states the credit cost before spending anything, runs
the lookups, and reports found and not found without rounding either up.

The number is data. Emelia does not dial it, does not record calls, and does not run
a dialler. You call from your own phone, or you push the number into your CRM and
your team calls from there.

## When to use it

Use it when a segment is worth a call: high value accounts, a warm reply that went
quiet, an executive who never answers email, a market where email is weak.

Do not use it as a default step on a whole list. A mobile costs roughly fifty times
what an email costs, so a phone run on 500 rows is a budget decision, not a
formality. Enrich the top slice, not the list.

Use a different skill when:

- The list is not filtered. `outreach-filter` first, always.
- You want email addresses. That is `outreach-find-email`, and it is far cheaper.
- You want the full waterfall with one budget for the run. That is
  `outreach-enrich`, which calls this skill last and only on the rows you flagged.

## Inputs

The finder takes exactly one input.

| Field | Required | Notes |
|-------|----------|-------|
| `linkedinUrl` | yes | A public LinkedIn profile URL: `https://www.linkedin.com/in/<slug>`. |

There is no name plus company path for phones. If a row has no LinkedIn URL, it
cannot be looked up. Say so, and count those rows separately in the summary.

URL shapes that work and do not work:

- `https://www.linkedin.com/in/marie-dupont-1a2b3c` works. This is the shape to use.
- `linkedin.com/in/marie-dupont-1a2b3c` works, but add the scheme yourself so the
  row is unambiguous later.
- A Sales Navigator lead URL (`.../sales/lead/ACwAAA...`) is not a profile URL. Get
  the public profile URL first, in the source data or through `outreach-leads`.
- A company page URL is not a person. Skip the row.

Files: `outreach/leads.csv` in, `outreach/leads.csv` and
`outreach/enrichment.json` out.

Access: `EMELIA_API_KEY` exported in the shell. The REST API is the documented path
and this skill assumes it. If the Emelia MCP server is also configured, its
`find_phone` tool wraps the same two calls. Without either, run in dry run: count the
eligible rows, quote the cost, spend nothing.

## How to do it

### 1. Count, quote, wait for a yes

At the time of writing, Emelia bills the phone finder **50 credits per number
actually found**. The credits are taken when the job starts and given back when the
job ends `not_found`, so a miss is free and a hit is expensive. Confirm the current
rate on your plan page before a large run.

Print this and stop:

```
Phone finder on outreach/leads.csv

  Rows in the file            412
  No LinkedIn URL             147   cannot be looked up
  Already have a phone          6   skipped
  Eligible                    259

  Cost: 50 credits per number found, nothing for a miss.
  Worst case 12,950 credits. At a realistic 25 to 40% hit rate,
  expect 3,200 to 5,200 credits.
  Your balance: 6,000 credits.

That is most of your balance for 259 rows. Two other options:
  - the 40 rows flagged "priority" in the list: 500 to 800 credits
  - a 20 row sample to measure your real hit rate: about 300 credits

Which one?
```

Always offer the smaller option when the full run is over a quarter of the balance.
This is the step where users lose money they did not mean to spend.

### 2. One lookup

Two REST calls: create the job, then poll it every 2 to 3 seconds.

```bash
curl -s -X POST https://api.emelia.io/tools/find/phone \
  -H "Authorization: $EMELIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"linkedinUrl":"https://www.linkedin.com/in/marie-dupont-1a2b3c"}'
# {"success":true,"jobId":"66f0d1..."}

curl -s https://api.emelia.io/tools/find/phone/66f0d1... \
  -H "Authorization: $EMELIA_API_KEY"
# {"success":true,"data":{"linkedinUrl":"https://www.linkedin.com/in/marie-dupont-1a2b3c",
#   "phoneNumber":"+33612345678","country":"FR","qualification":"found",
#   "status":"done","date":"..."}}
```

If the MCP server is configured, one call does both:

```
find_phone
  linkedinUrl: "https://www.linkedin.com/in/marie-dupont-1a2b3c"
```

It posts the job, polls it for up to 90 seconds, and returns the same `data` object.

### 3. Read the result

| Field | Values | Meaning |
|-------|--------|---------|
| `status` | `running`, `done`, `error` | The job. `error` means no result, retry once at most. |
| `qualification` | `found`, `not_found` | The number. There is no middle value here, unlike the email finder. |
| `phoneNumber` | E.164 string | Present only when `found`. |
| `country` | ISO 2 letter code | The country the number belongs to, present when `found`. |

**Phone jobs finish later than email jobs.** The result arrives at Emelia through a
callback from the data provider, so the job can sit in `running` well past the 90
seconds an MCP call waits. A result of
`{"jobId": "...", "status": "running", "note": "..."}` is normal here. Keep the
`jobId` and collect it later, with a plain `GET /tools/find/phone/{jobId}` or with
the MCP tool built for it:

```
get_enrichment_result
  type: "find_phone"
  jobId: "66f0d1..."
```

Never resubmit a lookup because your client stopped waiting. A second submission on
the same profile is charged again, even when Emelia already has the number: results
are cached on the server side, and a cached hit is still billed. One lookup per
person, ever. This is why you write every result to disk as it arrives.

### 4. Bulk: the loop

There is no bulk endpoint. Bulk is the single lookup repeated, so the loop carries
the discipline.

1. Build the work list: filtered rows, with a LinkedIn profile URL, with no phone
   number yet, and inside the segment the user approved. Nothing else.
2. Deduplicate on the profile slug (the part after `/in/`), not on the full URL.
   The same person with and without a trailing slash or a `?` tracking parameter is
   one person and must cost you one lookup.
3. Run one lookup at a time, or at most three in parallel. Roughly one new job per
   second. Your plan's ceiling is 100 requests per minute on Start, 300 on Grow,
   1,000 on Scale, and 30 with no subscription.
4. Write every result to `outreach/enrichment.json` as it arrives, before moving to
   the next row.
5. Because results come back late, run the loop in two passes: submit and collect
   what is ready, then come back for the `jobId` values still running. Two minutes
   between passes is enough in most cases.
6. Print a progress line every 25 rows: done, found, not found, credits spent.
7. On a credit error (HTTP 402, or a message mentioning credits), stop. Report where
   you stopped. Do not retry.
8. On HTTP 429, wait 60 seconds and resume from the same row.

Set a hard stop before you start: a number of credits, not a number of rows. When
the running total reaches it, stop the loop, write the file, and report. Ask before
going further.

### 5. Mobile or landline, and what the number is worth

The API returns a number and its country. It does not return a line type, so treat
"this is a mobile" as something you check, not something you were told.

- The finder targets direct mobile numbers, which is the point: a switchboard number
  is not worth 50 credits.
- In France, a mobile starts `+336` or `+337`. Anything starting `+331` to `+335` or
  `+339` is a landline or a special number.
- In most of Europe the mobile prefix is distinct in the same way (`+447` in the UK,
  `+3936` in Italy, `+491` in Germany).
- In North America there is no prefix that separates mobile from landline. A `+1`
  number cannot be classified from its digits. Say so rather than guessing.

Write `phone_type` as `mobile` when the prefix proves it, `unknown` when it does
not. Never write `mobile` because you assume it.

Two rules for what happens next:

- Numbers go to a human or to a CRM, not to an autodialler you built in a script.
- Cold calling rules differ from email rules. In France, check the Bloctel opt-out
  list before calling consumers, and prefer the professional line. `outreach-compliance`
  covers the market you are calling.

### 6. Realistic hit rates

Rules of thumb, not measured Emelia figures.

| Population | Expect |
|------------|--------|
| French and European B2B profiles with a complete LinkedIn page | 25 to 40% |
| US profiles | usually a few points higher |
| Executives of large groups, public sector, regulated industries | 10 to 20% |
| Sparse profiles, no recent activity, no current employer | low, and the profile is the reason |

If a 50 row sample comes back under 10%, the segment is not a phone segment. Say
that plainly and stop, rather than spending another 10,000 credits to prove it.

## Output

`outreach/leads.csv` keeps every original column and gains four:

```csv
first_name,last_name,company_name,linkedin_url,source,phone,phone_country,phone_type,phone_status
Marie,Dupont,Emelia,https://www.linkedin.com/in/marie-dupont-1a2b3c,basile,+33612345678,FR,mobile,found
Paul,Martin,Emelia,https://www.linkedin.com/in/paul-martin-9z8y7x,basile,,,,not_found
Sofia,Neri,Kotive,https://www.linkedin.com/in/sofia-neri,basile,+15125550142,US,unknown,found
Julien,Roche,Emelia,,basile,,,,no_linkedin_url
```

`outreach/enrichment.json`, the slice this skill owns:

```json
{
  "run": {
    "id": "2026-09-08-1530",
    "step": "find_phone",
    "list": "outreach/leads.csv",
    "segment": "priority accounts",
    "started_at": "2026-09-08T15:30:02Z",
    "finished_at": "2026-09-08T15:58:40Z"
  },
  "cost": {
    "rate_at_run_time": "50 credits per number found, refunded on a miss",
    "budget_credits": 2000,
    "credits_spent": 1650,
    "credits_before": 6000,
    "credits_after": 4350,
    "stopped_on_budget": false
  },
  "counts": {
    "rows_in": 412,
    "skipped_no_linkedin_url": 147,
    "skipped_already_had_phone": 6,
    "eligible": 259,
    "looked_up": 96,
    "found": 33,
    "not_found": 62,
    "error": 1,
    "pending": 0
  },
  "rates": { "discovery": 0.344, "note": "33 of 96 looked up" },
  "line_types": { "mobile": 27, "unknown": 6 },
  "notes": [
    "Run limited to the 96 rows tagged priority, agreed with the user.",
    "163 eligible rows were not looked up and are still available.",
    "6 US numbers cannot be classified as mobile or landline from the prefix."
  ]
}
```

Then say it in words:

```
96 lookups, 33 numbers found (34.4%), 62 not found, 1 error. 1,650 credits spent,
4,350 left. 27 are certainly mobiles, 6 US numbers cannot be classified.
163 eligible rows were not touched.
```

## Checks before finishing

- The cost was stated, with a smaller alternative when the run was large, and the
  user said yes before the first paid call.
- Every eligible row was looked up at most once. No profile slug appears twice in
  the job log.
- `leads.csv` keeps every original column, in order, unchanged.
- No number was written for a row whose job returned `not_found`. An empty cell is
  the correct answer.
- `phone_type` says `mobile` only where the prefix proves it.
- No `jobId` is left unresolved without being listed as pending.
- The summary gives the hit rate, the credits spent, and how many eligible rows were
  deliberately not touched.

## Failure modes

**400 on submission.** The URL is not a profile URL: a Sales Navigator lead link, a
company page, a search results page, or an empty string. Fix the input. No credits
were taken because no job was created.

**402, or an error mentioning credits.** The balance cannot cover the next lookup.
Stop the loop and report the resume point. At 50 credits a hit, this arrives faster
than people expect.

**429.** Over the plan's request ceiling. Wait 60 seconds and resume from the same
row.

**Everything stuck in `running`.** Expected for this tool, not a bug. Collect with
`get_enrichment_result` in a second pass. If a job is still running after 30
minutes, record it as pending and tell the user. Never resubmit.

**A number found for the wrong person.** Happens when the profile URL in the row was
copied from a search result and does not belong to the person named on the row.
Check the profile slug against the name before you call. If they disagree, drop the
number rather than calling a stranger.

**A number that looks like a switchboard** (ends in several zeros, matches the
company's public number). Keep it, mark `phone_type: unknown`, and do not present it
to the user as a direct line.

**The user asks you to call.** Refuse politely: this skill produces numbers, it does
not place calls, and no part of this repository does.

## Limits

This skill does not call anyone, does not send SMS, does not connect to a dialler,
and does not check a number against a do-not-call register. It cannot tell you
whether a number is still in service, and it cannot classify a North American number
as mobile or landline.

It cannot work without a LinkedIn profile URL: there is no name plus company path
for phones.

A found number is a number the data provider associated with that profile. It is not
a promise that the person will answer, that it is their work phone, or that they are
happy to be called. Treat it accordingly, and say so to the user.
