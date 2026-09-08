---
name: outreach-filter
description: "Clean and segment a lead list before a single credit is spent on it. Deduplicates by email, by company domain and by LinkedIn profile, handling the awkward cases (subdomains, plus aliases, apostrophes and accents in names, Sales Navigator URLs that never string match a public profile), excludes existing customers, competitors and blacklisted addresses using find_contact and the Emelia blacklist endpoints, drops generic mailboxes such as contact@ and info@ and the junior roles that cannot buy, checks that geography and headcount match the ICP, and splits what survives into segments that each deserve a different message. Reads outreach/leads.csv and outreach/icp.json, writes a smaller leads.csv plus a report of every row removed and why. Triggers on: filter, clean the list, dedupe, deduplicate, duplicates, remove customers, exclusion list, blacklist, suppression list, generic emails, contact@, role address, segment the list, segmentation, list hygiene, data quality, before enrichment."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Filter and segment the list

## What this does

Takes `outreach/leads.csv` and gives back a shorter one, plus a written account of every
row that left and why. It deduplicates, removes customers, competitors and blacklisted
addresses, drops shared mailboxes and roles that cannot buy, checks geography and size
against the ICP, and splits the rest into segments.

This step spends no Emelia credits, and it exists so that the next step does not spend
them on rows you were going to delete. Filtering before enriching is the single change
that most reduces the cost of a campaign.

## When to use it

Always, between [outreach-leads](../outreach-leads/SKILL.md) and any enrichment. Also on
its own, when a user arrives with an old list and asks what is still usable in it: this
skill answers that question for free.

Use a different skill when:

- The list does not exist yet: `outreach-leads`.
- The list is clean and needs addresses: `outreach-enrich`, which runs after this.
- The problem is who you are targeting, not the rows: go back to
  [outreach-icp](../outreach-icp/SKILL.md).

## Inputs

| Input | Required | If missing |
|---|---|---|
| `outreach/leads.csv` | yes | Ask for a path, or run `outreach-leads` first. |
| `outreach/icp.json` | strongly recommended | Without it you cannot check geography, size or segments. Ask for the country list and the headcount band as a minimum, and say which checks you skipped. |
| Customer domains | strongly recommended | Ask for a CRM export with a domain column. Without it, say plainly that customers will stay in the list. |
| Competitor domains | recommended | Ask for three or four names. |
| `outreach/blacklist.txt` | optional | Create it empty. It is the local mirror of the Emelia blacklist, which has no read endpoint. |
| The Emelia MCP server | optional | Without it `find_contact` is unavailable and you cannot ask "is this person already in one of my lists". Fall back to matching against an exported list, and say so. |

## How to do it

Run the free steps first and the metered ones last. Nothing here consumes credits, but
`find_contact` consumes rate limit, so it goes at the end, on the smallest list.

### 1. Build the comparison keys

Never compare raw values. Compute these keys in memory (or as `x_` columns if the user
wants to audit them), and compare on the keys.

**`k_email`.** Normalize to NFC, trim, strip a leading `mailto:` and any surrounding
angle brackets, lowercase the whole address, drop a trailing dot on the domain.

- Plus aliases: strip `+tag` from the local part **only** for consumer providers
  (gmail.com, googlemail.com, outlook.com, hotmail.*, live.*, yahoo.*, proton.me,
  protonmail.com, fastmail.com, icloud.com). On a company domain, a `+` in a sourced B2B
  list is unusual: flag the row, keep both, and do not merge on your own.
- Dots: remove dots from the local part **only** for gmail.com and googlemail.com.
  Everywhere else `j.dupont@acme.fr` and `jdupont@acme.fr` are two different mailboxes,
  and merging them loses a real contact.

**`k_domain`.** Lowercase, strip the scheme, `www.`, any port, path, query, fragment and
a trailing dot, then reduce to the registrable domain with a public suffix list.

- Do not take "the last two labels": that turns `bbc.co.uk` and `itv.co.uk` into the same
  key. Handle multi label suffixes at least for `co.uk`, `org.uk`, `ac.uk`, `gov.uk`,
  `com.au`, `com.br`, `com.mx`, `co.jp`, `co.nz`, `co.za`, `com.tr`, `gouv.fr`,
  `asso.fr`.
- Subdomains collapse: `careers.acme.com`, `shop.acme.com` and `www2.acme.com` are all
  `acme.com`. Merge them.
- Different registrable domains do **not** merge automatically. `acme.fr` and `acme.com`
  are usually the same company and sometimes are not. Flag them as
  `possible_same_company`, show the pairs, and let the user decide.

**`k_linkedin`.** Lowercase the host, drop a locale subdomain (`fr.linkedin.com` becomes
`www.linkedin.com`), drop the query and fragment (`?originalSubdomain=fr`, `?trk=...`),
drop the trailing slash, percent decode the slug, and keep the canonical form
`https://www.linkedin.com/in/<slug>`.

Two shapes will never match each other even when they are the same person, and you must
say so rather than silently treat them as different people: a Sales Navigator URL
(`/sales/lead/<urn>`) carries a different identifier from a public profile, and a URL of
the form `/in/ACwAAA...` is an opaque member identifier rather than a vanity slug. Keep
them, mark `x_linkedin_key: opaque`, and rely on the name plus domain pass to catch them.

**`k_name`.** Normalize to NFKD and drop combining marks, so `José` becomes `jose`.
Replace the typographic apostrophe (U+2019) with a plain one, then remove apostrophes, so
`O'Brien`, `D'Angelo` and `N'Diaye` become `obrien`, `dangelo`, `ndiaye`. Remove hyphens,
so `Jean-Pierre` and `Jean Pierre` match. Lowercase and collapse whitespace. Keep
particles (`de`, `van`, `von`, `le`, `di`, `da`, `del`): dropping them merges `Le Gall`
with `Gall`, who are two people.

`k_name` is never a deduplication key on its own. It is only a tiebreaker inside the same
`k_domain`.

### 2. Deduplicate, in this order

1. **Same `k_email`.** Merge.
2. **Same `k_linkedin`.** Merge.
3. **Same `k_name` and same `k_domain`.** Merge. This is what catches the same person
   sourced twice from two places without an email.
4. **Same `k_domain`, different people.** Not a duplicate. Handled at step 7.

Merge rule: keep the row with the most non empty contract columns. On a tie, prefer the
row that has an email, then the one that has a LinkedIn URL. Append the discarded
`lead_id` values to `x_merged_ids` so the merge can be undone, and keep the surviving
row's `source` and `source_url` untouched.

**One person, several companies.** French registry data lists an officer once per
mandate, so after step 3 the same person can still appear with two employers. Keep the
row whose employer matches the ICP. If both match, keep the larger company and record the
other in `x_other_employers`.

### 3. Remove customers, competitors and blacklisted rows

All of this is a local match on `k_domain` and `k_email`, which is free and instant, so
it runs before anything that talks to an API.

- **Customers.** Match `k_domain` against `exclusions.customer_domains` and the file at
  `exclusions.customer_domains_file`. Reason: `customer`.
- **Competitors.** Same, against `exclusions.competitor_domains`. Reason: `competitor`.
- **Blacklist.** Match against `outreach/blacklist.txt`, one entry per line, either an
  address or a bare domain. Reason: `blacklist`.
- **Forbidden industries.** Match `company_naf` against
  `exclusions.forbidden_industries.naf`, prefix aware (`84.` covers `84.11Z`). Reason:
  `forbidden_industry`.

**About the Emelia blacklist.** Two endpoints exist and both are writes:
`POST https://api.emelia.io/emails/blacklists/contact` with body `{"email": "..."}` adds
an entry, and `DELETE` on the same path removes it. The value is either an address or a
whole domain written as `domain.ltd`. There is **no documented endpoint that reads the
blacklist**, so you cannot ask Emelia whether an address is on it. That is why
`outreach/blacklist.txt` exists: it is your mirror, and it is the only copy you can read.
Every unsubscribe and every hard bounce belongs in both. Adding an entry changes the
user's account for every future campaign, so confirm before writing one.

### 4. Ask Emelia whether you already have these people

Only on the list that survived steps 1 to 3, and only when the user cares about not
contacting someone twice.

The cheap way first: if the user can export their existing Emelia lists or their CRM,
match locally on `k_email` and `k_domain`. Free, instant, no rate limit.

Otherwise use the MCP tool `find_contact`, which takes a single `query` that is either an
email address or a LinkedIn profile URL, searches every list on the account, and returns
whether it was found, which lists hold it, and the contact itself. It is one call per
row. Rate limits are per key and per minute: 30 without a subscription, 100 on Start, 300
on Grow, 1000 on Scale. So 1,000 rows on a Start plan takes about ten minutes at full
rate. State that before starting, and never run it across tens of thousands of rows.

Rows found in an existing list are removed with reason `already_in_emelia`, and the
report names the list they were found in, because "already in a list" and "already
emailed" are not the same thing and the user must be able to tell.

Without the MCP server there is no documented REST equivalent. Say so and use the local
match.

### 5. Generic mailboxes and roles that cannot buy

**Generic and role addresses.** Detect on the local part: `contact`, `info`, `hello`,
`bonjour`, `sales`, `commercial`, `support`, `help`, `admin`, `webmaster`, `postmaster`,
`abuse`, `noreply`, `no-reply`, `donotreply`, `billing`, `compta`, `comptabilite`,
`facturation`, `rh`, `hr`, `recrutement`, `jobs`, `careers`, `marketing`, `press`,
`presse`, `legal`, `dpo`, `privacy`, `security`, `team`, `office`, `accueil`,
`direction`, `secretariat`, `sav`, `service-client`, `devis`, `mail`, `enquiries`.

Three of these are never acceptable, whatever the segment and whatever the user says:
`postmaster`, `abuse` and anything containing `noreply`. The first two are addresses
every domain is required to keep for mail administrators, they are classic spam trap
territory, and mailing them damages the sending domain. Remove them, reason
`role_address`, and do not offer to keep them.

The rest is a decision, driven by `exclusions.role_addresses` in the ICP:

- `drop`: move them out with reason `role_address`.
- `keep`: move them into their own segment, `<segment>-generic`. They need a different
  message, because there is no first name to use, no personal claim you can make, and
  whoever opens the shared mailbox is not the person you are writing to.

Explain the trade-off rather than applying a rule blindly: at a three person building
firm, `contact@` is the owner and is the only address that exists. At a two hundred
person software company, `contact@` is a shared inbox that nobody on the buying committee
reads.

**Roles that cannot buy.** Match `job_title`, accent and case insensitive, on word
boundaries: assistant, assistante, adjoint, adjointe, stagiaire, alternant, apprenti,
intern, trainee, junior, charge de, chargee de, freelance, independant, auto
entrepreneur, retraite, retired, open to work, a la recherche, etudiant, student.
Reason: `unwanted_role`.

Match on word boundaries and list what you dropped, because substrings lie: `assistant`
also matches `Executive Assistant to the CEO`, and in some French companies `Directeur
Adjoint` is the person who actually signs. Show the titles you removed and let the user
put any of them back.

If the ICP targets a named role and a row has neither `job_title` nor `seniority`, remove
it with reason `unwanted_role` as well. You cannot write to a CTO you cannot confirm is
one.

### 6. Coherence with the ICP

- **Geography.** `country_code` outside `geography.countries` goes, reason
  `geo_out_of_scope`. Check the company's country before removing: a profile whose owner
  moved abroad while the company stayed put is usually still in scope.
- **Size.** `company_headcount` outside the band goes, reason `size_out_of_band`.
- **Unknown size.** Do not remove silently. Count them, flag `size_unknown`, and ask.
  They can be a large share of a list. Note that Basile's own `company_headcount` filter
  already excludes records with no known headcount (around 21% on a French sample, per
  the public documentation), so a list heavy in unknowns almost always came from LinkedIn
  or from a CSV.
- **French postal codes.** Five digits. The department is the first two, except Corsica
  (`2A` and `2B`, postal codes starting `20`) and the overseas departments where it is
  three digits, `971` to `978`. A four digit code lost a leading zero: pad it.
- **Platform domains are not company domains.** `wixsite.com`, `business.site`,
  `sites.google.com`, `myshopify.com`, `weebly.com`, `squarespace.com`, `e-monsite.com`,
  `wordpress.com`, `blogspot.com`, and directory or social pages used as a website
  (`linkedin.com`, `facebook.com`, `instagram.com`, `pagesjaunes.fr`, `societe.com`).
  Clear `company_domain`, keep `company_website` as found, set
  `x_domain_quality: platform`. Do not remove the row: the contact may still be valid.
- **Free mail domains are not company domains.** gmail.com, googlemail.com, outlook.*,
  hotmail.*, live.*, yahoo.*, icloud.com, me.com, aol.com, gmx.*, proton.me,
  protonmail.com, and the French ones that catch people out: orange.fr, wanadoo.fr,
  free.fr, sfr.fr, laposte.net, neuf.fr, bbox.fr, numericable.fr, aliceadsl.fr. Keep the
  address, clear `company_domain`, set `x_email_kind: personal`. Legitimate for a sole
  trader, wrong for a company, and never a deduplication key.
- **No contact key at all.** A row with no email, no LinkedIn URL, and no name plus
  company pair cannot be enriched or contacted. Remove it, reason `no_contact_key`.

### 7. Cap the contacts per company

One to three contacts per company is a reasonable ceiling, offered as a rule of thumb.
Two people at the same company receiving the same template in the same week is the
fastest way to be discussed internally, and not in your favour.

Rank the rows inside each `k_domain` by how well `job_title` matches `titles.include` in
the ICP, keep the top N, and move the rest out with reason `company_cap`. Keep them in
the removed file: they are the obvious second wave if the first contact does not answer.

### 8. Segment what is left

A segment is a group that would receive a different first sentence. Two groups that would
get the same opening line are one segment, whatever their fields say.

- **Ceiling: three.** The ICP already enforces this. If the cleaned list genuinely breaks
  into more, say so and propose splitting it into separate campaigns rather than writing
  four messages at a quarter of the volume each.
- **Floor: about 150 contacts.** Below that, a segment produces single digit replies at
  typical cold B2B rates, and single digit replies cannot separate a good message from a
  bad one. Merge it, or treat it as a manual list rather than a campaign.
- **Balance.** A segment holding more than about 70% of the list is not a segment, it is
  the list with a label on it. Look for the split that actually changes the message.

Write the result into the `segment` column on every row. Never leave it empty.

## Output

Three files. The 26 contract columns defined in
[outreach-leads](../outreach-leads/SKILL.md) are unchanged in all of them, so everything
downstream keeps working.

- `outreach/leads.csv`, overwritten with the surviving rows. Say before overwriting, and
  keep a copy at `outreach/leads-before-filter.csv`.
- `outreach/leads-removed.csv`, the 26 contract columns plus `removed_reason` and
  `removed_by` (the step number). Nothing is deleted, everything is moved.
- `outreach/filter-report.md`.

The reason vocabulary is fixed, so reports stay comparable between runs:
`duplicate_email`, `duplicate_linkedin`, `duplicate_name_domain`, `company_cap`,
`customer`, `competitor`, `blacklist`, `already_in_emelia`, `role_address`,
`unwanted_role`, `geo_out_of_scope`, `size_out_of_band`, `forbidden_industry`,
`no_contact_key`.

A real `outreach/filter-report.md`:

```markdown
## Filter report, 2026-09-08

Input: outreach/leads.csv, 1,284 rows
Output: outreach/leads.csv, 811 rows kept (63%), 473 removed

### What was removed

| Reason | Rows | Note |
|---|---|---|
| duplicate_linkedin | 96 | same profile from Basile and from the Sales Navigator search |
| duplicate_email | 21 | 4 of them were plus aliases on gmail.com |
| duplicate_name_domain | 34 | same person, no email on either row |
| company_cap | 118 | 3 contacts per company kept, ranked on title |
| customer | 62 | matched on domain against exports/customers.csv, 214 domains |
| competitor | 4 | datadoghq.com, newrelic.com |
| blacklist | 7 | from outreach/blacklist.txt |
| already_in_emelia | 39 | found by find_contact, mostly in the list "Q2 SaaS FR" |
| role_address | 28 | 3 were postmaster@ or abuse@ and were removed unconditionally |
| unwanted_role | 41 | assistant, stagiaire, alternant, open to work |
| geo_out_of_scope | 12 | BE and CH profiles, the ICP is FR only |
| size_out_of_band | 9 | above 200 employees |
| no_contact_key | 2 | no email, no LinkedIn, no company |

### Flagged, not removed

- 147 rows have no known headcount (18%). The ICP has a floor of 20, so these are a
  judgement call. They came from the LinkedIn search and from the CSV, not from Basile.
- 23 rows have a platform domain (wixsite.com, business.site). company_domain cleared,
  company_website kept.
- 11 rows have a personal email domain (orange.fr, free.fr). Kept, marked personal.
- 6 pairs share a name and a company under two different domains (acme.fr and acme.com).
  Not merged. Listed at the end of this file for your decision.

### Segments

| Segment | Rows | Why it is different |
|---|---|---|
| fr-saas-cto | 604 | opens on their status page, or the absence of one |
| fr-saas-cto-new | 207 | in the role under a year, opens on the first 90 days |

Both are above the 150 row floor. No segment holds more than 75% of the list, so the
split is worth keeping.

### What this did not do

No email was found or verified. No Emelia credit was spent. 39 rows were removed because
they are in an existing Emelia list, which means they were imported, not necessarily
emailed: check the list "Q2 SaaS FR" before assuming they were contacted.
```

Then say the three numbers out loud: rows in, rows out, and the largest single reason.
If the list lost more than half, say that too, and say whether the loss is duplicates
(good, the sourcing overlapped) or exclusions (worth checking the ICP).

## Checks before finishing

- `leads.csv` still has the 26 contract columns, in order, with any extra columns
  appended after them rather than inserted between them.
- Rows in the output plus rows in `leads-removed.csv` equals rows in the input. No row
  vanished.
- Every row in `leads-removed.csv` has a `removed_reason` from the fixed vocabulary.
- `lead_id` is unique in the output.
- Every surviving row has at least one contact key: an email, a LinkedIn URL, or a name
  plus a company.
- Every surviving row has a non empty `segment`.
- No segment is below roughly 150 rows without that being called out.
- No surviving row has a free mail or platform domain in `company_domain`.
- No surviving address is `postmaster@`, `abuse@` or a `noreply` variant.
- `outreach/leads-before-filter.csv` exists.
- No Emelia credit was spent. Say it in the report.

## Failure modes

**The list collapses to almost nothing.** Usually the customer file was matched on the
wrong column, or the headcount band removed every row whose headcount is unknown. Check
the removal table before touching the ICP: one reason will be carrying the whole drop.

**Deduplication merged two different people.** Almost always a name key that stripped
particles, or a domain key that took the last two labels of a `co.uk` address. Reload
`leads-before-filter.csv`, fix the key, and re-run. This is why the merged ids are kept.

**Deduplication missed obvious duplicates.** The two rows are a public LinkedIn URL and a
Sales Navigator URL, or a member identifier and a vanity slug. They cannot string match.
The name plus domain pass is what catches them, so make sure `company_domain` is filled
before running it.

**`find_contact` is slow or starts failing.** You are hitting the per minute rate limit.
Slow down to the plan's limit, or drop the step and use an exported list instead. Do not
retry in a tight loop.

**A user insists on keeping `contact@` for a large company.** State once what it costs: a
shared inbox has a lower reply rate and a higher complaint rate, and complaints follow
the sending domain rather than the campaign. Then, if they still want it, put those rows
in their own segment with their own message. Do not mix them into a personalized one.

**The customer list is a list of company names, not domains.** Matching names is
unreliable (`Acme`, `ACME SAS`, `Acme Group`). Ask for domains. If there are none,
match on a normalized name inside the same country, present the matches, and let the user
approve them one by one rather than removing them automatically.

## Limits

This skill does not find, verify or repair email addresses, and it spends no Emelia
credits. It cannot know whether a contact was actually emailed, only whether they exist
in a list. It cannot read the Emelia blacklist, because no documented endpoint returns
it, so its view of the blacklist is only as good as `outreach/blacklist.txt`. It will not
merge two domains it is not sure about, and it will not remove a row without recording
it. Deduplication on names is a heuristic: on a large list it will get a small number of
cases wrong, which is why every removal is kept and reversible.
