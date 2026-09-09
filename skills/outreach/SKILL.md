---
name: outreach
description: "Universal B2B outreach skill. Define an ICP, build and clean a lead list, find and verify professional emails and mobile numbers, write and personalize a multichannel sequence, check deliverability, launch the campaign, handle replies, and read the results. Works with the Emelia MCP server or REST API, the Basile API for French B2B data, or a plain CSV. Triggers on: outreach, cold email, prospecting, lead list, lead generation, email finder, email verification, phone finder, sequence, campaign, follow-up, deliverability, warmup, SDR, ICP, personalization, reply handling."
user-invokable: true
argument-hint: "[command] [target]"
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Claude for B2B Outreach

**Invocation:** `/outreach $1 $2` where `$1` is the command and `$2` is the target
(a brief, a list name, a CSV path, a campaign name or a URL).

This skill orchestrates 17 sub-skills and 5 sub-agents that take an outbound campaign
from a vague idea to replies in an inbox. Every step writes a file you can read,
edit and re-run. Nothing is a black box.

## Quick reference

| Command | What it does |
|---------|-------------|
| `/outreach pilot` | **Start here.** A guided first campaign on 100 contacts, with a checkpoint at every step |
| `/outreach full <brief>` | The complete pipeline: ICP, list, enrichment, copy, sequence, launch, analysis |
| `/outreach offer <url or description>` | Turn what you sell into an offer a competitor could not copy, from your website or from a conversation |
| `/outreach icp <brief>` | Turn a vague brief into a targeting spec: titles, industries, size, geography, signals |
| `/outreach leads <icp or query>` | Build the lead list from Basile (France), LinkedIn or a CSV |
| `/outreach filter <list>` | Deduplicate, exclude customers and blacklist, segment, drop unusable rows |
| `/outreach find-email <list>` | Find professional emails, in bulk or one by one |
| `/outreach find-phone <list>` | Find direct mobile numbers |
| `/outreach verify <list>` | Verify deliverability of every address before sending |
| `/outreach enrich <list>` | The full waterfall: find, verify, decide, fill custom fields |
| `/outreach write <angle>` | Write the sequence copy: subjects, openers, follow-ups, break-up |
| `/outreach personalize <list>` | Per-contact icebreakers and AI variables at scale |
| `/outreach sequence <spec>` | Design the multichannel flow: steps, delays, conditions, A/B tests |
| `/outreach deliverability` | SPF, DKIM, DMARC, warmup, sending limits, ramp plan |
| `/outreach campaign <spec>` | Create and launch the campaign in Emelia |
| `/outreach replies` | Triage replies, draft answers, handle unsubscribes |
| `/outreach audit <campaign>` | Rates per step and per variant, against benchmarks, what to change |

No command given? Ask what the user wants to do, then suggest `/outreach pilot`
if they have never run a campaign, or `/outreach full` if they know their market.

## The working directory

Everything a run produces lands in `outreach/` in the current directory, so the user
owns the output and can re-run a single step without redoing the rest:

```
outreach/
  offer.md            # what you sell, and the block the writing prompt consumes
  icp.json            # the targeting spec, human editable
  leads.csv           # the list, one row per contact, source column kept
  enrichment.json     # what was found, what was not, what it cost
  sequence.md         # the copy, step by step, with variables
  campaign.json       # what was created in Emelia, with ids
  audit.md            # what is wrong with the emails, and the one thing to fix
```

Never overwrite a file from a previous run without saying so. Append a suffix when
the user is clearly starting a second campaign (`leads-q4.csv`).

## Data sources

Three ways to get contacts, in this order of preference:

1. **Basile API** (`api.basile.cc`) for French B2B: around 26.8 million companies and
   29.5 million contacts, from the legal registry, LinkedIn and Google My Business.
   Header `Authorization: <raw key>`, no `Bearer`. Filters are nested objects, not
   flat arrays: `filters.result_role.include`, `filters.result_country_code.include`,
   `hide_legal_entities`. **Send `countOnly: true` to count for free**; without it
   every returned row costs a credit. The full spec is at
   `https://docs.basile.cc/openapi.yaml`, and an AI oriented index at
   `https://docs.basile.cc/llms.txt`. Read the spec before writing a filter, because
   a query written from intuition will be rejected.
2. **LinkedIn**, through a Sales Navigator search URL and the Emelia LinkedIn scraper.
   Best for a named account list or a role-based search outside France.
3. **A CSV the user already has.** Always supported, no key needed. Map the columns,
   then treat it exactly like a sourced list.

Enrichment (email, mobile, verification) always goes through Emelia, which bills in
credits. See "Credit discipline" below.

## Connecting to Emelia

Two ways in, and they do not cover the same ground. Read this before writing any call.

### The REST API, the documented path

This is what every sub-skill assumes by default. The user creates an API key at
[app.emelia.io/settings/api](https://app.emelia.io/settings/api) and exports it:

```bash
export EMELIA_API_KEY="..."      # required for anything that enriches or sends
export BASILE_API_KEY="..."      # optional, French B2B data
```

Base `https://api.emelia.io`, header `Authorization: <key>`. Never write a key into a
file. The full surface, which is all there is:

| Method and path | What it does |
|---|---|
| `POST /tools/find/email` then `GET /tools/find/email/{jobId}` | Find an email from `fullname`, `companyName` or `companyWebsite`, and `country`, which is **required** despite what some schemas say |
| `POST /tools/find/phone` then `GET /tools/find/phone/{jobId}` | Find a mobile from `linkedinUrl` |
| `POST /tools/verify/email` then `GET /tools/verify/email/{jobId}` | Verify one address |
| `POST /advanced/lists/contacts` | Add contacts to a list |
| `POST /advanced/campaign/contacts` | Add a contact straight into an email campaign, with custom fields |
| `PATCH /advanced/contacts` | Set a custom field on a contact |
| `POST /advanced/campaigns` | Create a campaign. Takes a `name` and nothing else |
| `GET /advanced/campaigns` | List campaigns |
| `GET /advanced/campaigns/{campaignId}/activities` | Activity feed: sent, opened, clicked, replied, bounced |
| `POST /emails/reply` | Reply to a reply: `messageId`, `providerId`, `to`, `subject`, `content` |
| `POST` and `DELETE /emails/blacklists/contact` | Add or remove an address from the blacklist |
| `POST /linkedin/campaigns`, `GET /linkedin/campaigns` | LinkedIn campaigns |
| `POST` and `DELETE /linkedin/campaign/contacts` | Contacts in a LinkedIn campaign |
| `POST /linkedin/lists/contacts`, `PATCH /linkedin/contacts` | LinkedIn lists and custom fields |

Rate limits, per minute and per key: 30 without a subscription, 100 on Start, 300 on
Grow, 1000 on Scale. Batch and pace accordingly.

### Building and launching a campaign, end to end

These routes are not in the public documentation yet, and they were verified against
the live API on 8 September 2026 with a plain API key. They are what makes the whole
pipeline programmable, so use them, and tell the user they are not contractual yet.

| Method and path | What it does |
|---|---|
| `GET /advanced/campaigns/{id}` | The full campaign: status, steps, schedule, recipients, identities |
| `PATCH /advanced/campaigns/{id}/steps` | Set the sequence. The body wraps the sequence in an object, not an array |
| `PATCH /advanced/campaigns/{id}/settings` | Schedule, daily volumes, tracking, stop conditions, wrapped in `settings` |
| `PATCH /advanced/campaigns/{id}/recipients` | Attach lists (`lists`) and exclusion lists (`excludedLists`) |
| `PATCH /advanced/campaigns/{id}/identities` | Choose the sending accounts |
| `POST /advanced/campaigns/{id}/test-email` | Send yourself a test before launching |
| `POST /advanced/campaigns/{id}/start` and `/pause` | Launch and pause. No body |
| `PATCH /advanced/campaigns/{id}/planned-start` | Schedule the launch for later |
| `POST /advanced/campaigns/{id}/duplicate` and `/archive` | Duplicate, archive |
| `DELETE /advanced/campaigns/{id}` | Delete a campaign, useful to clean up a test |
| `GET /advanced/campaigns/{id}/progress`, `/failed-activities`, `/export` | Follow a running campaign |

A freshly created campaign already carries a default schedule (35 contacts added per
day, 500 emails maximum, Europe/Brussels, Monday to Friday, 08:00 to 17:00) and four
empty steps. Read it back with `GET` before patching, so you change what you mean to
change and nothing else.

The order that works: create, patch the steps, patch the settings, attach the list,
choose the identities, send yourself a test email, then start. Never skip the test.

### The MCP server, an optional accelerator

If the user has it configured (`https://mcp.emelia.io/mcp`, header `Authorization`),
prefer it for the five things the REST API does not expose: `get_campaign_stats`,
`get_warmup_status` and `set_warmup`, `list_email_providers`, the list management
tools (`create_list`, `list_lists`, `get_list`, `rename_list`, `delete_list`,
`get_list_contacts`, `update_contact`, `delete_contact`) and `find_contact`, which
searches a contact across every list of the account.

Never assume it is there. Check, and fall back to REST or to asking the user.

Two things verified against the live server on 8 September 2026, because getting them
wrong costs a failed call every time: `find_email` rejects any request without
`country`, even though its schema lists only `fullname` and `companyName` as
required; and `find_contact` takes a single `query` parameter, not `email`, whatever
its description suggests. Enrichment jobs answer in under five seconds, so poll every
three seconds rather than every thirty. Bulk contact adds cap at 100 rows per call and
return a `created` / `duplicates` / `updated` / `failed` breakdown you should report
to the user as is. Deleting a list deletes its contacts too, and updates the campaigns
that used it.

### What no API can do, and what that means for you

The whole pipeline is programmable, but two things still deserve care.

**A campaign is never launched without the user saying so.** Not because the API
stops you, but because a message to a real person is not reversible. Show the copy,
the recipient count and the daily volume, send the test email, then ask.

**Contacts live in lists.** A list attached to a running campaign feeds it
continuously: every contact you add enters the campaign on its own. That is the
product's central mechanic, and it is what makes an ongoing campaign easy to feed
without touching its configuration again.

Say this plainly to the user the first time, rather than letting them discover it.
If neither key nor MCP is configured, offer **dry run**: every step still produces
its file, nothing is sent, nothing is charged.

### Why these skills exist next to an API

An endpoint tells you how to call it. It does not tell you to count before you
extract, to filter before you enrich, that a catch-all domain cannot be verified,
that a 40% open rate with no replies is an offer problem and not a deliverability
one, or that adding a thousand contacts to a live campaign on a cold domain will
burn it. That judgment is what each sub-skill carries. The transport is a detail.

## The rules that make this trustworthy

**Credit discipline.** Finding an email, a mobile or a verification costs the user
money. Before any bulk enrichment: count the rows, state the cost in credits, and get
an explicit yes. Never enrich a row you are going to filter out later, so filter first.

**Verify before you send.** A list that has not been verified will bounce, and bounces
cost sender reputation, which is far more expensive than the credits saved. Sending
to an unverified list is a refusal, not a warning.

**Deliverability is a gate, not a chapter.** `/outreach campaign` calls
`outreach-deliverability` first. If warmup is off, if SPF, DKIM or DMARC is missing,
or if the daily volume is above what the mailboxes can carry, stop and fix it.

**Identify yourself, and offer a way out.** Every message says who is writing and for
which company, and every step from the second onwards carries a working unsubscribe
link. That is not paperwork, it is what separates outreach from spam, and a reader who
cannot opt out marks you instead.

**Say what you did not do.** If the finder found 62% of the list, say 62%, do not
round it up and do not quietly drop the rest.

## How a full run flows

```
/outreach full "sell our API monitoring tool to CTOs of French SaaS, 20 to 200 people"

  1  outreach-offer           -> offer.md          what you sell, and why it is not generic
  2  outreach-icp             -> icp.json          you confirm before spending
  2  outreach-leads           -> leads.csv         count first, extract second
  3  outreach-filter          -> leads.csv         dedupe, exclude, segment
  4  outreach-enrich          -> enrichment.json   find, verify, cost stated up front
  5  outreach-write           -> sequence.md       copy, reviewed by you
  6  outreach-personalize     -> leads.csv         icebreakers per contact
  7  outreach-sequence        -> campaign.json     steps, delays, conditions, A/B
  8  outreach-deliverability  -> gate              blocks the launch if unsafe
  9  outreach-campaign        -> live in Emelia    you confirm the launch
 10  outreach-replies           -> replies triaged   labels and drafts, you send
 11  outreach-audit         -> audit.md          what is wrong with the emails
```

Steps 1, 4, 5 and 9 stop and wait for the user. The rest runs through.

## Parallel work

Use the sub-agents in `agents/` when a step fans out over many items:
`outreach-lead-sourcer` (several sources at once), `outreach-enricher` (batches),
`outreach-copywriter` (variants per segment), `outreach-deliverability-auditor`
(one mailbox each), `outreach-auditor` (per campaign or per step). Anything that reads many
things and returns one conclusion belongs in an agent.

## Sub-skills

Each command above maps to a skill in `skills/outreach-*`. Read the matching
`SKILL.md` before acting: it holds the field names, the API shapes, the benchmarks
and the failure modes for that step. Do not reimplement a step from memory.

## Limits worth stating to the user

This skill does not place calls, does not scrape LinkedIn outside the official Emelia
integration, does not buy data from grey market brokers, and does not guarantee an
email is deliverable when the domain is catch-all. Reply rates depend on your offer
far more than on your tooling: when the copy is the problem, say it.
