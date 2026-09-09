# Claude for B2B Outreach

**Run your whole outbound from Claude Code.** Define who you are targeting, build the
list, find and verify professional emails and mobile numbers, write a sequence that
does not read like a template, check your deliverability, launch the campaign, triage
the replies, and read what actually worked.

17 sub-skills, 5 sub-agents, MIT licensed, no lock-in. Bring your own data or source
it, bring your own mailboxes, keep every file on your machine.

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-F46D12)](https://docs.claude.com/en/docs/claude-code/skills)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](.claude-plugin/plugin.json)

---

## Contents

- [Why this exists](#why-this-exists)
- [Who it is for](#who-it-is-for)
- [Install](#install)
- [Quick start](#quick-start)
- [Commands](#commands)
- [What it does](#what-it-does)
- [Where the data comes from](#where-the-data-comes-from)
- [Compared to the alternatives](#compared-to-the-alternatives)
- [Use cases](#use-cases)
- [Sample output](#sample-output)
- [Architecture](#architecture)
- [Method](#method)
- [Requirements](#requirements)
- [Limits](#limits)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

---

## Why this exists

Outbound is a chain, and every link is a different tool. A data provider to find the
companies. A finder for the emails. A verifier so they do not bounce. A sender.
A warmup service. A LinkedIn tool. A spreadsheet to glue it together, and a human to
copy and paste between all of them.

The tools are not the hard part. The judgment is: whether this list is worth
enriching, whether this copy is worth sending, whether your domain can carry the
volume this week, whether a 2% reply rate is the offer or the deliverability.

That judgment is what a language model with the right context is genuinely good at,
and it is what this repository packages. Each skill holds the procedure, the field
names, the benchmarks and the failure modes for one step, so Claude does the step
the way someone who has run a thousand campaigns would do it.

## Who it is for

- **Founders** doing outbound themselves, who do not want to learn five products.
- **SDRs and growth teams** who want the boring 80% automated and the judgment kept.
- **Agencies** running outbound for several clients from one place.
- **Developers** who would rather describe a campaign than click through an interface.

You do not need to be technical. You need Claude Code and, for anything that
actually sends, an Emelia account.

## Install

**As a plugin** (recommended):

```
/plugin marketplace add emelia-io/claude-outreach
/plugin install claude-outreach@claude-outreach
```

**Manually**, into your user skills directory:

```bash
git clone https://github.com/emelia-io/claude-outreach.git
cp -r claude-outreach/skills/* ~/.claude/skills/
cp -r claude-outreach/agents/* ~/.claude/agents/
```

Windows PowerShell:

```powershell
git clone https://github.com/emelia-io/claude-outreach.git
Copy-Item -Recurse claude-outreach\skills\* $HOME\.claude\skills\
Copy-Item -Recurse claude-outreach\agents\* $HOME\.claude\agents\
```

**Add your keys** so the skills can enrich and send. Create an Emelia API key at
[app.emelia.io/settings/api](https://app.emelia.io/settings/api):

```bash
export EMELIA_API_KEY="..."      # enrichment, contacts, campaigns, replies
export BASILE_API_KEY="..."      # optional, French B2B data
```

That is all you need: the skills talk to the REST API, lists and campaigns included.
If you also run the [Emelia MCP server](https://docs.emelia.io/docs/mcp-server), they
will use it for the few things the REST API does not expose, such as warmup status.

Without a key, everything still runs in dry run: you get the list, the copy and the
sequence as files, nothing is sent and nothing is charged.

The whole pipeline runs through the API, campaign creation and launch included. Some
of the configuration endpoints are not in the public documentation yet, so treat them
as not contractual for now. See [docs/SETUP.md](docs/SETUP.md).

**Staying up to date.** This repository moves. Ask for an update check at any time, or
run it yourself:

```bash
bash scripts/check-update.sh
```

One call to the remote, one line back: `up to date`, or `behind by N commits` with the
`git pull` to run. The skills check it at the start of a run and tell you rather than
pulling behind your back.

## Quick start

```
/outreach pilot
```

A guided first campaign on 100 contacts. It asks who you sell to, builds a small
list, enriches it, writes the sequence with you, checks your deliverability, and
launches only when you say so. Roughly twenty minutes, and you keep every file.

Then, once you trust it:

```
/outreach full "sell our API monitoring tool to CTOs of French SaaS companies, 20 to 200 people"
```

## Commands

| Command | What it does |
|---------|-------------|
| `/outreach pilot` | Guided first campaign on 100 contacts, checkpoint at every step |
| `/outreach full <brief>` | The complete pipeline, ICP to analysis |
| `/outreach offer <url>` | Turn what you sell into an offer a competitor could not copy |
| `/outreach icp <brief>` | Turn a vague brief into a targeting spec |
| `/outreach leads <query>` | Build the list from Basile, LinkedIn or a CSV |
| `/outreach filter <list>` | Dedupe, exclude customers and blacklist, segment |
| `/outreach find-email <list>` | Find professional email addresses |
| `/outreach find-phone <list>` | Find direct mobile numbers |
| `/outreach verify <list>` | Verify the addresses you brought yourself, not the ones Emelia found |
| `/outreach enrich <list>` | Find what is missing, verify only what needs it, decide row by row |
| `/outreach write <angle>` | Subjects, openers, follow-ups, break-up |
| `/outreach personalize <list>` | Icebreakers and AI variables per contact |
| `/outreach sequence <spec>` | Steps, delays, conditions, A/B tests |
| `/outreach deliverability` | SPF, DKIM, DMARC, warmup, volume, ramp plan |
| `/outreach campaign <spec>` | Create and launch in Emelia |
| `/outreach replies` | Triage replies, draft answers, handle opt-outs |
| `/outreach audit <campaign>` | Rates per step and variant, against benchmarks |

Full reference in [docs/COMMANDS.md](docs/COMMANDS.md).

## What it does

**An offer, not a job description.** The first reason a sequence gets no reply is not
the copy, it is that the sender sells something generic. "We do SEO" is a line any
competitor could put their logo on. `/outreach offer` reads your site, names the
sentence everyone in your category writes, and works with you until what you sell is
specific enough to answer.

**Targeting that survives contact with reality.** Most campaigns fail before the
first email because the list is wrong. `/outreach icp` turns "SaaS companies" into
a spec with titles, headcount, industry codes, geography and exclusions, and makes
you confirm it before a single credit is spent.

**Enrichment that respects your budget.** Finding an email costs money. The skills
count the rows, tell you the cost, and filter before enriching rather than after.
What Emelia's finder returns is already verified, so it never goes to the verifier a
second time. Rows that cannot be found are reported as not found, never quietly dropped.

**Copy that is checked, not just generated.** Spam trigger words, variables that do
not exist in your list, subjects that get truncated on mobile, follow-ups that repeat
the first email: all caught before you send.

**Deliverability as a gate.** The campaign does not launch if warmup is off, if SPF,
DKIM or DMARC is missing, or if the daily volume is above what your mailboxes can
carry. This is the single most common reason outbound fails, so it blocks.

**Replies handled like a human would.** Interested, meeting request, not now, out of
office, unsubscribe: sorted, drafted, and left for you to send.

**Numbers you can act on.** Per step and per variant, against real benchmarks, with
one recommendation rather than a dashboard.

## Where the data comes from

| Source | Coverage | What you need |
|--------|----------|---------------|
| [Basile](https://basile.cc) | French companies and decision makers, including SMEs | A Basile API key |
| LinkedIn | Anywhere, role and account based | A Sales Navigator search plus Emelia |
| Your CSV | Whatever you already have | Nothing |

Emails, mobile numbers and verification go through [Emelia](https://emelia.io) and
are billed in credits. Nothing is bought from grey market brokers, and nothing is
scraped outside the official integrations.

## Compared to the alternatives

| | Doing it by hand | A sales engagement suite | This |
|---|---|---|---|
| Building the list | Hours in a spreadsheet | Built in, rigid filters | Described in a sentence, refined with you |
| Enrichment cost control | You find out on the invoice | Credit packs, opaque | Counted and confirmed before every run |
| Copy | You write it | Templates | Written with you, then checked |
| Deliverability | A checklist you skip | A score in a tab | A gate that blocks the launch |
| Reply handling | Inbox roulette | Labels you configure | Sorted and drafted |
| What you own | Everything | A seat | Every file, on your machine |
| Cost | Your time | Per seat, per month | Free, plus what you send |

## Use cases

- Launch a first campaign on a market you have never sold to, in an afternoon.
- Take a list of 4,000 rows you bought last year, clean it, verify it, and find out
  what is still usable before spending a credit on it.
- Rewrite a sequence that gets opens but no replies, and know whether the problem is
  the copy or the targeting.
- Audit why your emails land in spam, and get the ramp plan that fixes it.
- Run the same playbook across five client accounts without five spreadsheets.

## Sample output

```
/outreach audit "Q4 SaaS founders"

Campaign: Q4 SaaS founders, email + LinkedIn, 1,248 contacts, 21 days

  Delivered          1,203   96.4%   healthy, bounce rate 1.1%
  Opened               781   64.9%   above the 55% median
  Replied               71    5.9%   top quartile for cold B2B
  Interested            23    1.9%   32% of replies, strong offer fit
  Meetings booked        9

Step 2 is carrying the campaign: 41 of the 71 replies. Step 4 adds 3 replies and
7 unsubscribes, it is costing you more than it returns.

Variant B of step 1 wins on replies (6.8% against 4.9%), losing on opens. The
subject is worse, the body is better.

Recommended: cut step 4, promote variant B, and reuse the step 2 angle as the
opener of the next campaign.
```

## Architecture

```
claude-outreach/
  .claude-plugin/     plugin and marketplace manifests
  skills/
    outreach/         the dispatcher, /outreach <command>
    outreach-icp/     targeting
    outreach-leads/       outreach-filter/
    outreach-find-email/  outreach-find-phone/
    outreach-verify/      outreach-enrich/
    outreach-write/       outreach-personalize/    outreach-sequence/
    outreach-deliverability/  outreach-campaign/   outreach-replies/
    outreach-pilot/       the guided first campaign
  agents/             5 sub-agents for parallel work
  docs/               commands, architecture, data sources, setup, troubleshooting
  scripts/            shared helpers
  tests/              frontmatter, structure and link checks
```

Each skill is a single Markdown file that Claude loads only when it is relevant.
Nothing runs in the background, nothing phones home.

## Method

1. **Targeting before tooling.** A better list beats better copy, every time.
2. **Filter before you enrich.** Credits spent on rows you will delete are wasted.
3. **Verify before you send.** Bounces cost reputation, reputation costs everything.
4. **One variable at a time.** A/B the subject or the body, not both.
5. **Volume follows reputation, not ambition.** Ramp, do not spike.
6. **Reply rate is the metric.** Opens are a proxy that Apple broke.
7. **Every claim in a message must be true.** Fabricated personalization is worse
   than none.
8. **The user confirms anything that costs money or reaches a human.**

## Requirements

- [Claude Code](https://claude.com/claude-code)
- An [Emelia](https://emelia.io) account for enrichment and sending. The free trial
  is enough to run the pilot.
- Optional: a [Basile](https://basile.cc) API key for French B2B data.
- Optional: Python 3 for the test suite.

## Limits

This does not place calls. It does not scrape LinkedIn outside the official Emelia
integration. It cannot tell you an address is deliverable when the domain is
catch-all, and it says so rather than guessing. It will not write a message that
hides who is sending or how to opt out. And it cannot fix an offer nobody wants:
when the copy is not the problem, it says the copy is not the problem.

## FAQ

**Do I need an Emelia account?**
For enrichment and sending, yes. Everything else, including building and cleaning
the list and writing the sequence, runs in dry run without any key.

**Does this work outside France?**
Yes. Basile covers French companies specifically; LinkedIn and your own CSVs cover
everywhere, and enrichment and sending are global.

**Will my emails land in spam?**
Not if you follow what `/outreach deliverability` tells you, which is why it blocks
the launch when the setup is not ready.

**Can I use it with a different sending tool?**
The sourcing, cleaning, copy and sequence design produce plain files that work
anywhere. The launch and reply steps are built on Emelia.

**Is my data sent anywhere?**
Files stay on your machine. Calls go to the APIs you configured, and nowhere else.

## Contributing

Issues and pull requests are welcome. Read
[docs/SKILL-CONVENTIONS.md](docs/SKILL-CONVENTIONS.md) first: it is short, and it is
what keeps the skills consistent. Run `python3 tests/run.py` before opening a PR.

## License

MIT. Use it, fork it, ship it.

Built by the team behind [Emelia](https://emelia.io), the all-in-one B2B prospecting
platform: multichannel campaigns, email finder, verifier, phone finder, warmup and a
unified inbox, from one tool.
