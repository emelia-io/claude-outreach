# Command reference

Every command is `/outreach <command> <target>`. The dispatcher
([`skills/outreach/SKILL.md`](../skills/outreach/SKILL.md)) routes the command to
one sub-skill, which does the work and writes a file into `outreach/` in the
current directory.

Quote anything with spaces. `/outreach icp sell to CTOs` and
`/outreach icp "sell to CTOs"` are the same, but the quotes save you the day a
brief contains a comma or a slash.

No command at all is fine: `/outreach` asks what you want to do.

## At a glance

| Command | Writes | Costs credits | Waits for your yes |
|---|---|---|---|
| [`pilot`](#outreach-pilot) | everything, at 100 rows | yes, at the enrichment step | at every step |
| [`full`](#outreach-full-brief) | everything | yes, at the enrichment step | steps 1, 4, 5 and 9 |
| [`icp`](#outreach-icp-brief) | `icp.json` | no | yes, before spending |
| [`leads`](#outreach-leads-query) | `leads.csv` | Basile credits, not Emelia | yes, before extracting |
| [`filter`](#outreach-filter-list) | `leads.csv`, `leads-dropped.csv` | no | no |
| [`find-email`](#outreach-find-email-list) | `leads.csv`, `enrichment.json` | yes | yes |
| [`find-phone`](#outreach-find-phone-list) | `leads.csv`, `enrichment.json` | yes | yes |
| [`verify`](#outreach-verify-list) | `leads.csv`, `enrichment.json` | yes | yes |
| [`enrich`](#outreach-enrich-list) | `leads.csv`, `enrichment.json` | yes | yes |
| [`write`](#outreach-write-angle) | `sequence.md` | no | yes, you review the copy |
| [`personalize`](#outreach-personalize-list) | `leads.csv` | no | no |
| [`sequence`](#outreach-sequence-spec) | `campaign.json` | no | no |
| [`deliverability`](#outreach-deliverability) | `deliverability.md` | no | no |
| [`campaign`](#outreach-campaign-spec) | `campaign.json` | no, sending does | yes, always |
| [`inbox`](#outreach-replies) | `inbox.md` | no | yes, before any reply leaves |
| [`audit`](#outreach-audit-campaign) | `audit.md` | no | no |

The six files named in the dispatcher contract (`icp.json`, `leads.csv`,
`enrichment.json`, `sequence.md`, `campaign.json`, `report.md`) are the ones every
step agrees on. The others (`leads-dropped.csv`, `deliverability.md`, `inbox.md`,
`replies.md`) sit next to them in the same directory and are safe to delete.

---

## `/outreach pilot`

A guided first campaign on 100 contacts, with a checkpoint before every step that
costs money or reaches a person. Use it once, the first time. It exists so you find
out what each step produces on a list small enough that a mistake is cheap.

- **Argument** none. It asks you who you sell to.
- **Reads** nothing required. Picks up an existing `outreach/` if you have one.
- **Writes** `outreach/icp.json`, `outreach/leads.csv`, `outreach/enrichment.json`,
  `outreach/sequence.md`, `outreach/campaign.json`
- **Skill** [`outreach-pilot`](../skills/outreach-pilot/SKILL.md)
- **Credits** yes, at the enrichment step, on 100 rows, announced before it runs
- **Stops** at every step

```
/outreach pilot
```

## `/outreach full <brief>`

The whole pipeline in one command: ICP, list, filter, enrichment, copy,
personalization, sequence, deliverability gate, launch, replies, analysis. Use it
when you already know your market and do not want eleven prompts.

- **Argument** `<brief>`: who you sell to and what you sell, in one sentence.
- **Reads** anything already in `outreach/`, and reuses it rather than redoing it.
- **Writes** all six contract files.
- **Skill** none of its own. The dispatcher chains the eleven skills in order.
- **Credits** yes, at the enrichment step, announced with the row count first
- **Stops** at the ICP, at the enrichment cost, at the copy review, and at the launch

```
/outreach full "sell our API monitoring tool to CTOs of French SaaS companies, 20 to 200 people"
```

## `/outreach icp <brief>`

Turns a vague sentence into a targeting spec you can argue with: titles and their
local variants, industry or activity codes, headcount range, geography, buying
signals, and the exclusions that matter more than the inclusions.

- **Argument** `<brief>`: free text. A URL to your own site also works, and it will
  read it to infer what you sell.
- **Reads** nothing required.
- **Writes** `outreach/icp.json`
- **Skill** [`outreach-icp`](../skills/outreach-icp/SKILL.md)
- **Credits** none
- **Stops** yes. Nothing is spent until you confirm the spec.

```
/outreach icp "we sell an API monitoring tool to technical founders and CTOs of French SaaS companies between 20 and 200 people"
```

## `/outreach leads <query>`

Builds the list. Three sources: the Basile API for French B2B, a LinkedIn or Sales
Navigator search through Emelia, or a CSV you already have. It counts first, tells
you the number, and only then extracts. Which source to pick is
[docs/DATA-SOURCES.md](DATA-SOURCES.md).

- **Argument** `<query>`: nothing (it uses `outreach/icp.json`), or a path to a CSV,
  or a Sales Navigator URL, or a plain description that overrides the ICP.
- **Reads** `outreach/icp.json`, and `BASILE_API_KEY` when the source is Basile.
- **Writes** `outreach/leads.csv`, plus one `outreach/leads-<source>.csv` per source
  when several run in parallel.
- **Skill** [`outreach-leads`](../skills/outreach-leads/SKILL.md)
- **Agent** [`outreach-lead-sourcer`](../agents/outreach-lead-sourcer.md), one per source
- **Credits** Basile bills 1 credit per record returned. Counting is free.
- **Stops** yes, on the count, before extracting.

```
/outreach leads
/outreach leads ~/Downloads/salon-2026-exposants.csv
/outreach leads "https://www.linkedin.com/sales/search/people?query=..."
```

## `/outreach filter <list>`

Cleans the list before anyone spends a credit on it: deduplicates, drops rows that
can never be contacted, removes your existing customers and your blacklist, splits
the rest into segments. This is the step that decides how much the next one costs.

- **Argument** `<list>`: path to a CSV. Defaults to `outreach/leads.csv`.
- **Reads** `outreach/leads.csv`, your exclusion list if you have one.
- **Writes** `outreach/leads.csv` (rewritten in place) and
  `outreach/leads-dropped.csv` with a `dropped_reason` column, so nothing
  disappears without a trace.
- **Skill** [`outreach-filter`](../skills/outreach-filter/SKILL.md)
- **Credits** none. It saves them.
- **Stops** no, but it reports every count before and after.

```
/outreach filter
/outreach filter outreach/leads-q4.csv
```

## `/outreach find-email <list>`

Finds professional email addresses for rows that do not have one, from a full name
plus a company. Runs on `POST /tools/find/email` and its job result endpoint.

- **Argument** `<list>`: path to a CSV. Defaults to `outreach/leads.csv`.
- **Reads** `outreach/leads.csv`, `EMELIA_API_KEY`
- **Writes** `outreach/leads.csv` with `email` and `email_status` filled, and
  `outreach/enrichment.json` with the counters and the cost.
- **Skill** [`outreach-find-email`](../skills/outreach-find-email/SKILL.md)
- **Agent** [`outreach-enricher`](../agents/outreach-enricher.md), one per batch
- **Credits** yes, one per row attempted, whether or not the address is found.
  The count and the cost are stated before anything runs.
- **Stops** yes, on the cost.

```
/outreach find-email
```

## `/outreach find-phone <list>`

Finds direct mobile numbers. The phone finder takes a LinkedIn profile URL and
nothing else, so a row without one can never be found: it is skipped, not attempted,
and not billed.

- **Argument** `<list>`: path to a CSV. Defaults to `outreach/leads.csv`.
- **Reads** `outreach/leads.csv` (the `linkedin_url` column), `EMELIA_API_KEY`
- **Writes** `outreach/leads.csv` with `phone` filled, `outreach/enrichment.json`
- **Skill** [`outreach-find-phone`](../skills/outreach-find-phone/SKILL.md)
- **Agent** [`outreach-enricher`](../agents/outreach-enricher.md)
- **Credits** yes, one per row attempted
- **Stops** yes, on the cost

```
/outreach find-phone
```

## `/outreach verify <list>`

Verifies deliverability of every address before you send to it. This is the step
that protects your domain, and it is the one people skip. A campaign is refused on
an unverified list, not warned about.

- **Argument** `<list>`: path to a CSV. Defaults to `outreach/leads.csv`.
- **Reads** `outreach/leads.csv` (the `email` column), `EMELIA_API_KEY`
- **Writes** `outreach/leads.csv` with `email_status` set to `valid`, `invalid` or
  `unknown`, and `outreach/enrichment.json`
- **Skill** [`outreach-verify`](../skills/outreach-verify/SKILL.md)
- **Agent** [`outreach-enricher`](../agents/outreach-enricher.md)
- **Credits** yes, one per address verified
- **Stops** yes, on the cost

```
/outreach verify
```

## `/outreach enrich <list>`

The whole waterfall in the right order: filter, then find what is missing, then
verify what was found, then decide what is sendable. Use this instead of running
`find-email` and `verify` by hand, because it will not verify an address it just
found as invalid, and it will not find an address for a row the filter dropped.

- **Argument** `<list>`: path to a CSV. Defaults to `outreach/leads.csv`.
- **Reads** `outreach/leads.csv`, `outreach/icp.json`, `EMELIA_API_KEY`
- **Writes** `outreach/leads.csv`, `outreach/enrichment.json`
- **Skill** [`outreach-enrich`](../skills/outreach-enrich/SKILL.md)
- **Agent** [`outreach-enricher`](../agents/outreach-enricher.md), one per batch of 100
- **Credits** yes. One budget, announced once, for the whole waterfall.
- **Stops** yes, on the total cost, before the first call.

```
/outreach enrich
```

## `/outreach write <angle>`

Writes the sequence: subject lines, the first email, the follow-ups and the break-up,
per segment, with the variables that exist in your list and no others. Then checks
its own output for spam signals, unresolved variables, truncated subjects and claims
it cannot source.

- **Argument** `<angle>`: the problem you are leading with, in a few words. Omit it
  and it proposes three angles from the ICP.
- **Reads** `outreach/icp.json`, the header of `outreach/leads.csv` for the variable
  whitelist.
- **Writes** `outreach/sequence.md`
- **Skill** [`outreach-write`](../skills/outreach-write/SKILL.md)
- **Agent** [`outreach-copywriter`](../agents/outreach-copywriter.md), one per segment or variant
- **Credits** none
- **Stops** yes. You read the copy before it goes anywhere.

```
/outreach write "their alerting is noisy and nobody reads the Slack channel any more"
```

## `/outreach personalize <list>`

Writes a per-contact opening line from what is actually in the row, and fills the
custom fields the sequence expects. It will not write a sentence it cannot source
from a column, which is why some rows come back with the generic opener and are
reported as such.

- **Argument** `<list>`: path to a CSV. Defaults to `outreach/leads.csv`.
- **Reads** `outreach/leads.csv`, `outreach/sequence.md`
- **Writes** `outreach/leads.csv` with an `icebreaker` column and any custom variable
  the sequence uses.
- **Skill** [`outreach-personalize`](../skills/outreach-personalize/SKILL.md)
- **Credits** none for the writing. Custom fields pushed to Emelia later use
  `PATCH /advanced/contacts`, which does not bill credits.
- **Stops** no, but it reports how many rows got a real icebreaker and how many
  fell back.

```
/outreach personalize
```

## `/outreach sequence <spec>`

Designs the flow rather than the words: how many steps, on which channel, how many
days apart, what stops a contact, which step carries the A/B test, what the daily
volume works out to. Produces the spec you will build once in the Emelia app.

- **Argument** `<spec>`: free text, for example `"4 steps over 12 days, email only"`.
  Omit it and it proposes a flow from the segment and the volume.
- **Reads** `outreach/sequence.md`, `outreach/leads.csv` for the volume
- **Writes** `outreach/campaign.json` with the steps, delays, conditions and variants
- **Skill** [`outreach-sequence`](../skills/outreach-sequence/SKILL.md)
- **Credits** none
- **Stops** no

```
/outreach sequence "4 steps over 12 days, email then LinkedIn on step 3"
```

## `/outreach deliverability`

Audits your sending setup: SPF, DKIM, DMARC and MX on every sending domain, the
tracking domain, domain blocklists, warmup state per mailbox, and whether the volume
you are planning fits what those mailboxes can carry. Returns GO, GO WITH LIMIT or
NO GO. `/outreach campaign` calls this first and will not launch past a NO GO.

- **Argument** none, or a domain or mailbox to audit on its own.
- **Reads** `outreach/campaign.json` for the planned volume, `EMELIA_API_KEY`. Warmup
  and sending accounts need the MCP server; without it that part is reported as
  unverified rather than passed.
- **Writes** `outreach/deliverability.md`
- **Skill** [`outreach-deliverability`](../skills/outreach-deliverability/SKILL.md)
- **Agent** [`outreach-deliverability-auditor`](../agents/outreach-deliverability-auditor.md), one per mailbox
- **Credits** none
- **Stops** no, but its verdict blocks the launch

```
/outreach deliverability
/outreach deliverability acme.fr
```

## `/outreach campaign <spec>`

Creates the campaign in Emelia and pushes the contacts into it. Read this before you
run it: **the API creates a campaign, not a sequence.** `POST /advanced/campaigns`
takes a name and nothing else. Steps, schedule and sending accounts are built once
in the Emelia app. After that, contacts added to the attached list enter the running
campaign on their own, and that is the part this command automates.

- **Argument** `<spec>`: the campaign name, or nothing to use the one in
  `outreach/campaign.json`.
- **Reads** `outreach/campaign.json`, `outreach/leads.csv`, `outreach/sequence.md`,
  `EMELIA_API_KEY`
- **Writes** `outreach/campaign.json` with the campaign id, the list id and the
  contact counts
- **Skill** [`outreach-campaign`](../skills/outreach-campaign/SKILL.md)
- **Credits** none for creating. Sending consumes your sending plan.
- **Stops** yes, always, twice: once on the deliverability verdict, once before the
  first contact enters a live campaign.

```
/outreach campaign "Q4 SaaS founders"
```

## `/outreach replies`

Reads the replies, sorts them (interested, meeting, not now, wrong person, out of
office, unsubscribe, angry), drafts an answer for each, and leaves them for you.
Unsubscribes are processed straight away, because that one is not optional.

- **Argument** none, or a campaign name to restrict the triage.
- **Reads** `outreach/campaign.json`, the campaign activity feed, `EMELIA_API_KEY`
- **Writes** `outreach/inbox.md` with one block per reply and its draft
- **Skill** [`outreach-replies`](../skills/outreach-replies/SKILL.md)
- **Credits** none
- **Stops** yes. Nothing is sent without your explicit yes, per message.

```
/outreach replies
```

## `/outreach audit <campaign>`

Audits the **content** of the emails, step by step, and says what is costing you
replies. Nine checks: one ask per email, the links that dilute it, whether the
question can be answered with a thumb, length measured in rendered lines on a phone,
attachments, images, HTML weight, the signature, spam trigger words and hollow jargon.
A verdict per step (REWRITE, FIX or SHIP), a verdict for the sequence, and one thing
to fix first.

It is not a statistics report. Open and click rates are optional, come last, and are
skipped entirely when tracking is off, because your emails can be wrong either way.

- **Argument** `<campaign>`: a campaign name or id. With no argument it reads
  `outreach/sequence.md`, then falls back to the campaign in
  `outreach/campaign.json`.
- **Reads** `outreach/sequence.md`, or `GET /advanced/campaigns/{id}` saved as
  `outreach/campaign-raw.json`, plus `EMELIA_API_KEY` for the live path
- **Writes** `outreach/audit.md`
- **Skill** [`outreach-audit`](../skills/outreach-audit/SKILL.md)
- **Script** [`scripts/audit-emails.py`](../scripts/audit-emails.py), which does the
  counting and exits 1 on a blocking finding, so it works as a launch gate
- **Credits** none. It sends nothing and spends nothing, so it is safe on anything.
- **Stops** no

```
/outreach audit                      # audits outreach/sequence.md
/outreach audit "Q4 SaaS founders"   # pulls the live campaign and audits that
```

The signature is the one thing it cannot see on its own: `{{signature}}` is stored in
Emelia, not in the campaign steps. Paste it, or send yourself a test email with
`POST /advanced/campaigns/{id}/test-email` and read what arrives.

## Running one step again

Every command reads files and writes files, so you can re-run any single step
without redoing the ones before it. Edit `outreach/icp.json` by hand and re-run
`/outreach leads`. Edit `outreach/sequence.md` and re-run `/outreach campaign`.

A command never overwrites a previous run silently. When it is about to, it says so
and offers a suffixed name (`leads-q4.csv`) instead.

## Running without keys

With no `EMELIA_API_KEY`, everything that does not touch Emelia still works: ICP,
need Emelia run in dry run: they produce their file, state what they would have
called and what it would have cost, and change nothing. See
[SETUP.md](SETUP.md) for the keys and [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for
when one of them stops working.
