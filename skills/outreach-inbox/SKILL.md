---
name: outreach-inbox
description: "Triages the replies to a running campaign: pulls the reply, bounce and unsubscribe activities from Emelia, sorts every reply by intent (interested, meeting request, not now with the follow up date extracted, out of office with the stand in contact extracted, wrong person with the referral, unsubscribe, negative), drafts an answer in the sender's own voice, blacklists every opt out immediately, and lists the manual tasks waiting on a human. Writes outreach/replies.md with one block per contact and the exact call to send each answer. It prepares, you send. Triggers on: inbox, replies, reply handling, answer, respond, triage, out of office, unsubscribe, opt out, blacklist, not interested, meeting request, follow up date, wrong person, referral, manual task, bounce, response rate."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Triage the replies and draft the answers

## What this does

Reads every reply a campaign received, sorts them by what the person actually wants,
writes a draft answer for each one in the voice of the person who sent the campaign, and
handles the opt outs immediately and without asking. It writes everything to
`outreach/replies.md` and stops there.

**It prepares, you send.** No message reaches a real person without an explicit yes from
you, one message at a time. The only action taken without asking is honouring an
unsubscribe, because that is an obligation, not a decision.

## When to use it

Run it daily while a campaign is running, and once more a week after it ends: late
replies are often the good ones.

Use a different skill when you want the numbers rather than the messages
(`outreach-analyze` gives rates per step and per variant), when you want to fix the copy
that produced these replies (`outreach-write`), or when the campaign is not sending at
all, which is a deliverability question, not an inbox one.

## Inputs

- **A campaign.** The `emelia.campaignId` in `outreach/campaign.json`, or a name to
  resolve. Without either, `list_campaigns` (MCP) or `GET /advanced/campaigns` lists them
  with their id, name and status, so ask the user which one.
- **`outreach/sequence.md`.** The drafts must sound like the campaign, not like a
  chatbot. Read the copy before writing a single answer.
- **`EMELIA_API_KEY`**, or the Emelia MCP server. Without either there is nothing to read
  and nothing to send: say so rather than producing an empty triage.
- **The sender's calendar link**, if there is one. Ask once, reuse it in every draft. Do
  not invent a booking URL.

## How to do it

### 1. Pull the activities

With MCP:

```
get_campaign_activities { "campaignId": "6612f0a9b1c2d3e4f5a6b7c8", "type": "MAIL_REPLIED" }
```

Repeat for `LINKEDIN_REPLIED`, `UNSUBSCRIBED` and `BOUNCED`. The full event list is
`VISITED`, `INVITED`, `ACCEPTED`, `MESSAGE_SENT`, `INMAIL_SENT`, `LINKEDIN_REPLIED`,
`MAIL_REPLIED`, `RE_REPLY_EMAIL`, `RE_REPLY_LINKEDIN`, `FOLLOWED`, `LIKED`, `SENT`,
`BOUNCED`, `OPENED`, `UNSUBSCRIBED`, `CLICKED`, `TASK_COMPLETED`.

**The feed is paginated 30 at a time, and the MCP tool does not expose the page.** On a
campaign with more than 30 replies, go through REST to get the rest:

```bash
curl -s -H "Authorization: $EMELIA_API_KEY" \
  "https://api.emelia.io/advanced/campaigns/$CAMPAIGN_ID/activities?type=MAIL_REPLIED&page=0"
```

`page` starts at 0. Increase it until a page comes back empty. The `query` parameter
filters by contact but only accepts a full valid email address, anything else is ignored.

### 2. What a reply looks like

```json
{
  "_id": "6613a1...",
  "contact": { "_id": "660f...", "firstName": "Claire", "lastName": "Fontaine",
               "email": "claire.fontaine@nexora.fr", "companyName": "Nexora" },
  "event": "MAIL_REPLIED",
  "date": "2026-03-18T09:12:44.000Z",
  "customData": { "repliedTo": "paul@get-acme.com", "sentiment": { "classification": "INTERESTED", "score": 0.9 } },
  "step": 2,
  "version": 0,
  "reply": { "content": "<div>Bonjour Paul, ...</div>", "text": "Bonjour Paul, ...",
             "subject": "Re: Nexora + Postgres 16", "senderName": "Claire Fontaine" }
}
```

- Classify on `reply.text`. `reply.content` is HTML and includes the quoted history.
- `customData.repliedTo` is the mailbox that received it, which is the mailbox that must
  answer.
- `customData.sentiment.classification` is present on accounts that have reply
  classification enabled, with values among `INTERESTED`, `NOT_INTERESTED`, `NEUTRAL`,
  `OUT_OF_OFFICE`, `HOSTILE`, `DELEGATION`, `INCOMPREHENSION`, `QUESTION_ASK`, plus a
  `score` between 0 and 1. On `DELEGATION` it carries
  `additionalData.delegationEmail`, on `OUT_OF_OFFICE` it carries
  `additionalData.returnDate`: use those rather than re-extracting them by hand. Treat the
  classification as a hint that saves a first pass, and read the text yourself before
  acting on it, especially below a score of 0.7.
- `step` and `version` tell you which message they answered. Quote it in the draft rather
  than guessing what they saw.

### 3. Sort by intent

Seven buckets. Assign exactly one per reply, and record the phrase that decided it.

**Interested.** "tell me more", "how does it work", "send me a link", "interested",
"ça m'intéresse", "envoyez-moi". Draft: two sentences, answer the actual question, offer
one next step. Do not re-pitch, they already said yes to the conversation.

**Meeting request.** "let's talk", "can we schedule", "quelles sont vos dispos", "un call".
Draft: propose two or three concrete slots in their time zone and paste the calendar link
if there is one. Never invent a link.

**Not now.** "circle back", "not this quarter", "recontactez-moi en septembre", "budget".
Extract the date they gave. Draft: one line, agree, name the date, nothing else. Record
the date on the contact so the next campaign picks it up:

```bash
curl -s -X PATCH https://api.emelia.io/advanced/contacts \
  -H "Authorization: $EMELIA_API_KEY" -H "Content-Type: application/json" \
  -d '{"campaignId":"'$CAMPAIGN_ID'","email":"claire.fontaine@nexora.fr","fieldName":"follow_up_date","fieldValue":"2026-09-01"}'
```

With MCP, `update_contact` with
`{ contactId: "<contact._id from the activity>", fields: { follow_up_date: "2026-09-01" } }`
does the same, needs no campaign id, and can set several fields at once. Either way the
field is created if it does not exist yet, and becomes `{{follow_up_date}}` in a later
campaign.

**Out of office.** An automatic answer with a return date, and very often a stand in:
"in my absence contact X at x@company.com", "en mon absence, contactez". Extract two
things: the return date, and the replacement name and address. The replacement is a real
lead, so add them to the list (`add_contact_to_list` with MCP, or
`POST /advanced/lists/contacts` with `{"id":"<listId>","contact":{...}}`) and record where
they came from. Do not draft an answer to a robot. When `ignoreAutoReplies` is on in the
campaign settings these never appear as replies at all, which is the correct setting.

**Wrong person.** "not my area", "je ne suis pas la bonne personne", "you should speak to".
Draft: thank them, ask for the introduction by name, and stop. If they named someone,
add that person to the list.

**Unsubscribe.** "unsubscribe", "remove me", "stop", "désinscrivez-moi", "ne me
recontactez plus", "supprimez mes données". Handle it in section 4, first, before you
draft anything else.

**Negative.** "not interested", "we already have one", "pas intéressé", and everything
hostile. Draft at most one line acknowledging it, and only when the tone allows. Never
argue, never send a "just to be sure" follow up. A hostile reply that mentions spam or
legal action gets blacklisted, not answered.

### 4. Unsubscribes, immediately and without asking

An opt out is honoured on the same run it is detected. Do not queue it, do not batch it
for later, do not ask the user whether they agree.

```bash
curl -s -X POST https://api.emelia.io/emails/blacklists/contact \
  -H "Authorization: $EMELIA_API_KEY" -H "Content-Type: application/json" \
  -d '{"email":"claire.fontaine@nexora.fr"}'
```

- The `email` field also accepts a bare domain in the form `domain.ltd`, which blacklists
  everyone there. Use it when someone answers for their whole company, and only then. Ask
  before doing it: it is account wide and it is the one blacklist action worth confirming.
- `DELETE` on the same path with the same body removes an address, for the case where you
  blacklisted the wrong one.
- The blacklist is account wide, so it also protects every future campaign. That is the
  point.
- `blacklistUnsub` in the campaign settings already blacklists people who **click** the
  unsubscribe link. It does not catch someone who **writes** "unsubscribe" in a reply.
  That gap is exactly what this step closes.
- A reply that asks for data deletion is more than an opt out: blacklist, then tell the
  user it needs a human answer within the legal deadline of their market.

Report the count. "3 unsubscribes, blacklisted" is a line the user must see.

### 5. Draft in the sender's voice

Read two or three messages from `outreach/sequence.md` first, then hold to these rules:

- Match the length of their reply. A two line answer gets a two line answer.
- Match the language of their reply, not the language of the campaign.
- One question per message, at most.
- No attachment, no new pitch, no second call to action.
- No fabricated facts. If you do not know the price, the draft says the sender will
  confirm it, it does not invent a number.
- Sign with the sender's name. The mailbox signature is appended automatically by Emelia,
  so do not paste the signature into the body.
- Quote nothing. The reply endpoint appends the original thread by itself when it has a
  message id.

Write each draft into `outreach/replies.md`. That file is the deliverable.

### 6. Send, one at a time, only on an explicit yes

Show the draft, ask, wait for a yes for that specific message. Then:

```bash
curl -s -X POST https://api.emelia.io/emails/reply \
  -H "Authorization: $EMELIA_API_KEY" -H "Content-Type: application/json" \
  -d '{
        "providerId": "65e0aa11bb22cc33dd44ee55",
        "to": ["claire.fontaine@nexora.fr"],
        "subject": "Re: Nexora + Postgres 16",
        "content": "Bonjour Claire,<br><br>Merci pour votre retour. ..."
      }'
```

Four things that make this call fail, none of them obvious from the schema:

1. `content` is the only field the reference marks as required, but the server also
   requires **at least one of `providerId` or `senderEmail`**. Send one of them. The
   mailbox to use is `customData.repliedTo` from the activity, and `list_email_providers`
   maps that address to its `_id`.
2. `messageId` is what threads the answer: with it, Emelia sets `In-Reply-To`, adds the
   references and appends the quoted history. It comes from the merged inbox in the app,
   not from the activity feed, so you usually will not have it.
3. **Without `messageId` you must supply `to` and `subject` yourself.** The call has
   nothing to inherit from. That is the shape shown above, and it sends a normal email
   rather than a threaded reply.
4. With a `messageId` that Emelia cannot find, the call fails with
   `Original message not found`. Retry without it, adding `to` and `subject`.

`content` is HTML. Use `<br>` for line breaks, not `\n`. `cc`, `bcc` and `attachments`
(`[{ "name": ..., "url": ... }]`) exist if you need them, and you almost never do.

LinkedIn replies are not sendable through this endpoint. Draft them in the file and tell
the user to send them from the app.

### 7. Manual tasks

Steps of type `TASK` wait for a human. List them:

```
list_manual_tasks { "campaignId": "6612f0a9b1c2d3e4f5a6b7c8" }
```

Each task carries the contact, the step id as `taskId`, and its name. The action itself
is done by hand, outside Emelia. When it is genuinely done:

```
complete_manual_task { "campaignId": "...", "contactId": "...", "taskId": "...", "status": "ok" }
```

`ko` marks it failed and lets the sequence move on. Only mark `ok` for something that
actually happened: the sequence continues from there, and a false `ok` sends the next
step to someone who never got the previous one. These two tools have no documented REST
equivalent, so without MCP the tasks are handled in the app.

## Output

`outreach/replies.md`, rewritten on every run, newest first.

```markdown
# Replies, Q4 SaaS founders, run of 2026-03-18

17 replies since the last run: 4 interested, 2 meetings, 3 not now, 5 out of office,
1 wrong person, 3 unsubscribes (blacklisted), 1 negative. 2 bounces removed.
Nothing has been sent. 6 drafts are waiting for your yes.

---

## Claire Fontaine, Nexora, interested
claire.fontaine@nexora.fr | step 2, version A | 2026-03-18 09:12 | replied to paul@get-acme.com

> Bonjour Paul, sujet intéressant, on a justement migré en février. Comment vous
> vous comparez à Datadog sur le coût ?

Decided by: "comment vous vous comparez", a direct question, not a brush off.

**Draft** (French, 3 lines, answers the question, one next step)

> Bonjour Claire,
> Sur un parc de votre taille on est en général 40% sous Datadog, parce qu'on ne
> facture pas à l'ingestion. Je peux vous montrer le calcul sur vos volumes.
> 20 minutes jeudi ou vendredi matin ?

Send with: POST /emails/reply, providerId 65e0aa11bb22cc33dd44ee55,
to claire.fontaine@nexora.fr, subject "Re: Nexora + Postgres 16"

---

## Marc Ostrowski, Vlantis, out of office
marc@vlantis.io | step 1 | 2026-03-17 16:40

> Absent jusqu'au 30 mars. En cas d'urgence, contactez Julie Ferrand,
> j.ferrand@vlantis.io

No draft, this is an auto responder.
Done: Julie Ferrand added to list 65f1a2b3c4d5e6f7a8b9c0d1, source "OOO of marc@vlantis.io".
Done: follow_up_date set to 2026-03-31 on marc@vlantis.io.

---

## Unsubscribes, handled without asking

| Address | Phrase | Action | Time |
|---|---|---|---|
| t.roche@kavia.fr | "merci de me retirer de votre liste" | blacklisted | 09:31 |
| n.abadie@sorel.com | "unsubscribe" | blacklisted | 09:31 |
| d.wu@parqet.io | "stop" | blacklisted | 09:31 |

## Manual tasks waiting

| Contact | Task | Step |
|---|---|---|
| Sophie Lenoir | Comment on her post before the connection request | 3 |
```

## Checks before finishing

- Every reply pulled is in the file with a bucket and the phrase that decided it. No
  reply is silently dropped.
- Every unsubscribe was blacklisted **before** the file was written, and the file says so
  with a timestamp.
- The reply count in the file matches the number of activities pulled, and if you stopped
  paginating, the file says at which page.
- No draft contains a fact that is not in the reply, in the sequence, or given by the
  user. No invented price, no invented calendar link, no invented case study.
- Nothing was sent without a yes for that specific message. The file records what was
  sent and what is still waiting.
- Manual tasks marked `ok` were actually done by a human who said so.

## Failure modes

- **A reply is attached to the wrong contact.** Emelia matches a reply by sender address,
  message id or thread id. A reply from a colleague's address on a forwarded thread lands
  on the original contact. Read `reply.senderName` and the text before answering by name.
- **Out of office answers counted as replies.** `ignoreAutoReplies` is off in the campaign
  settings. Turn it on: otherwise every auto responder stops the sequence for that contact
  and inflates your reply rate.
- **Only 30 replies come back.** That is one page. Paginate through REST, page 0 upwards.
- **`Original message not found`.** The `messageId` is not in the merged inbox any more.
  Send without it, with `to` and `subject`.
- **`Provider not found`.** The `providerId` does not belong to the account, or the
  `senderEmail` is not a connected mailbox. Re-read `list_email_providers`.
- **The reply arrives with the signature twice.** The signature was pasted into `content`
  and Emelia appended the mailbox one. Remove it from the body.
- **You blacklisted a whole domain by mistake.** `DELETE /emails/blacklists/contact` with
  the same value undoes it. Say what happened, do not fix it quietly.
- **No replies at all after several days.** Check the campaign is `RUNNING` and that mail
  is actually going out, then look at deliverability. An empty inbox is rarely an inbox
  problem.

## Limits

This skill reads replies through the campaign activity feed. It does not read the mailbox:
there is no documented endpoint that lists the merged inbox, so a reply that Emelia did
not attach to a contact is invisible here and has to be handled in the app. It cannot send
LinkedIn replies, cannot book a meeting or touch a calendar, and cannot judge a reply that
says nothing (a bare "ok" is ambiguous and it will say so rather than guess). It drafts,
it does not decide: the answer that goes out is yours.
