# Language rules for the writing prompts

The prompts of this repository are written in English and write in any language. Four
answers from [outreach-write](../SKILL.md) section 1 turn them into prompts for one
language, one register and one signer: the language, the form of address, the gender of
the person signing, and the rules of that language. This file holds how those answers are
written into the prompts, and the rules per language.

## 1. How the answers go into a prompt

They go into the `LANGUAGE` block at the end of the system prompt of
[first-message-prompt.md](first-message-prompt.md) and of
[follow-up-prompt.md](follow-up-prompt.md), as a dash list, in this order. Nothing is
inserted anywhere else.

1. The form of address, from question 2. Skip in English.
2. The signer's gender, from question 3. Skip when the language does not agree.
3. The lines for that language, from section 2 below.
4. Any house rule the user gave in answer to question 4.

Write them in English, like the rest of the prompt, and quote the target language forms
literally so there is nothing to interpret. Worked example, French, "vous", a woman
signing:

```text
- Write in French and use "vous" throughout, including in the follow ups. Never "tu"
- The person signing is a woman: agree everything the sender says about herself in the
  feminine, "je serais ravie" and not "ravi", "je suis convaincue" and not "convaincu"
- Do not use a gendered salutation for the recipient ("Cher", "Chère"): the greeting is
  added for you, and the list does not carry a reliable gender
```

If the user does not know the signer's gender, or does not want to say, do not pick one
and do not guess from a first name: write the line "Nothing the sender says about
themselves may agree with a gender (in French, neither 'ravi' nor 'ravie')". In French
that is doable ("ce serait un plaisir" instead of "je serais ravi"); in Russian, where the
past tense agrees on every sentence about the sender, it is barely doable, and the honest
move is to ask again before writing.

## 2. The lines for each language

One or two lines per language, added as described in section 1. These are rules that
stop the two failures a translated cold email dies of: a grammatical mistake the reader
notices in the first line, and a phrase that reads as English wearing a costume.

| Language | Default form of address | Lines to add |
|---|---|---|
| English | No distinction, and do not ask about one | Nothing to add. Keep contractions, they are what makes it sound written by a person |
| French | "vous" | Agree everything about the sender with the signer's gender ("je serais ravi" or "ravie"). No gendered salutation for the recipient: "Bonjour <first name>". The forbidden openings of the French block of first-message-prompt.md, section 5, apply |
| German | "Sie" | Capitalise every noun, and the polite forms (Sie, Ihnen, Ihr). "Herr" or "Frau" needs the recipient's gender, so open with "Guten Tag <full name>" instead. "du" only when the company already says "du" on its own website |
| Spanish | "usted" in Mexico, Colombia, Peru and Chile; "tú" in Spain; "vos" in Argentina and Uruguay | Open questions and exclamations with the inverted mark, "¿" and "¡". Agree the sender's adjectives with the signer's gender ("encantado" or "encantada"). Pick one country's form for the run and never mix "tú" and "usted" inside a sequence |
| Portuguese | "você" in Brazil, third person in Portugal | Brazil: "você", warm, contractions are fine. Portugal: avoid "você", which reads blunt from a stranger, and use the third person with the person's name. Vocabulary splits too (Brazil "time" and "celular", Portugal "equipa" and "telemóvel"), so choose the variant and stay in it. Sender adjectives agree with the signer's gender |
| Italian | "Lei" | Capitalise "Lei" and its forms. Agree the sender's adjectives with the signer's gender ("sarei lieto" or "lieta"). "tu" only for a startup that already uses it publicly |
| Dutch | "je" in the Netherlands, "u" in Flanders | Dutch business email is informal and "je" is normal even from a stranger in the Netherlands. Flanders is more formal, so "u". Finance, law, insurance and public sector: "u" everywhere. Adjectives do not agree with the sender's gender, so question 3 does not apply |
| Russian | "вы" | The past tense agrees with the speaker, so the signer's gender is required: "я был рад" against "я была рада". There are no articles, so a sentence translated word for word from English reads wrong. Use the first name alone unless the list carries the patronymic |
| Polish | "Pan" or "Pani", never "ty" | Address with "Panie" or "Pani" plus the first name and put the verb in the third person. The past tense agrees with the signer's gender ("byłem" or "byłam"). The Pan and Pani choice needs the recipient's gender, so when the list has none, open with "Dzień dobry" and no title |
| Swedish, Danish, Norwegian | "du" to everyone | There is no polite form left in ordinary use. Swedish "Ni" reads archaic or sarcastic from a stranger, so never use it. No gender agreement, so question 3 does not apply |

For a language that is not in this table, say so before writing a word. Offer three
options: write in English, write in the language and have a native speaker read the sample
of the first batch before anything is sent, or drop that part of the list. A cold email with one
wrong agreement in it is worse than a cold email in English, and it is not recoverable:
the reader has already decided by the second line.
