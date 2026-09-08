---
name: outreach-icp
description: "Turn a vague outbound brief such as 'sell our tool to SaaS companies' into a targeting spec that a data source can actually execute: job titles with their real per-country variants, industries with NAF, NAICS and SIC codes, headcount band, geography, technographics, buying signals, and the exclusions that keep customers, competitors and unpayable prospects out of the list. Estimates the addressable market with free count calls before a single credit is spent, and splits the brief into separate campaigns when it covers too many audiences. Reads a brief in plain language, writes outreach/icp.json. Triggers on: ICP, ideal customer profile, targeting, target audience, who should I target, define my market, segment, segmentation, persona, buyer persona, job titles, NAF code, NAICS, SIC, headcount, firmographics, technographics, buying signals, exclusion list, TAM, addressable market, market sizing."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Define the ICP

## What this does

Takes a one line brief and turns it into `outreach/icp.json`, a targeting spec precise
enough that [outreach-leads](../outreach-leads/SKILL.md) can run it against Basile,
LinkedIn or a CSV without guessing. It writes down the titles, the industry codes, the
size band, the geography, the signals and, above all, the exclusions. It counts the
market for free before anything is extracted, and it refuses to hide three audiences
inside one campaign.

No credits are spent here. Counting is free on every source this repository uses.

## When to use it

Use it at the start of every campaign, and again whenever a campaign underperforms and
you suspect the list rather than the copy. A 1% reply rate with good deliverability is
almost always a targeting problem.

Use a different skill when:

- You already have `outreach/icp.json` and want contacts: go to
  [outreach-leads](../outreach-leads/SKILL.md).
- You already have a list and want it cleaned: go to
  [outreach-filter](../outreach-filter/SKILL.md).
- You know exactly who you want by name (a named account list): skip the ICP, write the
  account list straight into the leads step, and come back here only if it stops scaling.

## Inputs

| Input | Required | If missing |
|---|---|---|
| The brief, in plain language | yes | Ask for it in one question: what do you sell, to whom, and what does a deal cost you? |
| What the product costs | yes | Ask. Price sets the headcount floor. Without it the list will be full of companies that cannot pay. |
| Existing customer domains | strongly recommended | Ask for a CRM export, any CSV with a domain column. If there is none, say the list will contain customers and that you will catch them later in `outreach-filter`. |
| Competitor domains | recommended | Ask for three or four names, derive the domains. |
| Basile API key (`BASILE_API_KEY`) | optional | Without it you cannot count the French market. Say so, keep the spec, mark `size_estimate.method` as `"not measured"`. |
| Sales Navigator seat | optional | Without it you cannot count the LinkedIn market. Same treatment. |

Never invent a headcount band, a price point or a list of customers. Ask, or record the
gap in `open_questions` inside the output file.

## How to do it

### 1. Read the brief back, narrower

Restate the brief as a single sentence in this shape, and get a yes before continuing:

> We sell `<what>` to `<title>` at `<kind of company>` of `<size>` in `<geography>`,
> who have `<problem>`, and a deal is worth about `<amount>`.

Anything the user cannot fill in is an open question, not a value you choose for them.

### 2. Titles, with the variants that actually exist

A title filter written in one language and one country finds a fraction of the market.
Write every variant a real person puts on a real profile, in every language of the
target geography. These are starting points, not a nomenclature.

| Function | English | French | Other |
|---|---|---|---|
| General management | CEO, Chief Executive Officer, Founder, Co-Founder, Owner, Managing Director, President | PDG, President, Directeur General, DG, Gerant, Fondateur, Cofondateur, Dirigeant | Geschaftsfuhrer, Inhaber (DE), Director General, Gerente (ES), Amministratore Delegato (IT), Zaakvoerder (NL) |
| Sales | VP Sales, Head of Sales, Sales Director, CRO, Sales Manager | Directeur Commercial, Responsable Commercial, Directeur des Ventes | Vertriebsleiter (DE), Director Comercial (ES) |
| Marketing and growth | CMO, VP Marketing, Head of Marketing, Head of Growth, Demand Generation | Directeur Marketing, Responsable Marketing, Responsable Acquisition | Marketingleiter (DE) |
| Technology | CTO, VP Engineering, Head of Engineering, Head of Platform, Head of Infrastructure | Directeur Technique, DSI, Directeur des Systemes d'Information, Responsable Informatique | Technischer Leiter (DE) |
| Finance | CFO, Finance Director, Head of Finance, Financial Controller | DAF, Directeur Administratif et Financier, Directeur Financier | Kaufmannischer Leiter (DE) |
| People | CHRO, HR Director, Head of People, Talent Acquisition | DRH, Responsable RH, Responsable des Ressources Humaines | Personalleiter (DE) |

Write the accented and unaccented spelling of every French title, because sources differ
on both. Basile matches accent insensitively, LinkedIn does not always.

Three traps worth writing into the spec:

- **`Directeur` is not `Directeur General`.** A bare `Directeur Commercial` is a sales
  lead; `Directeur General` is the company boss. A substring filter on `Directeur`
  returns both, plus `Directeur Adjoint`. Put the full phrases in `include`.
- **In France the legal title and the job title differ.** `Gerant` is the statutory
  officer of a SARL, `President` of a SAS. On small companies that person is the buyer,
  and they may describe themselves on LinkedIn as `Fondateur`. Search both the legal
  role and the free text role, then deduplicate.
- **Junior lookalikes must be excluded, not ignored.** Always populate
  `titles.exclude` with at least: assistant, adjoint, adjointe, stagiaire, alternant,
  apprenti, intern, junior, `charge de`, `chargee de`, freelance, independant,
  consultant, retraite, `open to work`.

### 3. Industry, with codes and with doubt

Write the industry in three ways: as words, as codes, and as the filter your source
actually accepts.

**France, NAF codes.** NAF revision 2 (2008) is still the reference for the APE code
assigned to a company until 1 January 2027, when NAF 2025 takes over; during 2026 the
Sirene registry shows both codes (source: INSEE, insee.fr/fr/information/8181066).
Accept both revisions in a spec written now. Software and IT examples: `62.01Z`
programmation informatique, `62.02A` conseil en systemes et logiciels informatiques,
`62.02B` tierce maintenance, `62.03Z` gestion d'installations informatiques, `62.09Z`
autres activites informatiques, `63.11Z` traitement de donnees et hebergement, `63.12Z`
portails internet, `58.29A` `58.29B` `58.29C` edition de logiciels, `70.22Z` conseil
pour les affaires, `73.11Z` agences de publicite.

**United States, NAICS.** `511210` software publishers, `541511` custom computer
programming services, `541512` computer systems design services, `518210` computing
infrastructure, data processing and hosting, `541611` management consulting.

**United States, legacy SIC.** `7372` prepackaged software, `7371` custom computer
programming, `7379` computer related services. Some databases still only carry SIC.

**United Kingdom, SIC 2007.** `62012` business and domestic software development,
`62020` IT consultancy, `63110` data processing and hosting.

The doubt matters as much as the codes. A company's NAF or SIC code is declared once at
registration and almost never updated, so a ten year old SaaS is routinely filed under
`70.22Z` (consulting) or `62.01Z` (programming) rather than under software publishing.
Never let an industry code be the only industry filter. Pair it with at least one of:
the Basile `activity` concept (which merges NAF, LinkedIn and Google categories),
the LinkedIn industry, a headcount band, or a keyword on the company name or website.

### 4. Headcount, set by your price and not by your taste

The floor is arithmetic. A company will not buy a tool that costs more than a small
share of what it already spends on the problem. Work it backwards:

1. What does one deal need to be worth for the campaign to pay for itself?
2. If you charge per seat, how many seats does that need?
3. How many employees does a company need for that many seats to exist?

That number is `headcount.min`, and you write the reasoning into `headcount.basis` so
the next person does not relax it by accident. Two practical markers, offered as rules
of thumb rather than measurements: below roughly 10 employees the founder is the buyer,
the cycle is short and the budget is small; above roughly 500 there is a procurement
process that cold email does not survive on its own.

The ceiling is about who answers. Write it down even when it feels obvious.

### 5. Geography

Record `countries` as ISO 3166-1 alpha-2 codes, because that is what both Emelia's email
finder and Basile use. Add regions, cities or postal codes only when they change the
message. Add `exclude_countries` when a market is served by someone else or is out of
scope for legal reasons.

For France specifically: department is the first two digits of the postal code, except
Corsica (`2A`, `2B`, postal codes starting `20`) and the overseas departments, whose
codes are three digits (`971` to `978`). Get this wrong and you silently drop or add a
whole region.

### 6. Technographics

Useful when your product replaces or plugs into something. Be honest about detection:
neither Basile nor a Sales Navigator search carries a technology filter. You detect a
technology from the prospect's own site, their job postings, or a public directory, and
you record how in `technographics.how_detected`. If you cannot name the detection
method, drop the criterion instead of pretending it is filterable.

### 7. Buying signals

A signal is only worth listing if you can name the filter that implements it. For each
one record the source, the filter, the window in days, and whether it is strong.

| Signal | Implementable with | Reality |
|---|---|---|
| Company recently created | Basile `created_since_months` on companies | Direct filter, reliable |
| New in role | Basile `current_tenure_years` (LinkedIn source), or the Sales Navigator changed-jobs filter | Direct, but LinkedIn source only |
| Alumni of a company you know | Basile `past_employer` | Direct, LinkedIn source only |
| Headcount growth | Sales Navigator company growth filter | Pick it in the interface, no public API |
| Hiring for a role you serve | Job boards, read manually or from your own scraper | Not a filter, an input list you build |
| Raised funding | Public announcements, your own list | Not a filter on either source. Bring the account names in as a CSV |
| Leadership change | Press, LinkedIn posts | Not a filter |

Signals that cannot be filtered are still valuable: they become a named account list fed
into `outreach-leads`, and they become the first sentence of the email.

### 8. Exclusions, the part that saves the campaign

An ICP without exclusions produces a list that emails your own customers. Fill every
one of these, and write `"none"` explicitly rather than leaving a blank:

- **Existing customers.** By domain, ideally from a CRM export. Also add their parent
  and subsidiary domains if you know them.
- **Open opportunities.** Emailing a live deal from a cold sequence is worse than
  emailing a customer.
- **Competitors.** By domain. They sign up for everything.
- **Forbidden or pointless sectors.** By code where possible. Typical ones: public
  administration, primary and secondary education, hospitals, religious and political
  organisations, and any sector your legal or brand rules exclude. Write the reason.
- **Too small to pay.** This is `exclusions.min_headcount`, and it is the same number as
  `headcount.min`. Duplicating it here is deliberate: the filter step reads exclusions.
- **Already contacted.** A recontact window in days (90 is a common default, offered as
  a rule of thumb). Anyone in a campaign more recently than that is out.
- **Unsubscribes and hard bounces.** These live in the Emelia blacklist and in your local
  mirror `outreach/blacklist.txt`. Never re-add them.
- **Role addresses.** Decide now: `drop` or `keep`. Drop them when you target a named
  role at a company with real staff. Keep them (as their own segment, with their own
  message) when you target micro-businesses where `contact@` is the only address the
  company has.

### 9. Size the market before spending anything

Counting is free on both sources. Do it as a ladder, one filter at a time, and write
every step into `size_estimate.ladder`.

**Basile (France).** `POST https://api.basile.cc/people/find` with header
`Authorization: <your key>` (the raw key, no `Bearer` prefix) and `Content-Type:
application/json`. Send `{"countOnly": true, "filters": {...}}`. The response carries
`total` and an empty `leads` array, and nothing is charged. Do not use `limit: 1` to
count: that returns one record and costs one credit. Run one call per rung:

1. Geography only.
2. Geography plus industry.
3. Plus headcount.
4. Plus titles.
5. Minus the exclusions you can express as filters.

**LinkedIn.** Build the Sales Navigator search described in
[outreach-leads](../outreach-leads/SKILL.md) and read the result count above the list.
It is free and it is the same ladder.

Then read the ladder rather than only the last number. The rung that divides the count
by more than about ten is the rung that defines your campaign; check it says what you
meant. A title list that cuts a market by fifty is usually missing variants, not finding
a niche.

**From addressable to reachable.** The count is profiles, not inboxes. Do not budget on
it. Take a random sample of 100 rows, run the email finder on it (that costs 100
credits, announce it and wait for an explicit yes), and measure your own find rate.
Record it as `assumed_email_rate` with the date. Rates vary widely by source and
country, so a measured rate on your own sample beats any published average.

### 10. The three segment rule

If the spec needs more than three segments, it is more than one campaign.

A segment is a group that deserves a different first sentence. Two groups that would
receive the same opening line are one segment, whatever the filters say. A CTO at a
40 person SaaS and a CTO at a 40 person e-commerce company are two segments if your
value proposition differs, one segment if it does not.

When you count four or more, stop and say so: propose the top three by expected value,
and put the rest in a second campaign to run afterwards. Explain the reason plainly: a
campaign with four messages is four campaigns with a quarter of the volume each, and
none of them will have enough replies to tell you anything.

Also enforce a floor. Below roughly 150 contacts a segment produces single digit
replies, and single digit replies cannot separate a good message from a bad one. Merge
segments that small.

## Output

Write `outreach/icp.json`. Never overwrite a previous run silently: if the file exists,
show what changes and ask, or write `outreach/icp-<name>.json`.

Schema, every key required unless marked optional:

```
version              integer, always 1
created_at           ISO date
brief                the original sentence, verbatim
offer                what, problem, proof, price_point, minimum_viable_deal
segments[]           1 to 3 entries, each:
  id                 slug, used as the segment value in leads.csv
  label              human name
  why_different      one sentence: what changes in the message for this group
  priority           1 is first
  titles             include[], exclude[], seniority[] (optional), notes
  industry           naf[], naics[], sic[], basile_activity[], linkedin_industry[], notes
  headcount          min, max, basis
  geography          countries[], regions[], cities[], postal_codes[], exclude_countries[]
  technographics     uses[], does_not_use[], how_detected     (optional)
  signals[]          name, window_days, source, filter, weight (strong|weak)
  size_estimate      counted_at, source, ladder[{step,total}], addressable,
                     assumed_email_rate, reachable, method
exclusions           customer_domains[], customer_domains_file, competitor_domains[],
                     forbidden_industries{naf[],naics[],reason}, blacklist_file,
                     min_headcount, recontact_window_days, role_addresses (drop|keep),
                     notes
message_hooks[]      optional, phrases the copy step can reuse
open_questions[]     anything you had to leave undecided, in plain language
```

A filled example:

```json
{
  "version": 1,
  "created_at": "2026-09-08",
  "brief": "sell our API monitoring tool to CTOs of French SaaS, 20 to 200 people",
  "offer": {
    "what": "API uptime and latency monitoring with alerting",
    "problem": "outages found by customers before the team sees them",
    "proof": "3 minute setup, 40 teams switched from a homemade cron",
    "price_point": "90 EUR per month per project",
    "minimum_viable_deal": "1080 EUR per year"
  },
  "segments": [{
    "id": "fr-saas-cto",
    "label": "CTO at French SaaS, 20 to 200 employees",
    "why_different": "opens on their public status page, or the absence of one",
    "priority": 1,
    "titles": {
      "include": ["CTO", "Chief Technology Officer", "Directeur Technique",
                  "VP Engineering", "Head of Engineering", "Head of Platform",
                  "Responsable Technique"],
      "exclude": ["assistant", "adjoint", "stagiaire", "alternant", "junior",
                  "charge de", "freelance", "consultant"],
      "seniority": ["C-Level", "VP", "Director", "Head"],
      "notes": "DSI excluded on purpose: internal IT, not product engineering"
    },
    "industry": {
      "naf": ["62.01Z", "62.02A", "58.29C", "63.11Z"],
      "naics": [], "sic": [],
      "basile_activity": ["<concept ids from GET /companies/activity-suggest?q=logiciel>"],
      "linkedin_industry": ["Software Development", "IT Services and IT Consulting"],
      "notes": "NAF alone misses SaaS filed under 70.22Z, so activity is ORed with it"
    },
    "headcount": {
      "min": 20, "max": 200,
      "basis": "below 20 no dedicated engineering owner and no budget line; above 200 an observability vendor is already in place"
    },
    "geography": {
      "countries": ["FR"], "regions": [], "cities": [],
      "postal_codes": [], "exclude_countries": []
    },
    "technographics": {
      "uses": ["public status page", "public REST API"],
      "does_not_use": ["Datadog", "New Relic"],
      "how_detected": "manual check of the company site on the top 200 rows only. Not filterable at source"
    },
    "signals": [
      { "name": "new CTO in the last 12 months", "window_days": 365,
        "source": "basile", "filter": "current_tenure_years <= 1", "weight": "strong" },
      { "name": "raised a seed or series A in the last 6 months", "window_days": 180,
        "source": "manual account list", "filter": "none, brought in as a CSV of company names",
        "weight": "strong" }
    ],
    "size_estimate": {
      "counted_at": "2026-09-08", "source": "basile",
      "ladder": [
        { "step": "FR only", "total": 4210000 },
        { "step": "+ software and IT activity", "total": 96400 },
        { "step": "+ headcount 20 to 200", "total": 11800 },
        { "step": "+ CTO title variants", "total": 3140 },
        { "step": "- customers and competitors", "total": 3082 }
      ],
      "addressable": 3082,
      "assumed_email_rate": 0.58,
      "reachable": 1788,
      "method": "countOnly on POST /people/find, five free calls. Email rate measured on a random sample of 100 rows on 2026-09-08, 58 found"
    }
  }],
  "exclusions": {
    "customer_domains": ["acme.fr", "beta-labs.io"],
    "customer_domains_file": "outreach/customers.csv",
    "competitor_domains": ["datadoghq.com", "newrelic.com", "checkly.com"],
    "forbidden_industries": {
      "naf": ["84.11Z", "85.31Z", "86.10Z"], "naics": [],
      "reason": "public sector and health, procurement incompatible with self serve"
    },
    "blacklist_file": "outreach/blacklist.txt",
    "min_headcount": 20,
    "recontact_window_days": 90,
    "role_addresses": "drop",
    "notes": "customers exported from the CRM on 2026-09-05, 214 domains"
  },
  "message_hooks": [
    "you found out from a customer, not from a dashboard",
    "the cron job that checks the API and nobody maintains"
  ],
  "open_questions": [
    "no list of open opportunities was provided, so live deals may be in the list"
  ]
}
```

Then tell the user, in three lines: how many contacts the spec is worth, what the
biggest single cut was, and what you had to guess. Wait for a yes before anyone runs
`outreach-leads`.

## Checks before finishing

- `outreach/icp.json` parses as JSON and has between 1 and 3 segments.
- Every segment has a non empty `titles.include` and a non empty `titles.exclude`.
- Every segment has at least two independent industry signals, or an explicit note
  saying why one is enough.
- `headcount.min` is a number and `headcount.basis` explains it in terms of price.
- `geography.countries` uses ISO 3166-1 alpha-2 codes.
- Every entry in `signals[]` names a real filter or says `"none"` and how the list is
  built instead.
- Every key of `exclusions` is filled, `"none"` included, and `min_headcount` matches
  `headcount.min`.
- `size_estimate.ladder` has at least three rungs, or `method` says `"not measured"` and
  the reason.
- `assumed_email_rate` is either measured on a real sample (with the date) or absent.
  Never invent it.
- The user has confirmed the restated brief and the segment count out loud.

## Failure modes

**The brief is a product description, not a market.** "We sell an AI agent platform" has
no buyer in it. Ask who is currently doing the work by hand, and target their manager.

**Titles return almost nothing.** Usually a missing language or a full phrase used where
a fragment was needed. Run the title list through a suggestion endpoint before trusting
it: Basile exposes `GET /people/roles/suggest?q=` for exactly this.

**The count collapses at the industry rung.** The industry code is doing all the work and
it is probably wrong for this market. Loosen the code, tighten the headcount, and check
ten known companies: if fewer than seven of them appear, the filter is broken.

**The count is enormous.** Anything above a few hundred thousand people means a filter
did not apply. A common cause on Basile is sending a filter the API ignores; the public
documentation flags `headquarters_region_code` as removed at validation, so a region
filter written that way restricts nothing. Use `headquarters_postal_code` or the region
name instead, and recount.

**Four or more segments.** Do not compromise by merging them into a vague message. Say
it is three campaigns and propose an order.

**The user pushes back on exclusions.** "We can email our customers, it is fine" is the
one to resist. It is the fastest way to a complaint, and complaints follow the domain,
not the campaign.

## Limits

This skill does not buy or verify data, does not check whether a company can actually
afford your product, and does not know your win rates. The industry code lists above are
starting points, not an exhaustive nomenclature: verify a code before you build a
campaign on it. Buying signals that are not filterable stay manual, and this skill says
so rather than implying a filter exists. Nothing here estimates revenue: an addressable
count is a count of people, not of pipeline.
