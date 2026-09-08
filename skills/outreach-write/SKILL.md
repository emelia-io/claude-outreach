---
name: outreach-write
description: "Writes the copy of a cold outreach sequence: the angle, the subject lines, the opening line, the proof, the ask, the follow-ups and the break-up. Reads the ICP and the lead list, produces outreach/sequence.md, then runs mechanical checks on its own output (spam trigger words, length, links and images, variables that do not exist in leads.csv, subjects truncated on mobile, follow-ups that repeat the previous step, unverifiable claims) and refuses to hand over copy that fails them. Triggers on: write, copy, cold email copy, email copy, sequence copy, subject line, opener, icebreaker line, follow-up, follow up, relance, break-up email, CTA, call to action, spam words, rewrite my sequence, my emails get no replies."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Write the sequence

## What this does

Turns a target and an offer into the actual text of a 3 or 4 step outbound sequence,
written around the prospect's problem rather than around your product. It writes
`outreach/sequence.md`, then runs a checker over that file and reports every finding.
Copy with a blocking finding does not go to the launch step.

## When to use it

Use it after the list exists and before the flow is designed
([outreach-sequence](../outreach-sequence/SKILL.md) needs approved copy to build the
tree). Use it again when a running campaign gets opens and no replies, which is a copy
problem, not a deliverability one.

Use a different skill when: you want per contact icebreakers at scale
([outreach-personalize](../outreach-personalize/SKILL.md)), the step tree, delays and
A/B split ([outreach-sequence](../outreach-sequence/SKILL.md)), or answers to people
who replied (`outreach-inbox`).

## Inputs

| Input | Where it comes from | If it is missing |
|---|---|---|
| Segment, titles, pain, trigger | `outreach/icp.json` | Ask for the four angle questions below, then write |
| Column names | header row of `outreach/leads.csv` | Write with `firstName` only and say so |
| What the product does, in one sentence | the user | Ask. Do not invent a product |
| One number you can defend | the user | Write without proof and say the sequence has no proof |
| One customer you may name | the user | Use mechanism proof instead (step 5 below) |
| Sender name, company, city, opt-out method | the user | Ask. A message with no identity is not legal in most markets |

Never invent a customer name, a metric, a case study or a mutual connection. If the
user offers a number, ask where it comes from and write the source into the file.

## How to do it

### 1. Find the angle before you write a word

Answer these four in one sentence each. Say them to the user.

1. What happens in this person's week that your product touches?
2. What are they doing about it today? (usually: a spreadsheet, an agency, an intern,
   or nothing)
3. What does that workaround cost, in a unit they already measure? (hours, euros,
   headcount, churn, on call nights)
4. Why now? (a hire, a funding round, a launch, a regulation, a season, a tool they
   just installed)

If you cannot answer three of the four, the problem is the targeting. Stop and go back
to `outreach-icp` rather than writing prettier sentences around a guess.

The angle is one sentence with this shape, and the product does not appear in it:

> You are probably [workaround], which costs [unit], and [why now] makes it worse.

One angle per segment. If the list holds three segments, write three sequences. Do not
write one sequence and hope a variable covers the difference.

### 2. Subjects

- 3 to 6 words, 30 to 45 characters. On a phone in portrait, the mail apps show
  roughly the first 35 characters of a subject line, so treat everything past that as
  decoration. Check that the first 35 characters still make sense alone.
- Sentence case or lowercase. Title Case reads like a newsletter.
- No brackets, no currency, no "Re:" or "Fwd:" you did not earn, no exclamation mark.
- The subject sells the open, not the offer. Keep the offer out of it.
- The test: would a colleague send you this subject about this? If it only works
  coming from a vendor, rewrite it.

Shapes that survive: the bare noun phrase (`onboarding drop off`), the question about
their world (`who owns invoicing at {{companyName}}`), the two word context
(`{{companyName}} and SOC2`), the honest admission (`probably not your problem`).

Do not put a variable in a subject unless every row has a value for it. An unresolved
variable renders as an empty string in Emelia, so `quick question about ` is what part
of your list receives. Wrap it in a fallback or drop it.

### 3. The opening line

Rules, all three at once:

- It contains no `I`, no `we`, no `our`, and not your company name.
- It is one sentence.
- It is falsifiable, meaning that if it were wrong the reader could correct you.

Delete on sight: "I hope this email finds you well", "My name is X and I am the
founder of Y", "I am reaching out because", "I came across your profile", "I wanted to
introduce", "Hope you are having a great week".

The shape that works is observation then implication:

> Your changelog says the v3 API went public in June. [observation, checkable]
> Most teams ship the public API before the response monitoring. [implication]

When the row has an icebreaker from
[outreach-personalize](../outreach-personalize/SKILL.md), that is the observation.
When it does not, the implication becomes the opener on its own, which is why the
second line must stand alone.

### 4. The body: 50 to 125 words

One problem, one proof, one ask. Nothing else.

- One or two sentences per paragraph, blank line between them. It will be read on a
  phone with a thumb over half the screen.
- No bullet list in step 1. Bullets read as a deck.
- No attachment, no image, no logo, no banner. Emelia adds a tracking pixel when
  `trackOpens` is on, so any image you add is the second image in a cold email.
- Zero or one link in step 1. When `trackLinks` is on, every link is rewritten as a
  redirect, so a link in a first cold email is an unknown redirect from an unknown
  sender. Put the link in step 2 or later.
- Plain text beats HTML. If the user's step is HTML, keep the markup to paragraphs.

### 5. Proof

Only three forms count.

1. **Named customer**: who, what changed, over what period. "Kestrel Pay caught a
   schema regression 40 minutes before their first ticket" beats "we help engineering
   teams save time". Use only a name the user confirmed they may use.
2. **Mechanism proof**, when there is no name to use: one concrete sentence about how
   it works that only somebody who built it could write. "We assert on the response
   body, not the status code" is proof. "Best in class monitoring" is not.
3. **Negative proof**: "we are not a fit under 10 engineers" tells the reader you know
   the market and costs you nothing.

Banned: leading, innovative, game changing, trusted by hundreds, 10x, and any
percentage without a base. Every number must have a before and an after, or a source
you can paste when the prospect asks.

### 6. The ask

The ask is a question that can be answered by typing one line with a thumb. Ranked
from least to most friction:

1. "Is this owned by someone at {{companyName}} today, or is it still on the list?"
2. "Worth a look?"
3. "Want the two minute version?" (interest first, you send after they say yes)
4. "Open to 15 minutes next week?" (step 3 at the earliest)

Never in a first touch: a calendar link, two questions, "let me know your
availability", or a proposed slot. One ask per email, one question mark per email.

### 7. Follow-up rhythm, and what each one adds

Every follow-up brings one new thing, or it does not exist. New means a new angle, a
new proof, a new format, or a new ask. "Just bumping this up" brings nothing and
teaches the reader to ignore the thread.

| Step | Day | Thread | What it adds | Length |
|---|---|---|---|---|
| 1 | 0 | new | The angle and the ask | 50 to 125 words |
| 2 | 3 to 4 | same thread, empty subject | New proof, same angle. The shortest email of the sequence | 30 to 60 words |
| 3 | 7 to 9 | new thread | New angle on the same problem, or a format switch (one bare question) | 40 to 80 words |
| 4 | 14 to 16 | same thread as 3 | The break-up | 30 to 50 words |

Leave the subject of a follow-up empty when you want it in the same thread. Emelia
then reuses the last subject it sent to that contact, prefixes it with `Re: `, and
quotes the earlier emails underneath. So never paste the previous email into a
follow-up: it is already there, and pasting it doubles it.

Keep it to four email steps. Steps 5 and beyond mostly buy unsubscribes and spam
complaints, and a spam complaint costs the domain, not the campaign. If the deal size
really justifies more touches, add a LinkedIn step or a call task in
`outreach-sequence` rather than a fifth email.

### 8. The break-up

It closes the loop without guilt. It says you are stopping, gives one easy out, and
does not ask for a meeting. "Should I close the file, or check back after the new
year?" gets replies because a no is cheap to send.

Never: "I will assume you are not interested" followed by another email, "this is my
last attempt" when it is not, or invented scarcity.

### 9. Run the checks

Write the file first, then run the checker over it. Report every line it prints.

```bash
python3 scripts/check-copy.py outreach/sequence.md outreach/leads.csv
```

The script ships with this repository. Installed as a plugin, it sits next to the
skills instead, so try `check-copy.py` from the plugin directory too. It exits 1 when
something blocking is found, and a blocking finding is not a suggestion: fix the copy
and run it again. If the script is nowhere to be found, apply this table by hand, in
this order, and say that you checked by hand.

| Check | Threshold | Level |
|---|---|---|
| Subject length | 30 to 45 characters, hard stop at 60 | WARN then FAIL |
| Subject on mobile | first 35 characters must stand alone | WARN |
| Subject case | more than half the words capitalised, or any shouted word | WARN then FAIL |
| Step 1 length | 50 to 125 words | FAIL |
| Follow-up length | 90 words maximum | FAIL |
| Whole sequence | 400 words maximum | WARN |
| Links | 0 or 1 in step 1, 1 per step after | FAIL |
| Images | none, the open pixel is already one | FAIL |
| Variables | every `{{name}}` is a column of `leads.csv` or an Emelia contact field | FAIL |
| Variable in subject | must carry a fallback | WARN |
| Spam trigger words | one is a smell, three in one email is a stack | WARN then FAIL |
| Questions | one question mark per email | FAIL |
| Exclamation marks | none | WARN |
| Numbers | a figure with no base | WARN |
| Repetition | a follow-up sharing more than 40% of its content words with the step before | FAIL |
| Opt-out | `{{unsubscribe_link}}` or a plain opt-out sentence somewhere in the sequence | FAIL |
| Step count | more than 5 | WARN |

The spam word list the checker uses, grouped so you can see the logic:

- **Money and urgency**: free, 100% free, risk free, no cost, guarantee, guaranteed,
  act now, urgent, limited time, last chance, expires, order now, buy now, cheap,
  discount, cash, earn, make money, prize, winner, congratulations, exclusive offer,
  special promotion, double your.
- **Hype**: revolutionary, game changing, breakthrough, amazing, incredible, best in
  class, world class, cutting edge, supercharge, skyrocket, 10x, unleash, no brainer.
- **Sales cliche**: dear sir, dear friend, to whom it may concern, this is not spam,
  click here, click below, apply now, call now, increase sales, boost your, quick win.
- **Formatting**: shouted words, more than one exclamation mark, coloured or oversized
  text, several punctuation marks in a row.

Be honest with the user about what this list is. Gmail and Outlook weigh sender
reputation, authentication and engagement far more than vocabulary, so no single word
sends you to spam. These words matter because they correlate with the copy that gets
deleted, and deletion without a reply is what actually kills your reputation. The
checker flags a stack, not a word.

The variable check is the one that silently ruins a send. Emelia resolves `{{name}}`
against the contact fields first, then the contact custom fields, then the linked
company record, and renders an **empty string** when nothing matches. You do not get
an error and you do not get the raw token: you get a hole in the sentence. See
[outreach-personalize](../outreach-personalize/SKILL.md) for the fallback syntax.

### 10. Show the user, then stop

Print the whole sequence in the conversation, with the checker output under it, and
ask for a yes before anything else happens. This step ends with the user's approval,
not with a launch.

## Output

`outreach/sequence.md`. The header carries the decisions so the file can be re-read
six months later, and the step headings are what the checker parses, so keep the
format exactly.

````markdown
# Sequence: French SaaS CTOs, response level monitoring

Segment: CTO or VP Engineering, French SaaS, 20 to 200 employees, ships a public API
Angle: they learn about a broken API response from a customer, not from their monitor
Proof: Kestrel Pay, named with the account manager's permission on 2026-09-02
Ask: a question about ownership, no meeting before step 3
Variables used: firstName, companyNameClean, icebreaker
Written: 2026-09-08 by outreach-write
Checks: passed, 0 blocking, 2 warnings on the step 3 subject

## Step 1 | email | day 0 | new thread

**Subject:** status page vs reality

**Body:**

```text
Hi {# firstName | default: "there" #},

{{icebreaker}}

Most teams that ship a public API hear about a broken response from a customer
first. The uptime check returns 200, the payload changed underneath it, and the
support ticket arrives before the alert does.

Kestrel Pay caught a schema regression 40 minutes before their first ticket last
quarter. That gap is the only reason they still pay us.

Is response level monitoring owned by someone at {{companyNameClean}} today, or
is it still on the list?

Niels
Emelia, Paris
{{unsubscribe_link}}
```

## Step 2 | email | day 3 | same thread

**Subject:**

**Body:**

```text
One detail I left out: we assert on the body, not the status code. You write the
shape you expect once, and you get paged when a field disappears.

About ten minutes for a first endpoint.

Worth a look?

Niels
```

## Step 3 | email | day 8 | new thread

**Subject:** who gets paged

**Body:**

```text
Hi {# firstName | default: "there" #},

Different question. When a customer reports a bad response, who finds out first
on your side, and how long does that take?

I ask because the answer is usually support, about two hours, and that is the
number we move.

Happy to send the two minute version if it is useful.

Niels
```

## Step 4 | email | day 15 | same thread

**Subject:**

**Body:**

```text
No answer, so I will take it that response level monitoring is handled or not a
priority this quarter. Both are fine.

Should I close the file, or check back after the new year?

Niels
{{unsubscribe_link}}
```
````

The example above uses a fictional customer. Replace it with one the user confirmed
they may name, and write the confirmation date into the header.

## Checks before finishing

- `python3 scripts/check-copy.py outreach/sequence.md outreach/leads.csv` exits 0.
- Every variable used appears in the `leads.csv` header, or is an Emelia contact field,
  and any variable that is empty on some rows carries a fallback.
- Every factual claim in the copy has a source the user gave you, written in the header.
- The sender name, the company and an opt-out are present.
- Each follow-up brings something the previous step did not say.
- The user has read the sequence and said yes.

## Failure modes

**The angle is really the ICP.** If the four angle questions have no answers, more
copy will not help. Say it and go back to targeting.

**The user wants a longer email.** Longer emails do not convert better in cold
outreach; they convert differently in warm follow-up. Offer to move the detail into
step 2 or into a page you link from step 3.

**The user wants their metric in the subject.** It reads as an ad. Offer to put it in
the proof line instead.

**Variables look fine and render empty.** The row has the column but the cell is
blank. The checker only sees column names, so check coverage per column in
[outreach-personalize](../outreach-personalize/SKILL.md) before deciding a variable is
safe.

**The copy passes and still gets no replies.** After 300 sends with a verified list,
a good open rate and under 1% replies, the problem is the offer or the segment, not
the sentences. Say that plainly rather than producing a fourth variant.

**Spam words are not the reason you land in spam.** If the user's real problem is
placement, do not rewrite the copy. Send them to `outreach-deliverability`, which
looks at SPF, DKIM, DMARC, warmup and volume.

## Limits

This skill does not send anything and does not create the campaign. It does not know
your reply rate: the benchmarks it uses are rules of thumb, not measurements from your
account, and `outreach-analyze` is what gives you your own numbers. It cannot verify a
claim the user makes about their own product, so it writes claims down with their
source and leaves the responsibility where it belongs. It does not write in a language
it cannot check: if the user wants a language you are not confident in, say so, because
a cold email with an awkward sentence in it is worse than one in English.
