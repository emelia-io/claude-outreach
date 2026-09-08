# Architecture

Four layers, and each one is allowed to do less than the one above it.

```
you            /outreach enrich
  |
dispatcher     skills/outreach/SKILL.md
  |            picks the command, enforces the rules that apply to every step
  |
sub-skill      skills/outreach-enrich/SKILL.md
  |            the procedure for that one step: endpoints, fields, thresholds
  |
sub-agent      agents/outreach-enricher.md
  |            one batch, one budget, in parallel with its siblings
  |
files          outreach/leads.csv, outreach/enrichment.json
               what you keep, edit and re-run from
```

The layers exist so that a change stays local. A new data source is a change in one
sub-skill. A faster enrichment is a change in one agent. A new rule about spending
money is a change in the dispatcher, and it applies everywhere at once.

## What each layer is for

**The dispatcher** is the contract. It holds the command table, the working
directory, the transport (REST first, MCP when configured), and the four rules that
do not bend: count before you extract, filter before you enrich, verify before you
send, confirm anything that costs money or reaches a human. It routes, it does not
implement.

**A sub-skill** is one step, written so someone who has never used Emelia can run it:
the exact endpoint or tool, the required fields, the order of operations, the
thresholds, and the three things that make that step fail. One directory, one
`SKILL.md`. The format is [SKILL-CONVENTIONS.md](SKILL-CONVENTIONS.md).

**A sub-agent** is a specialist for work that fans out. Five sources to query, twenty
batches to enrich, three segments to write for, six mailboxes to audit, four
campaigns to compare. Each agent gets one item, one budget and one output format,
and returns a block the parent can merge without parsing prose. Agents read and
compute; they do not launch, do not send, and do not decide to spend.

**The files** are the product. Every step writes one, in the open, in the current
directory. That is what makes a step re-runnable: edit `outreach/icp.json` by hand
and run `/outreach leads` again, and nothing before it is repeated.

## The working directory

```
outreach/
  icp.json            the targeting spec, human editable
  leads.csv           the list, one row per contact, source column kept
  enrichment.json     what was found, what was not, what it cost
  sequence.md         the copy, step by step, with variables
  campaign.json       what was created in Emelia, with ids
  report.md           results and what to change next
```

Those six are the contract: any skill may read them and expects them to be there.
Steps also drop side files next to them (`leads-dropped.csv`,
`deliverability.md`, `inbox.md`, `compliance.md`, one `leads-<source>.csv` per
parallel sourcing agent). Side files are safe to delete; contract files are not.

### The columns every step expects in `leads.csv`

```
first_name,last_name,job_title,company_name,company_domain,linkedin_url,email,email_status,country,source,source_url,collected_at
```

Any step may add columns. No step may remove one of these, or rename it, because the
step after it is reading them. The ones added along the way:

| Column | Added by | Values |
|---|---|---|
| `email_status` | sourcing, then verification | `unverified`, `valid`, `invalid`, `unknown` |
| `phone` | `/outreach find-phone` | E.164, or empty |
| `segment` | `/outreach filter` | your segment name |
| `icebreaker` | `/outreach personalize` | one sentence, or empty |
| `dropped_reason` | `/outreach filter`, in `leads-dropped.csv` only | why the row left |

`email_status: unknown` is not a failure to report as valid. It is what a catch-all
domain returns, and it means nobody can tell you whether that address exists.

## The life of a campaign

```
  brief
    |
 1  outreach-icp ............... icp.json          GATE: you confirm the spec
    |
 2  outreach-leads ............. leads.csv         count first, extract second
    |                                              fans out: outreach-lead-sourcer
 3  outreach-filter ............ leads.csv         dedupe, exclude, segment
    |                                              this is what makes step 4 cheap
 4  outreach-enrich ............ enrichment.json   GATE: you approve the cost
    |                                              fans out: outreach-enricher
 5  outreach-write ............. sequence.md       GATE: you read the copy
    |                                              fans out: outreach-copywriter
 6  outreach-personalize ....... leads.csv         icebreakers, sourced or empty
    |
 7  outreach-sequence .......... campaign.json     steps, delays, conditions, A/B
    |
 8  outreach-deliverability .... deliverability.md GATE: NO GO blocks the launch
    |                                              fans out: outreach-deliverability-auditor
 9  outreach-campaign .......... live in Emelia    GATE: you confirm the launch
    |
10  outreach-inbox ............. inbox.md          GATE: you send every reply
    |
11  outreach-analyze ........... report.md         fans out: outreach-analyst
```

Six gates, and they are the whole point. Four of them protect your money and your
sender reputation; two protect the people you are about to email.

### The break in the middle, and why it is there

Between step 7 and step 9 there is something no API can do. `POST /advanced/campaigns`
creates a campaign with a name and nothing else: steps, schedule and sending accounts
are configured in the Emelia app. So the flow is not "generate and launch blindly":

1. The skills produce the sequence spec, the copy and the cleaned list.
2. You build that sequence once in the app, on the campaign, and start it.
3. The skills push contacts into the list attached to that campaign, and each
   contact added enters the running campaign on its own.

That third point is the mechanic the whole repository is built on. A campaign is a
running thing you feed, not a thing you fire once. It is also why re-running
`/outreach leads` and `/outreach enrich` next month adds contacts to the same
campaign without rebuilding anything.

## How a skill reaches Emelia

Two transports, and a skill picks in this order.

**REST, `https://api.emelia.io`, header `Authorization: <key>`.** The documented
surface, and the default. Enrichment jobs, contacts, lists, campaign creation,
activities, replies, blacklist. This is what every sub-skill assumes.

**The MCP server, `https://mcp.emelia.io/mcp`, when the user configured it.**
Preferred for what REST does not expose: `get_campaign_stats`, `get_warmup_status`,
`set_warmup`, `list_email_providers`, the list management tools, and `find_contact`.

A skill checks whether the MCP tools are there. If they are not, it uses REST, or it
says which specific thing it could not read. It never assumes, and it never reports a
check as passed when it could not run it.

**Neither configured** is a supported mode, not an error: dry run. Every step
produces its file, states what it would have called and what it would have cost, and
changes nothing. See [SETUP.md](SETUP.md).

A note if you restrict agent tools: the MCP tool names in the agent frontmatter are
written as `mcp__emelia__<tool>`, which assumes the server is registered under the
name `emelia`, as in [SETUP.md](SETUP.md). Register it under another name and those
entries stop matching, so rename them or drop the `tools:` line to inherit
everything.

## Where the data comes from

Three sources, one shared row shape, described in
[DATA-SOURCES.md](DATA-SOURCES.md). Sourcing is a fan-out: one
`outreach-lead-sourcer` per source, each writing its own partition, and the skill
merges and deduplicates. That is why every row carries `source` and `source_id`: a
merge that cannot tell you where a row came from cannot be audited later, when the
question is "why did we email this person".

## Adding a skill

1. **Pick the name.** `skills/outreach-<verb>/`. The directory name and the
   frontmatter `name` must match exactly, and the test checks it.
2. **Copy an existing skill** and keep the frontmatter block: `name`, a
   `description` that ends in `Triggers on: word, word, word.`, `license: MIT`, and
   the `metadata` block. Only the dispatcher is `user-invokable`.
3. **Write the eight sections**, in order: What this does, When to use it, Inputs,
   How to do it, Output, Checks before finishing, Failure modes, Limits. The test
   checks all eight are present.
4. **Put the procedure in "How to do it"**, not a description of it. Exact endpoint
   or tool name, required fields, order of calls, thresholds, and what to do when it
   fails. A step a reader has to guess at is a bug.
5. **Show a real file in "Output"**, a real fragment of the CSV, JSON or Markdown it
   writes.
6. **Wire it up**: add the row to the command table in
   [`skills/outreach/SKILL.md`](../skills/outreach/SKILL.md), the same row in the
   README table, and an entry in [COMMANDS.md](COMMANDS.md).
7. **Run the tests**: `python3 tests/run.py`. It checks frontmatter, the name to
   directory match, the eight sections, em dashes and en dashes (which are banned in
   prose), and relative links.

## Adding an agent

Add an agent when a step fans out over items that do not need to know about each
other: sources, batches, segments, mailboxes, campaigns. One Markdown file in
`agents/`, frontmatter with `name`, `description` and `tools`, then a body that says
three things and nothing else: what it receives, what it returns and in what exact
format, and what it is not allowed to do.

Keep the "not allowed to do" list real. The agents in this repository do not send,
do not launch, do not change DNS, do not enable warmup, do not exceed a budget and
do not spend without the parent having already got a yes. A parallel worker that can
spend money is how a fan-out turns into an invoice.
