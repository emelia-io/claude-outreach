---
name: outreach-audit
description: "Audits the content of the emails in an outreach sequence, step by step, and says what is costing replies. Reads outreach/sequence.md or a live campaign pulled from the Emelia API, then checks nine things: one ask per email, the links that dilute it, whether the question can be answered with a thumb, length against a rendered line count, attachments, images, HTML weight, the signature, spam trigger words and hollow jargon. Gives a verdict per step, a verdict for the sequence and one priority fix. Writes outreach/audit.md. Triggers on: audit, audit my emails, review my copy, check my sequence, why no replies, is this email too long, too many links, one CTA, call to action, spam words, my email looks like a newsletter, attachment, signature, HTML email, review campaign copy, roast my cold email."
license: MIT
metadata:
  author: Emelia
  version: "0.2.0"
  category: sales
---

# Audit the emails

## What this does

Reads the actual text of every email in a sequence and tells the user, step by step,
what is going to cost them replies: the ask, the links, the length, the markup, the
attachments, the images, the signature and the words. Writes `outreach/audit.md` with
a verdict per step, a verdict for the sequence, and one thing to fix first.

It does not lead with open rates or click rates. Those come last, if at all, because a
user who turned tracking off has no such data and their emails can still be wrong.

## When to use it

Before a launch, on the sequence just written. On a running campaign that is getting
no replies. On a sequence somebody else, or some tool, handed the user.

Use a different skill when you want the copy written rather than judged
([outreach-write](../outreach-write/SKILL.md)), the step tree and delays
([outreach-sequence](../outreach-sequence/SKILL.md)), SPF, DKIM, DMARC, warmup and
volume ([outreach-deliverability](../outreach-deliverability/SKILL.md)), or triage of
the replies you did get ([outreach-replies](../outreach-replies/SKILL.md)).

## Inputs

| Input | Required | If missing |
|---|---|---|
| `outreach/sequence.md` | one of the two | fall back to the live campaign |
| A campaign id plus `EMELIA_API_KEY` | one of the two | ask the user to paste the emails as plain text, and audit that |
| The signature block | no, but it changes the verdict | `{{signature}}` is stored in Emelia, not in the step: ask the user to paste it, or read a test email |
| `schedule.trackOpens` and `trackLinks` | no | assume both on, the Emelia default, and say you assumed it |

This skill spends no credits and sends nothing. It is safe to run on anything.

## How to do it

### 1. Get the text

**From the file.** `outreach/sequence.md`, in the shape
[outreach-write](../outreach-write/SKILL.md) produces: `## Step N`, a `**Subject:**`
line, the body in a fenced block.

**From a live campaign.** `GET https://api.emelia.io/advanced/campaigns/{id}`, header
`Authorization: <key>`, saved as `outreach/campaign-raw.json`. Resolve the id with
`GET /advanced/campaigns`, or `list_campaigns` on the MCP server.

`steps` is **a tree, not an array**. The root is a `START` node and each node points at
the next through `next`; a `CONDITION` node branches through `yes` and `no`. Walk all
three, keep the nodes whose `stepType` is `EMAIL`, read their `versions` array. Each
version carries `_id`, `subject`, `message` (HTML), `rawHtml`, `disabled` and
`attachments`. Skip `disabled: true` versions and say you did. Audit every enabled
version separately: an A/B test where one side is twice as long is not an A/B test.

An empty `subject` on a follow up is correct, not a bug. Emelia then reuses the last
subject sent to that contact, prefixes it with `Re: ` and threads the message.

### 2. Turn each step into what the reader sees

Strip the markup before judging the words, but keep the raw HTML, because two of the
checks are about that markup.

Then separate the body from its furniture. The **body** is the sentences: not the
greeting, not the sign-off, not `{{signature}}`, not the opt-out line. Only the body
counts toward length, because the furniture is fixed overhead that says nothing about
the writer's discipline.

Variables do not render as their token. Count a name, a company or a city at about 10
characters, and a variable carrying a written sentence (`icebreaker`, `accroche`, a
custom message from [outreach-personalize](../outreach-personalize/SKILL.md)) at a full
line, about 65. Say in the audit that the length is an estimate. The exact number comes
from a test email: `POST /advanced/campaigns/{id}/test-email`.

### 3. How long an email is allowed to be, and why

Length is the most common defect, so do the arithmetic in front of the user rather than
quoting a rule.

A phone in portrait gives an email about 390 points of width. Mail apps keep roughly 16
points of padding each side, so the text gets about 358. At the 16 point body size those
apps default to, a mixed case Latin character averages close to 8 points wide. That is
**about 45 characters per rendered line**, and across an iPhone in Mail and an Android
phone in Gmail the honest range is 40 to 50.

The shape to aim for in one email is three lines: one medium, one long, then one medium
or short. That shape is fixed by a reference email, measured rather than guessed:

```
Hello {{firstName}}

Lorem Ipsum is simply dummy text of the printing and typesetting industry.

Lorem Ipsum is simply dummy text of the printing and typesetting industry.Lorem Ipsum is simply dummy text of the printing and typesetting industry.

Lorem Ipsum is simply dummy text of the printing and typesetting industry?

{{signature}}
```

Measured: **74 characters, then 148, then 74**. The long paragraph is exactly twice the
medium one, and the last one is a question. Body total **300 characters, 47 words, three
paragraphs**. At 45 characters per rendered line on a phone that is 7 lines of text, 9
with the blank lines between paragraphs, 11 with the greeting and the sign-off.

That number is the point. A phone shows roughly 18 to 22 lines of an email under the
header block. Eleven lines means the whole message, ask included, is on screen before
the reader moves a thumb. Past that the ask sits below the fold, and an ask below the
fold is read after the decision has already been made.

**The shape matters as much as the total.** Three paragraphs: one medium, one long,
one short that carries the ask and ends in a question mark. Not five short paragraphs
adding up to the same count, and not one block of 300 characters. Check the shape, not
only the sum.

Step 1 sits at the reference. The follow-ups are shorter, because they have less to
establish and more to prove:

| Step | Body characters | Words | Rendered lines | Hard cap |
|---|---|---|---|---|
| 1 | 220 to 300 | 36 to 48 | 5 to 7 | 380 characters |
| 2 | 90 to 220 | 15 to 36 | 3 to 5 | 280 characters |
| 3 | 150 to 300 | 25 to 48 | 4 to 7 | 380 characters |
| 4, the break up | 80 to 200 | 13 to 33 | 2 to 5 | 260 characters |

Over the hard cap is blocking. Between target and cap is a fix. Under the floor, check
the email still says something: 40 characters is not discipline, it is an empty email.

The greeting line and `{{signature}}` are not counted: they are plumbing, and the
unsubscribe anchor is not counted either.

### 4. The nine checks

Run them in this order. The first one decides the verdict.

#### 1. One email, one ask, and the links that dilute it

This is the whole audit. An email has exactly one of three goals: the reader replies,
the reader goes to a page, or the reader books a time. Pick one, delete the others.

Reply is almost always the right one, because a reply starts a conversation you can
steer and a click does not. A reader who clicks through to the site reads for forty
seconds, closes the tab and never answers. You traded the answer you wanted for a page
view you cannot use.

Count the asks: every question mark, every calendar link, every "have a look at" or
"check out our pricing". More than one kind in one email is blocking, whatever the email
says otherwise.

Then count the links, excluding the opt-out.

- Step 1: zero. A link in a first cold email is a redirect from a stranger.
- Steps 2 and later: at most one, and only when the click is the ask.
- More than one besides the opt-out is blocking. Fourteen links is not a cold email, it
  is a landing page in an envelope.

Links cost deliverability too, and specifically here: verified against the Emelia
sending path on 9 September 2026, when `schedule.trackLinks` is on every link that is
not the opt-out is rewritten into a redirect on the tracking domain before the message
leaves. The filter does not see your domain, it sees an unknown redirect from an unknown
sender. The opt-out is excluded from that rewriting, so it costs nothing.

**The opt-out.** From step 2 onward, never at step 1, never as a bare variable: always a
link whose text is a word or a short phrase, from a plain "Unsubscribe" to something more
considered. Write it `<a href="{{unsubscribe_link}}">Stop these emails</a>`.

Say the trade out loud when you audit step 1: the `List-Unsubscribe` header is added only
when the message contains the unsubscribe variable, so a step 1 without it ships without
that header. That is a deliberate choice here, not an oversight, and the user should know
they made it.

#### 2. The ask itself

A question the prospect has to think about for ten minutes does not get answered. It does
not get a no either, it gets nothing, because "I will come back to this" is where cold
emails go to die.

An easy question passes all four: answerable yes or no or in one word; under twelve
words; about their world and not your product; commits them to nothing.

Ranked from least to most friction, so you can name where the email sits:

1. "Is this owned by someone at {{companyName}} today?"
2. "Worth a look?"
3. "Want the two minute version?"
4. "Open to 15 minutes next week?" (step 3 at the earliest)

Blocking: two question marks in one email; an open question of the "how do you currently
handle X" shape, which asks a stranger to write a paragraph about their own processes; a
choice of slots; "let me know your availability"; a calendar link at step 1. Picking
between three slots is work: open a calendar, form an opinion about next week, commit. A
yes or no costs three seconds.

#### 3. Length

Section 3 above. Report characters, words and rendered lines for every step, and name the
threshold you compared against.

#### 4. Attachments

The worst thing in the list. A version's `attachments` array becomes real mail attachments
at send, with the file name and its URL.

A file from an unknown sender is the most filtered shape in email. Corporate gateways
detonate attachments in a sandbox before delivery, which delays the message and marks it.
And a cold reader will not open a PDF from someone they have never heard of, so the work
in the deck is wasted anyway.

Instead: take the one number from the PDF, put it in the email as a sentence, and offer to
send the file when they answer. That turns the attachment into a reason to reply.

#### 5. Images

Blocking in the body. Emelia already adds one: with `schedule.trackOpens` on, an `<img>`
tracking pixel is appended at send time. Anything you add is the second image in a message
of forty words, and that image to text ratio is the newsletter shape filters are built to
sort. Many clients block remote images by default, so a message whose point lives in the
image arrives empty. And a banner says "this came out of a tool" in the first half second,
before a word is read.

A logo in the signature is an image. So is a background image, and so is an inline `cid:`
attachment.

#### 6. HTML

Emelia sends `text/html` with no plain text alternative, and wraps the body in a
`<div class="ltr">` at send, flattening paragraphs into `<span>` and `<br />` (verified
9 September 2026). So the goal is not a `text/plain` message, which you cannot have here.
The goal is markup that stops at paragraphs, line breaks and links.

Blocking: a layout `<table>`, `<td>`, `<tr>`, `<font>`, `<center>`, a fixed pixel width,
more than two inline `style=` attributes, or a version whose `rawHtml` flag is `true`,
which means it was pasted from a template rather than written.

One useful number: the markup ratio, raw HTML length over visible text length. Under 2 is
a written email, over 4 is a document that was designed. Say why it matters rather than
asserting it: a person writing to one person does not build a table. The markup is the
tell, and the filters read the tell before the reader does.

#### 7. The signature

The lightest possible: your name, one line saying who you are, at most one link.

Blocking: a banner or logo image, a quote, social icons, several links, legal boilerplate
(confidentiality notices, registration numbers, "please consider the environment"). Past
four lines it is not a signature, it is a footer.

It is not in the campaign steps. `{{signature}}` is a stored HTML block Emelia substitutes
at send, so you cannot audit it from the campaign JSON. Say so in the audit, then get the
real thing: ask the user to paste it, or send a test with
`POST /advanced/campaigns/{id}/test-email` and read what arrives. Do not sign off a
sequence with an unread signature, because that is where the logo hides.

#### 8. Spam trigger words

Use the list that already exists in
[`scripts/check-copy.py`](../../scripts/check-copy.py).
[`scripts/audit-emails.py`](../../scripts/audit-emails.py) reads it out of that file at
runtime, so there is one list in this repository and not two. To add words, extend the
`SPAM_EXTRA` block in the audit script rather than forking the list.

Be honest about what the list is worth. No single word sends you to spam: Gmail and
Outlook weigh sender reputation, authentication and engagement far above vocabulary.
These words matter because they correlate with the copy people delete unread, and deletion
without a reply is what actually burns a domain. One word is a smell, three in one email is
a stack, and a trigger word in the subject is blocking on its own, because the subject is
the part a filter reads first.

#### 9. Metaphors and hollow jargon

A sentence the reader has to read twice is a sentence you lost. In a cold email there is no
second chance to re-read, because there was never a first commitment.

- **The metaphor that needs decoding**: "a single pane of glass", "the Uber of
  procurement", "the glue that holds your stack together". The reader has to translate it
  into something concrete before they can judge it, and they will not.
- **The hollow abstraction**: "unlock value", "end to end ecosystem", "streamline your
  workflows", "move the needle". These say nothing that could be false, and a claim that
  cannot be false cannot be interesting.
- **The long sentence**: over 25 words. Not wrong, just unread on a phone.

The test, and show it to the user: rewrite the sentence as the literal thing it claims. If
the literal version is weaker or empty, the metaphor was hiding that. "A single pane of
glass for your funnel" becomes "one screen with all your deals on it", which is either true
and worth saying plainly, or false.

### 5. Run the script

```bash
python3 scripts/audit-emails.py outreach/sequence.md
python3 scripts/audit-emails.py outreach/campaign-raw.json
```

It parses both shapes, walks the campaign step tree, applies the nine checks, prints a
verdict per step and names the priority. It exits 1 when anything is blocking, so it also
works as a gate before a launch. Installed as a plugin it sits next to the skills rather
than in `scripts/`, so try the plugin directory too. Report every line it prints, then add
the judgement it cannot make: whether the ask is the right ask for this segment.

### 6. Verdicts

Per step, three values and nothing softer. **REWRITE** when anything is blocking, do not
launch it. **FIX** when there are only warnings, ten minutes of work. **SHIP** when it is
clean.

For the sequence, the worst step's verdict. One blocking step makes the sequence REWRITE,
because the reader meets the steps in order and step 1 is most of the list.

Then **one** priority fix, not a list. Rank the blocking findings by weight and take the
top: one ask and links 100, the ask itself 90, length 80, attachments 70, images 60, HTML
50, signature 40, spam words 30, jargon 20. Write it as an instruction the user can execute
today, on a named step.

### 7. Optional, and last: a quick look at the numbers

Only when the campaign has run, and only after the content verdict. Four sentences at most,
because it is not what the user came for.

Check `schedule.trackOpens` first. When it is off there is no open data at all and a 0%
open rate is a configuration fact, not a finding. What survives tracking being off is
`sent`, `bounced`, `replied` and `unsubscribed`, and those are the ones worth having.

| Number | Compute it as | Read it as |
|---|---|---|
| Bounce | `bounced / sent` | over 3% pause, over 5% stop and fix the list |
| Reply | unique repliers / `contacted` | 2 to 5% is the usual band for cold B2B, a rule of thumb, not a measurement |
| Unsubscribe | `unsubscribed / (sent - bounced)` | over 2% means the list or the tone |

Never copy the precomputed `bounced_percent`: it divides by the whole attached list, not by
what was sent, so on a running campaign it reads calm while the real rate is several times
higher. Under about 100 sends, report counts and not percentages. If the user wants the
full numbers treatment, rates per step and per version with their denominators, say so
rather than half doing it here.

## Output

`outreach/audit.md`. Real example, on a two step campaign pulled from the API:

````markdown
# Content audit: Acme Q4 outbound

Campaign `66f1c0a2e4b0a1d3f9c2ab77`, status PAUSED, 2 email steps, 1 version each.
Read from GET /advanced/campaigns/{id} on 2026-09-09. trackOpens off, trackLinks on.
Lengths are estimates: variables counted at 10 characters, sentence variables at 65.

**Verdict: REWRITE.** Both steps are blocking. 16 blocking findings, 5 to fix.

| Step | Verdict | Blocking | To fix |
|---|---|---|---|
| 1 | REWRITE | 14 | 2 |
| 2 | REWRITE | 2 | 3 |

## Step 1, subject "Unlock Your Revenue Potential With Acme"

861 characters, 150 words, 5 paragraphs, about 26 rendered lines on a phone. The cap for
step 1 is 350. This email is two and a half screens.

| Check | Verdict | Finding |
|---|---|---|
| One ask | blocking | 3 asks: book a meeting, go to a page, reply |
| Links | blocking | 7 links besides the opt-out |
| The ask | blocking | "How do you currently handle pipeline forecasting at {{companyName}}, and what are your biggest challenges with your current stack this quarter?" needs a paragraph to answer |
| Length | blocking | 861 characters against a 350 cap |
| Attachments | blocking | 2 (Acme-one-pager.pdf, Kestrel-case-study.pdf) |
| Images | blocking | 2, a header banner and a logo in the signature |
| HTML | blocking | rawHtml, a 600px layout table, 3 inline styles |
| Signature | blocking | legal boilerplate and a quote, 7 lines |
| Spam words | blocking | "unlock" in the subject, a stack of 8 in the body |
| Jargon | blocking | "think of it as", "a single pane of glass", 6 hollow terms |

### What it says now

> Hi {{firstName}},
>
> My name is Paul and I am the Head of Growth at Acme, the best-in-class, end-to-end
> revenue intelligence ecosystem for modern go-to-market teams. Think of it as a single
> pane of glass for your entire funnel.
>
> We help companies like yours unlock value, streamline their pipeline and move the
> needle on revenue [...]
>
> I have attached our one pager and a case study [...]
>
> How do you currently handle pipeline forecasting at {{companyName}}, and what are your
> biggest challenges with your current stack this quarter?
>
> You can also have a look at the product page, check out our pricing, read the case
> studies or just book a 30 minute call here.

Nobody answers this. The reader has four things to do and no reason to do any of them, so
they do the fifth thing, which is archive it.

### The rewrite

Subject: `forecast vs the CRM`

> Hi {{firstName}},
>
> Your Q3 board deck says {{companyName}} closed 82% of forecast.
>
> Most revenue teams find that gap in the CRM three weeks after the quarter closes, when
> the slipped deals are already gone.
>
> Is that number owned by someone at {{companyName}} today?
>
> {{signature}}

234 characters, 41 words, 3 paragraphs, about 9 rendered lines. One ask, answerable with a
name or a "not really". Zero links, zero images, zero attachments, no markup beyond
paragraphs. Verdict SHIP.

The 82% is the user's own number, given on 2026-09-08. Replace it or drop the line: do not
ship a figure nobody can source.

## Step 2, subject empty (same thread)

280 characters, 55 words, about 8 rendered lines. Length is a fix, not a rewrite.

| Check | Verdict | Finding |
|---|---|---|
| One ask | blocking | 2 asks: a question, and "let me know your availability" |
| The ask | blocking | picking a slot is work, and the question is about a PDF |
| Length | fix | 280 characters against a 220 target |
| Spam words | fix | "just following up" |
| Opt-out | fix | the link shows a raw URL, give it words |

Rewrite: cut the availability sentence, keep one question, make the opt-out
`<a href="{{unsubscribe_link}}">Stop these emails</a>`. That lands at 149 characters and
verdict SHIP.

## The one thing to do first

**Step 1: delete six of the seven links and both attachments, and keep one ask.**
Everything else in this audit is smaller than that. As written, the email offers the reader
four exits and one question, so the reader takes an exit and you never find out what they
thought.

## Numbers, briefly

trackOpens is off on this campaign, so there is no open data and none is reported here.
412 contacts attached, campaign paused before any step 2 went out.
````

## Checks before finishing

- Every email step and every enabled version was audited, and any `disabled` version is
  named as skipped.
- Each step has one of REWRITE, FIX or SHIP, and the sequence verdict is the worst of them.
- Length is reported as characters, words and rendered lines, with the threshold it was
  compared against, and labelled an estimate when variables were counted rather than
  rendered.
- The number of asks and the number of links is stated for every step, even the clean ones.
- The signature was either read or explicitly reported as unread.
- Every blocking finding names the step it is on.
- The file ends with exactly one priority fix, written as an instruction.
- Numbers, if present at all, come after the content and take less space than it.

## Failure modes

**The sequence is in the app, not in a file.** `GET /advanced/campaigns/{id}` returns it. A
401 saying the campaign was not found usually means the id belongs to another API key, not
that the key is bad: re-list the campaigns.

**Only step 1 comes back.** You read `steps` as an array. It is a tree: follow `next`, and
`yes` and `no` on condition nodes, until there is nothing left.

**The email looks short in the editor and long on the phone.** The editor is 700 pixels
wide and the phone is 390. Judge on rendered lines, not on a laptop.

**The length is wrong because of a variable.** A personalized opener can be a full
sentence, and the audit only estimates it. Send a test email and measure that.

**The user pushes back on one ask.** The objection is always "but they might want the
pricing page". They might, and they can ask for it in the reply, which is the reply you
wanted. Say it once and move on: this is a judgement about what the email is for, not a
rule about links.

**Everything passes and there are still no replies.** After 300 sends to a verified list
with clean copy, the problem is the offer or the segment, not the sentences. Say it plainly
and send them back to [outreach-icp](../outreach-icp/SKILL.md). A fourth polished variant
of a message nobody wants is the expensive mistake here.

**The user asks for their open rate instead.** If `trackOpens` is off there is nothing to
give them, and if it is on the number is inflated by image proxies and security scanners.
Neither case changes what the emails say.

## Limits

This skill reads text. It cannot tell you whether a message landed in spam, cannot see the
rendered email in the recipient's client, and cannot judge whether your offer is worth a
reply: it can only tell you whether the email asks for one clearly. It does not rewrite the
sequence, though it shows a corrected version of the worst step so the direction is not
abstract. It does not check SPF, DKIM, DMARC, warmup or volume. It cannot audit a signature
it has not been shown, and it says so rather than assuming the signature is fine. The
length thresholds are arithmetic from an assumed 45 characters per rendered line, not a
measurement, until the reference screenshot replaces them.
