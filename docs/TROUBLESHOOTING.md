# Troubleshooting

The failures people actually hit, in the order they usually hit them. Each one
starts with how to tell it apart from the failure it looks like.

| What you see | Go to |
|---|---|
| `401`, "Invalid or disabled Emelia API key" | [The key is refused](#the-key-is-refused) |
| `429`, `402`, "Rate limit exceeded", "Not enough credits" | [Quota and rate limits](#quota-and-rate-limits) |
| A find or verify that returns `status: running` and stays there | [An enrichment job that never finishes](#an-enrichment-job-that-never-finishes) |
| The campaign exists in Emelia but sends nothing | [The campaign will not start](#the-campaign-will-not-start) |
| Delivered, opened by nobody, replies at zero | [Emails going to spam](#emails-going-to-spam) |
| Recipients received a literal `{{first_name}}` | [Variables that did not resolve](#variables-that-did-not-resolve) |
| 12,000 rows in, 0 rows out | [An empty list after filtering](#an-empty-list-after-filtering) |

---

## The key is refused

**Emelia REST** answers `401`. **The Emelia MCP server** says "Invalid or disabled
Emelia API key. Generate one in the Emelia app (Settings, API) and reconnect."
**Basile** answers `401` with `{"error": "Unauthorized"}`.

A different message, `Missing Emelia API key`, with JSON-RPC code `-32001`, means the
header never arrived. That is a configuration problem, not a bad key.

Work down this list, it is ordered by how often each one is the answer.

1. **The variable is empty in the shell Claude Code is running in.**

   ```bash
   echo ${#EMELIA_API_KEY}     # prints the length, not the key
   ```

   Zero means the export never reached this process. Exporting a key in one terminal
   does not affect a Claude Code started from another. Restart it from a shell where
   the variable exists.

2. **The key has whitespace or quotes in it.** A copy and paste that caught a
   trailing newline, or a value stored as `"sk_live_..."` with the quotes included.
   Re-export it, and check the length looks like a key rather than a key plus two.

3. **The key was regenerated.** Emelia keys are shown once. If someone rotated it,
   every old copy is dead. Create a new one at
   [app.emelia.io/settings/api](https://app.emelia.io/settings/api).

4. **The wrong key is in the header.** A Basile key sent to `api.emelia.io` gives a
   clean `401` with no hint that it is the wrong service. Check which variable each
   call is using.

5. **`Bearer` where a raw key is expected.** Emelia accepts the raw key, `Bearer
   <key>`, or `X-Api-Key`. Basile accepts the raw key only, with no prefix, so
   `Authorization: Bearer sk_live_...` fails there.

Confirm the fix with a call that costs nothing:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://api.emelia.io/advanced/campaigns \
  -H "Authorization: $EMELIA_API_KEY"
```

---

## Quota and rate limits

Two different problems with similar codes. Read the message, not just the status.

### Too many requests per minute

Emelia answers `429` and the MCP server says the rate limit was reached. The limit
is per key on a rolling sixty second window: 30 with no subscription, 100 on Start,
300 on Grow, 1,000 on Scale.

Basile answers `429` with `rate_limit_exceeded` and a `Retry-After` header in
seconds. Respect it.

What to do:

- Wait sixty seconds. Do not retry immediately, it extends the window.
- Halve the concurrency and continue.
- **Never retry a POST that may have started a job.** A retried
  `POST /tools/find/email` starts a second job and bills a second credit. Poll the
  `jobId` you already have.

Why it happens more than you expect: polling counts. One enrichment is a POST plus a
GET every two seconds until the job finishes, so a slow row can cost fifteen
requests. Divide your limit by fifteen for a safe number of rows in flight: 2 with no
subscription, 6 on Start, 20 on Grow, 60 on Scale.

### Out of credits

Emelia answers `402`, or an error message mentioning credits, typically "You do not
have enough credits to perform this action". Nothing was found and nothing more will
be until the balance is topped up. Stop the batch rather than retrying it row by row:
a hundred rows against an empty balance is a hundred failures and ten wasted minutes.

Worth knowing before you argue with an invoice: **the credit is taken when the job
starts, not when it succeeds.** A find that comes back `invalid` or `not_found` cost
the same as one that found somebody. That is why filtering first, and skipping rows
that can never be found, is where the money is saved.

Basile has three of these and they mean different things:

- `402 quota_exhausted`: the plan's record quota is spent. It is returned **before**
  any record, so nothing was delivered and nothing was charged.
- `402 subscription_required`: page 1 of a search works without a subscription, page
  2 does not.
- `429 export_limit_reached`: the monthly export quota, not the per minute limit.

### Spending less next time

- Count before you extract. Basile counting (`countOnly: true`) is free and
  unlimited, and it is the whole reason the sourcing step asks you before extracting.
- Filter before you enrich. Every row the filter drops is a credit not spent. Running
  the two in the wrong order is the single most expensive mistake available here.
- Do not enrich a row that cannot be enriched: no company name means the email finder
  has nothing to work with, no LinkedIn URL means the phone finder cannot run at all.
  Those rows are skipped, not attempted, and skipping is free.

---

## An enrichment job that never finishes

Enrichment is asynchronous. `POST /tools/find/email` returns a `jobId`, and the
result arrives on `GET /tools/find/email/{jobId}` once `status` stops being
`running`. Same shape for `/tools/find/phone` and `/tools/verify/email`.

**A job still running after ninety seconds is normal, not a failure.** The MCP tools
wait ninety seconds and then hand back `status: "running"` with the `jobId` so you
are not blocked. Pick it up later:

```
get_enrichment_result { type: "find_email", jobId: "..." }
```

or, on REST:

```bash
curl -s https://api.emelia.io/tools/find/email/$JOB -H "Authorization: $EMELIA_API_KEY"
```

What to do, in order:

1. **Do not start the job again.** Re-POSTing bills a second credit and gives you a
   second job that will finish no faster.
2. **Poll it twice, a minute apart.** Uncommon domains and catch-all mail servers
   take longer, because the finder has more to check.
3. **Move on and come back.** Leave the row in `pending_jobs` in
   `outreach/enrichment.json`, finish the batch, then collect the stragglers.
4. **If it is still running after several minutes**, treat it as not found for the
   purposes of the campaign, keep the `jobId`, and check it later. The credit is
   spent either way, and reporting the row as not found is honest.

**Keep your job ids.** If you lose a `jobId` you cannot recover the result and the
credit is gone. `outreach/enrichment.json` stores them for exactly this reason, which
is also why you should not delete it after a run.

---

## The campaign will not start

Go through these in order. The first one is the answer far more often than the rest
put together.

1. **The campaign has no steps.** `POST /advanced/campaigns` creates a campaign with
   a name and nothing else. Steps, delays, schedule and sending accounts are built in
   the Emelia app. A campaign with no steps is a valid campaign that sends nothing,
   and it looks exactly like a broken one. Build the sequence in the app, then start
   it.

2. **The contacts went into a list the campaign does not use.** Adding a contact to a
   list only feeds a campaign when that list is attached to it. Check what the
   campaign is actually reading: `get_campaign` returns `recipients.lists` and
   `recipients.excludedLists`, each with an id, a name and a contact count. If your
   list is in `excludedLists`, that is working as configured.

3. **No sending account, or a disconnected one.** `list_email_providers` with
   `disconnectedOnly: true` finds dead accounts in one call. A disconnected provider
   sends nothing and reports no error.

4. **The schedule.** A campaign outside its sending window, in a timezone you did not
   mean, or with no working days selected, waits quietly. Check the schedule in
   `get_campaign` before assuming anything is broken.

5. **The contacts were duplicates.** Adding a contact whose email or LinkedIn URL is
   already in the list does not create a second one: the response returns the
   existing `leadId` with `duplicate: true`. That is not an error, and it means your
   thousand new contacts may have been three. Read the `created`, `duplicates`,
   `updated` and `failed` counts that bulk adds return, and pass `updateIfExists` when
   you meant to update.

6. **The address is blacklisted.** A previous unsubscribe or a manual entry on the
   blacklist stops that contact silently. Check with the blacklist endpoint before
   concluding the campaign is broken.

7. **The deliverability gate said NO GO.** In that case nothing is broken and nothing
   started, on purpose. Read `outreach/deliverability.md`.

---

## Emails going to spam

Diagnose in this order. Fixing the content of an email that fails authentication is
wasted work, and it is the most common wasted work in outbound.

**1. Authentication.** Check what is actually published, not what you remember
setting up.

```bash
dig +short TXT acme.fr | grep spf1
dig +short TXT google._domainkey.acme.fr
dig +short TXT _dmarc.acme.fr
```

- Two SPF records is a hard fail at most receivers, and it is the most common finding
  of all. There must be exactly one.
- An SPF record ending in `+all` authorizes the whole internet, which is worse than
  publishing nothing.
- More than ten DNS lookups in an SPF record and it stops evaluating, which reads as
  no SPF at all.
- DKIM lives on a selector. Google Workspace usually publishes on `google`,
  Microsoft 365 on `selector1` and `selector2`. Guessing the wrong selector and
  concluding there is no DKIM is a common false alarm.
- DMARC must exist. Since February 2024 Google and Yahoo require an aligned record
  from bulk senders, and cold outreach is bulk as far as a filter is concerned.
  `p=none` satisfies it.

**Do not tighten DMARC to `p=quarantine` or `p=reject` in the same week as a launch.**
If alignment is not already clean, you will stop your own mail.

**2. Warmup and age.** A domain sending cold email in its first weeks lands in spam
whatever the copy says. Warmup for two weeks minimum before the first campaign, three
to four for comfort. Those are rules of thumb, not measured thresholds.
`get_warmup_status` gives the score, emails sent and received, and the spam count; a
spam count above roughly 3% of warmup mail received means the mailbox is already
being filtered.

**3. Volume.** A jump from 20 to 200 a day reads as a compromised account. Ramp:
around 20 a day per new mailbox, plus 5 to 10 a day, topping out around 40 to 50 for
a hosted mailbox on cold traffic. More mailboxes, not more per mailbox.

**4. The tracking domain.** This one surprises people. If open or click tracking uses
the shared tracking domain instead of a subdomain of yours, your links carry other
senders' reputation. Either set up `track.acme.fr` as a CNAME in Emelia, or turn open
tracking off. Turning it off costs you a number that Apple Mail Privacy Protection
already made unreliable.

**5. The content, last.** Spam words, all caps, three exclamation marks, a URL
shortener, an image-only first email, an attachment on a cold email. The copywriter
checks catch these before sending, so if you got here they are probably not the
problem.

**How to confirm which one it is:** compare bounce and reply rates per recipient
domain. If gmail.com is dramatically worse than everything else, it is authentication
or reputation. If every domain is equally bad and the bounce rate is clean, it is the
list or the offer, not the spam folder. `/outreach analyze` splits it out.

---

## Variables that did not resolve

Someone received `Bonjour {{first_name}},`. It is unrecoverable for that contact, so
the fix is prevention.

Why it happens, in order of frequency:

1. **The variable is not a column in the list.** The copy uses `{{firstName}}`, the
   list has `first_name`. Nothing matches, nothing renders.
2. **The variable exists but the cell is empty**, and there is no fallback. Every
   variable needs one. A variable that can be empty must never sit in a subject line.
3. **A typo created a new empty variable instead of failing.** Adding a contact with
   an unrecognized field name creates a custom variable automatically. So
   `firstNmae` does not error, it quietly creates `firstNmae`, empty for everybody.
   This is convenient when you mean it and invisible when you do not.
4. **The custom field was set on the wrong campaign or contact.**
   `PATCH /advanced/contacts` needs `campaignId`, `fieldName`, `fieldValue`, plus
   either `email` or `linkedinUrlProfile` to identify the person. Wrong campaign id,
   no error, no value.
5. **The contact was added before the field existed.** Adding the field later does
   not backfill contacts already in the campaign. Update them explicitly.

Prevention, which is what the skills do:

- Build the variable whitelist from the header of `outreach/leads.csv`, and refuse
  any variable that is not in it.
- Give every variable a fallback.
- Keep the variable count low. More than three in one email reads as a mail merge.
- Send yourself the first email of the sequence before the campaign goes out. A test
  send finds this in thirty seconds, and nothing else does.

---

## An empty list after filtering

12,000 rows went in and nothing came out. Filters combine with AND, so the count only
ever goes down, and one wrong filter takes everything with it.

**Find the step that emptied it.** Re-run the count with one filter at a time. The
sourcing and filtering steps report a count before and after, so read those numbers
first: the drop is in one of them.

Common causes, sourcing side, all specific to Basile:

- **The `activity` concept id is wrong.** `activity` takes ids, not words. Resolve
  them with `GET /companies/activity-suggest?q=logiciel` and pass what comes back.
- **`headquarters_region_code` is dropped at validation.** It restricts nothing, and
  sent on its own the request goes out with no filter at all and the API answers 400
  "At least one filter is required". Use `region` with the canonical name, or
  enumerate `headquarters_postal_code`.
- **A full date in `creation_date_min`.** It takes a year. `2015-03-01` is ignored
  silently, which usually gives too many results rather than none, but combined with
  other filters it can do either.
- **`company_headcount` drops records with unknown headcount**, roughly a fifth of a
  French sample. Combined with a tight range, that empties a search fast.
- **Contradictory source flags.** `with_legal_data` and `with_linkedin_profile`
  together, or a `source` forced to one side while filtering on a field the other side
  owns, returns nothing by construction.

Common causes, filtering side:

- **The exclusion list matched on domain instead of email.** Excluding
  `@acme.com` when you meant one person removes the whole company. Check what the
  exclusion is keyed on.
- **Deduplication against a previous campaign removed everyone**, because you already
  emailed this segment. That is the filter working. Look at
  `outreach/leads-dropped.csv`, where every row carries a `dropped_reason`.
- **Filtering on `email_status: valid` before verification ran.** Nothing is `valid`
  until it has been verified, so this removes the whole list. Rows fresh from a source
  are `unverified`.

`outreach/leads-dropped.csv` exists so that this is a five minute question rather
than a rerun. Nothing is dropped without a reason written next to it.
