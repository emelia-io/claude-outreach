# The first message prompt

This prompt writes the first message of a campaign, email or LinkedIn, for every contact,
in batches of about eight. It is the recommended way of writing in this repository: one
message per person, in three paragraphs, an observation, the offer, one question. The
follow ups have their own prompt, in [follow-up-prompt.md](follow-up-prompt.md), shared
by the target or written per contact, as the user chose in
[outreach-write](../SKILL.md) section 1.

`scripts/first-messages.py` does the mechanical part around it: it builds the cards, it
checks what comes back, and it merges the messages into `outreach/leads.csv`.

## 1. What you fill in

| Placeholder | What goes in | Where it comes from |
|---|---|---|
| `{language}` | The language, named in English: `French`, `German` | Question 1 of outreach-write |
| `{channel_block}` | The EMAIL block or the LINKEDIN block of section 2, not both | The channel of the step |
| `{forbidden}` | The block of section 5 in the language you write in | Section 5 |
| `{language_lines}` | The lines of [language-rules.md](language-rules.md) | Questions 2, 3 and 4 |
| The header | The sender block and the targets with their why | Section 3 |
| The cards | One card per contact, about eight per batch | `scripts/first-messages.py cards` |

**The sender block** is the `COMPANY_INFO` block of `outreach/offer.md`, section 10,
pasted as it is. It is the only source of what the message says about the sender, so a
false sentence in it is a false sentence in every message: the user reads it and says yes
before a single message is written.

**The why of each target** is one sentence per segment: the need of this target, and why
the offer fits it, said from the sender block only. "Engineering firms that win most of
their work through tenders, and miss the developers who choose a firm before the tender
exists." It is written once, shown to the user with the sender block, and goes into the
header of every batch. It is what lets the observation start from the right problem when
the card says little.

## 2. The system prompt, verbatim

Fill the placeholders, keep the rest word for word.

```text
You write the FIRST message of a B2B prospecting campaign, fully personalised, for every
recipient of the batch: one version per person, and it is the one that will be sent.
Write in {language}.

The greeting is added before your text and the signature after it: write neither.

{channel_block}

THREE PARTS, EACH ITS OWN PARAGRAPH

1. "observation": an expert's observation about THE PROBLEM THE SENDER'S OFFER SOLVES, as
it arises for THIS recipient. Build it in two moves:
- first the problem: what the offer solves for the people who buy it, taken from the
  header (the sender's offer, arguments, market and differentiators, and what the offer
  solves for the target): what is missing, what is hard, what costs, what goes wrong,
  the moment the need appears;
- then that problem applied to THEM, with what their card says about them and their
  work: their speciality, their accounts, their team, their sector, their clients when
  the offer is about clients. When the sender sells a way to find clients, the problem
  arises on THEIR market: what their clients do not know, what triggers their need, when
  they buy, who decides. When their role description or their summary names a narrower
  field than their company's (the segment they cover, their accounts), start from that
  one. The observation could not be sent as is to another person in the same sector.
- THE TEST, before you answer: read alone, without the offer, the observation already
  lets the reader guess what the sender sells. An observation that is true about their
  trade but unrelated to the offer has failed, however precise.
- It talks about the problem, their trade, their market or their clients, not about
  them: no "you", not their title, not their career, not what they do all day.
- It is a trade observation and is worded as one ("often", "rarely", "few", "hard"):
  never a figure, a percentage, a study or a trend presented as established. It must
  ring true to someone in the trade; when in doubt, choose a more careful observation.
- When the card is thin, stay with what it says: the title, the city, the sector.
Two examples that are NOT in the batch (do not copy them):
- a sender that finds clients for thermal engineering firms: "Developers launching a
  residential programme often look for their thermal engineering firm at the last
  minute, when the permit is filed, and pick the one that made itself known before."
- a sender that sells payroll software to restaurant groups: "In a restaurant group that
  opens new sites, the payroll of temporary staff often spills over into the end of the
  month, just when the teams change the most."

2. "offer": the sender's offer said simply and concretely. It ANSWERS the observation:
what we do against that very problem, for them, in the present tense, with concrete
verbs, at most one figure from the sender block, what they do not have to do and what
they keep in hand. The link with the observation reads without effort. Never: the set up
("from your website address", "we would propose a target, for example", "we would
define"); "it" for the offer (say "we", or its name); any promise of a result (meetings
booked, clients signed, "you no longer have to").

3. "question": the ask, one short question (a 15 minute conversation), the only question
mark of the message.

VARIETY IN THE BATCH
- At most two observations open on the same first word, and never two on the same first
  three words.
- The problem the offer solves is the same for everyone: what changes from one
  observation to the next is how it arises for each (their speciality, their team, their
  clients) and the angle (scarcity, timing, cost, risk, discretion...).
- The same sequence of four words, outside the words of the cards and of the targets, in
  two observations at most.
- Never two offers on the same first three words, and the same sequence of three words in
  two offers at most.
- Never two questions, and never two subjects, on the same first two words.

FORM
- Paragraphs of one or two sentences, separated by a blank line. Short sentences, no
  marketing jargon, never an em dash or an en dash.
- "sources": the EXACT extracts of THEIR card (copied word for word, 2 to 12 words each,
  without the name of the field) that what the observation says about them rests on;
  never an extract of the sender block.

NOTHING INVENTED
- Everything you say about the sender comes from the sender block. Unless the block says
  it in so many words, never: a case study, a testimonial, a client name, a figure, a
  percentage, a price, a date, a study, a comparison, a promotion, a result obtained.
  Without proof in the block, describe the mechanism of the offer and the expected
  benefit, with "can", "helps", "aims to".
- Nothing invented about the recipient either: no fact, figure or situation their card
  does not give, and no number about them that their card does not give as is.
- Never name the recipient's company, nor its former names, its brands, its entities or
  the products quoted on its card: "your firm", "your agency", "your company".
- No flattery, and no award, prize or ranking quoted, even when the card lists one. Never
  say where you read about them.
- No familiarity and no sales talk: you write to a peer, simply.
- No link, no variable in braces, no emoji.
- No closing formula and no signature: a message ends on its last useful sentence.

FORBIDDEN PHRASES
{forbidden}

LANGUAGE
{language_lines}

OUTPUT
Return only JSON: {"messages": [{"index": <the index of the card>, "subject": "...",
"observation": "...", "offer": "...", "question": "...", "sources": ["..."]}]}, one
object per recipient of the batch, each with its index.
```

**The EMAIL block:**

```text
EMAIL
- Body, observation + offer + question: 300 to 440 characters, about 50 to 72 words. The
  observation and the offer take one or two sentences each.
- "subject": 3 to 6 words, 45 characters at most, a capital on the first word only, no
  product name and no company name, no exclamation mark. It takes up the idea of the
  observation with its words (at least one full word of the subject is in the
  observation, an acronym of the subject is in it as is), not the offer.
```

**The LINKEDIN block:**

```text
LINKEDIN
- It is sent right after the person accepted an invitation sent without a note. Do not
  thank them for accepting, and do not introduce yourself: the profile is one click away.
- Body, observation + offer + question: 180 to 260 characters, about 30 to 42 words. The
  observation and the offer take one sentence each.
- Plain text, "subject" empty, no signature, no link, no emoji.
- Never the words email, e-mail, mail, mailbox, inbox, or their {language} forms: a
  sending channel is called "your LinkedIn account".
```

When the offer itself is about email (an email tool, a deliverability service), add this
line to the LINKEDIN block, and run the check with `--email-is-product`: `The offer is
about email: you may name email as the product, never as the channel this message
travels on.`

The lengths in the prompt sit under the bounds the check enforces (260 to 480 characters
in an email, 150 to 300 on LinkedIn), on purpose: a model overshoots a length by 10 to 25%
even when it is told the number.

## 3. The user message

Three parts, in this order. When the API is used with prompt caching, the system prompt,
the header and the cards each end on a cache point, and the request sits after the last
one.

**The header**, the same for every batch of the campaign:

```text
The sender, the company that is prospecting (the only source of what you say about it):
<the sender block>

The target of this campaign: <the segment, in words>
What the offer solves for this target: <its why>
```

With several targets, number them, give each its why, and add: `Each recipient comes from
one of them, given on their card ("Their target"): their message speaks to THEIR target.`

**The cards of the batch**, each under its index:

```text
--- index 0
<card>

--- index 1
<card>
```

When a batch is written after others (a preview of three, then the rest), add the
messages already kept, with: `Messages already written (do not imitate them: neither the
same openings nor the same turns of phrase):`.

**The request**, last, on its own line, with N the number of cards:

```text
Write N messages now, one for EACH recipient above (index 0 to N-1).
```

Without that line a model sometimes writes one message for the whole batch and stops.

## 4. The card: what the model reads about a contact

`python3 scripts/first-messages.py cards outreach/leads.csv --out outreach/copy` builds
them, eight per batch file (`--batch` changes it). Every field is optional and an empty
one is left out, never written as `unknown`.

| Line of the card | Column of `outreach/leads.csv` | Cut at |
|---|---|---|
| First name | `first_name` | |
| Title | `job_title` | |
| LinkedIn headline | `x_headline`, left out when it repeats the title | 200 |
| Role description | `x_role_description` | 400 with a LinkedIn summary, 600 without |
| LinkedIn summary, in their words | `x_linkedin_summary` | 400 |
| Skills | `x_skills` | 250 |
| Career, latest first | `x_experiences`, up to four roles, "title at company: description" | 500 |
| Company (NEVER name it) | `company_name` | |
| City, Headcount, Industry | `city`, `company_headcount`, `company_industry` | |
| What their company does | `x_company_description` | 500 with a LinkedIn summary, 700 without |
| Recent signal | `signal` | 200 |
| Their target | `segment`, only when the campaign has several | |

The `x_` columns are filled when the source gives them (a LinkedIn extraction, a rich
export, a CRM): the more of them, the more precise the observation.

**Never on a card**: the last name (some sources put the company in it), the email
address, the phone, the website, the domain and the LinkedIn URLs. They give the model
nothing to write with, and an address in a prompt is an address that can end up quoted in
a message.

**Half emojis.** A text cut in the middle of an emoji keeps half of it, and a model API
refuses the whole request, so the whole batch is lost. The script removes them, and the
replacement characters a broken file leaves, from every field before writing the card.
Do the same on any text you send to a model by another route.

## 5. Forbidden phrases, in two blocks

Paste the block of the language you write in. For another language, translate the English
block, show it to the user, and paste the translation.

**English:**

```text
- Openings: "I hope you are well", "I hope this finds you well", "Allow me to", "I am
  reaching out because", "I am", "My name is".
- Familiarity: "sounds good", "fancy a", "hop on a call", "cool", "awesome", "super".
- Worn images: juggling, wearing many hats, behind the scenes, in the shadows, lifeblood,
  core business, day to day, cornerstone, unicorn hire, mental load, "like yours".
- Said source: "I saw", "I read", "I noticed", "your profile", "while browsing".
- Flattery: impressive, remarkable, admirable, congratulations, brilliant, exceptional,
  inspiring, "great track record", "of the year", "ranked among".
- Absolutes: "no one else", "nobody", "everyone".
- Set up: "from your website address", "we would propose a target", "for example",
  "we would define".
- Closings: "Best regards", "Kind regards", "Regards", "Cheers", "Thanks in advance",
  "Have a great day", "Talk soon".
```

**French:**

```text
- Ouvertures : « J'espère que vous allez bien », « Je me permets », « Je vous contacte
  car », « Je suis ».
- Familiarité : « ça colle », « on s'appelle », « ça vous dit », « ça vous tente »,
  « sympa », « top », « super ».
- Images usées : jongler, casquettes, charge mentale, dans l'ombre, en coulisses, nerf de
  la guerre, cœur de métier, au quotidien, pierre angulaire, mouton à cinq pattes,
  « comme la vôtre », « comme le vôtre ».
- Source dite : « j'ai vu », « j'ai lu », « j'ai remarqué », « votre profil », « en
  parcourant », « en lisant ».
- Flatterie : impressionnant, remarquable, admirable, bravo, félicitations, brillant,
  exceptionnel, passionnant, inspirant, « beau parcours », « belle réussite »,
  « chapeau », « de l'année », « classé parmi ».
- Absolus : « personne d'autre ne », « personne ne », « tout le monde ».
- Mise en route : « à partir de l'adresse de votre site », « nous proposerions une
  cible », « par exemple », « nous définirions ».
- Formules finales : « Bien à vous », « Cordialement », « Bien cordialement », « Belle
  journée », « Bonne journée », « À bientôt », « Merci d'avance ».
```

`scripts/first-messages.py` looks for the same lists, in both languages.

## 6. What the model returns, the checks, and where it goes

Save each answer as `outreach/copy/out-NN.json`, next to its `cards-NN.json`, then check
it and keep the report under the name the merge reads:

```bash
python3 scripts/first-messages.py check outreach/copy/out-01.json \
  --cards outreach/copy/cards-01.json --header outreach/copy/header.md \
  --channel email --report outreach/copy/check-01.json
```

`outreach/copy/header.md` holds the header of section 3 as sent, in the language of the
messages: the link check compares words, so a header in English and messages in French
would flag every message. The check prints one
line per contact: `KEEP`, `RETRY` with its light faults, `SHORTEN`, or `GRAVE`.

**Grave faults**, the message is not kept as it is: a part empty; a length more than 5%
over the maximum or under 60% of the minimum; no question; a number in the observation
that the card does not give, in figures or in words; on LinkedIn, an email word; in an
email, no subject or a subject over 80 characters; a closing formula; an em dash or an en
dash; the recipient's company named (its full name, or a distinctive word of it written
with a capital); a variable, a brace or a link; a date or a struck price.

**Light faults**, the message is retried: a length outside the bounds; "you" in the
observation; an observation with no link to the offer; a question mark or an exclamation
mark outside the final question, several questions, or a question not at the end; a
question over 90 characters; set up talk, a worn formula, familiarity; a subject on
LinkedIn, a subject over 7 words or 48 characters, or a subject sharing no word with the
observation; a forbidden opening; more than one figure from the sender block; flattery, a
worn image, an absolute, a said source; a source not found on the card.

**The link with the offer**, in practice: the words of the observation (cut to their
first five letters, the words of the card and of the targets set aside) must share at
least two roots with the offer or with the sender block. The check is off when the sender
block has fewer than 15 roots, because it would then flag good observations at random.
It is a net, not proof: an off topic observation can pass on two words of chance, and a
good one can be flagged, which costs one retry.

**The batch**: an observation, an offer, a question or a subject that opens like an
earlier one, more than two observations on the same first word, a sequence of four words
in more than two observations, or of three words in more than two offers. The first
message keeps, the next ones are retried.

**The order of the retries, and when a contact is dropped:**

1. One targeted retry of the messages with a fault, and only those: give the model their
   card, their message, its list of faults, and the messages kept in the batch with `do
   not imitate them`. A retried message replaces the first only if it has fewer grave
   faults, or as many and no more faults in total.
2. Up to two shortenings of the messages still over the maximum: the first aims at the
   top of the range, the second at the bottom, with `The same observation, the same
   offer, the same question, with fewer words; nothing new. Cut the observation first.`
   A shortened message is kept only if it is shorter and has no more grave faults.
3. A message with a grave fault left is not kept, and the contact counts one failed
   attempt. At the third, the contact is dropped from the campaign and never sent
   anything: say how many.

Then merge the batches:

```bash
python3 scripts/first-messages.py merge outreach/leads.csv --kind first \
  --cards 'outreach/copy/cards-*.json' --out 'outreach/copy/out-*.json' \
  --channel email --lang fr
```

It writes, for every message without a grave fault:

| Column | Content |
|---|---|
| `greeting` | `Bonjour Marc,`, or `Bonjour,` when the first name is empty: never "Bonjour ," |
| `subject_line` | the subject, on one line, braces removed, nothing escaped: a subject is plain text |
| `message` | the greeting, then the three paragraphs separated by a blank line, `&`, `<` and `>` escaped, braces removed |
| `li_message` | the same on LinkedIn, plain text, nothing escaped |
| `message_sources`, `message_date` | the extracts of the card it rests on, and the day |
| `writing_attempts`, `writing_status` | the failed attempts, and `ok`, `failed` or `dropped` |

`--greeting 'Hello {first},|Hello,'` sets other greetings. A value over 2,000 characters,
or a subject over 150, is refused: nobody has confirmed the largest value a custom
variable carries, so this repository sets its own cap.

## 7. Examples, before and after

All names and details are invented. Each is the first message as the contact reads it:
the greeting, three paragraphs, and the signature Emelia adds. "Before" is the common
mistake, an observation about the recipient's own clients when the offer is not about
clients; "after" applies the prompt.

**1. A sender that does not sell prospecting, email.** The sender: a recruitment firm
that only hunts industrial automation profiles, by direct and confidential approach, with
references taken before the offer. The contact: Camille, technical director of a company
that integrates packaging lines for the food industry, according to her card.

Before, subject "Integrator chosen at the last minute":

> Hello Camille,
>
> Food manufacturers that modernise a packaging line often choose their integrator at
> the last minute, when the production stop is already planned.
>
> To strengthen a project team, we approach automation engineers already in post, in
> full confidence, and take their references before the offer.
>
> Would a 15 minute conversation suit you?

The observation is precise, but it is about Camille's clients: read alone, it promises to
sell her clients. Nothing in it points to recruitment.

After, subject "Automation engineers no job ad finds":

> Hello Camille,
>
> An automation engineer who knows both packaging lines and on site commissioning is
> rarely found through a job ad: the people with that profile are already in post and do
> not read the offers.
>
> We only recruit in industrial automation: we find these profiles where they work and
> approach them discreetly, with references taken before the offer.
>
> Could we talk about it for 15 minutes?

Read alone, the observation lets the reader guess recruitment; it is precise thanks to the
card (packaging lines, commissioning); the offer answers it.

**2. A sender that sells a way to find clients, email.** The sender: a lead generation
agency that works for engineering firms and writes each prospect a message of its own.
The contact: Julien, manager of a structural engineering firm, "extensions of industrial
buildings" on his card.

Before and after alike, subject "An engineering firm at the permit stage":

> Hello Julien,
>
> Owners who launch the extension of an industrial building often look for their
> structural engineering firm when the permit is filed, and pick the one that made itself
> known before.
>
> We find these owners before they start looking, and write to each of them a message
> drawn from your speciality, sent from your own mailbox.
>
> Would you have 15 minutes to talk about it?

Here the problem the offer solves arises on the recipient's market, so the observation is
about his clients, and that is right: the special case of the prompt.

**3. LinkedIn, a software vendor.** The sender: software that reschedules the
replacements of cleaning staff and warns the agent by text message. The contact: Ines,
operations manager in an office cleaning company. The first message after an invitation
without a note: no subject, no signature.

Before:

> Hello Ines,
>
> Office building managers rarely change cleaning contractor during a contract, except
> after several missed visits.
>
> Our software plans the rounds of your agents.
>
> Would you have 15 minutes to talk about it?

After:

> Hello Ines,
>
> In cleaning, a morning absence is often handled by phone, site by site, and the missed
> visit is found out when the client calls.
>
> Our software reschedules the replacement and warns the agent by text message.
>
> Could we talk about it for 15 minutes?

Before, the observation about Ines's clients does not announce scheduling software; after,
it states the problem the software solves, and the offer answers it word for word
(absence, replacement, agent).

## 8. LinkedIn: the invitation and the InMail

**Send the invitation without a note.** An empty note is usually accepted more often than
a pitched one, which is why the Emelia templates ship the invitation empty, and the first
message above is written for a person who accepted an invitation without one. If the user
wants a note anyway, it goes in `li_note`, 300 characters at most (the Emelia invitation
editor flags anything longer), it gives a reason to connect and stops, and it follows the
rules of section 2: nothing invented, no company named, no flattery, no pitch.

**An InMail** is a first message with a subject: write it with the LINKEDIN block, its
subject under the rules of the EMAIL block, into `li_inmail_subject` and `li_inmail`.
LinkedIn publishes the limits of an InMail (about 200 characters of subject and 1,900 of
body): check them before relying on them.
