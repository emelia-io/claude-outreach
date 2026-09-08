---
name: outreach-personalize
description: "Personalizes a sequence at scale without inventing anything. Decides what can genuinely vary row by row and what must stay a segment, ranks the sources (role and company, recent LinkedIn content, company news, technology used), writes AI variables with fallbacks that cannot break when the data is missing, refuses fabricated personalization, and forces a quality review on a 20 row sample before generating the other thousand. Also covers spintax and when it actually helps. Produces the icebreaker columns in outreach/leads.csv with their source and date. Triggers on: personalize, personalization, personalisation, icebreaker, ice breaker, first line, AI variable, custom variable, merge tag, merge field, fallback, spintax, variables, mass personalization, personalization at scale, accroche."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Personalize at scale

## What this does

Fills the per contact parts of a sequence: the icebreaker sentence, the cleaned
company name, and any custom variable the copy uses. It writes those columns into
`outreach/leads.csv` with the source and the date behind each one, so every sentence
you send can be traced back to something somebody actually read.

## When to use it

Use it after the copy exists and before the campaign is built, because the copy tells
you which variables are needed and the coverage tells you whether the copy can use
them. Use it again when a list ages and the icebreakers no longer match reality.

Use a different skill when: you are writing the sentences of the sequence itself
([outreach-write](../outreach-write/SKILL.md)), splitting a list into segments
(`outreach-filter`), or finding emails and phone numbers (`outreach-enrich`).

## Inputs

| Input | Where it comes from | If it is missing |
|---|---|---|
| The list | `outreach/leads.csv`, one row per contact | Stop, there is nothing to personalize |
| The variables the copy uses | `outreach/sequence.md` header line `Variables used:` | Read the `{{...}}` tokens out of the body |
| Source material per row | LinkedIn URL, company website, news, job posts already in the list | Leave the row without an icebreaker, never guess |
| Freshness limits | defaults below | Use the defaults and say so |

If a variable in the copy has no source at all, say so before generating anything and
offer two honest options: drop the variable from the copy, or split the list so the
sentence only goes to the rows that can carry it.

## How to do it

### 1. Decide what is a variable and what is a segment

The rule: **anything you cannot fill for at least 80% of a segment is not a variable,
it is a segment.** Splitting the list is always better than a sentence that only works
for a third of it.

| Signal | Where it comes from | Coverage you can expect | Goes stale after | What it is worth |
|---|---|---|---|---|
| First name | the list | close to 100% | never | almost nothing on its own |
| Job title, company name | the list | high | about a year | picks the sequence, does not personalize it |
| Recent post by the person | LinkedIn | low, most B2B buyers outside sales and marketing do not post | 3 to 4 weeks | the strongest signal there is |
| Company news: funding, hire, launch, office, certification | the company site, press, job boards | partial | about 3 months | strong when you use the consequence, not the fact |
| Technology used | the site, job posts, a detection source | high | slowly | a qualifier more than an opener |
| Industry, headcount, region | the list | high | slowly | segment, never a sentence |

Coverage figures here are rules of thumb, not measurements. Measure yours on the first
200 rows before you trust them, and write the number you measured into the run.

### 2. Source hierarchy, in the order you try them

1. **Role and company.** Free, complete, weak. Use it to pick which sequence a row
   gets, not to fill a blank in a sentence.
2. **Recent content by the person.** A post, a comment, a talk, a repository. Strong,
   because it proves you looked. Low coverage and fast decay.
3. **Company news.** Use the consequence, not the announcement. "You raised a Series A"
   is worthless. "Six new sales hires since March" is a reason to write today.
4. **Technology used.** Works as a qualifier inside a sentence you were writing anyway:
   "since you are on Stripe Billing" is fine, "I noticed you use Stripe" is filler.
5. **Anything about neither this person nor this company.** Stop here. This is exactly
   where fabricated personalization starts.

### 3. Write variables that cannot break

This part is Emelia specific and it is where campaigns quietly go wrong.

**How Emelia resolves a variable.** For each contact, `{{name}}` is looked up in this
order: the contact's own fields, then the contact's custom fields, then the company
record linked to the contact. Contact fields resolvable by name include `firstName`,
`lastName`, `fullName`, `email`, `phone`, `mobilePhone`, `jobTitle`, `seniority`,
`department`, `language`, `linkedinUrlProfile`, `country`, `region`, `city`,
`companyName`. Company fields collide with contact fields for `country` and `city`, so
use `{{companyCountry}}` and `{{companyCity}}` when you mean the company. Any other
name you send with a contact becomes a custom variable automatically.

**What happens when nothing matches: you get an empty string.** Not an error, not the
raw token. The sentence simply loses its middle and the email goes out anyway. This is
the single most common way a good sequence is ruined at scale.

**Fallbacks are Liquid, with unusual delimiters.** Emelia already uses double braces
for its own variables, so its Liquid output tag is `{#` and `#}`, and its logic tag is
the standard `{% %}`:

```text
Hi {# firstName | default: "there" #},
```

```text
{% if icebreaker %}{{icebreaker}}

{% else %}Quick context on why I am writing to you rather than to your CTO.

{% endif %}Most teams that ship a public API ...
```

Order of evaluation, which explains the traps below: `{{ }}` variables are substituted
first, then Liquid runs, then spintax runs last.

Five rules that follow from that:

1. **Prefer whole sentence variables.** The variable holds one complete sentence
   including its final full stop, or it holds nothing. An empty value then removes a
   sentence and the paragraph still reads. A variable in the middle of a sentence
   leaves a hole nobody catches until a prospect screenshots it.
2. **Never let a variable carry the grammar.** `I saw {{companyName}} just opened in
   {{city}}` breaks in two places. `Congrats on the Lyon office.` as a single variable
   does not.
3. **Never open a sentence with a variable.** A missing value leaves a capital letter
   somewhere odd.
4. **Give every optional variable a blank line above and below**, so an empty value
   collapses without leaving a double space or a stray line.
5. **Strip `{`, `}` and `|` out of every generated value.** Spintax runs after the
   variables are substituted, so a brace or a pipe inside an icebreaker gets parsed as
   spintax and part of your sentence disappears.

One more trap worth knowing: if a Liquid tag is malformed, Emelia catches the error and
**deletes every `{% ... %}` and `{# ... #}` block in the message** rather than failing
loudly. You get no warning, you get a message with the conditional paragraph missing.
Preview every Liquid tag on a real contact before sending.

### 4. Clean the company name before you use it in a sentence

Legal names look wrong inside a sentence. Write a `companyNameClean` column and use
that in the copy:

- Strip legal suffixes: SAS, SASU, SARL, EURL, SA, SCI, GmbH, BV, Ltd, LLC, Inc, Corp,
  and the trailing punctuation around them.
- Fix all caps names to title case, except tokens of 2 to 4 letters, which are usually
  acronyms and stay as they are.
- Drop a trailing "Group", "France" or "Holding" when the short name is unambiguous.
- Never touch the original `companyName` column: enrichment and deduplication need it.

### 5. Refuse fabricated personalization

Fabricated means any sentence that asserts something you did not read. It is worse than
no personalization: an empty first line costs you nothing, a wrong one gets you a
correction, a screenshot, and a burnt sender domain.

The forms it takes, all common:

- "I read your post about X" when the post is a repost, a like, or somebody else's.
- "Loved your article" when the byline is the marketing team.
- "Congrats on the funding" for a round that closed three years ago.
- "I saw you are hiring five engineers" from a job board that recycles old ads.
- "I know [industry] teams struggle with X", which is an inference dressed as an
  observation.
- A summary of a company page rewritten as though you had a conversation.

The rules that stop it:

- **Every generated sentence carries a source.** Store `icebreaker_source` (the URL you
  actually fetched) and `icebreaker_date` next to `icebreaker`. No source, no
  icebreaker: leave the cell empty and let the fallback handle it.
- **Apply a freshness limit per type** and blank anything older: a LinkedIn post 30
  days, a hiring signal 45 days, company news 90 days, a technology signal 12 months.
- **Never write "I saw", "I read" or "I noticed"** unless the row holds a URL you
  fetched. If the sentence would survive without those three words, drop them anyway.
- **The reversal test.** If the prospect replied "where did you see that?", could you
  paste a link within ten seconds? If not, delete the sentence.
- When the user asks for an icebreaker on a row with nothing behind it, refuse and say
  what the row is missing. Do not fill it with a paraphrase of the industry.

### 6. Review 20 rows before generating a thousand

Generate 20 first. Always. The sample is not random on its own:

- 10 rows at random,
- 5 rows with the shortest source text, which is where the model starts inventing,
- 5 rows with awkward company names: accents, ampersands, legal suffixes, all caps.

Then, for each of the 20, render the full step 1 as the recipient will see it, with
variables and fallbacks applied, and read all twenty. Score each one:

- **usable**: true, specific, and it would not embarrass you,
- **weak**: true but generic, it adds nothing,
- **wrong**: one factual error, of any size.

The gates:

| Gate | Threshold | What you do if it fails |
|---|---|---|
| Wrong rows | 0 out of 20 | Fix the generation rule, not the row, then re-sample |
| Usable rows | at least 14 out of 20 | The source is too thin for a variable, demote it to a segment |
| Empty case | blank the variable on 2 rows and re-render | If the email stops reading, the fallback is wrong |
| Length | 25 words maximum per icebreaker | Long icebreakers read as generated |
| Repetition | no two of the 20 share an opening construction | You wrote a template with a slot, not a personalization |

Only after all five gates pass do you generate the rest. Then re-run the empty case
check on the full file: count the rows where the variable is blank and tell the user
the number. "812 of 1,000 rows have an icebreaker, 188 fall back to the generic
opener" is the sentence to say, not "list personalized".

Cost note: generating icebreakers costs model tokens, not Emelia credits. But fetching
the source material can cost, because a LinkedIn scrape and any enrichment are billed.
State the row count and the cost before any fetch, and wait for an explicit yes.

### 7. Spintax, and what it is actually for

Spintax picks one option at random per send: `{Hi|Hello|Hey} {{firstName}}`. It nests:
`{Hi|{Hello|Hey}}`. Emelia runs it last, after the variables and after Liquid, and it
runs on the subject line as well as on the body.

**What it is for:** reducing the fingerprint of an identical body sent from several
mailboxes to the same receiving domain. It is a deliverability hygiene tool, and a
small one.

**What it is not for:** personalization. Spinning "quick question" into "fast question"
does not move a reply rate, and it will not rescue a weak angle.

Rules:

- Spin only the low meaning parts: greeting, connector, sign off. Never spin the proof,
  the number or the ask, because you cannot tell afterwards which one was sent.
- 2 or 3 options per spin point, 2 to 4 spin points per email. More than that and the
  email stops being one email.
- Every option must be grammatical in every combination. If there are fewer than twelve
  combinations, read them all. If there are more, you have too many.
- Never allow a `{`, `}` or `|` inside a variable value, for the reason in section 3.
- The Emelia preview picks a variant at random too, so what you see is not necessarily
  what a given contact received. Do not debug a body from one preview.
- Spintax is not an A/B test. You cannot attribute a result to a spun variant. Use the
  step versions described in [outreach-sequence](../outreach-sequence/SKILL.md)
  instead.

## Output

`outreach/leads.csv`, with the personalization columns added and the original columns
untouched. Source and date sit next to the sentence so any claim can be checked.

```csv
email,firstName,lastName,jobTitle,companyName,companyNameClean,linkedinUrlProfile,segment,source,icebreaker,icebreaker_type,icebreaker_source,icebreaker_date
marc.leroy@kestrelpay.fr,Marc,Leroy,CTO,KESTREL PAY SAS,Kestrel Pay,https://www.linkedin.com/in/marcleroy,saas-20-200,basile,"Your changelog says the v3 API went public in June.",changelog,https://kestrelpay.fr/changelog,2026-08-29
sophie.nguyen@baleine.io,Sophie,Nguyen,VP Engineering,Baleine SAS,Baleine,https://www.linkedin.com/in/sophienguyen,saas-20-200,basile,"You wrote last month that on call was the hardest part of the year.",linkedin_post,https://www.linkedin.com/posts/sophienguyen-oncall,2026-08-12
t.brun@orvalgroup.fr,Thomas,Brun,Directeur technique,ORVAL GROUP,Orval,https://www.linkedin.com/in/thomasbrun,saas-20-200,basile,,,,
```

Row three has no icebreaker on purpose: nothing recent was found, so the cell stays
empty and the fallback in the copy takes over. That is the correct outcome, not a gap
to fill.

Report to the user in this shape:

```text
1,000 rows
  812 with an icebreaker   linkedin_post 214, company_news 331, changelog 267
  188 without              they receive the fallback opener
  0 rows with an icebreaker older than its freshness limit
  20 row sample: 18 usable, 2 weak, 0 wrong
```

## Checks before finishing

- Every row that has an `icebreaker` also has an `icebreaker_source` and an
  `icebreaker_date`, and the date is inside the freshness limit for its type.
- Every icebreaker is a complete sentence ending in a full stop, at most 25 words, and
  contains no `{`, `}` or `|`.
- Every variable used by `outreach/sequence.md` exists as a column here, and any
  variable with less than 100% coverage carries a fallback in the copy.
- The 20 row sample was rendered and read, with zero wrong rows.
- The empty case was rendered on purpose and the email still reads.
- The user has been told the coverage number, not a rounded one.

## Failure modes

**Coverage looks fine, the sentences are all the same.** The model found a template
with a slot. Check the 20 sample for repeated openings and regenerate with the source
text in front of it rather than the company description.

**The icebreaker contradicts the copy.** The sentence is true but it points at a
different problem than the angle. Personalization must land on the angle, otherwise the
second paragraph reads as a swerve.

**A variable renders empty for part of the list.** The column exists so the check in
[outreach-write](../outreach-write/SKILL.md) passes, but the cells are blank. Only per row coverage
catches this, so always report the count.

**A Liquid conditional disappears from the sent message.** The tag was malformed and
Emelia stripped every conditional block silently. Rebuild the tag and preview it on a
real contact before resending.

**The LinkedIn source is a repost.** The person shared somebody else's post. Treat the
author field as mandatory, and drop the row when the author is not the contact.

**Accented and all caps names.** `MARTIN & FILS SAS` inside a sentence looks like a
mistake. That is what `companyNameClean` is for, and why five sample rows are chosen
for their names.

## Limits

This skill does not fetch data on its own beyond what the list already holds and what
the sourcing step collected: it will not browse for a prospect. It cannot verify that a
source URL still says what it said when it was captured, which is why every row carries
a date and a freshness limit. It does not decide the copy, only fills it. And it will
not write an icebreaker for a row with no source, whatever the deadline: on cold
outreach, an empty first line costs a reply, and a fabricated one costs the domain.
