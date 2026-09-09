# The LinkedIn message prompt

Read this when the campaign has LinkedIn steps and you are writing a message for each
contact. It is the sibling of [per-contact-prompt.md](per-contact-prompt.md), which
writes email. They are not interchangeable: an email needs a subject, a signature and an
opt out link, and a LinkedIn message has none of the three.
[outreach-write](../SKILL.md) section 1, under "Mode A on LinkedIn", covers when you run
this rather than the email prompt.

Four things about the channel decide everything in the prompt below.

1. **The reader can see who you are in one click.** Your name, your photo, your title and
   your company are already on the screen. Introducing yourself spends the two lines that
   decide whether they keep reading, on information they already have.
2. **You do not sign.** No name, no company, no job title, and no closing formula: not
   "Best regards", not "Bien à vous", not "Cordialement". A signed LinkedIn message reads
   like an email that got lost.
3. **Every message ends on a question.** A LinkedIn thread is a conversation, and a
   conversation that ends on a statement ends. This is a house rule, applied to every
   piece except the invitation note.
4. **The first message lands after an acceptance.** This person clicked accept. They are
   not a stranger any more, and writing to them as if they were is the fastest way to be
   ignored by someone who had already said yes once.

## 1. What you fill in

Same three placeholders as the email prompt, filled the same way.

| Placeholder | Where it sits | What goes in |
|---|---|---|
| `{variable}` | line 1 | The language, named in English: `French`, `German`, `Brazilian Portuguese` |
| `{{PROSPECT}}` | inside `<prospect_info>` | One contact, built from one row of `outreach/leads.csv`. Section 3 |
| `{{COMPANY_INFO}}` | inside `<company_info>` | Your offer, built once from `outreach/icp.json`. Section 3 |

`{{PROSPECT}}` and `{{COMPANY_INFO}}` look like Emelia variables and are not. They are
placeholders in this prompt, replaced before the model reads the text. The only Emelia
variables in a LinkedIn step are the ones you put in the step body yourself, and in a per
contact campaign that is one: the column holding the message.

## 2. The prompt, verbatim

```text
You are tasked with writing a highly personalized and creative LinkedIn outreach sequence in {variable}.
You will be given information about a prospect, which you should use to craft messages that read as if one person wrote them to another person.
You will also be given information about what the company offers, proposes, or sells.

<prospect_info>
{{PROSPECT}}
</prospect_info>

<company_info>
{{COMPANY_INFO}}
</company_info>

1. What you are writing:
- An invitation note, sent with the connection request. 300 characters maximum, spaces included
- A first message, sent after the invitation has been accepted
- A follow-up message
- A final message that closes the loop

2. What LinkedIn is, and what changes because of it:
- The recipient can open your profile in one click. Do NOT introduce yourself, do NOT explain your role, do NOT name your company in the opening line. One short clause about why you are writing is enough
- By the time the first message arrives, this person has accepted your invitation. Write to someone who has already let you in, not to a stranger. Do not thank them for accepting
- There is no subject line. The first sentence is the subject line
- The message is read in a narrow column, usually on a phone. Two or three short paragraphs, never a block of text
- Plain text only. No HTML, no bold, no bullet points, no emoji, and no link unless the message is worthless without one
- Do NOT sign. No name, no company, no job title, no signature block, and never an invented one
- Do NOT end with a closing formula. No "Best regards", no "Looking forward to hearing from you", no "Bien à vous", no "Cordialement"
- End every message with a question. The last sentence of every message ends with a question mark
- There is no unsubscribe link on LinkedIn and there must be no mention of one. This is not an email

3. Guidelines for the sequence:
- Make each message short, specific, and value-focused
- Use the prospect's information to create relevant, personalized content
- Ensure a logical progression from one message to the next
- Don't repeat yourself between messages
- If company information is limited or unclear, focus on industry-level insights and pain points rather than inventing specific details
- When unsure about specific details, use broader value propositions that would apply to most companies in the relevant industry
- When company information is minimal, emphasize general business challenges that your solution addresses

4. Style and Tone Requirements:
- NEVER INVENT DETAILS YOU DON'T KNOW. If information is insufficient, focus on what you do know or use industry-standard pain points
- Si tu écris en français, ne sois pas trop flatteur, n'utilise pas des "captivé", "subjugué", "fasciné" etc. Fais juste en sorte que la personne voie qu'on connaît son profil, sans la flatter trop
- Never open with "I saw your profile", "I came across your profile", "I noticed that you", or any variation. That is the opening line of every automated message on the platform
- Never compliment the prospect's profile, career or company as an opening move
- Write the way a person writes to a colleague, not the way a company writes to a market
- Look for a unique angle or observation about their business that others would miss
- Use a pattern interrupt that makes your message stand out from typical LinkedIn outreach
- Feel free to use subtle humor or clever wordplay if it fits the context
- Don't propose a "virtual coffee" - instead, suggest a video call or phone call
- Keep the ask small and easy to answer. A question someone can answer in one line beats a meeting request

5. Structure the sequence in 4 pieces:
- Invitation note: one honest reason to connect. No pitch, no product name, no ask beyond the connection itself. 300 characters maximum. This is the only piece that does not have to end on a question
- First message: the observation and the ask, written to someone who has just accepted
- Follow-up: a new angle, a new piece of proof, or a different question. Never "just following up" and never a repeat of the first message
- Final message: say you are stopping, make a no cheap to send, and close on one question

6. Refinement Guidelines:
- Ensure your creative elements serve a purpose and aren't just clever for cleverness' sake
- Keep the core message about your solution clear and understandable
- Maintain a balance between creativity and professionalism
- Ensure personalized elements flow naturally within the creative framework
- Keep messages short despite creative elements
- If unsure about specific details, use conditional language rather than making definitive statements
- Don't invent facts or make false claims
- Don't sign, don't add a name, don't invent a name or a brand

Important: Each message should feel fresh and unique. Avoid standard LinkedIn outreach phrases and templates. Find creative ways to show you have done your research without being obvious about it. When company information is vague, keep the personalization broader and focus on the value proposition.

Be sure not to include any invalid control characters in JSON strings

DON'T INCLUDE ANY VARIABLES, SIGNATURES OR CLOSING FORMULAS - MESSAGES MUST BE READY TO SEND
```

**When the flow has an InMail step**, append this block, and only then. An InMail costs a
credit and goes to someone who never accepted, so it is the coldest piece of the five and
the only one with a subject line.

```text
7. Also write one InMail, sent to a prospect who never accepted the invitation:
- It is the only piece with a subject line. Subject 200 characters maximum, body 1900 characters maximum
- It is colder than the rest: this person has not accepted anything. Give the reason for writing in the first sentence
- Same rules as above. No signature, no closing formula, ends on a question
```

## 3. The prospect and company blocks

Built exactly as in [per-contact-prompt.md](per-contact-prompt.md), sections 3 and 4:
one labelled line per fact, a missing line rather than `unknown`, the company block under
about 150 words, and no claim the user cannot source. Two differences.

- **`linkedin_url` is not optional here.** A row with no profile URL cannot be sent a
  LinkedIn message at all. Drop it from this run, and count the rows you dropped.
- **`email` stays out of the block, as always**, and on this channel it also has no use:
  nothing in a LinkedIn message should reference an address you found.

Everything the profile itself says (headline, current role, tenure, the post they wrote
last week) is the best material this prompt can get, and it is exactly what
[outreach-personalize](../../outreach-personalize/SKILL.md) puts in `icebreaker` with its
source and date. Pass it. A LinkedIn message that shows you read the profile is fair
game, as long as it does not open by saying so.

## 4. The rules you append to block 4

Same four questions as the email prompt, same answers, appended to the end of
**"4. Style and Tone Requirements"** in the same dash list. Ask them once for the campaign
and reuse the answers on both channels.
[outreach-write](../SKILL.md) section 1 has the wording of the questions, and
[per-contact-prompt.md](per-contact-prompt.md) sections 5 and 6 have the order of the
added lines and the rules per language. Both apply here unchanged, with three additions
that come from the channel.

1. **The signer's gender still matters, even though you do not sign.** Not signing removes
   the name, not the grammar: "je serais ravi d'en parler" is still first person, and it
   is still wrong when a woman writes it. Ask question 3 for the languages that agree, and
   do not skip it on the grounds that the message is unsigned.
2. **The register is the one from question 2, not a softer one.** LinkedIn feels informal
   and that tempts a model into "tu" on a segment the user answered "vous" for. Repeat
   the register line in this block even when it is already in the email run.
3. **The no gendered salutation rule matters more here.** The greeting is at most one
   short line, first name only, and it is optional: "Bonjour Marc," or nothing at all.
   Never "Cher Monsieur", never "Sehr geehrter Herr Leroy", never "Panie Marku".

Worked example, French, "vous", a woman signing:

```text
- Write in French and use "vous" throughout, including in the follow-ups. Never "tu"
- The person writing is a woman: agree everything she says about herself in the feminine,
  "je serais ravie" and not "ravi", "je suis convaincue" and not "convaincu"
- Greeting: "Bonjour" plus the first name, on one line, or no greeting at all. Never a
  gendered salutation, the list does not carry a reliable gender
- Never write "J'espère que vous allez bien" or "Je me permets de vous contacter": both
  are the tics that mark a message as a template
- No closing formula: no "Bien à vous", no "Cordialement", no "Au plaisir d'échanger"
```

## 5. Lengths, and what the channel enforces

| Piece | Characters | Cap | Where the cap comes from |
|---|---|---|---|
| Invitation note | 0, or 120 to 250 | 300 | The Emelia invitation editor flags anything longer |
| First message | 250 to 450 | 600 | House rule, it is what reads in one phone screen |
| Follow-up | 120 to 300 | 400 | House rule |
| Final message | 80 to 200 | 300 | House rule |
| InMail subject | 30 to 60 | 200 | LinkedIn's published limit, check it before you rely on it |
| InMail body | 300 to 600 | 1900 | LinkedIn's published limit, check it before you rely on it |

Only the first row is enforced by anything: Emelia's invitation editor shows an error
above 300 characters. The others are this repository's numbers, and they exist because a
LinkedIn message is read in a column about half the width of an email.

**The best invitation note is often no note at all.** An empty note is usually accepted
more often than a pitched one, which is why the Emelia templates ship the invitation with
an empty message. Generate the note anyway, show the user both options, and let them
choose. If they keep it, the note may not pitch: it gives a reason to connect and stops.

## 6. What the model returns, and where it goes

The prompt does not name a shape, so state one when you run it, as a separate line after
the prompt:

```text
Return only a JSON array of objects, in order, each with the keys "piece" and "text",
where "piece" is one of "note", "message_1", "message_2", "message_3". Add a fifth object
with "piece": "inmail" and an extra "subject" key only if an InMail was asked for. No
prose around the array.
```

```json
[
  {"piece": "note", "text": "Bonjour Marc, votre changelog dit que l'API v3 est publique depuis juin. Je travaille sur la surveillance des reponses d'API et je serais curieuse de savoir comment vous la suivez de votre cote."},
  {"piece": "message_1", "text": "..."},
  {"piece": "message_2", "text": "..."},
  {"piece": "message_3", "text": "..."}
]
```

Columns written into `outreach/leads.csv`, one row per contact. The `li_` prefix is this
repository's convention, and it exists so a multichannel campaign can carry both an email
message and a LinkedIn message on the same row without one overwriting the other.

| Piece | Column | Emelia step and field |
|---|---|---|
| Invitation note | `li_note` | `CONNECTION`, `versions[0].message` |
| First message | `li_message` | `MESSAGE`, `versions[0].message` |
| Follow-up | `li_message_2` | `MESSAGE`, `versions[0].message` |
| Final message | `li_message_3` | `MESSAGE`, `versions[0].message` |
| InMail | `li_inmail_subject`, `li_inmail` | `INMAIL`, `versions[0].subject` and `versions[0].message` |

Plus `li_message_source` and `li_message_date` next to them, on the same terms as every
other generated column: what the model was given, and when it was run.

Before any value goes into the CSV, strip `{`, `}` and `|` out of it, for the same reason
as the email columns: Emelia runs spintax after variable substitution, so a stray brace
eats part of the sentence at send time.
[outreach-personalize](../../outreach-personalize/SKILL.md) section 4 has the detail.

## 7. Checking the sample

Run the same sample of 20 as the email path, and read it in the target language. Four of
the rules are mechanical, so check them with a script rather than by eye:

```bash
python3 - <<'PY'
import csv, re
BAD = re.compile(r"(bien [àa] vous|cordialement|best regards|kind regards|"
                 r"looking forward|sincerely|au plaisir d'[ée]changer|mit freundlichen)", re.I)
SEEN = re.compile(r"(i saw your profile|i came across your profile|j'ai vu votre profil|"
                  r"je suis tomb[ée] sur votre profil)", re.I)
cols = ["li_note", "li_message", "li_message_2", "li_message_3"]
for i, row in enumerate(csv.DictReader(open("outreach/leads.csv"))):
    if i >= 20: break
    for c in cols:
        v = (row.get(c) or "").strip()
        if not v: continue
        if c != "li_note" and not v.endswith("?"):
            print(f"row {i} {c}: does not end on a question")
        if c == "li_note" and len(v) > 300:
            print(f"row {i} {c}: {len(v)} characters, over the 300 cap")
        if BAD.search(v): print(f"row {i} {c}: closing formula")
        if SEEN.search(v): print(f"row {i} {c}: opens on the profile")
        if "{{" in v or "<" in v: print(f"row {i} {c}: variable or markup in the value")
print("done")
PY
```

What the script cannot see, and you have to read for: whether the message introduces the
sender anyway (a whole paragraph explaining who they are), whether the follow-up is the
first message with different words, and whether the question at the end is a real question
or a meeting request with a question mark stapled on it. Those three are the ones that
come back wrong most often, and all three are fixed at the prompt, never row by row.
