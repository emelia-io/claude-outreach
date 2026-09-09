---
name: outreach-write
description: "Writes the copy of a cold outreach sequence: the angle, the subject lines, the opening line, the proof, the ask, the follow-ups and the break-up. Picks between one message written per person and pushed into a custom variable, and two A/B variants that test genuinely different approaches. Prices the generation before it starts, because a thousand per contact messages do not fit in a Claude Code subscription. Lays out the step body the way Emelia actually sends it: the message, then the signature variable, then a real unsubscribe link from step 2 on. Produces outreach/sequence.md, then runs mechanical checks on its own output (length, spam trigger words, links and images, variables that do not exist in leads.csv, missing signature, opt out in the wrong place, follow-ups that repeat the previous step) and refuses to hand over copy that fails them. Triggers on: write, copy, cold email copy, email copy, sequence copy, subject line, opener, icebreaker line, follow-up, follow up, relance, break-up email, CTA, call to action, spam words, rewrite my sequence, my emails get no replies, personalized message, personalised message, A/B variant, variants, unsubscribe link, opt out, signature, bulk generation, Anthropic API key, Claude Sonnet."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Write the sequence

## What this does

Turns a target and an offer into the actual text of a 3 or 4 step outbound sequence,
written around the prospect's problem rather than around your product. It decides first
whether the campaign is one message per person or two A/B variants for everybody, says
what generating it will cost, writes `outreach/sequence.md` in the shape Emelia sends,
then runs a checker over that file and reports every finding. Copy with a blocking
finding does not go to the launch step.

## When to use it

Use it after the list exists and before the flow is designed
([outreach-sequence](../outreach-sequence/SKILL.md) needs approved copy to build the
tree). Use it again when a running campaign gets opens and no replies, which is a copy
problem, not a deliverability one.

Use a different skill when: you want per contact icebreakers at scale
([outreach-personalize](../outreach-personalize/SKILL.md)), the step tree, delays and
A/B split ([outreach-sequence](../outreach-sequence/SKILL.md)), or answers to people
who replied (`outreach-replies`).

## Inputs

| Input | Where it comes from | If it is missing |
|---|---|---|
| Segment, titles, pain, trigger | `outreach/icp.json` | Ask for the four angle questions below, then write |
| Column names | header row of `outreach/leads.csv` | Write with `firstName` only and say so |
| What the product does, in one sentence | the user | Ask. Do not invent a product |
| One number you can defend | the user | Write without proof and say the sequence has no proof |
| One customer you may name | the user | Use mechanism proof instead (section 6 below) |
| Sender name, company, city | the user | Ask. A message with no identity behind it is not legal in most markets |
| A signature configured on the sending identity | the Emelia account | Ask the user to set one before the launch. `{{signature}}` renders nothing when there is none |
| How many contacts will be written for | `outreach/leads.csv` | Ask. The count decides the mode and where the generation runs, see section 1 |

Never invent a customer name, a metric, a case study or a mutual connection. If the
user offers a number, ask where it comes from and write the source into the file.

## How to do it

### 1. Pick the mode, and price the generation before you start

Two ways to write a campaign. Decide with the user, out loud, before writing a word.

**Mode A, one message per person.** Every contact gets a message written for them, and
that message is pushed into a custom variable. The Emelia step body is then that variable
and nothing else (section 10). It is the only shape where the whole email, not just its
first line, is about this person, and it costs one model call per contact.

**Mode B, one text for everybody.** The sentences are written once. Do not write one
bland message and pretend it is personal: write **two variants that test genuinely
different approaches**, so the send teaches you something.

There is a middle shape, and it is the most common one: a written body plus a
personalized opening line in a variable. That is Mode B for the copy, since the sentences
are written once, and Mode A for the bill, since you still generate one thing per
contact. [outreach-personalize](../outreach-personalize/SKILL.md) covers it.

Write the mode into the header of `outreach/sequence.md`, because the rest of the
pipeline reads it.

#### Mode A: the per contact writing prompt

**Status: not filled in yet.** The house prompt Emelia uses to write these messages,
with its own rules, is not in this repository. It belongs here, in this section, and
nowhere else.

```text
PER CONTACT WRITING PROMPT
(waiting on the prompt Emelia uses. Paste it here, unchanged, when it lands.)
```

Until it is here, do not improvise a long house prompt of your own and present it as the
method. Do one of these two things, and say which one you did:

1. Ask the user for the prompt they already use, run that, and store it with the run so
   the next campaign reproduces the same voice.
2. Fall back to Mode B, write two real variants, and tell the user that per contact
   messages are available as soon as they supply their prompt.

The rest of this skill still applies to Mode A. The angle (section 2), the proof rules
(section 6), the ask (section 7), the length ceiling (section 5) and the assembly rules
(section 10) are constraints on whatever prompt is used, not alternatives to it. A per
contact message that breaks them is still bad copy, it is just bad copy a thousand times.

#### Mode B: two variants that test something

A variant is not a synonym. If A and B differ only in wording, a win tells you nothing
you can reuse on the next campaign. Change exactly one thing, keep everything else
identical, and write down what you expect to learn.

| What you vary | Variant A | Variant B | What a win tells you |
|---|---|---|---|
| The angle | the workaround costs time | the workaround carries a risk | which of the two is live in this market |
| The promise | fix the problem | see the problem | whether they already know they have it |
| The ask | a question about ownership | an offer to send the short version | whether the segment answers questions from strangers |
| The proof | a named customer | the mechanism, in one sentence | whether social proof or competence opens this door |
| The subject | a bare noun phrase | a question about their world | how they triage, not what they buy |

Rules that make the test worth running:

- One variable at a time. Two changes and the result is a coin flip with extra steps.
- Same list, same days, same sending accounts. A variant sent from a warmer mailbox wins
  for the wrong reason.
- Both variants must be defensible. Writing a weak B to make A win is a waste of a send.
- The metric is replies, never opens.

**Check the list is big enough before you write two of anything.** The sample size table
lives in [outreach-sequence](../outreach-sequence/SKILL.md), under "A clean A/B test".
Short version: on 1,000 contacts you can detect 5% against 10% replies, not 5% against
6%. If the list cannot carry the test, say so, write one version, and call it a learning
campaign rather than a test.

#### Generation volume, and where the generation runs

Say this when the user asks for the messages, not in a footnote afterwards.

| Messages to generate | Where it runs | What to do |
|---|---|---|
| Up to about 200 | a normal Claude Code subscription | Generate in batches of 20 to 50 and read them as you go |
| 200 to about 1,000 | the subscription over several days, or an API key | Ask which the user prefers before starting |
| 1,000 and above | an Anthropic API key, billed per message | Use Claude Sonnet, model id `claude-sonnet-5` |

A sequence is a handful of model calls. A per contact message is one call each, so the
two scale very differently. Writing 100 to 200 sequences in a day sits comfortably inside
a normal Claude Code subscription. Generating 1,000 or 10,000 per contact messages does
not, and starting anyway means stopping halfway down the list with half a campaign
written and no way to finish it today. For that volume the user sets `ANTHROPIC_API_KEY`
and the run goes against the Anthropic API, billed per message. **Use Claude Sonnet**:
writing a cold email from a filled brief is not a reasoning problem, Sonnet does it as
well as a larger model, and at 10,000 rows the price is what decides.

An order of magnitude, with its assumptions on the table: at roughly 1,500 input and 300
output tokens per message, and Claude Sonnet 5 listed at $2 per million input tokens and
$10 per million output tokens on anthropic.com/pricing in September 2026, 1,000 messages
come to about $6, and less with a cached instruction block and the Batch API. Check the
current price before you quote it to anyone.

The question to ask before any run above 200:

> Your list has 4,000 contacts. One message each means 4,000 model calls, which will not
> fit inside a Claude Code subscription. Three options: write 200 today as a first batch
> and continue tomorrow, run the whole list on an Anthropic API key with Claude Sonnet,
> roughly $25 at today's prices and one evening, or drop to two A/B variants for the
> whole list and spend nothing on generation. Which one?

Never start a run above 200 messages without that answer.

### 2. Find the angle before you write a word

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

### 3. Subjects

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

### 4. The opening line

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

### 5. The body: 50 to 125 words

One problem, one proof, one ask. Nothing else.

- One or two sentences per paragraph, blank line between them. It will be read on a
  phone with a thumb over half the screen.
- No bullet list in step 1. Bullets read as a deck.
- No attachment, no image, no logo, no banner. Emelia adds a tracking pixel when
  `trackOpens` is on, so any image you add is the second image in a cold email.
- Zero or one link in step 1. When `trackLinks` is on, every link is rewritten as a
  redirect, so a link in a first cold email is an unknown redirect from an unknown
  sender. Put the link in step 2 or later. The opt out link does not count against this:
  it is never rewritten (section 10).
- Plain text beats HTML. If the user's step is HTML, keep the markup to paragraphs.

### 6. Proof

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

### 7. The ask

The ask is a question that can be answered by typing one line with a thumb. Ranked
from least to most friction:

1. "Is this owned by someone at {{companyName}} today, or is it still on the list?"
2. "Worth a look?"
3. "Want the two minute version?" (interest first, you send after they say yes)
4. "Open to 15 minutes next week?" (step 3 at the earliest)

Never in a first touch: a calendar link, two questions, "let me know your
availability", or a proposed slot. One ask per email, one question mark per email.

### 8. Follow-up rhythm, and what each one adds

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

### 9. The break-up

It closes the loop without guilt. It says you are stopping, gives one easy out, and
does not ask for a meeting. "Should I close the file, or check back after the new
year?" gets replies because a no is cheap to send.

Never: "I will assume you are not interested" followed by another email, "this is my
last attempt" when it is not, or invented scarcity.

### 10. How the email is assembled in Emelia

Everything above is the text. This is what actually goes in the editor, and getting it
wrong is how a good sequence ships broken.

The body of an email step is three blocks, in this order, separated by a blank line:

1. **The message.** In Mode A this is the custom variable and nothing else. In Mode B it
   is the written text.
2. **`{{signature}}`**, on its own line.
3. **The opt out link**, from step 2 on, as a real link.

```html
{{message}}

{{signature}}

<p><a href="{{unsubscribe_link}}">Unsubscribe</a></p>
```

In Mode A, do not paste the written message into the editor and sprinkle variables
through it. The message lives in the contact's custom field, and the step only renders
it. One variable, one message, no editing in the app.

#### The signature

`{{signature}}` renders the signature attached to the sending identity, so the same
sequence signs correctly whichever mailbox sends it. Four things to know:

- **Lowercase only.** `{{signature}}` works, `{{Signature}}` and `{{SIGNATURE}}` do not:
  they fall through to the contact fields and render as nothing. This is the opposite of
  the opt out variable below, which is case insensitive.
- **Give it its own line**, with a blank line above it. The engine unwraps the paragraph
  around it before inserting the signature block.
- **Do not type your name above it as well.** The signature already carries the name, the
  company and the address. Two sign offs in one email reads as a mistake.
- **If no signature is configured on the identity, it renders as nothing**, silently. Ask
  the user to check theirs before the launch, and make sure it names who is writing and
  which company, because that is what makes a cold email lawful in most markets.

#### The opt out link, and why it must be a link

`{{unsubscribe_link}}` renders a **URL**, not a link. Pasted bare it puts a long tracking
URL in the middle of an otherwise plain email, which is about the loudest "this is bulk"
signal you can add to a cold message. Wrap it in an anchor whose text is a word or a short
phrase. English:

```html
<p><a href="{{unsubscribe_link}}">Unsubscribe</a></p>
<p><a href="{{unsubscribe_link}}">Unsubscribe from these emails</a></p>
```

French:

```html
<p><a href="{{unsubscribe_link}}">Se désabonner</a></p>
<p><a href="{{unsubscribe_link}}">Ne plus recevoir mes emails</a></p>
```

In the Emelia editor you do not have to type HTML. Select the word, use the link button,
and put `{{unsubscribe_link}}` in the URL field. The editor prefixes a URL it does not
recognise with its own domain, and the sending engine detects and repairs exactly that
case, so a variable in the URL field is a supported way to do it. Write the HTML into
`outreach/sequence.md` anyway, because that is what the checker reads.

Four facts about that variable, verified against the Emelia sending pipeline on
9 September 2026:

- **The name is case insensitive.** `{{unsubscribe_link}}` and `{{UNSUBSCRIBE_LINK}}` are
  the same variable: the V3 editor inserts the lowercase form, the legacy editor the
  uppercase one, and both resolve.
- **The opt out link is never rewritten by link tracking.** Every other `href` becomes a
  redirect when `trackLinks` is on. This one keeps its own URL, so it does not count
  against the one link per step rule and it does not look like a redirect to a filter.
- **It is what sets the `List-Unsubscribe` header.** The header is added only when the
  variable is present in that step's body. A step without the variable goes out without
  the header.
- **Wording rules.** No question mark, because the one question in the email is the ask.
  No URL as the anchor text. Not "click here", which is on the spam list in section 11.

#### The opt out does not go in step 1

The default rule in this repository, applied by this skill and enforced by the checker:
**no opt out link in step 1, one from step 2 on.**

Why that is defensible. The first contact is the one that has to be shortest, and a
footer is the first thing that turns a one to one email into a mailing. Nobody
unsubscribes from an email they have not yet decided about, so the link buys nothing on
day 0 and costs the impression the whole message depends on. By step 2, three days later,
the reader has seen you twice, which is exactly when an exit becomes useful, and it is
there. Between the two, every ordinary reply still works: an answer saying no stops the
sequence through `eventToStop`, faster for the recipient than any form.

What it costs, plainly: step 1 goes out without a `List-Unsubscribe` header, because that
header comes from the variable. If you send at bulk volume from one domain, or your
market expects one click opt out on every message, that is a real reason to override.

**To override it**, write `Opt-out: every step` in the header of `outreach/sequence.md`.
The checker then requires the link on every email step instead of forbidding it on step 1.
A single step sequence is treated as "every step" automatically, since there is no step 2
to carry the link.

### 11. Run the checks

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
| Signature | `{{signature}}` in every email step, lowercase | FAIL |
| Opt-out placement | absent from step 1, present from step 2 on, unless the header says `Opt-out: every step` | FAIL |
| Opt-out shape | inside an `<a href="{{unsubscribe_link}}">` with a short text, never pasted bare | FAIL |
| Opt-out wording | anchor text that is a URL, or longer than six words | FAIL then WARN |
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

In Mode A the body is one variable, so the checker cannot measure the length, the spam
words or the questions from `sequence.md`: there is nothing to measure yet. It says so
and skips those rows. The copy checks still have to be run, on the rendered sample of 20
that [outreach-personalize](../outreach-personalize/SKILL.md) produces. Never report a
Mode A sequence as checked when only the carrier was checked.

### 12. Show the user, then stop

Print the whole sequence in the conversation, with the checker output under it, and
ask for a yes before anything else happens. This step ends with the user's approval,
not with a launch.

In Mode A, print the carrier and three rendered examples, not a thousand. The user
approves the prompt and the shape, then
[outreach-personalize](../outreach-personalize/SKILL.md) runs the sample of 20 that
approves the generation itself.

## Output

`outreach/sequence.md`. The header carries the decisions so the file can be re-read
six months later, and the step headings are what the checker parses, so keep the
format exactly. `Mode:` and `Opt-out:` are read by the checker, so spell them as below.

````markdown
# Sequence: French SaaS CTOs, response level monitoring

Segment: CTO or VP Engineering, French SaaS, 20 to 200 employees, ships a public API
Angle: they learn about a broken API response from a customer, not from their monitor
Mode: B, two variants, no per contact message
Opt-out: from step 2
Proof: Kestrel Pay, named with the account manager's permission on 2026-09-02
Ask: a question about ownership, no meeting before step 3
Variables used: firstName, companyNameClean, icebreaker
Written: 2026-09-09 by outreach-write
Checks: passed, 0 blocking, 0 warnings

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

{{signature}}
```

No opt out link on step 1, on purpose. See section 10.

## Step 2 | email | day 3 | same thread

**Subject:**

**Body:**

```text
One detail I left out: we assert on the body, not the status code. You write the
shape you expect once, and you get paged when a field disappears.

About ten minutes for a first endpoint.

Worth a look?

{{signature}}

<p><a href="{{unsubscribe_link}}">Unsubscribe from these emails</a></p>
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

{{signature}}

<p><a href="{{unsubscribe_link}}">Unsubscribe from these emails</a></p>
```

## Step 4 | email | day 15 | same thread

**Subject:**

**Body:**

```text
No answer, so I will take it that response level monitoring is handled or not a
priority this quarter. Both are fine.

Should I close the file, or check back after the new year?

{{signature}}

<p><a href="{{unsubscribe_link}}">Unsubscribe from these emails</a></p>
```
````

The example above uses a fictional customer. Replace it with one the user confirmed
they may name, and write the confirmation date into the header.

In Mode A the same file holds the carrier instead of the copy, because the copy lives in
the CSV, one message per row:

````markdown
# Sequence: French SaaS CTOs, response level monitoring

Mode: A, one message per person, variables `message` and `message_2`
Opt-out: from step 2
Variables used: subject_line, message, message_2
Generation: 2,360 messages for 1,180 contacts, Anthropic API key, claude-sonnet-5,
  run on 2026-09-09
Checks: carriers checked here, copy checked on the sample of 20 in outreach/leads.csv

## Step 1 | email | day 0 | new thread

**Subject:** {{subject_line}}

**Body:**

```text
{{message}}

{{signature}}
```

## Step 2 | email | day 3 | same thread

**Subject:**

**Body:**

```text
{{message_2}}

{{signature}}

<p><a href="{{unsubscribe_link}}">Unsubscribe from these emails</a></p>
```
````

The checker prints `carrier step` on both, and one warning about the subject variable
having no fallback. That warning is the point: give `subject_line`, `message` and
`message_2` full coverage before the launch, because a carrier has nothing to fall back
on and an empty `message` sends an empty email. Coverage is counted in
[outreach-personalize](../outreach-personalize/SKILL.md), not here.

## Checks before finishing

- `python3 scripts/check-copy.py outreach/sequence.md outreach/leads.csv` exits 0.
- The header carries `Mode:` and `Opt-out:`, and the mode matches what was actually done.
- Every variable used appears in the `leads.csv` header, or is an Emelia contact field,
  and any variable that is empty on some rows carries a fallback.
- Every factual claim in the copy has a source the user gave you, written in the header.
- Every email step ends with `{{signature}}`, lowercase, on its own line, and the sending
  identity has a signature configured that names the sender and the company.
- Step 1 has no opt out link, every later email step has one, and each one is an anchor
  with a short text rather than a bare variable. Unless the header says
  `Opt-out: every step`, in which case every step has one.
- Each follow-up brings something the previous step did not say.
- If more than 200 messages were generated, the user was told what that costs and where
  it would run, and chose, before the run started.
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

**A long URL appears at the bottom of the received email.** The opt out variable was
pasted bare instead of being wrapped in an anchor. Fix the copy, not the tracking
settings.

**The signature is missing from the received email.** Either the variable was written
with a capital letter, which does not resolve, or the sending identity has no signature
configured. Check both, in that order.

**The A and B variants are the same email in different words.** That is not a test, it is
two sends. Go back to the table in section 1, pick one thing to vary, and rewrite B
around it.

**The generation stops halfway through the list.** A per contact run above a couple of
hundred messages hit the subscription limit. Do not restart it and hope: finish the run
on an Anthropic API key with Claude Sonnet, or cut the list. This is what the question in
section 1 exists to avoid.

## Limits

This skill does not send anything and does not create the campaign. It does not yet
hold the per contact writing prompt: section 1 is the place it goes, and until it is
there this skill asks for the user's own prompt rather than inventing one. It cannot
check a Mode A message it has not rendered, so a carrier that passes the checker is not
a campaign that passed the checker. It does not know your reply rate: the benchmarks it
uses are rules of thumb, not measurements from your account, and `outreach-audit` is
what gives you your own numbers. It cannot verify a
claim the user makes about their own product, so it writes claims down with their
source and leaves the responsibility where it belongs. It does not write in a language
it cannot check: if the user wants a language you are not confident in, say so, because
a cold email with an awkward sentence in it is worse than one in English.
