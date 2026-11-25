# The follow up prompt

Messages 2, 3 and 4 of a campaign, email or LinkedIn. Each follow up is either **shared**,
written once for the whole target, or **personalised**, written for each contact from
their card, as the user chose step by step in [outreach-write](../SKILL.md) section 1.
Both kinds follow the same follow up rules; a personalised one also follows every rule of
the first message, in [first-message-prompt.md](first-message-prompt.md).

## 1. The rules every follow up keeps

- **It reads on its own.** The reader may never have opened the first message. Never "as
  I wrote", "following my message", "my previous email", in any language.
- **Arguments first, not features.** Before writing, the model fills a `plan` that is
  never sent: the gain, the cost of doing nothing, an honest comparison, the main
  objection and its answer, the trigger of the need. Each follow up carries one argument
  from it.
- **Three different asks, in this order.** Follow up 2 offers to send something concrete,
  a thing to receive, not a call. Follow up 3 is the only one that offers the
  conversation, and the only one that may say "15 minutes". Follow up 4 asks for a
  permission or a last element (should I close the file, who else to ask), soberly.
- **Exactly one question mark, on the last sentence.** No exclamation mark.
- **Figures.** At most one figure from the sender block, and no other figure but "15
  minutes".
- **Lengths**, on the body without the greeting:

| Follow up | Email | LinkedIn |
|---|---|---|
| 2, something to receive | 90 to 220 characters | 80 to 200 |
| 3, the conversation | 180 to 380 | 120 to 280 |
| 4, the way out | 80 to 200 | 80 to 200 |

- **Subjects, by email.** Follow ups 2 and 4 stay in the thread: their subject is empty,
  and Emelia reuses the subject it sent last with `Re: ` in front. Follow up 3 starts a
  new thread and needs its own subject, 3 to 6 words, under the rules of the first
  message. On LinkedIn there is never a subject.
- **The greeting** is added for you, never written by the model.
- **Forbidden**, in two blocks: section 4.

## 2. Shared follow ups

Written once per target, and the step carries the text itself with `{{greeting}}` as its
first paragraph. One run per target. By email each step may carry up to three versions,
an A/B test; on LinkedIn never more than one, because every version of a `MESSAGE` step is
sent, one after the other.

```text
You write the follow ups of a B2B prospecting campaign: messages 2, 3 and 4, the same for
every recipient of the target. Write in {language}. {channel_line}

Each follow up must read on its own, without the others: never "as I wrote", "following
my message", "my previous email", or their {language} forms.

ARGUMENTS FIRST, NOT FEATURES. First fill "plan", which is never sent: the gain, the cost
of doing nothing, an honest comparison, the main objection and its answer, the trigger of
the need, each from the sender block only. Then each follow up carries one argument of the
plan, not a feature of the offer.

Three different asks, in this order: something to receive (follow up 2, never a call),
the conversation (follow up 3, the only one that may say "15 minutes"), a permission or a
last element (follow up 4, soberly). Exactly one question mark per follow up, on its last
sentence. No exclamation mark. At most one figure from the sender block, and no other
figure but "15 minutes". At least one follow up names the target, its trade, never a
company.

Lengths, on the body: {lengths}. {subject_line}

Do not write the greeting, the signature, a link or any variable. Paragraphs of one or two
sentences, separated by a blank line. Never an em dash or an en dash.

NOTHING INVENTED: the same rules as the first message. Everything about the sender comes
from the sender block; nothing about the recipients, who are not named here. No case
study, testimonial, client name, figure, price, date or result that the block does not
give in so many words. No promise of a result. No presumption about the reader ("you
feel", "as you know").

FORBIDDEN PHRASES
{forbidden}

LANGUAGE
{language_lines}

OUTPUT
Return only JSON: {"plan": {"gain": "...", "cost_of_inaction": "...", "comparison": "...",
"objection": "...", "trigger": "..."}, "followups": [{"step": 2, "version": "A",
"subject": "", "body": "..."}]}.
```

`{channel_line}` is `By email.` or `On LinkedIn, after the person accepted an invitation
and received a first message. Never the words email, mail, mailbox or inbox.`.
`{lengths}` and `{subject_line}` come from section 1: by email, `Follow ups 2 and 4 stay
in the thread, subject empty; follow up 3 starts a new thread, with a subject of 3 to 6
words, 45 characters at most.`; on LinkedIn, `No subject.`.

The user message gives the header of the first message prompt (the sender block, the
target and its why), the channel, the arguments already drawn from the offer if
`outreach/offer.md` has them, and five real cards of the target, under `A real sample of
the target, for the tone only, never to take a fact from:`. Then: `Write follow ups 2, 3
and 4 now.`

The step body by email, for every version:

```
<p>{{greeting}}</p><p></p><p>paragraph</p><p></p><p>paragraph</p><p></p><p>{{signature}}</p><p></p><p><a href="{{unsubscribe_link}}">Unsubscribe</a></p>
```

On LinkedIn the body is the plain text with `{{greeting}}` on the first line, and no
signature and no link.

## 3. Personalised follow ups

Written for each contact, in the same batches of about eight as the first message, after
the first messages of the batch are kept. Each follow up is one more personalised message:
every rule of the first message applies to it (nothing invented about the sender or the
contact, never the company's name, no flattery, no said source, the link with the offer,
the sources, the batch variety), and every rule of section 1 too.

**A different angle each time.** The first message already used one angle on the problem
the offer solves. Each follow up takes another: scarcity, timing, cost, risk, discretion,
the trade's habit, the moment of the year. It never repeats the observation of the first
message, not even reworded, and never repeats another follow up.

```text
You write follow ups {steps} of a B2B prospecting campaign, fully personalised, for every
recipient of the batch. The first message each recipient received is given under their
card. Write in {language}. {channel_line}

Each follow up is a short message of its own about THE PROBLEM THE SENDER'S OFFER SOLVES,
as it arises for THIS recipient, from what their card says, and it follows every rule of
the first message: nothing invented, never their company's name, no flattery, never say
where you read about them, no "you" in the sentence that states the problem.

A DIFFERENT ANGLE EACH TIME: the first message took one angle on the problem; each follow
up takes another (scarcity, timing, cost, risk, discretion...), never the observation of
the first message again, not even reworded, and never the angle of another follow up.

Each follow up must read on its own: never "as I wrote", "following my message", "my
previous email", or their {language} forms.

Asks, in this order: something to receive (follow up 2, never a call), the conversation
(follow up 3, the only one that may say "15 minutes"), a permission or a last element
(follow up 4). Exactly one question mark per follow up, on its last sentence. No
exclamation mark. At most one figure from the sender block, no other figure but "15
minutes", and no number about the recipient that their card does not give.

Lengths, on the body: {lengths}. {subject_line}

Do not write the greeting, the signature, a link or any variable. Paragraphs of one or two
sentences, separated by a blank line. Never an em dash or an en dash.

VARIETY IN THE BATCH: never two follow ups of the same step on the same first two words,
and the same sequence of four words in two follow ups of a step at most.

FORBIDDEN PHRASES
{forbidden}

LANGUAGE
{language_lines}

OUTPUT
Return only JSON: {"messages": [{"index": <the index of the card>, "followups":
[{"step": 2, "angle": "timing", "subject": "", "body": "..."}], "sources": ["..."]}]}, one
object per recipient, with one follow up per step asked.
```

`{steps}` lists the steps the user chose to personalise, `2, 3 and 4` or `3` alone. The
user message is the header of the first message prompt, then each card under its index
with, under it, `The first message they received:` and the kept observation, offer and
question. Then: `Write the follow ups now, for EACH recipient above (index 0 to N-1).`

Each personalised follow up has its own column, with the names every skill of this
repository reads, and the step carries that variable alone in its paragraph:

| Follow up | Email column | LinkedIn column |
|---|---|---|
| 2 | `message_2` | `li_message_2` |
| 3 | `message_3`, and `subject_line_3` for its new thread | `li_message_3` |
| 4 | `message_4` | `li_message_4` |

A personalised follow up and a shared one can sit in the same campaign: the step of a
personalised follow up is `<p>{{message_3}}</p>...`, the step of a shared one carries its
text. Every variable a step uses is then checked on every contact before the launch,
and an empty one blocks, as `outreach-campaign` section 7 says.

## 4. Forbidden phrases of the follow ups

On top of the blocks of [first-message-prompt.md](first-message-prompt.md), section 5.

**English:**

```text
- Openings: "One point that matters", "Another angle", "Quick reminder", "Just a
  reminder", "I am following up", "To complete", "Following my", "As agreed", "For your
  information", "I wanted", "I wished", and any announcement followed by a colon.
- References to an earlier message: "as I wrote", "following my message", "my previous
  email".
- Way out cliches: "my door remains open", "I won't insist", "closing this thread",
  "clutter your inbox", "last attempt", "don't hesitate", "without a reply from you",
  "circle back later", "not to disturb you", "leave you alone", "at your disposal",
  "looking forward to talking".
- Plastered testimonial: a name and a title followed by "says" or "reports", a figure in
  quotation marks.
- Presumption: "you feel", "you know that", "as you know".
- Promise: "guaranteed", "you will get", "you will gain", "never again".
- Five words in a row copied from the sender block: a feature pasted in is not an
  argument.
```

**French:**

```text
- Ouvertures : « Un point qui compte », « Autre angle », « Petit rappel », « Je reviens
  vers vous », « Pour compléter », « Je me permets », « J'espère que », « Je vous
  contacte », « Suite à », « Comme convenu », « Pour information », « Je voulais »,
  « Je souhaitais », et toute annonce suivie de deux points.
- Renvois : « comme je vous l'écrivais », « suite à mon message », « mon précédent
  e-mail ».
- Clichés de sortie : « ma porte reste ouverte », « je n'insiste pas », « je ne vais pas
  insister », « je clos ce fil », « encombrer votre boîte », « dernière tentative »,
  « n'hésitez pas », « sans réponse de votre part », « je me permets une dernière »,
  « revenir vers vous plus tard », « ne pas vous déranger », « je vous laisse
  tranquille », « je reste à votre disposition », « au plaisir d'échanger ».
- Témoignage plaqué : un nom et un titre suivis de « cite », « rapporte » ou
  « témoigne », un chiffre entre guillemets.
- Présomption : « vous vous sentez », « vous savez que », « comme vous le savez ».
- Promesse : « garanti », « vous obtiendrez », « vous gagnerez », « plus jamais ».
- Tournures usées : « Si cela vous est utile », « le sujet peut attendre », « Souhaitez-vous
  que je vous l'envoie », « ce que cela donnerait », « à comparer avec ».
- Cinq mots d'affilée recopiés du bloc de l'émetteur.
```

## 5. The checks

```bash
# shared
python3 scripts/first-messages.py followups outreach/copy/followups.json \
  --header outreach/copy/header.md --channel email
# personalised, per batch
python3 scripts/first-messages.py followups outreach/copy/fu-01.json \
  --cards outreach/copy/cards-01.json --first outreach/copy/out-01.json \
  --header outreach/copy/header.md --channel email --report outreach/copy/fucheck-01.json
```

Grave: a length more than 5% over the maximum or under 60% of the minimum; not exactly one
question mark on the last sentence; an em dash or an en dash; a variable, a brace or a
link; a figure the sender block does not give; by email, follow up 3 without a subject;
on LinkedIn, an email word. On a personalised follow up, also the grave faults of the first
message that apply: the company named, a number about the contact the card does not
give, a date or a struck price, a closing formula.

Light: a length outside the bounds, an exclamation mark, more than one figure from the
sender block, a call asked outside follow up 3, a subject on follow up 2 or 4 by email, a
forbidden opening, a cliche, a reference to an earlier message, a presumption, a promise,
a plastered testimonial, an announcement followed by a colon, two follow ups that open
alike, five words copied from the sender block. On a personalised follow up, also: no
link with the offer, flattery and the other light faults of the first message, and a
follow up that repeats four words in a row of the first message's observation.

The order of the retries and the three attempts are those of the first message,
[first-message-prompt.md](first-message-prompt.md) section 6. A personalised follow up
merges into its column with `merge --kind followups`, which adds the greeting, escapes
`&`, `<` and `>` by email, and writes nothing for a contact whose follow up still has a
grave fault.
