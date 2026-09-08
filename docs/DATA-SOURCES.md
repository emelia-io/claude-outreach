# Data sources

Three ways to get contacts into `outreach/leads.csv`. They do not cover the same
ground, they do not cost the same, and picking the wrong one is the most expensive
mistake in the whole pipeline, because everything downstream is priced per row.

| | [Basile](#basile-french-b2b) | [LinkedIn](#linkedin) | [Your CSV](#your-own-csv) |
|---|---|---|---|
| Geography | France only | anywhere | whatever you have |
| Finds companies you have never heard of | yes | partly | no |
| Covers small companies without a website | yes | no | maybe |
| Gives you an email | no | no | sometimes |
| Gives you a LinkedIn URL | often | always | rarely |
| Freshness | legal registry plus LinkedIn plus Google | live | as old as the file |
| What it costs | 1 Basile credit per record returned | a Sales Navigator seat, plus scraping time | nothing |
| What you need | `BASILE_API_KEY` | a Sales Navigator search plus Emelia | the file |

None of them gives you a verified email. Email finding and verification are a
separate, billed step through Emelia, and they run **after** filtering, never before.

## Choosing

- **Selling in France, to companies rather than to named accounts?** Basile. It is
  the only source here that covers the French company that has 12 employees, no
  LinkedIn page and a website from 2014.
- **Selling outside France?** LinkedIn, or your own CSV. Basile is French data and
  pretending otherwise wastes credits.
- **You already know the accounts you want?** Skip sourcing. Put the company names
  in a CSV, and use Basile `employer` or LinkedIn to find the right person inside
  each one.
- **Targeting a role that only exists on LinkedIn** (Head of Growth, RevOps, DevRel)?
  LinkedIn. Those titles are not in a legal registry.
- **Targeting a legal role** (president, gerant, directeur general)? Basile. Those
  are registry facts, not self-declared job titles.
- **You have a list already?** Use it, but run `/outreach filter` and
  `/outreach verify` before you spend anything on it. A list bought last year is
  typically worth verifying and rarely worth finding emails for twice.

You can use more than one. `/outreach leads` runs one
[`outreach-lead-sourcer`](../agents/outreach-lead-sourcer.md) per source in
parallel, then merges and deduplicates on email, then normalized LinkedIn URL, then
last name plus domain. Every row keeps its `source`, so you can always answer where
a contact came from.

---

## Basile, French B2B

Documentation: [docs.basile.cc](https://docs.basile.cc). Base
`https://api.basile.cc`. Header `Authorization: <key>` with the **raw key and no
`Bearer` prefix**, plus `Content-Type: application/json`. The key lives in
`BASILE_API_KEY`.

### What it actually covers

Around 26.8 million French companies and 29.5 million contacts, from three sources
crossed together:

- **Legal**, the French registry (INSEE and INPI-RNE): SIREN, NAF code, legal form,
  capital, creation date, headcount, and the officers of record.
- **LinkedIn**: job title, seniority, function, skills, schools, past employers,
  tenure, company followers.
- **Google My Business**: rating, review count, opening hours, category, address.

That 26.8 million counts companies that no longer trade. Pass
`company_ceased: false` on company searches unless you specifically want dead ones.

Where it wins over everything else: a French company with no LinkedIn page and no
marketing site is still in the registry, with its officers named. That is most of
the French market by count, and it is invisible to sources built on LinkedIn alone.

Where it does not help: it is French data. Non-French entities are not the point of
the product.

### Two searches, and one thing to know about each

**`POST /people/find`** returns the person and **not their company**. You get
identity, location, job title, LinkedIn URL, and the name plus internal id of the
employer, but none of the employer's data: no SIREN, no NAF, no headcount, no
Google rating.

**`POST /companies/find`** already crosses the three sources. Each result carries
its own record plus, when a match exists, the other two under `x_legal`, `x_lki` and
`x_gmb`. Unlike people, you do not need an export to see all three.

**`POST /people/export`** returns the full row as CSV: 79 columns, 22 on the person,
18 on their LinkedIn company, 18 on their registry company, 11 from Google Maps, and
6 presence flags. **This is what you want for outreach**, because the company context
is what makes personalization possible. `POST /companies/export` is the company
equivalent, 57 columns.

The practical rule from the documentation: `/find` is for targeting and counting,
`/export` is what produces usable data.

### Counting is free, extracting is not

Send `countOnly: true` (or `limit: 0`) and you get `total` with an empty `leads`
array, no charge, no cap on how often. Anything that returns records costs **1 credit
per record returned**, on `/find`, on `/people/{id}`, on `/companies/{id}` and on
`/export`. It is charged on every call: asking for the same records twice is billed
twice, because there is no "already paid" ledger.

`limit: 1` is not a count. It returns one record and costs one credit.

So the shape of every Basile query in this repository is: count, show the user the
number, get a yes, then extract once and keep the file.

```bash
# free: how many are there?
curl -s https://api.basile.cc/people/find \
  -H "Authorization: $BASILE_API_KEY" -H "Content-Type: application/json" \
  -d '{"countOnly":true,"filters":{
        "result_role":{"include":["CTO","Chief Technology Officer","Directeur Technique"]},
        "activity":{"include":["saas_software"]},
        "company_headcount":{">=":20,"<=":200},
        "result_country_code":{"include":["FR"]},
        "hide_legal_entities":true}}'

# billed: the same filters, as a 79 column CSV
curl -s https://api.basile.cc/people/export \
  -H "Authorization: $BASILE_API_KEY" -H "Content-Type: application/json" \
  -d '{"filters":{ ...identical... }}' -o outreach/raw-basile-people.csv
```

Exports are streamed and capped by plan. Read `X-Export-Max-Rows` and
`X-Export-Capped` on the response: `true` means the result was truncated and you
need to split the search by department, NAF code or creation year.

### Filters worth knowing

Text filters are `{"include": [...], "exclude": [...]}`. Inside `include` the values
are ORed, `exclude` removes matches, and separate filters are ANDed.
Numeric filters are `{">=": 20, "<=": 200}`.

On people: `result_role`, `result_full_name`, `result_city`,
`result_country_code`, `activity`, `company_headcount`, `employer`, `siren`,
`mandate_role` (registry roles: `gerant`, `president`, `dg`, `dgd`,
`administrateur`, `associe`), `current_seniority`, `current_job_functions`,
`skills`, `education`, `past_employer`, `current_tenure_years`, `linkedin_url`.

On companies: `name`, `activity`, `naf_code`, `headquarters_postal_code`,
`headquarters_city`, `headquarters_department_code`, `legal_form`, `siren`,
`headcount_min` and `headcount_max`, `capital_min` and `capital_max`,
`company_ceased`, `created_since_months`, `company_domain`, `followers_min`, `rating_min`,
`reviews_min`.

### The traps, all from the public documentation

- **`activity` takes concept ids, not words.** Resolve them first with
  `GET /companies/activity-suggest?q=logiciel` and pass what comes back.
- **Do not chain companies into people.** `activity` and `company_headcount` work
  directly on `/people/find`, so one request does what two would. The detour through
  `/companies/find` is only useful when you start from named companies or from
  Google listings.
- **`headquarters_region_code` is silently dropped** at validation. Sent alone, the
  request goes out with no filter at all and the API answers 400. Use `region` with
  the canonical name, or enumerate `headquarters_postal_code`.
- **`creation_date_min` and `creation_date_max` take a year.** A full date like
  `2015-03-01` is ignored without an error, so your results come back unfiltered and
  look fine. Use `created_since_months` when you want recency.
- **`company_headcount` excludes records with no known headcount**, roughly a fifth
  of a French sample according to the documentation. Your count drops, and that is
  the filter working, not a bug.
- **`hide_legal_entities: true`** on people searches, unless you want companies
  listed as officers of other companies.
- **Asking for `limit: 500` and receiving 20 costs nothing extra.** Billing is on
  records returned, not requested.
- Page 1 works without a subscription; paginating past it needs an active one and
  answers **402 `subscription_required`** otherwise. Running out of quota is also
  402, as `quota_exhausted`, and it is returned before any record, so nothing is
  delivered and nothing is charged.

---

## LinkedIn

The right source when the title only exists on LinkedIn, when the market is outside
France, or when you are working a named account list and need the person inside it.

### How it works here

1. You build the search in Sales Navigator and give the skill the URL. Nobody can
   rebuild your filters, your saved leads and your seat's reach better than you can,
   so the skill does not try.
2. The scrape runs through Emelia. With the MCP server configured, that is the
   `linkedin_scrap` tool, which takes a name for the scrape, the search URL, and the
   connected LinkedIn account it runs from. Read the tool's own parameter
   description in your client before calling it: the scraper is not part of the
   public REST reference, so its options move faster than the rest of the API.
   Without the MCP server, you start the scrape in the Emelia app.
3. The scrape produces a contact list in Emelia. Reading it back also needs the MCP
   server: `list_lists` with `source: "linkedin_scrap"` to find it, then
   `get_list_contacts` to page through it, 100 rows at a time. With neither, export
   the list to CSV from the app and treat it as a CSV source.

### What you get and what you do not

You get the profile: name, headline, title, company, location, profile URL. You do
not get an email, ever. LinkedIn does not publish them, and anything that claims to
read them from the profile is either guessing a pattern or breaking something.

That matters for cost: a LinkedIn-sourced list is a list of names that still needs
the Emelia email finder, one credit per row attempted, found or not. Filter hard
before you enrich.

The profile URL is worth keeping for another reason: it is the only input the Emelia
phone finder accepts. No LinkedIn URL, no mobile number, ever.

### The limits that are real

Scraping is slow on purpose. LinkedIn restricts accounts that behave like scrapers,
and the account at risk is yours. Plan a scrape in hours, not minutes, and do not
run several large ones in parallel from the same account. If a scrape is still
running when you need the data, take the partial list and say it is partial.

You also need the seat. Sales Navigator is what makes the search worth scraping;
without it the free search caps out fast.

---

## Your own CSV

Always available, needs no key, and it is the right answer more often than people
expect: an event attendee list, a CRM export, a webinar sign-up, last year's
prospecting file.

Point `/outreach leads` at the file. The skill reads the header, maps your columns
onto the shared shape, and tells you what it mapped and what it could not:

```
first_name,last_name,job_title,company_name,company_domain,linkedin_url,email,email_status,country,source,source_url,collected_at
```

Two rules it will not break. It does not invent a column you did not give it: no
domain derived from an email address, no country guessed from a phone prefix.
And an email that came with the file is marked `unverified`, not `valid`, however
much you trust the source.

### The old list trap

A file from last year is not a list, it is a hypothesis. Roughly a fifth to a third
of B2B contact data goes stale each year through job changes alone, which is a rule
of thumb rather than a measurement of your file. Sending to it without verification
is the fastest way to a bounce rate that costs you the domain.

The order that saves money: filter first, drop what can never be contacted, then
verify what remains, then find emails only for the rows still missing one. Verifying
4,000 rows and discovering 1,200 are dead is the cheap version of this discovery.

---

## What none of these do

- No personal email addresses, and no data bought from grey market brokers.
- No email inferred from a pattern. `firstname.lastname@company.com` guessed from a
  domain is not a found address, and it will pass verification on a catch-all domain
  while bouncing in production.
- No scraping outside the official Emelia integration.
- No source can tell you an address is deliverable when the domain is catch-all. That
  comes back as `unknown`, and `unknown` is reported as `unknown`.
