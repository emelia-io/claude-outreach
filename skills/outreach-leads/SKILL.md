---
name: outreach-leads
description: "Build the lead list from the three sources this repository supports: the Basile API for French B2B (count for free with countOnly, then export), a LinkedIn Sales Navigator search built from the ICP and collected through the Emelia LinkedIn scraper, or a CSV the user already has (encoding, separator and column mapping handled). Writes outreach/leads.csv with a fixed 26 column schema that every other skill in this repository reads, including a source and a source_url column on every row. Reads outreach/icp.json, a Sales Navigator URL or a file path. Triggers on: build a list, lead list, source leads, find companies, find prospects, Basile, api.basile.cc, French companies, SIREN, NAF, Sales Navigator, LinkedIn search, LinkedIn scraper, scrape LinkedIn, import CSV, upload a list, column mapping, leads.csv, export contacts, count before extracting."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Build the lead list

## What this does

Turns a targeting spec into `outreach/leads.csv`, one row per contact, from Basile,
from a LinkedIn Sales Navigator search, or from a CSV the user already has. The output
schema is fixed and is the contract every other skill in this repository reads, so the
mapping work happens here once and nowhere else.

Basile counting is free and always happens before extraction. Basile extraction costs
Basile credits (1 per record returned), so it is announced and confirmed. No Emelia
credits are spent here: finding and verifying emails happens later, after
[outreach-filter](../outreach-filter/SKILL.md) has cut the list down.

## When to use it

Use it after [outreach-icp](../outreach-icp/SKILL.md) has produced a spec you agreed to,
or when the user arrives with a CSV or a Sales Navigator URL and wants it turned into a
workable list.

Use a different skill when:

- The list exists and needs cleaning, deduplicating or segmenting: `outreach-filter`.
- The list exists and needs email addresses: `outreach-enrich`. Filter first.
- You do not yet know who you are targeting: go back to `outreach-icp`. Sourcing before
  targeting produces a large list nobody can write to.

## Inputs

| Input | Required | If missing |
|---|---|---|
| `outreach/icp.json` | for Basile and LinkedIn | Ask, or accept a plain description and write a throwaway spec first. Do not source from a one line brief. |
| `BASILE_API_KEY` | for Basile | Say Basile is unavailable, offer LinkedIn or a CSV. Do not fall back to guessing French company data. |
| A Sales Navigator URL, or a seat to build one | for LinkedIn | Ask the user to build the search and paste the URL. You cannot construct the opaque ids yourself. |
| `EMELIA_API_KEY` or the Emelia MCP server | to collect a LinkedIn scrape | Ask the user to export the list as CSV from the Emelia app and treat it as a CSV source. |
| A CSV path | for the CSV route | Ask for the path. |
| Target volume | recommended | Default to the whole segment, but state the count and the credit cost before extracting. |

## How to do it

### 0. The column contract

`outreach/leads.csv` has exactly these 26 columns, in this order, always, whatever the
source. This is a contract: `outreach-filter`, `outreach-enrich`, `outreach-personalize`
and `outreach-campaign` all read these names.

```
lead_id, first_name, last_name, full_name, job_title, seniority,
email, email_status, phone, phone_status, linkedin_url,
company_name, company_domain, company_website, company_linkedin_url,
company_headcount, company_industry, company_naf, company_siren,
city, country_code, segment, signal, source, source_url, collected_at
```

File rules:

- UTF-8 without BOM, comma separated, RFC 4180 quoting (double the quote inside a
  quoted field), LF line endings, header on line 1.
- An empty cell means unknown. Never write `N/A`, `null`, `-` or `unknown`.
- The 26 are never renamed, reordered or removed. Later skills append their own columns
  after `collected_at` (the enrichment step adds `send_decision`, the phone step adds
  `phone_country` and `phone_type`, the personalization step adds its icebreakers), and
  that is expected. Prefix a column `x_` when it is a source specific or diagnostic
  detail, so it cannot collide with a column a later step wants to own.

Field rules:

- `lead_id`: `<source>:<id at the source>`, for example `basile:64f0a...` or
  `linkedin:jane-doe-1a2b`. For a CSV without an id, use `csv:<line number>`. It must be
  stable across re-runs so a second pass can be merged rather than duplicated.
- `full_name`: fill it even when you have first and last, because the Emelia email
  finder takes `fullname`, not the parts.
- `email_status`: empty, `found`, `not_found`, `valid` or `invalid`. Emelia returns only
  `valid` or `invalid` as a qualification, so do not invent `risky` or `catch_all`
  values here. Leave it empty at this stage.
- `phone_status`: empty, `found` or `not_found`. The phone step may write a more precise
  reason in place of `not_found` (for example `no_linkedin_url`, since the phone finder
  needs one); treat any value other than `found` as "no usable number".
- `company_domain`: the registrable domain, lowercased, no scheme, no `www.`, no path.
  This is the dedup and exclusion key, so it matters more than `company_website`.
- `company_headcount`: an integer number of employees. When the source only gives a
  band, write the lower bound and put the band in `x_headcount_band`.
- `country_code`: ISO 3166-1 alpha-2, uppercase.
- `segment`: the `id` of the segment in `icp.json` this row belongs to. Never empty when
  an ICP exists.
- `signal`: short free text, the reason this row is timely, if any.
- `source`: exactly one of `basile`, `linkedin`, `csv`, `manual`.
- `source_url`: the URL that lets a human re-check this row. Basile:
  `https://api.basile.cc/people/<id>`. LinkedIn: the Sales Navigator search URL the row
  came from. CSV: `file:<path of the original file>`.
- `collected_at`: ISO date of the extraction.

How the contract maps onto Emelia later, so you can see why these names exist:
`first_name` becomes `firstName`, `last_name` becomes `lastName`, `email` becomes
`email`, `phone` becomes `phone`, `linkedin_url` becomes `linkedinUrlProfile`,
`company_name` becomes `companyName`, `company_website` becomes `websiteUrl`. Everything
else becomes a custom variable. `full_name` plus `company_name` is what the email finder
needs; `linkedin_url` is what the phone finder needs.

### 1. Basile, for France

Base `https://api.basile.cc`. Header `Authorization: <your key>` with the raw key and
**no `Bearer` prefix**, plus `Content-Type: application/json`. Public documentation:
https://docs.basile.cc, with the full spec at https://docs.basile.cc/openapi.yaml.

**Write the filters.** Every text filter has the same shape:

```json
{ "include": ["Directeur Technique", "CTO"], "exclude": ["adjoint", "assistant"] }
```

`include` is OR between its values, `exclude` removes anything matching, and two
different filters combine with AND. Numeric filters use bounds:
`{ ">=": 20, "<=": 200 }`.

People filters worth knowing, from the public spec:

| Filter | Type | Note |
|---|---|---|
| `result_role` | text | Free text job title. Put every variant from the ICP here |
| `activity` | text | Sector, unified across NAF, LinkedIn and Google. The best sector filter |
| `company_headcount` | range | Size of the contact's **current** employer, multi source |
| `result_country_code`, `result_city` | text | Where the person is |
| `employer` | text | Current employer. A value in quotes is an exact match, bare is contains |
| `siren` | text | Every officer and LinkedIn employee of that company |
| `hide_legal_entities` | boolean | Set `true`. Hides companies listed as people, without excluding LinkedIn |
| `result_is_current` | boolean | Registry only. Current mandate only |
| `mandate_role` | text | Registry only. Fixed codes: `gerant`, `president`, `dg`, `dgd`, `administrateur`, `commissaire_comptes`, `associe`, `directeur_non_dg`, `autre` |
| `current_seniority`, `current_job_functions` | text | LinkedIn only |
| `current_tenure_years` | range | LinkedIn only. Years in the current role, the new-in-seat signal |
| `past_employer`, `past_title`, `skills`, `education` | text | LinkedIn only |

**The trap that costs the most.** Basile merges two people sources, the legal registry
and LinkedIn. Switching on a registry-only filter drops every LinkedIn profile, and
switching on a LinkedIn-only filter drops every officer from the registry. So combining
`mandate_role` with `current_seniority` returns nothing at all, and adding
`result_is_current` to a title search silently halves a market. Pick one source per
query when you need source-specific filters, and run two queries if you need both.

**Two filters that save a detour.** `activity` and `company_headcount` both work
directly on `/people/find`, meaning sector and size of the employer without querying
companies first. The public documentation says so explicitly: do not chain
`/companies/find` then `/people/find` to filter by sector or size. Go through companies
only when you start from named accounts or from Google listings. Note that
`company_headcount` excludes records with no known headcount, around 21% on a French
sample per the same documentation, so it is a real cut and not a free refinement.

**Resolve the sector before using it.** `GET /companies/activity-suggest?q=logiciel`
returns concept ids to put in `activity`. The filter also accepts `naf:`, `lki:` and
`gmb:` prefixes. Check titles the same way with `GET /people/roles/suggest?q=directeur`.
Both are free.

Company filters, when you do need them: `naf_code` (accepts a prefix such as `62.x` or
an exact `62.01Z`), `headquarters_postal_code` (the reliable geographic filter, takes
long lists), `headquarters_city` (case and accent insensitive, matches by prefix, so one
spelling is enough), `headquarters_country_code`, `company_ceased` (set `false`),
`headcount_min` and `headcount_max`, `created_since_months` for companies created in the
last N months, `creation_date_min` and `creation_date_max`, `domain`, `legal_form`,
`rating_min` and `reviews_min` for Google data.

Two documented traps: `headquarters_region_code` is stripped at validation and restricts
nothing, so use `headquarters_postal_code` or the `region` name in its canonical spelling
instead; and `creation_date_min` takes a **year** (`2015`), a full date being silently
ignored, which returns an unfiltered result that looks filtered.

**Count first, always.** Counting is free and unlimited:

```bash
curl -s https://api.basile.cc/people/find \
  -H "Authorization: $BASILE_API_KEY" -H "Content-Type: application/json" \
  -d '{"countOnly":true,"filters":{
        "result_role":{"include":["CTO","Directeur Technique","VP Engineering"]},
        "activity":{"include":["<concept id from activity-suggest>"]},
        "company_headcount":{">=":20,"<=":200},
        "result_country_code":{"include":["FR"]},
        "hide_legal_entities":true}}'
```

The response has `total` and an empty `leads` array, and nothing is charged. Never count
with `limit: 1`: that returns one record and costs one credit.

**Then extract, once, with the count in hand.** State the number and the cost (1 Basile
credit per record returned) and wait for an explicit yes.

`POST /people/export` with the same `filters` returns a CSV of 79 columns: 22 on the
person, 18 on their LinkedIn company, 18 on their company at the legal registry, 11 from
Google Maps and 6 presence flags. It is streamed, so one call covers the whole result up
to the plan's per-export ceiling. Read the response headers: `X-Export-Max-Rows` is the
ceiling and `X-Export-Capped: true` means results were cut off. When capped, split the
search into segments (by department, by NAF code, by creation year) and export each.

Use `POST /people/find` instead only when you want JSON. Be aware of what it does not
return: the person, their role, their LinkedIn URL and the **name** of their employer,
but none of that employer's data, no SIREN, no NAF, no headcount. If you build
`leads.csv` from `/find`, the company columns stay empty. Paginate with
`paginationToken` from `pagination.nextToken`; page 2 and beyond require an active
subscription. `idsOnly: true` returns only `{_id, source}` and allows `limit` up to 5000
on people, which is the cheap way to collect ids before a `POST /people/export` with
`{"ids": [...]}`.

`POST /companies/find` is the mirror for companies and already merges all three sources
into `x_legal`, `x_lki` and `x_gmb` on each result, so no export is needed just to see
them. `total` is deduplicated companies and `establishmentsTotal` counts sites.

**Errors.** `401` bad or missing key. `402` `subscription_required` on pagination, or
`quota_exhausted`, which is returned before any record so nothing is delivered and
nothing is charged. `429` `rate_limit_exceeded`, respect the `Retry-After` header, or
`export_limit_reached` when the monthly export quota is gone.

**Map to the contract.** Read the header line of the export and map by name. Do not
hardcode column positions, and do not assume a column exists. Fill `source` with
`basile`, `source_url` with `https://api.basile.cc/people/<id>`, `lead_id` with
`basile:<id>`, and `segment` with the segment id from `icp.json`.

### 2. LinkedIn, through Sales Navigator

**Build the search URL.** A lead search URL is
`https://www.linkedin.com/sales/search/people?query=(...)` where the query is a
structured expression:

```
https://www.linkedin.com/sales/search/people?query=(spellCorrectionEnabled:true,filters:List(
 (type:CURRENT_TITLE,values:List((text:CTO,selectionType:INCLUDED),
                                 (text:Directeur Technique,selectionType:INCLUDED),
                                 (text:assistant,selectionType:EXCLUDED))),
 (type:COMPANY_HEADCOUNT,values:List((id:C,text:11-50,selectionType:INCLUDED),
                                     (id:D,text:51-200,selectionType:INCLUDED))),
 (type:REGION,values:List((id:<LinkedIn geo id>,text:France,selectionType:INCLUDED)))))
```

Filter types that map onto the ICP: `CURRENT_TITLE` and `PAST_TITLE` from
`titles.include`, the same types with `selectionType:EXCLUDED` from `titles.exclude`,
`SENIORITY_LEVEL` and `FUNCTION`, `COMPANY_HEADCOUNT` from the headcount band, `REGION`
from geography, `INDUSTRY` from the industry, `CURRENT_COMPANY` and `PAST_COMPANY` for
named accounts and alumni, `YEARS_IN_CURRENT_POSITION` for the new-in-seat signal.

Headcount ids are letters: `A` self employed, `B` 1-10, `C` 11-50, `D` 51-200,
`E` 201-500, `F` 501-1000, `G` 1001-5000, `H` 5001-10000, `I` 10001 and above.

**The rule that keeps this honest:** any value written as `text:` you may type yourself;
any value carrying an `id:` (region, industry, company, school) is an opaque LinkedIn
identifier that is not publicly documented and does change. Never guess one. Build the
search in the Sales Navigator interface, copy the URL from the address bar, then edit
only the `text:` values by hand. Store the URL verbatim, parentheses and commas included.

The result count above the list is free and is the ground truth. Read it back to the
user before collecting anything, and compare it against the ICP estimate.

**Collect the results.** Checked against the current Emelia surface: no MCP tool and no
documented REST endpoint starts a LinkedIn scrape. The scrape itself is started in the
Emelia app, with the LinkedIn Scraper, by pasting the Sales Navigator URL. Say this to
the user rather than implying it is automatable, then pick up the result:

1. `list_lists` with `source: "linkedin_scrap"` finds the list the scrape produced.
   Add `search` to narrow by name, and `sortBy: "createdAt"` with `sortDir: "desc"` to
   put the newest first.
2. `get_list` with the `listId` gives the counters: leads, emails, phones, linkedins.
   Report them as they are.
3. `get_list_contacts` with the `listId` pages through the rows: `page` starting at 1
   and `pageSize` up to 100. Loop until you have them all.
4. Map each row onto the contract. `source` is `linkedin`, `source_url` is the Sales
   Navigator URL, `lead_id` is `linkedin:<the profile slug>`.

Without the MCP server, ask the user to export the list to CSV from the Emelia app and
run the CSV route below. If your MCP client does advertise a LinkedIn scraping tool,
read its declared input schema before calling it and do not assume parameters.

### 3. A CSV the user already has

**Detect the encoding, in this order.** Check the first bytes for a byte order mark:
`EF BB BF` is UTF-8, `FF FE` is UTF-16LE, `FE FF` is UTF-16BE. With no BOM, try a strict
UTF-8 decode; if it raises, try `cp1252`, then `iso-8859-1` last, since that one never
raises and will happily produce nonsense. The tell that you guessed wrong is mojibake in
accented names: `Ã©` where `é` belongs, or `â€™` where an apostrophe belongs. Excel on a
French Windows machine writes cp1252 by default, so this is common, not exotic.

**Detect the separator.** Count `,`, `;`, tab and `|` outside quotes on the first five
non-empty lines. The winner is the one whose count is both highest and identical on
every line. French Excel writes `;`. If two candidates tie, or the count varies by line,
stop and ask rather than shredding the file.

**Detect the header.** If line 1 contains cells that look like data (an address, a
digit-only cell) rather than labels, ask whether the file has a header.

**Map the columns.** Compare lowercased, accent-stripped, punctuation-stripped names:

| Contract column | Accepted aliases |
|---|---|
| `first_name` | first name, firstname, prenom, given name, fname |
| `last_name` | last name, lastname, nom, nom de famille, surname, family name |
| `full_name` | name, full name, nom complet, contact, contact name |
| `email` | email, e-mail, mail, courriel, adresse email, work email, professional email |
| `phone` | phone, telephone, mobile, portable, tel, phone number, direct dial |
| `job_title` | title, job title, position, poste, fonction, intitule, role |
| `linkedin_url` | linkedin, linkedin url, linkedin profile, profil linkedin, li url |
| `company_name` | company, company name, societe, entreprise, organisation, account, employer, raison sociale |
| `company_website` | website, site, site web, url, company url |
| `company_headcount` | employees, headcount, size, effectif, taille, employee count |
| `company_siren` | siren, siret |
| `city` | city, ville, town, localite |
| `country_code` | country, pays, country code |

Anything unmapped is kept as `x_<original name>`, never dropped. Show the user the
mapping you inferred and the columns you could not place, and let them correct it.

**Decide which rows are usable.** A row survives if it has at least one of:

- an `email`, which is enough to send to;
- a `full_name` (or first plus last) **and** a `company_name` or `company_domain`, which
  is what the email finder needs;
- a `linkedin_url`, which is enough for a LinkedIn campaign and for the phone finder.

Rows with none of the three go to `outreach/leads-unusable.csv` with a `reason` column.
Count them and say the number. Do not delete them silently.

**Five things that go wrong in real files.**

- Splitting `full_name` is guesswork with compound names. Split only when there is no
  first or last column: take the first token as the first name and the rest as the last
  name, then set `x_name_split` to `guessed`.
- Registry exports often put the surname first and in capitals. If most first tokens are
  all caps, the columns are probably reversed. Ask, do not swap on your own.
- Excel eats leading zeros. A `company_siren` with 8 digits lost one, and a French
  postal code `01000` becomes `1000`. Left pad to 9 and 5. A SIRET is 14 digits and its
  first 9 are the SIREN.
- A phone column stored as a number (`3.36e+10`) has lost digits and cannot be repaired.
  Report the count and leave the cells empty.
- Duplicate rows are normal at this stage. Leave them: `outreach-filter` removes them and
  reports what it removed.

Fill `source` with `csv`, `source_url` with `file:<path>`, `lead_id` with
`csv:<line number>`, and `collected_at` with today.

### 4. Several sources at once

When the ICP has more than one segment, or the user wants France plus another market,
dispatch one `outreach-lead-sourcer` sub-agent per source and merge the results. Keep
`source` and `lead_id` intact through the merge: they are what makes the merge reversible
and what lets `outreach-filter` explain a removal.

## Output

`outreach/leads.csv`, and `outreach/leads-unusable.csv` when rows were rejected. If
`leads.csv` already exists, say so and either merge on `lead_id` or write
`outreach/leads-<name>.csv`.

```csv
lead_id,first_name,last_name,full_name,job_title,seniority,email,email_status,phone,phone_status,linkedin_url,company_name,company_domain,company_website,company_linkedin_url,company_headcount,company_industry,company_naf,company_siren,city,country_code,segment,signal,source,source_url,collected_at
basile:66f1a4c2e8,Camille,Rousseau,Camille Rousseau,Directrice Technique,C-Level,,,,,https://www.linkedin.com/in/camille-rousseau-dev,Netvia,netvia.fr,https://www.netvia.fr,https://www.linkedin.com/company/netvia,64,Edition de logiciels,62.01Z,824503917,Lyon,FR,fr-saas-cto,in role since 7 months,basile,https://api.basile.cc/people/66f1a4c2e8,2026-09-08
basile:66f1a4d071,Marc,Bettan,Marc Bettan,VP Engineering,VP,,,,,https://www.linkedin.com/in/marcbettan,Prismeo,prismeo.io,https://prismeo.io,https://www.linkedin.com/company/prismeo,110,Edition de logiciels,58.29C,910447226,Paris,FR,fr-saas-cto,,basile,https://api.basile.cc/people/66f1a4d071,2026-09-08
linkedin:sofia-kandel,Sofia,Kandel,Sofia Kandel,Head of Platform,Head,,,,,https://www.linkedin.com/in/sofia-kandel,Arboris,arboris.com,https://arboris.com,,145,Software Development,,,Bordeaux,FR,fr-saas-cto,,linkedin,https://www.linkedin.com/sales/search/people?query=(spellCorrectionEnabled:true...),2026-09-08
csv:412,Tom,Vasseur,Tom Vasseur,CTO,C-Level,tom.vasseur@lumenda.fr,,,,,"Lumenda",lumenda.fr,https://lumenda.fr,,,,,,Nantes,FR,fr-saas-cto,from Q2 webinar,csv,file:./exports/webinar-q2.csv,2026-09-08
```

Then report, in this shape and with real numbers:

```
1,284 rows written to outreach/leads.csv

  basile     1,050   counted 3,082 first, extracted the top segment only
  linkedin     198   from one Sales Navigator search, 212 in the list, 14 without a name
  csv           36   from exports/webinar-q2.csv, 41 rows, 5 unusable

  emails already present   36 of 1,284  (3%)
  LinkedIn URLs present  1,248 of 1,284 (97%)
  company domain present 1,190 of 1,284 (93%)

Basile credits used: 1,050. Emelia credits used: 0.
Nothing has been enriched or verified. Next: /outreach filter
```

## Checks before finishing

- `leads.csv` has exactly the 26 contract columns, in order, with any extras appended
  and prefixed `x_`.
- Every row has a non empty `lead_id`, `source`, `source_url` and `collected_at`.
- `lead_id` values are unique within the file.
- `source` is one of `basile`, `linkedin`, `csv`, `manual` on every row.
- `country_code` is two uppercase letters wherever it is filled.
- `company_domain` has no scheme, no `www.`, no path, and is lowercase.
- `segment` is filled on every row when `icp.json` exists.
- For Basile: a `countOnly` call was made and its `total` was reported before any
  extraction, and the credit cost was confirmed by the user.
- The row count in the file matches the number you reported, and rejected rows are in
  `leads-unusable.csv` rather than gone.
- No Emelia credit was spent.

## Failure modes

**Basile returns far fewer people than the company count suggested.** Almost always a
source conflict: a registry-only filter and a LinkedIn-only filter in the same query
return the intersection of two disjoint sets. Remove one, or split into two queries.

**Basile returns everything, unfiltered.** A filter was accepted and ignored. The two
documented cases are `headquarters_region_code`, which is removed at validation, and a
full date in `creation_date_min`, which takes a year only. Recount after each filter is
added and watch for the rung that does not move the number.

**A Basile export comes back short.** Check `X-Export-Capped`. If it is `true` you hit
the plan ceiling in `X-Export-Max-Rows`, and you need to segment the search and export
each piece.

**`402 quota_exhausted`.** The Basile quota is gone. Nothing was delivered and nothing
was charged. Say so and stop; do not retry in a loop.

**The Sales Navigator URL returns a different count than yesterday.** LinkedIn ids and
result sets move. Re-read the count in the interface rather than trusting a stored
number, and record the date in `collected_at`.

**The scraped LinkedIn list has fewer contacts than the search showed.** Normal. Report
both numbers, the search count and the list count, and never present the smaller one as
the market.

**The CSV looks fine but the accents are broken.** You decoded as `iso-8859-1` a file
that was cp1252 or UTF-8. Re-decode before writing anything downstream: a mangled name
in a first line is worse than no personalization.

**Two sources returned the same person.** Expected, and not your problem here. Keep both
rows with their own `lead_id`, and let `outreach-filter` merge them and say so.

## Limits

This skill sources contacts, it does not find or verify email addresses, and it spends
no Emelia credits. Basile covers France only. It cannot start a LinkedIn scrape by
itself, because no documented Emelia endpoint or MCP tool does, so that one step happens
in the Emelia app and this skill says so instead of pretending otherwise. It does not
guess LinkedIn's internal ids, it does not scrape LinkedIn outside the official
integration, and it does not buy data from brokers. Coverage of any source is partial:
report the counts you actually got, never an extrapolation.
