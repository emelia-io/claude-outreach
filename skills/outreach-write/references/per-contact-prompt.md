# The per contact writing prompt

Read this when `outreach/sequence.md` says `Mode: A`, one message written for each
contact and pushed into a custom variable. It holds the prompt Emelia uses to write
those messages, what fills its placeholders, and the rules you add to it before you run
it. [outreach-write](../SKILL.md) section 1 covers when to use Mode A at all, what the
generation costs, and the four questions you ask first.

The prompt below is reproduced **unchanged**. Its two French sentences are deliberate,
its English is the English it was written in, and its rules are the house rules. Do not
translate it, shorten it, reorder it or improve it. You fill three placeholders, you
append rules to its block 2, and nothing else about it moves.

## 1. What you fill in

| Placeholder | Where it sits | What goes in |
|---|---|---|
| `{variable}` | line 1 | The language, named in English: `French`, `German`, `Brazilian Portuguese` |
| `{{PROSPECT}}` | inside `<prospect_info>` | One contact, built from one row of `outreach/leads.csv`. Section 3 |
| `{{COMPANY_INFO}}` | inside `<company_info>` | Your offer, built once from `outreach/icp.json`. Section 4 |

`{{PROSPECT}}` and `{{COMPANY_INFO}}` look like Emelia variables and are not. They are
placeholders in this prompt, replaced before the model reads the text, and none of this
is ever sent to Emelia. The only Emelia variables in a Mode A campaign are the carrier
ones in the step body: `{{message}}`, `{{signature}}`, `{{unsubscribe_link}}`.

One oddity to leave alone: the line "Here is the information about the company" sits
above the prospect block, not above the company block. The model reads the
`<prospect_info>` and `<company_info>` tags, which are correct, so the sentence costs
nothing. Do not tidy it.

## 2. The prompt, verbatim

```text
You are tasked with creating a highly personalized and creative 4-step cold email sequence in {variable}.
You will be given information about a prospect, which you should use to craft an innovative and memorable email sequence.
You will also be given information about what the company offers, proposes, or sells.
Here is the information about the company:

<prospect_info>
{{PROSPECT}}
</prospect_info>


<company_info>
{{COMPANY_INFO}}
</company_info>

1. Guidelines for creating the email sequence:
- Make each email concise, engaging, and value-focused
- Use the prospect's information to create relevant, personalized content
- Include a clear call-to-action in each email
- Ensure a logical progression from one email to the next
- Don't repeat yourself between emails
- It's not necessarily required to personalize with many elements at the beginning of the first email
- If company information is limited or unclear, focus on industry-level insights and pain points rather than inventing specific details
- When unsure about specific details, use broader value propositions that would apply to most companies in the relevant industry
- When company information is minimal, emphasize general business challenges that your solution addresses

2. Style and Tone Requirements:

- NEVER INVENT DETAILS YOU DON'T KNOW. If information is insufficient, focus on what you do know or use industry-standard pain points
- Si tu écris en français, ne sois pas trop flatteur, n'utilise pas des "captivé", "subjugué", "fasciné" etc. Fais juste en sorte que la personne voie qu'on connaît son profil, sans la flatter trop
- Think outside the box - avoid generic "I saw your profile" approaches
- Use creative analogies, metaphors, or stories that relate to the prospect's industry
- Create unexpected but relevant opening lines that make them stop and think
- Be bold in your creativity while maintaining professionalism
- Write as if you're the most interesting person in their inbox
- Look for unique angles or observations about their business that others might miss
- Use pattern interrupts that make your email stand out from typical cold outreach
- When appropriate, incorporate relevant trends, events, or industry-specific references
- Feel free to use subtle humor or clever wordplay if it fits the context
- Don't propose a "virtual coffee" - instead, suggest a video call or phone call

3. Structure your email campaign in 4 distinctive steps:
- Initial Outreach: Break the pattern of typical cold emails with an unexpected but relevant opener that makes them think "This is different!" Connect it naturally to your value proposition. If company details are limited, focus on industry trends or general business challenges.
- Follow-up: Build intrigue through storytelling or unique perspectives on their business challenges. Use creative analogies that illuminate their pain points in a new way. If specific challenges are unclear, address common industry pain points.
- Value Reinforcement: Present your solution through an unconventional lens that relates to their specific context. Make the benefits tangible through innovative examples or scenarios. If context is limited, focus on universal benefits.
- Final Attempt: Create urgency through creative scenarios or analogies relevant to their industry, while maintaining authenticity. If industry specifics are unclear, use general business timing factors (quarter end, annual planning, etc.).

4. Refinement Guidelines:
- Ensure your creative elements serve a purpose and aren't just clever for cleverness' sake
- Keep the core message about your solution clear and understandable
- Maintain a balance between creativity and professionalism
- Ensure personalized elements flow naturally within the creative framework
- Keep emails concise despite creative elements (3-4 short paragraphs max)
- Make sure calls-to-action are clear and aligned with the creative approach
- When information is limited, focus on quality over quantity of personalization
- If unsure about specific details, use conditional language rather than making definitive statements
- Don't invent facts or make false claims
- Don't sign the email, don't add name. Don't invent name or brand


Important: Each email should feel fresh and unique. Avoid standard cold email phrases and templates. Find creative ways to show you've done your research and understand their business without being obvious about it. When company information is vague, acknowledge this indirectly by keeping personalization broader and focusing on value proposition.
For each email in the sequence, provide:

The email body
The subject line

Be sure not to include any invalid control characters in JSON strings

DON'T INCLUDE ANY VARIABLES OR SIGNATURES - EMAILS MUST BE READY TO USE

Remember to keep the emails authentic, genuinely creative, and tailored to the lead's information while maintaining readability and professionalism. The goal is to stand out through intelligent creativity, not gimmicks.
```

## 3. Building the prospect block

One block per contact, from the row you are writing for. Label each line, one fact per
line, and **leave a line out when the cell is empty**. An absent line works with the
prompt's "NEVER INVENT DETAILS YOU DON'T KNOW". A line reading `Industry: unknown` does
the opposite: it hands the model a fact, and it will write around it.

| Line | Column in `outreach/leads.csv` |
|---|---|
| First name, Last name | `first_name`, `last_name` |
| Job title | `job_title`, and `seniority` when it adds something |
| Company | `company_name`, or `companyNameClean` when the personalization step wrote one |
| Website | `company_website`, else `company_domain` |
| Industry, Headcount | `company_industry`, `company_headcount` |
| City, Country | `city`, `country_code` |
| LinkedIn | `linkedin_url` |
| Segment | `segment`, so the model knows which angle it is writing to |
| Timely signal | `signal` |
| What was read about them | `icebreaker`, with `icebreaker_source` and `icebreaker_date` |

Leave out `email`, `phone`, `lead_id`, `source_url`, `collected_at`, `email_status`,
`phone_status`, `company_naf` and `company_siren`. None of them give the model anything
to write with, and an email address inside the prompt is an email address that can end
up quoted in the body.

The last line is the one that carries the email. It is the sentence
[outreach-personalize](../../outreach-personalize/SKILL.md) generated from a source
somebody actually fetched, and passing its URL and date along keeps the prompt honest:
the model can lean on it because it is checkable.

```text
First name: Marc
Last name: Leroy
Job title: CTO
Company: Kestrel Pay
Website: https://kestrelpay.fr
Industry: Software
Headcount: 45
City: Lyon
Country: FR
LinkedIn: https://www.linkedin.com/in/marcleroy
Segment: fr-saas-cto
Timely signal: took the CTO role in March 2026
What was read about them: their changelog says the v3 API went public in June.
Source: https://kestrelpay.fr/changelog, read 2026-08-29
```

A row with nothing beyond a name, a title and a company is still writable: the prompt
says so, and drops to industry level. A row with no company at all is not. Remove it
rather than generating a message with a hole in it, and count the rows you removed.

## 4. Building the company block

Built once per campaign, reused on every row, from `outreach/icp.json` plus the two
things [outreach-write](../SKILL.md) asks the user for: one number they can defend and
one customer they may name.

| Line | Where it comes from |
|---|---|
| What we sell | `offer.what` |
| The problem it removes | `offer.problem` |
| How it works, in one sentence | `offer.proof`, or the mechanism proof the user gave |
| Proof we may use | the named customer, with the date permission was given |
| Price point | `offer.price_point` |
| Who it is not for | `exclusions`, or the negative proof the user gave |
| What changes for this segment | `segments[].why_different` and `message_hooks[]` |

Keep it under about 150 words. The prompt is built to fall back to industry level
insight when the company block is thin, and that fallback works. What breaks it is the
opposite: paste a homepage, a pitch deck or a feature list in here and the model starts
quoting your marketing back at the prospect.

```text
What we sell: API uptime and latency monitoring with alerting.
The problem it removes: teams hear about a broken API response from a customer before
their own monitor notices.
How it works, in one sentence: we assert on the response body, not the status code.
Proof we may use: Kestrel Pay caught a schema regression 40 minutes before their first
ticket. Named with their permission on 2026-09-02.
Price point: 90 EUR per month per project.
Who it is not for: teams under 10 engineers.
What changes for this segment: they open on their public status page, or the absence
of one.
```

Every claim in that block is a claim you will send to a stranger. If the user cannot
say where a number comes from, it does not go in the block.

## 5. The rules you append to block 2

The four answers from [outreach-write](../SKILL.md) section 1 become lines at the end of
**"2. Style and Tone Requirements"**, in the same dash list as the rest, right after the
"virtual coffee" line. Nothing is inserted anywhere else in the prompt.

Write them in English, like the rest of the block, and quote the target language forms
literally so there is nothing to interpret.

Order of the added lines:

1. The form of address, from question 2. Skip in English.
2. The signer's gender, from question 3. Skip when the language does not agree.
3. The language rules from section 6.
4. Any house rule the user gave in answer to question 4.

Worked example, French, "vous", a woman signing:

```text
- Write in French and use "vous" throughout, including in the follow-ups. Never "tu"
- The person signing is a woman: agree everything the sender says about herself in the
  feminine, "je serais ravie" and not "ravi", "je suis convaincue" and not "convaincu"
- Do not use a gendered salutation for the recipient ("Cher", "Chère"). "Bonjour" plus
  the first name is enough, and the list does not carry a reliable gender
- Never write "J'espère que vous allez bien" or "Je me permets de vous contacter": both
  are the translated tics that mark an email as a template
```

If the user answered "I do not know" to the gender question, do not pick one and do not
guess from the signature. Write the sequence in a form that avoids the agreement, say
which sentences you had to bend to do it, and ask again before the launch. In French
that is doable ("ce serait un plaisir" instead of "je serais ravi"); in Russian, where
the past tense agrees on every sentence about the sender, it is barely doable, and the
honest move is to wait.

## 6. Language rules

One or two lines per language, added as described in section 5. These are rules that
stop the two failures a translated cold email dies of: a grammatical mistake the reader
notices in the first line, and a phrase that reads as English wearing a costume.

| Language | Default form of address | Lines to add |
|---|---|---|
| English | No distinction, and do not ask about one | Nothing to add. Keep contractions, they are what makes it sound written by a person |
| French | "vous" | Agree everything about the sender with the signer's gender ("je serais ravi" or "ravie"). No gendered salutation for the recipient: "Bonjour <first name>". Ban "J'espère que vous allez bien" and "Je me permets de vous contacter" |
| German | "Sie" | Capitalise every noun, and the polite forms (Sie, Ihnen, Ihr). "Herr" or "Frau" needs the recipient's gender, so open with "Guten Tag <full name>" instead. "du" only when the company already says "du" on its own website |
| Spanish | "usted" in Mexico, Colombia, Peru and Chile; "tú" in Spain; "vos" in Argentina and Uruguay | Open questions and exclamations with the inverted mark, "¿" and "¡". Agree the sender's adjectives with the signer's gender ("encantado" or "encantada"). Pick one country's form for the run and never mix "tú" and "usted" inside a sequence |
| Portuguese | "você" in Brazil, third person in Portugal | Brazil: "você", warm, contractions are fine. Portugal: avoid "você", which reads blunt from a stranger, and use the third person with the person's name. Vocabulary splits too (Brazil "time" and "celular", Portugal "equipa" and "telemóvel"), so choose the variant and stay in it. Sender adjectives agree with the signer's gender |
| Italian | "Lei" | Capitalise "Lei" and its forms. Agree the sender's adjectives with the signer's gender ("sarei lieto" or "lieta"). "tu" only for a startup that already uses it publicly |
| Dutch | "je" in the Netherlands, "u" in Flanders | Dutch business email is informal and "je" is normal even from a stranger in the Netherlands. Flanders is more formal, so "u". Finance, law, insurance and public sector: "u" everywhere. Adjectives do not agree with the sender's gender, so question 3 does not apply |
| Russian | "вы" | The past tense agrees with the speaker, so the signer's gender is required: "я был рад" against "я была рада". There are no articles, so a sentence translated word for word from English reads wrong. Use the first name alone unless the list carries the patronymic |
| Polish | "Pan" or "Pani", never "ty" | Address with "Panie" or "Pani" plus the first name and put the verb in the third person. The past tense agrees with the signer's gender ("byłem" or "byłam"). The Pan and Pani choice needs the recipient's gender, so when the list has none, open with "Dzień dobry" and no title |
| Swedish, Danish, Norwegian | "du" to everyone | There is no polite form left in ordinary use. Swedish "Ni" reads archaic or sarcastic from a stranger, so never use it. No gender agreement, so question 3 does not apply |

For a language that is not in this table, say so before writing a word. Offer three
options: write in English, write in the language and have a native speaker read the 20
row sample before anything is sent, or drop that part of the list. A cold email with one
wrong agreement in it is worse than a cold email in English, and it is not recoverable:
the reader has already decided by the second line.

## 7. What the model returns

The prompt asks for a body and a subject line per email and mentions JSON without giving
a shape, so state the shape when you run it. That instruction sits **after** the prompt,
outside it, as a separate line:

```text
Return only a JSON array of four objects, in step order, each with the keys "step",
"subject" and "body". No prose around the array.
```

```json
[
  {"step": 1, "subject": "page de statut et realite", "body": "Bonjour Marc,\n\n..."},
  {"step": 2, "subject": "", "body": "..."},
  {"step": 3, "subject": "qui est prevenu en premier", "body": "..."},
  {"step": 4, "subject": "", "body": "..."}
]
```

The four steps of the prompt are the four steps of the rhythm table in
[outreach-write](../SKILL.md) section 8, in the same order: Initial Outreach is step 1,
Follow-up is step 2, Value Reinforcement is step 3, Final Attempt is step 4.

Steps 2 and 4 stay in the thread of the step before them, so their generated subject is
dropped and the Emelia step is left with an empty subject. Emelia then reuses the last
subject it sent and prefixes it with `Re: `. Keep the generated subject in the CSV
anyway, in case the flow is later changed to a new thread.

Columns written into `outreach/leads.csv`, one row per contact:

| Step | Subject column | Body column | Used by the Emelia step as |
|---|---|---|---|
| 1 | `subject_line` | `message` | subject `{{subject_line}}`, body `{{message}}` |
| 2 | `subject_line_2` | `message_2` | subject empty, body `{{message_2}}` |
| 3 | `subject_line_3` | `message_3` | subject `{{subject_line_3}}`, body `{{message_3}}` |
| 4 | `subject_line_4` | `message_4` | subject empty, body `{{message_4}}` |

Plus `message_source` and `message_date` next to them, on the same terms as every other
generated column: what the model was given and when it was run.

Before any value goes into the CSV, strip `{`, `}` and `|` out of it. Emelia runs
spintax after variable substitution, so a stray brace inside a message value eats part
of the sentence at send time. The rule and the reason are in
[outreach-personalize](../../outreach-personalize/SKILL.md) section 4.
