---
name: outreach-offer
description: "Turns what you sell into an offer a stranger would answer. Starts from a sentence you write, from your website (it reads the homepage, the pricing page, the service pages, the case studies, the about page and the blog titles with WebFetch and WebSearch) or from nothing at all. Names the category you are filed under, writes out the sentence every one of your competitors already uses, and runs the swap test: if a competitor can put their logo on your sentence without changing a word, that is a description of your trade and not an offer. Then applies the levers that make an offer specific (a narrow segment, a result with a number, a named mechanism, a deadline, risk reversal, an unusual format, a contrarian angle), and refuses to manufacture proof you do not have. Writes outreach/offer.md, ending in a paste ready block that fills the COMPANY_INFO placeholder of the per contact writing prompt. Triggers on: offer, my offer, value proposition, value prop, positioning, what do I sell, what we sell, USP, unique selling point, differentiation, differentiator, we sound generic, everyone says the same thing, my pitch, elevator pitch, company info, COMPANY_INFO, read my website, analyse my website, why would they buy from me, proof, case study, guarantee, productized offer, no one replies to my emails."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Define the offer

## What this does

Turns what you sell into a sentence a stranger has a reason to answer, and writes it to
`outreach/offer.md`. It works from your own words, from your website, or from a blank
page. Its core job is one thing: get you out of the sentence your whole category uses,
because that sentence is the first reason cold email fails, well before the copy.

The file ends with a block you paste straight into the `{{COMPANY_INFO}}` placeholder of
the per contact writing prompt. Nothing here spends Emelia credits and nothing is sent.

## When to use it

Run it before you write a single email, and before or alongside the ICP. If you cannot
say in one sentence what you sell and why someone would pick you rather than the next
name in their inbox, the sequence is already lost and no amount of copy fixes it.

Run it again when a campaign has good deliverability, decent open rates and almost no
replies. That combination is an offer problem, not a copy problem.

Use a different skill when:

- You know what you sell and need to know who to send it to:
  [outreach-icp](../outreach-icp/SKILL.md). That skill answers "to whom", this one
  answers "what, and why us".
- You have both and want the actual sentences:
  [outreach-write](../outreach-write/SKILL.md).
- You want a line about one specific prospect:
  [outreach-personalize](../outreach-personalize/SKILL.md). Personalization decorates an
  offer. It does not replace one.

## Inputs

Three entry points, and all three are supported. Pick the first one that matches.

| Input | Required | If missing |
|---|---|---|
| A description of what you sell, in your own words | one of the three | Go to entry point B or C |
| Your website URL | one of the three | Ask for it once. If there is no site, go to C |
| Nothing at all | one of the three | Ask the six questions in section 3 |
| `outreach/icp.json` | optional | If it exists, read its `offer` object and treat it as a draft to be tested, not as the answer |
| One number you can defend | strongly recommended | The offer ships without a number and says so. Never invent one |
| One customer you may name, and the date they agreed | recommended | Fall back to mechanism proof, section 8 |
| Your price, or your last three deal sizes | recommended | Ask. Price is what makes an offer concrete, and it sets the headcount floor in the ICP |
| Two or three competitor names | recommended | Derive them with WebSearch on your category and city, then confirm with the user |

Never invent a customer, a number, a guarantee or a delivery time. Anything you cannot
source goes into `open questions` in the output file, not into the offer.

## How to do it

### 1. Pick the entry point

- **A, the user explains what they sell.** Take their sentence verbatim, write it down,
  and go to section 4. You will come back for the facts you are missing.
- **B, the user gives a URL and nothing else.** Read the site, section 2, then go to 3
  for the gaps.
- **C, the user gives nothing.** Ask the six questions in section 3.

Say which entry point you are on, so the user knows whether you are reading or asking.

### 2. Read the site, for real

WebFetch costs nothing and takes a minute. Do not skim the homepage and call it research.
Budget about 8 fetches, in this order, and stop early when the picture is complete.

| Order | Page | Candidate paths | What you take from it |
|---|---|---|---|
| 1 | Homepage | `/` | The hero heading and subheading verbatim, the main call to action, the nav labels, any customer logos. This is the positioning they think they have |
| 2 | Pricing | `/pricing`, `/tarifs`, `/prix`, `/plans`, `/nos-offres`, `/packages` | The real offer. Price points, the unit they bill (per seat, per month, per project, per audit), the smallest plan, what triggers "contact us" |
| 3 | Services or product | `/services`, `/prestations`, `/solutions`, `/product`, `/features`, `/offres`, `/expertises` | The deliverables. What the client actually receives, which is almost never what the homepage says |
| 4 | Case studies | `/case-studies`, `/etudes-de-cas`, `/clients`, `/references`, `/temoignages`, `/customers`, `/success-stories` | The only place proof lives. Names, numbers, before and after, dates |
| 5 | About | `/about`, `/a-propos`, `/qui-sommes-nous`, `/equipe`, `/team` | Team size, founding year, the founder's previous job. The origin story is often the differentiator nobody put on the homepage |
| 6 | Blog index | `/blog`, `/ressources`, `/actualites`, `/insights` | Titles only, not the posts. The topic they keep writing about is where their real expertise is |
| 7 | Footer and legal | on any page, plus `/mentions-legales`, `/legal` | Legal entity, city, company number. Tells you the country and roughly the size |

Practical mechanics:

- Fetch the homepage first and ask WebFetch for the nav and footer links, then follow the
  real URLs instead of guessing paths.
- When a guessed path 404s, read `/sitemap.xml`, `/sitemap_index.xml`, or find the
  sitemap through `/robots.txt`.
- When the site is JavaScript only and WebFetch returns a shell with a handful of nav
  words, use WebSearch on `site:<domain>` and read the search snippets, which carry the
  meta descriptions. If that also fails, say the site could not be read and switch to
  entry point C. Do not narrate an empty page as if you had read it.
- Run one WebSearch on the company name plus `avis`, `review` or `alternative`. How the
  market describes them is often sharper than how they describe themselves, and the same
  search surfaces the competitors you will need in section 5.

**The six extraction targets.** Write down what you found for each, and write "not found"
where you found nothing. This list is the report you give the user.

1. What they actually sell, as a deliverable.
2. Who it is for, and any sign of who it is not for.
3. Price and billing unit.
4. Proof: named clients, numbers, dates.
5. Their current positioning sentence, quoted exactly.
6. Their vocabulary: which words are theirs, and which belong to the whole category.

**When the site is a single page.** Everything is in sections rather than pages. Extract
the same six targets from the sections, and expect pricing and proof to be absent. Ask
for exactly those in section 3, and nothing else.

**When the site is an empty brochure.** A homepage that says "we support companies in
their digital transformation" and three stock photos gives you nothing to work with, and
paraphrasing it produces exactly the email this skill exists to prevent. Say it plainly:
the site does not say what they sell, which is the same reason their emails will not.
Then run the six questions. This is a common and recoverable situation, not a failure.

### 3. The six questions

Ask these when there is nothing to read, and ask only the ones still open when there is.
One at a time when the user is answering in a chat, all six at once when they asked for
a list. Every one of them asks about something that already happened, because facts about
real transactions are specific by construction and opinions about your own value are not.

1. **When it works, what does the client end up with?** Name the thing they receive, not
   the discipline you practise.
2. **Who paid you last, what did they buy, and how much did they pay?** The last three
   deals, with amounts.
3. **What were they doing before they hired you?** A person, a tool, a spreadsheet, an
   agency, or nothing at all. That is what you actually displace.
4. **For one client you can name, what changed, with a number?** And may you use their
   name, and when did they say so?
5. **What do you refuse to do, and who do you turn away?** A boundary is the cheapest
   differentiator there is, and almost nobody publishes one.
6. **Why do you do this rather than something else?** What you learned in a previous job,
   or built, or got wrong, that your competitors did not.

Questions 5 and 6 produce the differentiator more often than the other four combined. If
the user brushes them off, come back to them once.

### 4. Name the category, and write the sentence everyone in it uses

Write down the category the prospect will file you under in the first second: the label
they would pick from a dropdown. Then write, in one line, the sentence every company in
that category has on its homepage. Show it to the user. Seeing it written down is the
point of the exercise.

| Category | The sentence the whole category uses |
|---|---|
| SEO agency | "We improve your visibility on Google and bring you qualified traffic." |
| Web agency or freelance developer | "We build modern, high performance websites tailored to your business." |
| Management consultant | "We support companies through their transformation." |
| Recruitment firm | "We find the talent that matches your culture." |
| Accounting firm | "We handle your accounting so you can focus on your business." |
| Outsourced sales or SDR | "We generate qualified leads for your sales team." |
| Fractional CFO | "We give you the financial visibility you need to grow." |
| Design studio | "We create brands that stand out." |
| IT services or MSP | "We take care of your IT so you do not have to." |
| Training provider | "We upskill your teams with tailor made programmes." |
| B2B SaaS | "The all in one platform for <function> teams." |

These are observations of what such homepages tend to say, not a measurement. If the
category is not in the table, write the sentence yourself after reading three competitor
homepages with WebFetch. It takes two minutes and it is never hard to find.

Then ask the user, out loud: what in your sentence is not in that one? The honest answer
is usually "nothing", and that is the finding.

### 5. The swap test

**Take your sentence. Replace your company name with your closest competitor's name. Read
it again. If it is still true, and still something they would happily publish, you have
not written an offer. You have written a job description for your trade.**

Run it with a named competitor, not a hypothetical one, and write the competitor's name
into the output file next to the result. A test run against nobody in particular is a
test that always passes.

Two tests behind it, for the clauses that survive:

- **Compared to what?** Ask it of every clause. "Fast delivery" compared to what, by how
  much, measured how? If the answer is "compared to nothing", cut the clause. It is
  taking up space a fact could use.
- **The reverse test.** Would any serious competitor publicly claim the opposite? "We
  deliver quality work on time" fails: nobody advertises late and bad. "We only work with
  law firms of 10 to 50 lawyers, and we do not do retainers" passes, because plenty of
  firms proudly say the opposite. **Only a claim someone could sanely refuse is a
  positioning claim.** Everything else is table stakes worn as a hat.

### 6. The seven levers

These are what actually make an offer specific. Two levers is enough. Three is strong.
One is usually not enough to survive the swap test. All seven at once reads as a scam.

| Lever | What it does | The question that finds it | The trap |
|---|---|---|---|
| **A narrow segment** | Replaces "companies" with a group that recognises itself in three words | Who were your last five clients, and what do three of them share that has nothing to do with your product? | Narrowing by size alone is not narrow. Narrow by situation: post acquisition, first CMO, migrating off X, audited next quarter |
| **A result with a number and a clock** | Turns a promise into something checkable | What number did your best client move, from what to what, in how long? | The number must come from a real client, with a date. No client, no number |
| **A named mechanism** | Explains why you get the result, in a sentence the client can repeat to their boss | What do you do that most of your competitors do not do, physically, in the work? | A name with nothing behind it is worse than no name. The name must point at a real difference in the work |
| **A deadline** | The easiest specific claim to make and to verify | How long does the first useful deliverable take? | Do not name a delay you have not hit three times |
| **Risk reversal** | Moves the risk from the buyer to you, which is the loudest signal of confidence there is | What part of this would you be willing to do before being paid? | Offer only what you can survive if 20% of them take it |
| **An unusual format** | Same expertise, different shape: fixed price and fixed scope instead of an open ended project, a subscription instead of a project, one day instead of three months | If you had to sell this as a product with a price tag, what would be in the box? | A format with no result attached is still generic, just tidier |
| **A contrarian angle** | A belief your market holds that you can argue against, with evidence | What does your industry do by default that you think is wrong? | Contrarian without proof is just rude, and it invites an argument you have to win in email |

### 7. Rewrite it, and show both

Write the before and the after side by side, and name the levers used. The user has to see
the distance. More worked examples, across more trades, are in
[references/before-after.md](references/before-after.md).

The numbers below are illustrative. Yours come from your own deals or they do not go in.

**SEO agency.** The example everybody recognises.

> **Before.** "We are an SEO agency. We improve your Google rankings and bring you
> qualified traffic."
>
> **After.** "We do SEO for French Shopify stores doing 1 to 10 million a year. We work on
> the 30 category pages that carry your revenue, not on 300 blog posts. Our last three
> clients gained between 22% and 51% more non brand organic revenue in six months. 4,500
> a month, fixed, six month minimum, and you get the list of pages we will work on before
> you sign anything."

Levers: narrow segment (Shopify, 1 to 10M, France), named mechanism (category pages, not
blog volume), a result with a number and a clock (22 to 51% in six months, from three
named clients), unusual format (fixed price, published scope before signature).

**Freelance web developer.**

> **Before.** "I build modern, high performance websites tailored to your business."
>
> **After.** "I rebuild slow WooCommerce checkouts. Your checkout goes under one second on
> mobile, in three weeks, for a fixed 6,000. If it is not under a second, you do not pay
> the second half."

Levers: narrow segment, result plus deadline, risk reversal.

**Management consultant.** The "I support companies through their transformation" case.

> **Before.** "I support companies through their organisational transformation."
>
> **After.** "I run the first 90 days after an industrial company changes hands. I sit with
> both management teams, land the org chart and the ten decisions that cannot wait, and
> hand the buyer's board a plan they sign. Eleven times since 2019, in food processing and
> packaging. 30,000, fixed, 90 days."

Levers: narrow segment (post acquisition, industrial), deadline, unusual format (fixed
price sprint), proof through repetition (eleven times since 2019).

**B2B SaaS.**

> **Before.** "The all in one platform for HR teams."
>
> **After.** "We do one thing: onboarding for companies hiring 5 to 50 people a month
> across several countries. Laptop, accounts, contract and first week schedule ready
> before day one, without anyone in HR opening a ticket. 4 per employee per month. Our
> customers went from about three hours of admin per hire to under twenty minutes."

Levers: narrow segment, named mechanism (what concretely happens), a result with a number,
a price.

### 8. Proof, and what to write when you have none

Three tiers, strongest first. Use the strongest you can actually support.

1. **A named client, a number, a date, and their permission.** "Kestrel Pay caught a schema
   regression 40 minutes before their first ticket, March 2026, named with their written
   permission on 2 September 2026."
2. **An unnamed but specific client, with a number and a date.** "A Shopify store doing 4
   million a year, plus 31% non brand organic revenue in five months, ended June 2026."
   Weaker, and honest, and still checkable in a call.
3. **Mechanism proof.** One sentence describing something you do that a stranger can judge
   from the outside, with no number at all. "We assert on the response body, not the
   status code." This is the correct fallback, not a consolation prize: it makes a claim
   about competence rather than about results, and it cannot be wrong.

**When you have no proof at all.** New offer, first client, or a business you cannot talk
about. Do not fabricate the fourth tier. Write what is true instead:

- **Your own record before this business.** "I ran this in house at a 400 person retailer
  for three years, about forty times." That is experience, and it is provable.
- **A public artefact.** A repository, a template, a teardown, a benchmark, a tool, a
  calculator. Anything a stranger can check in thirty seconds without talking to you.
  Building one is often a better use of a week than another sequence.
- **The offer itself as the proof.** "I will do the first one and you decide afterwards
  whether it was worth paying for." Risk reversal is what confidence looks like when you
  have nothing to point at yet.
- **And say it plainly in the sequence.** "We are new at this, here is why we think we are
  right, here is what it costs you to find out" outperforms a borrowed statistic.

**The line you do not cross.** Never write a number you could not source in ten seconds if
the prospect asked for it in the reply. Never name a customer without their permission and
the date of it. Never promise a result the user cannot deliver to the person receiving the
email: the sequence is a promise and the sales call is where it gets tested, so a claim
that fails there costs the meeting, not just the credibility. When the user insists on a
claim you cannot source, do not argue about honesty, argue about the reply: record it in
the file as `unverified` and keep it out of the paste ready block.

### 9. The words that carry no information

These are the words that survive the swap test, which is exactly what makes them useless.
Ban them from the offer and from the sequence.

**English:** solutions, innovative, cutting edge, best in class, seamless, robust,
scalable (unquantified), synergy, end to end, holistic, turnkey, bespoke, tailor made, we
help companies, we support, empower, unlock, leverage, game changer, revolutionary,
passionate, expert, leader, industry leading, state of the art, next generation, one stop
shop, value added, your trusted partner.

**French:** solutions, accompagnement, accompagner, sur mesure, cle en main, innovant, a
taille humaine, expertise, expert, leader, partenaire de confiance, savoir faire,
performant, optimiser, booster, revolutionner, notre ADN, passionne, ecoute, reactivite,
proximite, au service de votre croissance, nous vous accompagnons dans.

Treat the list as a diagnostic, not as a style rule. When one of these words appears, a
fact is missing at exactly that spot. Replace the word with the fact. Deleting the word
and leaving the sentence shorter changes nothing.

### 10. Assemble the COMPANY_INFO block

This is the deliverable that matters. Everything above exists to make these eight lines
true.

**The shape.** Plain text. One labelled fact per line. No markdown, no bullets, no
headings. Under about 150 words. Leave a line out entirely when you do not have the fact.

```text
What we sell: <the deliverable, in one sentence>
Who it is for: <the segment, narrow enough to recognise itself>
The problem it removes: <what happens today, in their words, not yours>
How it works, in one sentence: <the named mechanism>
Proof we may use: <claim, number, date, and the date permission was given>
Price point: <amount and billing unit>
Who it is not for: <the boundary you actually enforce>
What changes for this segment: <the one thing the opener should lean on>
```

**Why that length and that shape**, since it is a real constraint and not a preference:

- The block is read once per contact and reused unchanged. An error in it does not appear
  once. It appears on every email you send.
- The prompt around it is built to degrade well when the block is thin: it falls back to
  industry level insight, and that fallback works. It has no defence against a block that
  is too rich. Paste a homepage, a deck or a feature list in there and the model starts
  quoting your marketing back at the prospect, which is the failure this whole skill
  exists to prevent.
- One fact per labelled line means a missing fact is an absent line. A line reading
  `Proof: none` is something for the model to write around. No proof line at all is
  nothing to write around, which is what you want.
- No markdown. The model mirrors the structure it is handed, and a bulleted block produces
  bulleted emails.
- Eight lines is what fits under 150 words while still carrying what an email needs: the
  deliverable, the buyer, the problem, the mechanism, the proof, the price, the boundary,
  and the angle.

Seven of these labels are the ones the per contact prompt already expects, in
[outreach-write/references/per-contact-prompt.md](../outreach-write/references/per-contact-prompt.md)
section 4. `Who it is for` is the line this skill adds, because the offer defines the buyer
and the model reads it as context. If the ICP has two or three segments, produce one block
per segment and change only the last line.

### 11. Hand off

**This runs before [outreach-write](../outreach-write/SKILL.md).** Its block is what fills
`{{COMPANY_INFO}}` in the per contact prompt (Mode A), and it is the source of the value
proposition and the proof in the A/B variants (Mode B). The levers in section 6 are also
what makes two variants genuinely different rather than two wordings of the same claim:
variant A on the number, variant B on the contrarian angle is a real test, and two
synonyms are not. Running this first also answers, in advance, the two things
`outreach-write` asks the user for in its Inputs table: one number you can defend, and one
customer you may name.

**This is not [outreach-icp](../outreach-icp/SKILL.md).** The ICP defines who you talk to.
This defines what you sell them and why they would pick you. They feed each other in both
directions, and it is worth saying which way:

- **Offer into ICP.** The narrow segment you choose in section 6 is the first draft of
  `segments[].label`. Your price point sets `headcount.min`, because the ICP builds the
  headcount floor backwards from what a deal has to be worth. Your `Who it is not for`
  line becomes an entry in `exclusions`.
- **ICP into offer.** `icp.json` already carries an `offer` object (`what`, `problem`,
  `proof`, `price_point`, `minimum_viable_deal`). When the file exists, read it, run it
  through the swap test, and say whether it survived. If you rewrite the offer here, tell
  the user that the ICP's `offer` object is now behind and should be updated.
- **The ICP is the reality check on your narrowing.** A segment that sounds perfect and
  counts 40 people is a named account list, not a campaign: the ICP's floor is roughly 150
  contacts per segment. Count before you commit to a narrow offer, then widen one criterion
  if you have to.

Run this skill first when the user cannot say what makes them different, which is most of
the time. Run the ICP first when the offer is already sharp and only the audience is open.
Both files exist before anyone writes an email.

## Output

Write `outreach/offer.md`. If it already exists, show what changes and ask, or write
`outreach/offer-<name>.md`.

````markdown
# Offer

Created: 2026-09-09
Entry point: website (https://exemple-seo.fr) plus five questions answered by the user
Pages read: /, /tarifs, /prestations, /etudes-de-cas, /a-propos, /blog
Not found on the site: price (it said "sur devis"), any boundary on who they turn away

## 1. What we sell

SEO for Shopify stores: we work the category pages that carry revenue, and we report in
revenue, not in positions.

## 2. Who it is for

French Shopify stores doing 1 to 10 million a year, with an in house marketing person and
no SEO agency currently under contract.

## 3. The problem it removes

Their organic revenue is flat while their ad costs rise. They have a blog nobody reads and
category pages nobody optimised, and their last agency reported keyword positions that did
not turn into orders.

## 4. What makes it different

| Lever | How it is implemented here |
|---|---|
| Narrow segment | Shopify only, 1 to 10M, France. We turn down WooCommerce and marketplaces |
| Named mechanism | The 30 pages rule: we rank the 30 category and collection pages that carry the revenue, and publish nothing until they are done |
| Result with a clock | 22% to 51% more non brand organic revenue in six months, on the last three clients |
| Unusual format | Fixed price, and the page list is sent before signature so the scope is visible up front |

Swap test, run against Agence Kiwi (agence-kiwi.fr) on 2026-09-09: fails on the before
sentence, passes on the after sentence. Kiwi could not publish "we turn down WooCommerce"
or "the 30 pages rule" without changing how they work.

## 5. Proof

| Tier | Claim | Source | Date | May we name them |
|---|---|---|---|---|
| 2 | +51% non brand organic revenue in 6 months | client dashboard, GA4 export | ended 2026-06 | no, NDA. Described as "a Shopify store doing 4M" |
| 1 | +22% in 6 months, home and garden | GA4 export | ended 2026-04 | yes, Maison Verte, agreed by email 2026-09-02 |
| 3 | Mechanism: we do not publish a blog post until the 30 category pages are done | our own process | n/a | n/a |

## 6. Price and packaging

4,500 per month, fixed, six month minimum. No setup fee. Smallest engagement is the six
months: we do not sell audits on their own.

## 7. Category and the sentence we were using

Category: SEO agency.
The sentence the whole category uses: "We improve your visibility on Google and bring you
qualified traffic."
What our homepage said on 2026-09-09: "Boostez votre visibilite et generez du trafic
qualifie." Same sentence, translated.

## 8. Words we do not use

visibility, qualified traffic, boost, expertise, accompagnement, sur mesure, partenaire de
confiance, solutions, leader.

## 9. Open questions

- No boundary on deal size below 1M revenue: we say we turn those down, but we took one in
  March. Decide before the campaign or drop the claim.
- The 51% figure is under NDA, so it can only be used unnamed. Confirm that is acceptable.

## 10. COMPANY_INFO block

Paste this between the `<company_info>` tags of the per contact writing prompt. 138 words.

```text
What we sell: SEO for Shopify stores, on the category pages that carry the revenue.
Who it is for: French Shopify stores doing 1 to 10 million a year, marketing handled in
house, no SEO agency under contract.
The problem it removes: organic revenue is flat while ad costs rise, and their last agency
reported positions instead of orders.
How it works, in one sentence: we rank the 30 category pages that carry the revenue, and
publish nothing until those are done.
Proof we may use: Maison Verte, plus 22% non brand organic revenue in six months, named
with permission on 2 September 2026.
Price point: 4,500 per month, fixed, six month minimum.
Who it is not for: WooCommerce, marketplaces, stores under 1 million a year.
What changes for this segment: they measure agencies in orders, not positions.
```
````

Then tell the user three things: which sentence they were using, which levers you applied,
and what you could not prove. Wait for a yes on the block before anyone writes an email.

## Checks before finishing

- `outreach/offer.md` exists and section 10 holds the block inside a fenced code block.
- The block is under about 150 words, plain text, one labelled fact per line, no markdown
  and no bullets inside it.
- Every line of the block is a fact. Any line that is a category label ("a leading agency",
  "tailor made support") is not finished.
- The swap test was run against a named competitor, and the file records the competitor and
  the result.
- At least two levers from section 6 are named in section 4, and each one names the fact
  that implements it.
- Every number anywhere in the file carries a source and a date. Unsourced numbers live in
  `open questions`, never in the block.
- Every named customer carries the date they gave permission.
- No word from the section 9 list appears in the block.
- If a website was read, the file lists the URLs fetched and which of the six extraction
  targets came back empty.
- If there is no proof at all, the file says so in one sentence and the block uses
  mechanism proof rather than a number.
- The user has confirmed the block line by line. It goes on every email in the campaign, so
  it gets read once, carefully, by the person whose name is on it.

## Failure modes

**Every answer comes back generic.** The user rewords the category sentence six times.
Symptom: their answers contain the section 9 words. Stop asking about the offer and ask
about the last three deals instead, one at a time, with amounts. Facts about transactions
that actually happened cannot be generic.

**There are no clients yet.** Then there is no offer to sharpen, there is a hypothesis. Say
so, write it into the file as a hypothesis with today's date, put a boundary and a risk
reversal on it (the two levers that need no history), and treat the first campaign as the
test. Do not manufacture a positioning to fill the section.

**The user wants to keep a claim you cannot source.** Do not turn it into an argument about
honesty. Make it about the reply: an unsourced number gets checked on the call, and a
prospect who catches one stops reading. Mark it `unverified` in the file, keep it out of
the block, and move on.

**The narrow segment kills the market.** The offer is sharp and Basile counts 40 people.
Widen one criterion, usually geography or headcount, and recount. Below roughly 150
contacts a segment cannot be a campaign, only a named account list.

**The site will not render.** WebFetch returns nav labels and nothing else. Try the
sitemap, then WebSearch on `site:<domain>` for the meta descriptions, then stop and switch
to the questions. Never present an unread page as read.

**The company sells four things.** One block covering four products produces four vague
emails. Pick the single offer this campaign is about, write its block, and say the others
are separate campaigns. The three segment rule from the ICP applies to offers too.

**The offer is sharp and undeliverable.** "Page one in six months, guaranteed" from someone
who has never done it. The sequence writes a cheque the delivery cannot cash, and the
refund is the cheapest of the consequences. Ask, for every claim in the block: if twenty
people say yes next week, does this still hold?

## Limits

This skill does not do market research, does not size demand, does not price your product,
and does not verify that a competitor's claims are true. It cannot invent a differentiator
you do not have: if you do the same work, at the same price, for the same people as
everyone else, the honest output is that the differentiator has to be built before it can
be written, and this file will say so rather than dress it up.

The category sentences and the banned word lists are observations of what such homepages
tend to say, not measurements. Reading a website tells you what a company publishes, not
what it sells: the pricing page and the last three invoices disagree more often than not,
so the questions in section 3 always beat the site when the two conflict. Nothing here is
a legal, regulatory or trademark review of a claim you intend to publish.
