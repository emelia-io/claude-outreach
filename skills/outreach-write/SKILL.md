---
name: outreach-write
description: "Writes the copy of a cold outreach sequence, email or LinkedIn. The recommended way: the first message written for every contact, in batches of about eight, in three paragraphs (an observation about the problem the offer solves as it arises for that person, which must let the reader guess what is sold, then the offer answering it, then one question asking for 15 minutes), checked mechanically and retried before anything is kept. The follow ups are shared by the whole target or written per contact as well, step by step, as the user chooses. Asks what to personalise, the language, the formal or informal you, the gender of the person signing and the rules of the language, and has the offer reviewed before a single message is written, since a false sentence in it ends up in every message. Never invents a fact about the sender or the contact, never names the contact's company, no flattery, no closing formula. Lays out the step body the way Emelia sends it: the message variable alone in its paragraph, then the signature variable, then a real unsubscribe link from step 2 on. Produces the message columns of outreach/leads.csv and outreach/sequence.md, then runs the checkers. Triggers on: write, copy, cold email copy, email copy, sequence copy, subject line, opener, first line, first message, icebreaker line, observation, follow-up, follow up, relance, break-up email, CTA, call to action, 15 minutes, spam words, rewrite my sequence, my emails get no replies, personalized message, personalised message, personalized follow ups, A/B variant, variants, unsubscribe link, opt out, signature, bulk generation, batches, Anthropic API key, Claude Sonnet, writing prompt, which language, write in French, write in German, tu or vous, vouvoiement, tutoiement, du or Sie, usted, gender agreement, signer gender, language rules, LinkedIn message, LinkedIn copy, connection request, invitation note, InMail, DM, direct message, message LinkedIn."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Write the sequence

## What this does

Turns a target and an offer into the text of a 3 or 4 step outbound sequence, email,
LinkedIn or both, written around the problem the offer solves rather than around the
product. The recommended way writes the first message for every contact, from what their
card says, and lets the user decide, follow up by follow up, whether the others are
shared by the whole target or written per contact too. It says what the generation will
cost, writes in batches, checks every message mechanically, retries what fails, drops a
contact after three failed attempts, and merges the messages into `outreach/leads.csv`.
The steps go into `outreach/sequence.md` in the shape Emelia sends. Copy with a blocking
finding does not go to the launch step.

## When to use it

Use it after the list exists and before the flow is designed
([outreach-sequence](../outreach-sequence/SKILL.md) needs approved copy to build the
tree). Use it again when a running campaign gets opens and no replies, which is a copy
problem, not a deliverability one. Use it for LinkedIn as well as for email: the
messages, the optional invitation note and the InMail are written here, with the LINKEDIN
block of the prompt, never by adapting the email copy.

Use a different skill when: you want a short per contact line inside a shared text, the
Mode B of section 1 ([outreach-personalize](../outreach-personalize/SKILL.md)), the step
tree, delays and A/B split ([outreach-sequence](../outreach-sequence/SKILL.md)), or
answers to people who replied (`outreach-replies`).

## Inputs

| Input | Where it comes from | If it is missing |
|---|---|---|
| The offer block, `COMPANY_INFO` | section 10 of `outreach/offer.md`, written by [outreach-offer](../outreach-offer/SKILL.md) | Build it from `outreach/icp.json` and the three answers below, show it, and say that you did |
| The why of each target | one sentence per segment, written here from the offer block and confirmed by the user | Write it, show it with the offer block, wait for a yes |
| Segment, titles, pain, trigger | `outreach/icp.json` | Ask for the four angle questions of section 2, then write |
| The cards | `outreach/leads.csv`, through `scripts/first-messages.py cards` | Stop: there is nobody to write for |
| What the product does, in one sentence | `outreach/offer.md`, else the user | Ask. Do not invent a product |
| One number you can defend | `outreach/offer.md`, else the user | Write without proof and say the sequence has no proof |
| One customer you may name | `outreach/offer.md`, else the user | Use mechanism proof instead (section 6 below) |
| Sender name, company, city | the user | Ask. An email with no identity behind it is not legal in most markets. A LinkedIn message carries that identity in the profile, so it does not repeat it |
| Which channels the steps use | `outreach/campaign.json`, or the user | Ask. Email and LinkedIn have their own block in the prompts, and a multichannel campaign needs both |
| What to personalise | question 0 in section 1 | Ask, with the short recommendation, never assume |
| The language, one per country if the list spans several | question 1 in section 1 | Ask. Never default to English on a list that is not English speaking |
| Formal or informal you, in languages that separate them | question 2 in section 1 | Ask, except in English. Default to the formal one and say that you did |
| The gender of the person signing, in languages that agree | question 3 in section 1 | Ask, and say why in the same sentence. Never infer it from a first name |
| A signature configured on the sending identity | the Emelia account | Ask the user to set one before the launch. `{{signature}}` renders nothing when there is none |
| How many contacts will be written for | `outreach/leads.csv` | Count them. The count decides where the generation runs, see section 1 |

Never invent a customer name, a metric, a case study or a mutual connection. If the
user offers a number, ask where it comes from and write the source into the file.

## How to do it

### 1. Decide what is written for each person, and price it

**The offer comes first, and the user reads it.** The sender block, the `COMPANY_INFO`
block of `outreach/offer.md`, is the only source of what any message says about the
sender. A false sentence in it, a promise the product does not keep, a figure nobody can
source, ends up in every message of the campaign, and correcting it afterwards means
rewriting every message that was not sent yet. Show the block and the why of each target
to the user, and wait for a yes on both before writing anything.

#### The recommended way, and the choices around it

**Mode A, written per contact.** The first message of the campaign is written for every
contact: three paragraphs, an observation, the offer, one question. The prompt, the card,
the forbidden phrases, the checks and three examples are in
[references/first-message-prompt.md](references/first-message-prompt.md). In short:

- **The observation** is about the problem the offer solves, as it arises for that
  person, from what their card says. It does not talk about them (no "you"), quotes no
  figure, and passes **the test**: read alone, without the offer, it lets the reader guess
  what is sold. When the sender sells a way to find clients, the problem arises on the
  contact's own market, their clients. When the card is thin, it stays with the title,
  the city and the sector.
- **The offer answers the observation**, in the present tense, with at most one figure
  from the sender block and no promise of a result.
- **The question**, the only one of the message, asks for 15 minutes.
- **Sources**: the exact extracts of the card the observation rests on, which the check
  looks for.

Then **question 0, what to personalise.** Ask it before anything else, with one short
recommendation, and never decide for the user:

> What should be written for each person? (a) the first message only, with follow ups
> shared by the whole target; (b) the first message and every follow up; (c) a mix: tell
> me which follow ups. My advice for a first campaign: (a). The first message is the one
> the card changes most, shared follow ups are written and checked once, and they cost
> nothing per contact. Go to (b) or (c) when the cards are rich enough to say something
> new three or four times.

> Qu'est-ce que j'écris pour chaque personne ? (a) le premier message seul, avec des
> relances communes à toute la cible ; (b) le premier message et chaque relance ; (c) un
> mélange : dites-moi quelles relances. Mon conseil pour une première campagne : (a). Le
> premier message est celui que la fiche change le plus, des relances communes s'écrivent
> et se contrôlent une fois, et ne coûtent rien par contact. Passez à (b) ou (c) quand les
> fiches sont assez riches pour dire du neuf trois ou quatre fois.

A personalised follow up follows every rule of the first message (nothing invented, never
the company's name, no flattery, the link with the offer, the checks) and every rule of
the follow ups (it reads alone, exactly one question mark on its last sentence, the asks
in the order 2, 3, 4, no reference to an earlier message), and it takes **another angle
than the first message's observation**: scarcity, timing, cost, risk. A shared follow up
keeps the follow up rules. Both prompts are in
[references/follow-up-prompt.md](references/follow-up-prompt.md).

Write the choice into the header of `outreach/sequence.md`, because the rest of the
pipeline reads it: `Mode: A`, then `Personalised: 1, 3` and `Shared: 2, 4`. Choice (b)
is `Personalised: 1, 2, 3, 4`: every message of the sequence written for the person.

**Mode B, one text for everybody**, as an option when the cards carry too little to
write a whole message from: one written body with small per contact variables, an
icebreaker sentence for instance, filled by
[outreach-personalize](../outreach-personalize/SKILL.md). It follows the same rules as
Mode A: the three paragraph shape, one question asking for 15 minutes, nothing invented,
never the company's name, the same forbidden phrases. Do not write one bland message and
pretend it is personal: write **two variants that test genuinely different approaches**,
as below, so the send teaches you something. `Mode: B` in the header.

##### Ask these four questions before you generate anything

The prompts write in one language, in one register, for one signer. Getting any of those
wrong is not a style problem, it is a mistake in the first sentence of every message you
send. Ask. Do not infer.

**1. The language.** Always. If `outreach/icp.json` makes it obvious, state the
assumption rather than asking blind, and still wait for the answer.

> Which language should I write these messages in? If the list spans several countries I
> can write one language per group: tell me which ones and I will route on `country_code`
> in `outreach/leads.csv`.

> Dans quelle langue est-ce que j'écris ces messages ? Si la liste couvre plusieurs pays,
> je peux écrire une langue par groupe : dites-moi lesquelles, je répartis sur la colonne
> `country_code` de `outreach/leads.csv`.

Several languages means several runs: one language, one set of answers below, one
generation, one header, its batches checked in that language.

**2. The form of address.** Only for languages that make the distinction: French,
German, Spanish, Portuguese, Italian, Dutch, Russian, Polish and the others in
[references/language-rules.md](references/language-rules.md). **Never ask it in
English**, where the question has no meaning and asking it only makes you look automated.

> French separates "tu" and "vous". Which do you use with this segment? "Vous" is the
> safe default in cold B2B, "tu" only if you already speak that way to these people.

> Le français distingue le tutoiement et le vouvoiement. Lequel voulez-vous pour ce
> segment ? Le vouvoiement est la valeur sûre en B2B à froid, le tutoiement seulement si
> vous parlez déjà comme ça à ces gens.

**3. The gender of the person signing.** Only for languages where what the sender says
about themselves agrees: French, Italian, Spanish, Portuguese, Russian, Polish. Ask it
even when it feels intrusive, explain why in the same breath, and **never infer it from
a first name**. If the user prefers not to say, the prompt writes so that nothing agrees
with the sender.

> One grammar question, and I would rather ask it than guess. In French, what the sender
> says about themselves agrees: "je serais ravi" becomes "ravie" when a woman signs.
> Which form should I use for the person signing these messages? I will not work it out
> from a first name.

> Une question de grammaire, que je préfère poser plutôt que deviner. En français, ce que
> l'expéditeur dit de lui s'accorde : « je serais ravi » s'écrit « ravie » quand c'est une
> femme qui signe. Quelle forme est-ce que j'utilise pour la personne qui signe ? Je ne le
> déduis pas d'un prénom.

The recipient's gender is a different problem, and the answer is not to ask: the list
does not carry it reliably, so the greeting is the first name, never a gendered
salutation.

**4. The rules for that language.** Do not ask this one open. Read the lines for the
chosen language out of [references/language-rules.md](references/language-rules.md), show
them, and ask what to add.

> For French I will add these rules to the prompt: [the lines]. Anything to add, or a
> house rule of your own?

> Pour le français, j'ajoute ces règles au prompt : [les lignes]. Vous voulez en ajouter,
> ou imposer une règle maison ?

The answers go into the `LANGUAGE` block of the prompts, as
[references/language-rules.md](references/language-rules.md) section 1 shows, and into
the header of `outreach/sequence.md` (`Language:`, `Address:`, `Signer:`), because the
next batch six weeks from now has to come out in the same voice.

##### How a batch runs

1. `python3 scripts/first-messages.py cards outreach/leads.csv --out outreach/copy` builds
   the cards, eight contacts per batch file. A card carries what the model may read about
   a contact and nothing else: never the last name, the email address, the website or
   the LinkedIn URL. Half emojis are removed from every field, since one of them makes a
   model API refuse the whole batch.
2. Write the header once (`outreach/copy/header.md`: the sender block, the targets and
   their why, in the language of the messages), then send each batch with the system
   prompt and the last line `Write N messages now, one for EACH recipient above (index 0
   to N-1).`
3. `scripts/first-messages.py check` on each answer: grave faults, light faults, the
   batch faults, the messages to shorten.
4. One targeted retry of the faulty messages, then up to two shortenings of the ones
   still too long. A message with a grave fault left is not kept, and the contact counts a
   failed attempt; at the third, the contact is dropped and never sent anything.
5. Personalised follow ups, if the user chose some, for the contacts whose first message
   is kept, batch by batch, with the first message under each card, then
   `scripts/first-messages.py followups` on each answer.
6. `scripts/first-messages.py merge` writes the columns into `outreach/leads.csv`:
   `greeting`, `subject_line`, `message`, then `message_2`, `subject_line_3`,
   `message_3`, `message_4` for the personalised follow ups (`li_message`,
   `li_message_2`... on LinkedIn).

The reference files hold the detail of every step:
[first-message-prompt.md](references/first-message-prompt.md) sections 4 and 6, and
[follow-up-prompt.md](references/follow-up-prompt.md) section 5.

##### The greeting, the signature and the opt out stay out of the model

The model writes neither the greeting nor the signature. The merge puts the greeting at
the head of every per contact value, `Bonjour Marc,`, or `Bonjour,` when the first name
is empty, so a contact never receives "Bonjour ,". A shared follow up opens on
`{{greeting}}`, the same per contact column. `{{signature}}` stays in the step, never in
a value, and so does the opt out link: section 10.

##### Lengths

Counted on the body, without the greeting and the signature, and enforced by the scripts
from one table, the one of `scripts/audit-emails.py`:

| Message | Email | LinkedIn |
|---|---|---|
| First message | 260 to 480 characters, the prompt aims at 300 to 440 | 150 to 300, aimed at 180 to 260 |
| Follow up 2, something to receive | 90 to 220 | 80 to 200 |
| Follow up 3, the conversation | 180 to 380 | 120 to 280 |
| Follow up 4, the way out | 80 to 200 | 80 to 200 |

The prompt aims under the bounds on purpose: a model overshoots by 10 to 25% even when it
is told the number. A message that still overshoots is shortened, not edited by hand: at
1,000 rows nobody edits them one by one.

#### LinkedIn

The prompts carry a LINKEDIN block, and it is not the email with fewer words. No subject,
no signature, no link, no HTML (the body is escaped before it is rendered, so a `<p>`
arrives as visible characters), and never the words email, mail or inbox: a sending
channel is "your LinkedIn account", unless the product itself is about email. The first
message arrives right after an acceptance, so it does not thank them for accepting and
does not introduce the sender: the profile is one click away. The invitation goes out
without a note by default, since an empty note is usually accepted more often than a
pitched one; the note, when the user wants one, and the InMail are in
[references/first-message-prompt.md](references/first-message-prompt.md) section 8.

A multichannel campaign needs both blocks, with the same answers to the four questions,
and keeps the two sets of columns apart: `message`... for email, `li_message`... for
LinkedIn.

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

| Contacts to write for | Where it runs | What to do |
|---|---|---|
| Up to about 200 | a normal Claude Code subscription | Fan the batches of eight out over parallel agents |
| 200 to about 1,000 | the subscription over several days, or an API key | Ask which the user prefers before starting |
| 1,000 and above | an Anthropic API key, billed per message | Use Claude Sonnet, model id `claude-sonnet-5` |

Count the messages, not only the contacts: choice (b) of question 0 writes four messages
per contact instead of one, plus the retries, which a first batch shows the rate of.
Shared follow ups are a handful of calls for the whole target. Per contact messages are
one share of a batch call each, so the two scale very differently. Writing 100 to 200 sequences in a day sits comfortably inside
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

#### Generate in parallel, never in one long loop

One agent writing a hundred sequences one after another is the slowest possible way to
do this, and it is also the worst: by message sixty it has forgotten the brief and every
opener sounds the same. Split the contacts and fan out.

1. Write the brief **once**, to files, and pass their paths to every agent: the filled
   system prompt and `outreach/copy/header.md`. One file means one voice, and a
   correction to it applies to every agent you launch next.
2. Give each agent its own batch files, `cards-NN.json` in and `out-NN.json` out, a few
   batches each. Disjoint batches, so no two agents write the same person and no work is
   paid for twice. Each agent runs the check and the retries on its own batches.
3. Launch them **in the same message**, not one after another. Ten agents of ten finish
   in about the time one agent takes to write ten.
4. Tell the user what you launched before it starts, and report each slice as it lands.
   Silence for ten minutes reads as a hang.
5. Read the outputs back and check them yourself, against the brief: the count, the ids,
   the lengths, the forbidden characters, and the repetition **across** slices, which is
   the one failure no single agent can see:

   ```bash
   python3 scripts/check-repetition.py outreach/leads.csv
   ```

   It reports every sentence more than a couple of contacts share, and which step it
   sits in. Expect the subject lines and the openers to come back clean and the **asks**
   to be the problem: on a real run of 75 contacts the same closing question came back
   17 times, because every agent reached for the same phrasing once the personalised
   part was written. The offer facts are allowed to repeat, they are facts. The question
   at the end is not: it is the line that earns the reply, and a hundred people getting
   the same one is a hundred people getting a template. Fix it by rewriting those
   sentences with a rotation of genuinely different asks, or by re-running the slices
   with an instruction to vary the ask, never by editing a hundred messages by hand.

Tell each agent to write the messages itself and not to write a script that generates
them. An agent that hits a wall on a long task will reach for a template loop, and a
templated message is a Mode B message with extra steps and Mode A's bill.

The same shape applies to any step that loops: sourcing several cities, auditing several
mailboxes, enriching several batches. If it divides into independent slices, it runs as
parallel agents.

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
write one sequence and hope a variable covers the difference. In Mode A the angle is what
the why of the target says, and it is what every observation starts from.

### 3. Subjects

- 3 to 6 words, 45 characters at most. On a phone in portrait, the mail apps show
  roughly the first 35 characters of a subject line, so check that they make sense alone.
- A capital on the first word only. Title Case reads like a newsletter.
- No product name and no company name, the recipient's least of all. No brackets, no
  currency, no "Re:" or "Fwd:" you did not earn, no exclamation mark.
- The subject takes up the idea of the observation, with its words, not the offer: at
  least one full word of the subject is in the first paragraph, and an acronym of the
  subject is in it as is. The check looks for that.
- One line, always. A subject is plain text: nothing in it is escaped.

Shapes that survive: the bare noun phrase (`onboarding drop off`), the problem in four
words (`automation engineers no job ad finds`), the honest admission (`probably not your
problem`). Steps that stay in the thread leave the subject empty.

### 4. The opening line

The opening paragraph is the observation, in both modes, and section 1 has its rules: the
problem the offer solves, as it arises for that person, without "you", without a figure,
and passing the test (read alone, it lets the reader guess what is sold). Also:

- It contains no `I`, no `we`, no `our`, and not your company name.
- It is one or two sentences.
- It rings true to someone in the trade. When in doubt, a more careful observation.

Delete on sight: "I hope this email finds you well", "My name is X and I am the
founder of Y", "I am reaching out because", "I came across your profile", "I wanted to
introduce", "Hope you are having a great week". The full lists, in English and in French,
are in [references/first-message-prompt.md](references/first-message-prompt.md) section 5.

> Developers launching a residential programme often look for their thermal engineering
> firm at the last minute, when the permit is filed, and pick the one that made itself
> known before.

That one is written for a sender that finds clients for thermal engineering firms: the
problem arises on the recipient's market, and the observation lets the reader guess what
is sold. In Mode B, when the row has an icebreaker from
[outreach-personalize](../outreach-personalize/SKILL.md), the icebreaker plays that part;
when it does not, the written observation stands on its own.

### 5. The body: three paragraphs, 260 to 480 characters

Characters are what the checks measure, because that is what decides how many lines a
phone renders. Three paragraphs: the observation, the offer, the question. The floor is
the reference shape of `outreach-audit`, 74 characters, then 148, then 74; a first
message that carries a real observation and an offer that answers it sits above, up to
480 characters, which still fits on one phone screen with the greeting and the signature.
The length table in `outreach-audit` is the one every script reads.

One problem, one offer, one ask. Nothing else.

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

Word counts are a habit, not the gate. The checkers measure characters, because
characters are what a phone renders: 260 to 480 on step 1, and less on the follow ups.
The table is in section 1 and the reasoning is in `outreach-audit` section 3.

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

The ask is a question that can be answered by typing one line with a thumb, and it is the
only question mark of the message. Each step asks something different, in this order:

1. **The first message** asks for a 15 minute conversation, in one short question of 90
   characters at most: "Could we talk about it for 15 minutes?"
2. **Follow up 2** offers something to receive, never a call: "Should I send you the
   short version?"
3. **Follow up 3** is the only follow up that offers the conversation again, and the only
   one that may say "15 minutes".
4. **Follow up 4** asks for a permission or a last element: "Should I close the file,
   or is someone else in charge of this?"

Never: a calendar link, two questions, "let me know your availability", a proposed slot,
or a "virtual coffee".

### 8. Follow-up rhythm, and what each one adds

Every follow-up brings one new thing, or it does not exist. New means a new angle, a
new proof, a new format, or a new ask. "Just bumping this up" brings nothing and
teaches the reader to ignore the thread.

| Step | Day | Thread | What it adds | Length |
|---|---|---|---|---|
| 1 | 0 | new | The observation, the offer, the 15 minute question | 260 to 480 characters |
| 2 | 3 to 4 | same thread, empty subject | Something concrete to receive, one argument of the plan | 90 to 220 characters |
| 3 | 7 to 9 | new thread, its own subject | Another angle on the same problem, and the conversation | 180 to 380 characters |
| 4 | 14 to 18 | same thread as 3 | The way out, a permission or a last element | 80 to 200 characters |

Every follow up reads on its own: the reader may never have opened the one before, so
never "as I wrote" or "following my message". Exactly one question mark, on its last
sentence. A personalised follow up takes another angle than the first message's
observation (scarcity, timing, cost, risk); a shared one carries one argument of the plan
of [references/follow-up-prompt.md](references/follow-up-prompt.md).

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

This whole section is about **email** steps. A LinkedIn step body is the message and
nothing else: no signature variable, no opt out link, no HTML. See "LinkedIn" in
section 1.

**The reference, in Mode A.** A step written per contact carries its variable alone in
its paragraph, so the line breaks of the value become paragraphs and nothing else:

```
subject: {{subject_line}}
body:    <p>{{message}}</p><p></p><p>{{signature}}</p>
```

A personalised follow up, from step 2 on, with the opt out, and an empty subject on a
step that stays in the thread:

```
subject:
body:    <p>{{message_2}}</p><p></p><p>{{signature}}</p><p></p><p><a target="_blank" rel="noopener noreferrer" href="{{unsubscribe_link}}">Se désabonner</a></p>
```

A shared follow up carries its own text, after the greeting of the contact:

```
subject:
body:    <p>{{greeting}}</p><p></p><p>First paragraph.</p><p></p><p>Last paragraph, the question?</p><p></p><p>{{signature}}</p><p></p><p><a target="_blank" rel="noopener noreferrer" href="{{unsubscribe_link}}">Se désabonner</a></p>
```

The names are those `scripts/first-messages.py merge` writes into `outreach/leads.csv`,
and every skill of this repository reads them: `greeting`, `subject_line` and `message`
for step 1, then `message_2`, `subject_line_3` and `message_3` (step 3 opens a new
thread), `message_4`; `li_message`, `li_message_2`... on LinkedIn, `li_note` for an
invitation note. Use exactly those names: the column, the declared custom variable and
the step must agree letter for letter, or the step renders empty.

**Four rules, each of which has already broken a real campaign:**

**The body is HTML, not text.** A paragraph is `<p>...</p>`, a blank line between two
paragraphs is `<p></p>`. A newline character does nothing: write `\n` in the body and
the whole email renders as one run-on block. This is the most common way a well written
sequence arrives looking careless.

**Variables are double braces, with nothing but the name inside.** `{{firstName}}`. A
filter inside double braces, `{{ firstName | default: "" }}`, is not Liquid and does not
work.

**A fallback is written in Liquid, on a custom variable, and filled data still beats
it.** An unresolved variable renders as **nothing**, silently, which is why
"Hi {{firstName}}," on a row with no first name ships as "Hi ,". Emelia runs Liquid after
the double braces are substituted, on email and on LinkedIn, with `{#` and `#}` as its
output tag and the usual `{% %}` tags. On a custom variable it always works:
`{% if icebreaker %}...{% endif %}`. On a standard field such as `firstName`, it depends on
the version of the sending engine: recent ones read the field, older ones read it as
empty and greet everyone with the default. So give a standard field its fallback through
a custom variable that carries the value, `Hi {# greeting_name | default: "there" #},`,
or through a `CONDITION` on `$firstName`: both work whatever the version. Two cautions. A malformed Liquid tag makes the
engine delete every Liquid block of the message without a word, so preview each one on a
real contact before the launch. And a default hides a column you should have filled:
check the column is filled on every row first, and keep the fallback for the rows you
genuinely cannot fill. The syntax and its traps are in
[outreach-personalize](../outreach-personalize/SKILL.md), section 4.

**The greeting is in the value or in `{{greeting}}`, never typed as `Hi {{firstName}},`.**
In a per contact step the merge has put "Bonjour Marie," at the head of the value, or
"Bonjour," when the first name is empty. A shared step opens on `{{greeting}}`, the same
column. Either way a contact with no first name never receives "Bonjour ,". In Mode B,
where you write the text in the editor, open on `{{greeting}}` too.

**What a value never carries, and why.** No signature: Emelia replaces `{{signature}}` in
the step before it substitutes the variables, so a `{{signature}}` inside a value renders
empty. No brace of any kind: Liquid and spintax run after the variables are substituted,
on the body and on the subject alike, so a `{` in a value eats part of the sentence. No
raw `&`, `<` or `>` in a body: the value is pasted into the HTML as it is, so the merge
escapes them; a subject is plain text, so nothing is escaped there, and it stays on one
line, since a line break in a subject comes out as markup.

In Mode A, do not paste the written message into the editor and sprinkle variables
through it. The message lives in the contact's custom field, and the step only renders
it. One variable, one message, no editing in the app.

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

Two checkers, both shipped with this repository. Report every line they print.

The messages written per contact are checked batch by batch, as they come back, by
`scripts/first-messages.py check` and `followups`, before they are merged: section 1,
"How a batch runs", and [references/first-message-prompt.md](references/first-message-prompt.md)
section 6. Then `python3 scripts/check-repetition.py outreach/leads.csv` looks for the
sentences shared across batches, which no single batch can see.

The step texts are checked in `outreach/sequence.md`, shared follow ups and Mode B
included, once the file is written:

```bash
python3 scripts/check-copy.py outreach/sequence.md outreach/leads.csv
python3 scripts/first-messages.py followups outreach/copy/followups.json \
  --header outreach/copy/header.md --channel email
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
| Step 1 length | 260 to 480 characters, 504 hard cap | FAIL |
| Follow-up length | the table of section 1, by step: 90 to 220, 180 to 380, 80 to 200 | FAIL over the cap |
| Whole sequence | 400 words maximum | WARN |
| Links | 0 or 1 in step 1, 1 per step after | FAIL |
| Images | none, the open pixel is already one | FAIL |
| Variables | every `{{name}}` is a column of `leads.csv` or an Emelia contact field | FAIL |
| Filter in double braces | a pipe or a `default:` inside `{{ }}`, which does not work | FAIL |
| Liquid on a standard field | a `{# #}` or `{% %}` block that reads a standard or company field, which some versions of the sending engine read as empty | WARN |
| Liquid block | a `{# #}` or `{% %}` block, to preview on a real contact | INFO |
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

On a carrier step the body is one variable, so `check-copy.py` cannot measure the
length, the spam words or the questions from `sequence.md`: there is nothing to measure
there. It says so and skips those rows. Those messages are checked by
`scripts/first-messages.py`, batch by batch. Never report a Mode A sequence as checked
when only the carriers were checked.

### 12. Show the user, then stop

Print the whole sequence in the conversation, with the checker output under it, and
ask for a yes before anything else happens. This step ends with the user's approval,
not with a launch.

In Mode A, write the first batch, check it, and print its messages with the shared steps:
the user approves the offer block, the why of the target and the shape on those eight,
before the other batches are written. Then print a handful more at the end, with the
counts: written, retried, shortened, dropped.

## Output

Two files. The messages written per contact live in `outreach/leads.csv`, one row per
contact, and `outreach/sequence.md` holds the steps: the carriers of the personalised
steps, the text of the shared ones. Its header carries the decisions so the file can be
re-read six months later, and the step headings are what the checker parses, so keep the
format exactly. `Mode:` and `Opt-out:` are read by the checker, so spell them as below.

The columns of one contact after the merge, in French (`greeting`, `subject_line`,
`message`, then the personalised follow up `subject_line_3` and `message_3`):

```text
greeting       Bonjour Camille,
subject_line   Automaticiens introuvables par annonce
message        Bonjour Camille,

               Un automaticien qui connaît à la fois les lignes de conditionnement et la
               mise en service sur site se trouve rarement par annonce : ceux qui ont ce
               profil sont déjà en poste et ne lisent pas les offres.

               Nous ne recrutons qu'en automatisme industriel : nous identifions ces
               profils là où ils travaillent et les approchons discrètement, avec des
               références prises avant l'offre.

               Pourrions-nous en parler 15 minutes ?
message_sources lignes de conditionnement | mise en service sur site
writing_status ok
```

And `outreach/sequence.md` for that campaign, first message and follow up 3 written per
contact, follow ups 2 and 4 shared:

````markdown
# Sequence: packaging line integrators, automation recruitment

Segment: technical directors of packaging line integrators, France, 20 to 200 people
Why: integrators who need automation engineers that know commissioning, without a job ad
Mode: A
Personalised: 1, 3
Shared: 2, 4
Language: French
Address: vous
Signer: unknown, nothing agrees with the sender
Opt-out: from step 2
Variables used: greeting, subject_line, message, subject_line_3, message_3
Generation: 412 contacts in 52 batches, 9 dropped after 3 attempts, run on 2026-11-25
Checks: first-messages.py on every batch, check-copy.py 0 blocking

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
{{greeting}}

Pour un intégrateur, le profil le plus rare est celui qui sait mettre une ligne en
service chez le client.

Voulez-vous recevoir trois profils anonymisés de ce type ?

{{signature}}

<p><a href="{{unsubscribe_link}}">Se désabonner</a></p>
```

## Step 3 | email | day 8 | new thread

**Subject:** {{subject_line_3}}

**Body:**

```text
{{message_3}}

{{signature}}

<p><a href="{{unsubscribe_link}}">Se désabonner</a></p>
```

## Step 4 | email | day 15 | same thread

**Subject:**

**Body:**

```text
{{greeting}}

Faute de réponse, je suppose que le recrutement n'est pas un sujet ce trimestre.

Dois-je clore le dossier, ou quelqu'un d'autre s'en occupe-t-il chez vous ?

{{signature}}

<p><a href="{{unsubscribe_link}}">Se désabonner</a></p>
```
````

The checker prints `carrier step` on steps 1 and 3, and one warning about the subject
variable having no fallback. That warning is the point: a carrier has nothing to fall
back on, so `subject_line`, `message`, `subject_line_3` and `message_3` are filled on
every contact before the launch, which the merge and the pre-flight of
`outreach-campaign` count.

In Mode B the header says `Mode: B, two variants`, and every step carries its text, with
`{{greeting}}` first and the small variables where the copy puts them.

The LinkedIn steps are shorter, because there is no subject, no signature and no opt out
link to carry. A personalised message is its variable alone; a shared one is plain text
after `{{greeting}}`; the invitation goes out without a note unless the user chose one:

````markdown
## Step 1 | linkedin invitation | day 0

**Body:**

```text
```

## Step 2 | linkedin message | day 1 | after acceptance

**Body:**

```text
{{li_message}}
```
````

Nothing under the variable. A `{{signature}}` added here renders as nothing, and an
unsubscribe anchor added here renders as visible HTML tags in the middle of a chat
message.

## Checks before finishing

- The user read the offer block and the why of each target, and said yes, before any
  message was written.
- The user answered question 0, and the header says which steps are personalised and
  which are shared.
- The four questions were asked and answered before the generation started, and the
  answers are in the header as `Language:`, `Address:` and `Signer:`. The form of address
  was not asked in English, and the signer's gender was never inferred from a first name.
- The prompts of [references/first-message-prompt.md](references/first-message-prompt.md)
  and [references/follow-up-prompt.md](references/follow-up-prompt.md) were used with
  their placeholders filled, the block of the channel, and the forbidden phrases of the
  language.
- No card carried a last name, an email address, a website or a LinkedIn URL.
- `scripts/first-messages.py check` ran on every batch, and `followups` on every set of
  follow ups. No message kept has a grave fault; the retries and the shortenings were
  done in the order of section 1, and the contacts dropped after three attempts were
  counted and reported.
- `python3 scripts/check-repetition.py outreach/leads.csv` ran after the merge.
- `python3 scripts/check-copy.py outreach/sequence.md outreach/leads.csv` exits 0.
- Every variable a step uses is filled on every contact that stays in the list: a
  personalised step with an empty value is an empty message.
- No LinkedIn step body carries `{{signature}}` or `{{unsubscribe_link}}`. Neither
  resolves there, and the second one arrives as visible markup.
- On a multichannel campaign, both channel blocks were run with the same answers to the
  four questions, and the LinkedIn columns are the `li_` ones.
- No value contains a variable, a brace, a signature, a closing formula or an
  unsubscribe link. Those belong to the step, not to the value.
- Every factual claim in the copy comes from the offer block, and nothing in it names the
  contact's company.
- Every email step ends with `{{signature}}`, lowercase, on its own line, and the sending
  identity has a signature configured that names the sender and the company.
- Step 1 has no opt out link, every later email step has one, and each one is an anchor
  with a short text rather than a bare variable. Unless the header says
  `Opt-out: every step`, in which case every step has one.
- Each follow up brings something the previous step did not say, and a personalised one
  takes another angle than the first message.
- If more than 200 contacts were written for, the user was told what that costs and where
  it would run, and chose, before the run started.
- The user has read a sample of the messages and the shared steps, and said yes.

## Failure modes

**The angle is really the ICP.** If the four angle questions have no answers, more
copy will not help. Say it and go back to targeting.

**The observation is true and sells nothing.** It speaks of the contact's own clients
while the offer is not about clients, or of their trade in general: read alone, it does
not let anyone guess what is sold. The check flags it as having no link with the offer.
Retry with the fault, and look at the why of the target: when the observation goes off
topic across a whole batch, the why is the problem, not the model.

**All the observations sound alike.** A narrow target, and cards that carry little. The
batch check flags the shared openings and the repeated sequences of words; when it flags
most of a batch, add what the cards are missing (a role description, a summary), or say
so to the user rather than retrying the same thin material.

**The model wrote one message for a batch of eight.** The request line at the end of the
user message is missing. It has to be the last thing the model reads.

**A batch is refused by the model API as invalid JSON.** A half emoji in a field. Build
the cards with the script, which removes them, or remove them from any text you send.

**Variables look fine and render empty.** The row has the column but the cell is
blank. `check-copy.py` only sees column names; the merge counts what it wrote, and the
pre-flight of `outreach-campaign` counts every contact before the launch.

**The copy passes and still gets no replies.** After 300 sends with a verified list,
a good open rate and under 1% replies, the problem is the offer or the segment, not
the sentences. Say that plainly rather than producing another variant.

**Spam words are not the reason you land in spam.** If the user's real problem is
placement, do not rewrite the copy. Send them to `outreach-deliverability`, which
looks at SPF, DKIM, DMARC, warmup and volume.

**A long URL appears at the bottom of the received email.** The opt out variable was
pasted bare instead of being wrapped in an anchor. Fix the copy, not the tracking
settings.

**The signature is missing from the received email.** Either the variable was written
with a capital letter, which does not resolve, or the sending identity has no signature
configured. Check both, in that order.

**The messages come back too long.** The model overshoots even when told. Do not trim
by hand: the two shortenings of section 1 exist for it, and the prompt already aims
under the bound.

**Every French message says "je serais ravi" and a woman signs them.** Question 3 was
skipped, or the answer never made it into the `LANGUAGE` block. Regenerate: this is one
wrong letter in the first person singular and French readers see it immediately.

**A message opens on "Bonjour ,".** The greeting was typed in the step as
`Bonjour {{firstName}},`. Use `{{greeting}}`, or the greeting the merge put in the value.

**The LinkedIn message is signed, or ends on "Bien à vous".** The EMAIL block was used on
a LinkedIn step, or the forbidden phrases of the language were left out. Regenerate with
the LINKEDIN block rather than trimming a thousand rows.

**A LinkedIn message arrives with `<p>` visible in it.** HTML was pasted into a LinkedIn
step. The body is escaped before it is rendered, so tags show up as characters. Strip
them, and never carry the email footer across.

**The A and B variants are the same email in different words.** That is not a test, it is
two sends. Go back to the table in section 1, pick one thing to vary, and rewrite B
around it.

**The generation stops halfway through the list.** A per contact run above a couple of
hundred contacts hit the subscription limit. Do not restart it and hope: finish the run
on an Anthropic API key with Claude Sonnet, or cut the list. This is what the question in
section 1 exists to avoid.

## Limits

This skill does not send anything and does not create the campaign. Its prompts write
one way of prospecting, the observation, the offer and a 15 minute question, in a plain
register; a user who wants another register writes Mode B or hands it their own prompt,
and the checks still apply. On LinkedIn it covers the messages, the invitation note and
the InMail, and nothing else on the platform: no posts, comments, voice notes or replies
to a conversation that has started, and no way to check whether the sending account can
carry the volume, which is `outreach-deliverability` and
[outreach-sequence](../outreach-sequence/SKILL.md) section 5. Its checks are mechanical:
they catch an invented number, a named company or an off topic observation by their
words, not by understanding them, so a sample is still read by the user. It does not
know your reply rate: the benchmarks it uses are rules of thumb, and `outreach-audit` is
what gives you your own numbers. It cannot verify a claim the user makes about their own
product, which is why the offer block is read and approved before anything is written.
It does not write in a language it cannot check:
[references/language-rules.md](references/language-rules.md) lists the languages it has
something true to say about, and for anything outside it, say so and offer English or a
native reader on the first batch, because a cold message with one wrong agreement in it is
worse than one in English.
