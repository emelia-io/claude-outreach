---
name: outreach-enrich
description: "The full enrichment waterfall on a lead list: filter first, find the missing emails, verify only the addresses that came from somewhere other than Emelia's finder, find mobile numbers only where they are worth 50 credits, then decide row by row who is sendable, who is on hold and who is dropped. Ends by routing the rows to separate destinations, one list per destination: addresses found go to the email campaign list, rows with no address but a valid LinkedIn profile URL are proposed as a separate LinkedIn campaign, and the rest is set aside and counted. Never pushes a whole enriched base into a single Emelia list. Runs under a credit budget fixed before the first call and stops when it is reached. Writes outreach/enrichment.json with every counter and updates outreach/leads.csv without losing a single original column, then fills the custom fields your sequence needs. Triggers on: enrich, enrichment, enrich my list, waterfall, find and verify, clean and enrich, contact data, credits budget, how much will this cost, prepare my list, custom fields, route the list, split the list, push to Emelia, LinkedIn campaign for the rest."
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

Then it **routes**. An enriched list is not one list: the rows with an address go to
the email campaign, the rows with no address but a real LinkedIn profile are a
different channel, and the rest goes nowhere. Each destination gets its own file and
its own Emelia list. Pushing the whole base into one list is the mistake this step
exists to prevent.

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
`company_domain` (or `website`), `country`, `linkedin_url`, `x_trade_name` if the
source gave one (the finder's third attempt uses it), `email` if some rows already have
one. Map the user's real column names once, at the start, and say what you mapped.

`linkedin_url` matters twice here, so do not treat it as decoration: it is the only
input the phone finder accepts, and it is what decides whether a row with no address
has a second channel or none at all.

An Emelia list id, or permission to create one, before the routing step. Not needed
until then, so ask for it at the end and not at the start.

Missing key, no budget, or no filtered list: say which one is missing and stop. In
dry run, produce the plan and the cost estimate and spend nothing. Dry run still
produces the four destination files, because splitting the rows costs nothing and it
is often the answer the user actually wanted.

## How to do it

### 0. How many rows to enrich

Enrich for the target, not for the list. The finder lands somewhere around half the
rows, so a campaign of 100 contacts means sending **about 250 rows** to enrichment, and
250 is the sensible default when the user asks for a first campaign.

Do not trim that number to save credits. A miss is refunded, the found ones cost about
one credit each, and running short means paying twice: once for the first pass, once for
the rebuild. If the budget genuinely cannot take 250, say what the expected yield is at
the number you can afford, and let the user choose with the figure in front of them.

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
                                    |
                                    +-- route --> email list      (address found)
                                                \ LinkedIn list   (no address, real profile)
                                                \ hold list       (needs a decision)
                                                \ dropped         (counted, not deleted)
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

| Row state | Verdict from | Decision | Destination | Written reason |
|-----------|--------------|----------|-------------|----------------|
| No email, no LinkedIn URL | nothing | `drop` | none | `no reachable channel` |
| Email `invalid`, no LinkedIn URL | verifier, or the finder's own answer | `drop` | none | `would hard bounce` |
| Email `invalid`, LinkedIn URL present | verifier | `drop` for email | `linkedin` | `bad address, real profile` |
| Email `unknown` after two attempts | verifier | `drop` | none | `no verdict, not worth the reputation` |
| Email is a role mailbox (`contact@`, `info@`) | any | `hold` | `hold` | `role mailbox, not a person` |
| Email `valid`, domain known catch-all | verifier | `hold` | `hold` | `catch-all domain, unproven` |
| Email `valid`, returned by the finder | finder | `send` | `email` | `found and verified by Emelia` |
| Email `risky` from the finder, then verified `valid` on a domain that is not catch-all | verifier | `send` | `email` | `risky find, verified` |
| Email `risky` from the finder, not verified | nothing | `hold` | `hold` | `unproven, verify it or drop it` |
| Email `valid`, carried in, domain not catch-all | verifier | `send` | `email` | `verified` |
| No email, LinkedIn profile URL present | nothing | `hold` | `linkedin` | `no address, LinkedIn channel only` |
| No email, only a LinkedIn company page URL | nothing | `drop` | none | `company page, not a person` |

The order of the rows matters: the drops and the holds come first on purpose, so a
role mailbox that verifies valid is held rather than sent.

The two `send` lines that come from the finder are the point of the whole rewrite.
A finder `valid` sends on the finder's own verdict, with no verification call behind
it. Nothing about the row is less proven than a carried-in address you paid to check:
the same kind of check produced both, one of them was just included in the price of
the find.

Write both columns on every row, `send_decision` and `destination`. The decision says
what you concluded, the destination says where the row goes, and step 7 does nothing
but read the second one. A row has exactly one destination: a person who is in the
email list and in the LinkedIn list is a bug, and it is also the fastest way to look
like a machine to that person.

`send` rows go into the campaign. `hold` rows go into a second, smaller batch or into
a different channel, never mixed into the first send. `drop` rows stay in the file
with their reason, so the user can see the cost of their data quality instead of
watching rows disappear.

**Before a row is routed to `linkedin`, check the URL is a person.** Normalise it,
then keep it only if it survives:

- lowercase the host, drop the query string and the trailing slash;
- it must match `https://www.linkedin.com/in/<slug>` with a non empty slug;
- `linkedin.com/company/<slug>` is a company page, not a person: destination none;
- a Sales Navigator link (`/sales/lead/...`) is a seat bound URL that the campaign
  cannot use: try to recover the public `/in/` URL from the source row, otherwise
  destination none;
- an empty slug, a search URL or a `/pub/dir/` link is not a profile;
- deduplicate on the normalised URL, because two rows pointing at the same profile
  would send the same person two connection requests.

Count what each rule removed. "412 rows had no email, 361 had a usable profile URL, 51
had a company page or a Sales Navigator link" is the useful sentence.

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

### 7. Route the rows, one list per destination

**Never push the whole enriched base into a single Emelia list.** This is the rule of
this step and it has three concrete reasons, worth saying to the user once:

1. **A list attached to a running campaign feeds it continuously.** Every contact you
   add enters the campaign on its own. So a row with no address, a role mailbox or a
   catch-all row dropped into the campaign list is not sitting there harmlessly, it is
   queued to be sent to.
2. **Different destinations are different channels.** An email campaign and a LinkedIn
   campaign have different sending accounts, different daily limits and different
   copy. One list cannot feed both.
3. **A mixed list ruins your reading of the results.** A bounce rate that comes from
   unverified rows you should not have added looks exactly like a copy problem, and
   you will spend a week rewriting the wrong thing.

Write one file per destination. These are plain CSVs in `outreach/`, they cost
nothing, and they are what you show the user before anything is created in Emelia:

| File | Who is in it | What happens to it |
|---|---|---|
| `outreach/list-email.csv` | `destination = email` | Becomes the email campaign list. This is the only one that is pushed by default, and still only after the user says yes |
| `outreach/list-linkedin.csv` | `destination = linkedin` | **Proposed** as a separate LinkedIn campaign. Nothing is created until the user asks |
| `outreach/list-hold.csv` | `destination = hold` | Waits for a decision: verify the risky ones, or drop them. Never merged into the email list |
| `outreach/list-dropped.csv` | everything else | Counted, kept with its reason, sent nowhere |

Split further when the copy differs: one list per segment inside the email
destination, because a list is what a campaign consumes and two segments with two
sequences are two campaigns. Name them `list-email-<segment>.csv`.

**The email destination.** Create the list, then add the rows to it, then attach the
list to the campaign. There is no documented REST route that creates a list, so use
the MCP tool `create_list` with a `name`, or create it in the Emelia app and take its
id. Then push with `add_contacts_to_list_bulk` (up to 100 flat contacts per call,
`updateIfExists: true` so a re-run does not duplicate), or one row at a time over
REST as in step 8. Report the `created` / `duplicates` / `updated` / `failed`
breakdown it returns, as it is.

Attaching the list to the campaign is `outreach-campaign`'s job, with
`PATCH /advanced/campaigns/{id}/recipients` and its `lists` and `excludedLists`
fields. Hand over the list id and its name rather than doing it here, and remember
what attaching means: from that moment the list feeds the campaign, so the list you
hand over must contain only rows you are willing to send to today.

Typical shape of that campaign, for context rather than as a decision made here: four
steps, and a freshly created Emelia campaign already carries four empty ones. Five is
reasonable. The step count, the delays and the A/B variants belong to
`outreach-sequence`, not here.

**The LinkedIn destination, which you propose and do not create.** Write the file,
then stop and ask. Something like:

```
361 rows had no email address but a usable LinkedIn profile.

They are in outreach/list-linkedin.csv. They are not in the email campaign and they
never will be: there is no address to send to.

A LinkedIn campaign would reach them, and it is a different exercise: it needs a
LinkedIn account connected in Emelia, it runs at a much lower daily volume than
email, and the sequence is a connection request followed by at most three messages.

Want me to prepare it? (yes / not now / show me 10 of them first)
```

Only if the user says yes: create the LinkedIn campaign with
`POST /linkedin/campaigns` (it takes a `name` and nothing else), then add the contacts.
Watch the field name, because the two LinkedIn routes disagree and a wrong key is a
400 every time:

```bash
# into a LinkedIn list: the profile URL is "url"
curl -s -X POST https://api.emelia.io/linkedin/lists/contacts \
  -H "Authorization: $EMELIA_API_KEY" -H "Content-Type: application/json" \
  -d '{"id":"<linkedinListId>","contact":{"url":"https://www.linkedin.com/in/marie-dupont-1a2b3c",
       "firstName":"Marie","lastName":"Dupont"}}'

# straight into a LinkedIn campaign: the same value is "linkedinUrlProfile"
curl -s -X POST https://api.emelia.io/linkedin/campaign/contacts \
  -H "Authorization: $EMELIA_API_KEY" -H "Content-Type: application/json" \
  -d '{"id":"<linkedinCampaignId>","contact":{"linkedinUrlProfile":"https://www.linkedin.com/in/marie-dupont-1a2b3c",
       "firstName":"Marie","lastName":"Dupont"}}'
```

If the user has no LinkedIn account connected in Emelia, say so, keep the file, and
leave it there. A CSV nobody can use today is still better than a channel you never
mentioned.

**The hold list.** Say what would unlock it and what it would cost: verifying the
risky finds at 0.25 credit each, or dropping them. Do not decide alone, and do not
quietly merge it into the email list because the numbers look better that way.

**The dropped list.** Kept, counted, grouped by reason. It is the data quality report
of the whole run, and it is what tells the user whether to change the source or the
targeting next time.

Whatever you do here, the check is simple: the four files must add up to the row count
that came in, and no `lead_id` may appear in two of them.

### 8. Fill the custom fields the sequence needs

Enrichment is only useful if the values reach the campaign, so do this last, once
the routing exists. Push contacts with their fields into the list attached to the
campaign, which is how a contact enters a running campaign:

```bash
curl -s -X POST "https://api.emelia.io/lists/list/<listId>/contacts/batch?updateIfExists=true" \
  -H "Authorization: $EMELIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contacts":[{"email":"marie@emelia.io","firstName":"Marie",
       "lastName":"Dupont","linkedinUrlProfile":"https://www.linkedin.com/in/marie-dupont-1a2b3c",
       "companyName":"Emelia","icebreaker":"your post on outbound benchmarks"}]}'
```

A hundred contacts per call, 1 MB per body, so chunk the file by 100 and clip long text
to about 4,000 characters before sending. `updateIfExists=true` turns a row that is
already there into an update instead of a duplicate, which is what makes a re-run safe.

Any key that is not a known contact field becomes a custom variable, so `icebreaker`
above is usable as a variable in the sequence. The response returns it under
`createdCustomVariables`, and the `technicalName` there, not your column header, is what
the copy must spell. To set one field on a contact already in a campaign:

```bash
curl -s -X PATCH https://api.emelia.io/advanced/contacts \
  -H "Authorization: $EMELIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"campaignId":"<campaignId>","email":"marie@emelia.io",
       "fieldName":"icebreaker","fieldValue":"your post on outbound benchmarks"}'
```

The single contact route, `POST /advanced/lists/contacts` with
`{"id":"<listId>","contact":{...}}`, exists for adding one person to a list that already
feeds a running campaign. Its published schema lists both `linkedinUrlProfile` and `email`
as required; the server accepts one of the two. Do not use it to load a file, one call per
row spends the whole rate limit of the plan for nothing.

Push only the rows of the destination you are working on. The list you feed here is
the email list from step 7, not `leads.csv`.

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
first_name,last_name,company_name,company_domain,linkedin_url,source,email,email_source,email_status,email_verification,verification_source,email_domain_type,email_verified_at,phone,phone_country,phone_type,send_decision,destination,decision_reason
Marie,Dupont,Emelia,emelia.io,https://www.linkedin.com/in/marie-dupont-1a2b3c,basile,marie@emelia.io,finder,valid,valid,finder,standard,2026-09-09,+33612345678,FR,mobile,send,email,found and verified by Emelia
Paul,Martin,Kavia,kavia.fr,https://www.linkedin.com/in/paul-martin-9z8y7x,csv,p.martin@kavia.fr,csv,,invalid,verifier,standard,2026-09-09,,,,drop,linkedin,bad address but a real profile
Sofia,Neri,Kotive,kotive.fr,https://www.linkedin.com/in/sofia-neri,basile,sofia.neri@kotive.fr,finder,risky,valid,verifier,standard,2026-09-09,,,,send,email,risky find verified
Luc,Bernard,Vantia,vantia.fr,,csv,contact@vantia.fr,csv,,valid,verifier,standard,2026-09-09,,,,hold,hold,role mailbox not a person
Julien,Roche,Emelia,emelia.io,,basile,,,not_found,,,,2026-09-09,,,,drop,,no reachable channel
```

`verification_source` is the column that proves the rule held: every row that reads
`finder` there is a row you did not pay to check twice. `destination` is the column
step 7 reads, and the one that keeps the four output lists disjoint.

### The destination lists

`outreach/list-email.csv`, `outreach/list-linkedin.csv`, `outreach/list-hold.csv` and
`outreach/list-dropped.csv`. Same columns as `leads.csv`, one file per destination,
and their row counts add up to the row count of `leads.csv`. The LinkedIn one carries
the normalised profile URL and nothing about email:

```csv
lead_id,first_name,last_name,full_name,job_title,company_name,company_domain,linkedin_url,segment,decision_reason
basile:66f1a4d071,Paul,Martin,Paul Martin,CTO,Kavia,kavia.fr,https://www.linkedin.com/in/paul-martin-9z8y7x,fr-saas-cto,bad address but a real profile
basile:66f1a51b30,Ines,Fabre,Ines Fabre,Head of Platform,Solveo,solveo.fr,https://www.linkedin.com/in/ines-fabre,fr-saas-cto,"no address, LinkedIn channel only"
```

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
      "no verdict, not worth the reputation": 2,
      "finder error, not retried": 4,
      "no name or company, never looked up": 18
    }
  },
  "routing": {
    "rule": "one list per destination, a row belongs to exactly one",
    "email": {
      "rows": 269, "file": "outreach/list-email.csv",
      "list_id": "66f2b0c1a4", "list_name": "FR SaaS CTO, September",
      "pushed": true, "created": 266, "duplicates": 3, "updated": 0, "failed": 0
    },
    "linkedin": {
      "rows": 61, "file": "outreach/list-linkedin.csv",
      "profile_urls_normalised": 61, "company_pages_rejected": 9,
      "sales_navigator_urls_rejected": 5, "duplicate_profiles_removed": 2,
      "proposed": true, "created_in_emelia": false,
      "note": "waiting for the user, no LinkedIn campaign exists yet"
    },
    "hold": {
      "rows": 23, "file": "outreach/list-hold.csv",
      "unlock_cost_credits": 5.75, "pushed": false
    },
    "dropped": { "rows": 59, "file": "outreach/list-dropped.csv" },
    "checksum": { "in": 412, "email_linkedin_hold_dropped": 412, "overlap": 0 }
  },
  "bounce_projection": { "send_group": 0.0, "verdict": "safe to send" },
  "pending_jobs": [],
  "notes": [
    "218 finder results went straight to the send group. Verifying them would have cost 54.5 credits and returned the same verdict.",
    "18 rows had no name or company and were never sent to the finder.",
    "9 of 34 tested domains are catch-all, which is why 12 rows are on hold.",
    "61 rows with no address have a real LinkedIn profile. Proposed as a separate campaign, nothing created.",
    "No phone lookups ran. The 269 sendable rows have a LinkedIn URL if you want them."
  ]
}
```

### The spoken summary

```
412 rows in, 269 ready to send (65%), 23 on hold, 120 with no address. 273 credits
spent of a 300 cap, 977 left.

Of the 269: 218 came from the finder already verified, 37 were addresses you
brought that I verified here, 14 were risky finds that verified clean.

The verification pass cost 32 credits instead of 90, because the 218 finder
results were not checked twice. That is 54.5 credits kept.

They are not all going to the same place. Four files, no row in two of them:

  outreach/list-email.csv       269   the email campaign, four steps
  outreach/list-linkedin.csv     61   no address, but a real LinkedIn profile
  outreach/list-hold.csv         23   role mailboxes and catch-all domains
  outreach/list-dropped.csv      59   nothing to reach them with

The 269 are in the Emelia list "FR SaaS CTO, September": 266 created, 3 were
already there. Nothing has been sent, the campaign is not started.

The 61 LinkedIn rows are a proposal, not a campaign. They have no email address
and never will, so email is closed for them. A LinkedIn campaign needs an account
connected in Emelia, runs at a much lower daily volume, and its sequence is a
connection request then at most three messages. Want me to prepare it?

The 23 on hold need one decision: 5.75 credits to verify the risky ones, or drop
them. They are not in the campaign either way.

The 59 dropped are not lost data: 37 had no findable email and no profile, 18 had
no name or company to search on, 4 errored. They are still in leads.csv with their
reason.

Bounce projection on the 269: near zero. Ready for outreach-write.
```

Say the percentage. Say what the discipline saved. Say where each group went. Never
say "the list is enriched", and never say "the list is in Emelia" when four different
groups went four different ways.

## Checks before finishing

- A budget cap was set and confirmed before the first paid call, and the run stayed
  under it or stopped and asked.
- The order held: filter, then find and verify on disjoint sets, then decide, then
  phone. No phone lookup ran on a row before its email verdict existed.
- **No address the finder returned as `valid` was sent to the verifier.** Check it in
  the file: no row may have `email_source: finder`, `email_status: valid` and
  `verification_source: verifier` at the same time. Report the count you skipped and
  the credits it saved, in the summary the user reads.
- Every row in `leads.csv` has a `send_decision`, a `destination` and a
  `decision_reason`.
- **The four destination files exist and are disjoint.** Their row counts add up to the
  row count of `leads.csv`, and no `lead_id` appears in two of them. A row in both the
  email list and the LinkedIn list is a bug, not a double chance.
- **Nothing was pushed to Emelia except the email destination**, and only after a yes.
  The LinkedIn list was proposed, not created: check that no `POST /linkedin/campaigns`
  was called unless the user asked for it in this session.
- Every URL in the LinkedIn list is a `linkedin.com/in/<slug>` profile. No company
  page, no Sales Navigator link, no duplicate profile.
- The summary names the four groups with their counts, and says the LinkedIn one is a
  proposal.
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

**Everything went into one Emelia list.** The failure this step exists to prevent, and
it is silent until the campaign runs. Symptoms: the list contact count equals the row
count of `leads.csv`, or the campaign starts sending to rows that have no address, or
the bounce rate on day one is far above the projection. If the list is not attached to
a running campaign yet, delete the rows that do not belong and push the email
destination only. If it is already running, pause the campaign first, then clean the
list, then explain what happened rather than letting the numbers speak.

**A LinkedIn campaign was created without being asked for.** The rule is propose, then
wait. If it was created and nothing has been sent, say so and offer to delete it. If
connection requests went out, they are not reversible, so say that plainly.

**The LinkedIn list is full of company pages.** `linkedin_url` in a sourced list often
holds `linkedin.com/company/<slug>`, because the row's company had a page and the
person did not. Those rows are not reachable on LinkedIn either. Apply the URL rules
of step 4, count what they removed, and do not present a company page count as a reach
number.

**A person is in the email list and the LinkedIn list.** The destination rule was
applied twice, or a duplicate was never merged. Fix the merge, not the symptom: that
person would get an email and a connection request from the same company in the same
week, which is exactly what makes people mark you as spam.

**The hold list was merged into the email list because the numbers looked thin.** A
role mailbox and a catch-all domain do not become safe because you need volume. Send
the 269 you have, and go back to the source for more rows.

## Limits

This skill spends money on the user's behalf, so it does nothing without an explicit
yes and a cap. It cannot recover credits already spent, and it cannot tell you a row
was worth enriching before it enriched it.

It does not build the list, does not filter it, does not write the copy, does not
check your sending setup and does not launch anything. Those are `outreach-leads`,
`outreach-filter`, `outreach-write`, `outreach-deliverability` and
`outreach-campaign`.

It routes, it does not launch. It creates the email list and fills it when you say so,
and it stops there: the sequence, the schedule and the start belong to
`outreach-sequence` and `outreach-campaign`. The LinkedIn destination is only ever a
proposal here, and creating that campaign needs a LinkedIn account connected in Emelia,
which this skill cannot check for you.

It cannot make a bad list good. If 60% of the rows drop out, the problem is upstream:
the targeting, the source, or the column mapping. Say that instead of running the
waterfall twice.
