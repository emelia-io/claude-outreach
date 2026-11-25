---
name: outreach-replies
description: "Triage the replies your Emelia campaigns received. Reads who replied, and to which step, in the campaign activity feed, then, once the Emelia Inbox is set up, reads each thread and prepares a reply in the same conversation through the inbox tools of the Emelia MCP server or the Emelia Inbox API. Sorts every reply by intent (interested, meeting request, not now with the follow up date extracted, out of office with the stand in contact extracted, wrong person with the referral, unsubscribe, negative), drafts an answer in the sender's own voice, blacklists every opt out immediately, and lists the manual tasks waiting on a human. Writes outreach/replies.md with one block per contact and the exact call to send each answer. It prepares, you send. Triggers on: replies, reply handling, campaign replies, answer, respond, triage, inbox, out of office, unsubscribe, opt out, blacklist, not interested, meeting request, follow up date, wrong person, referral, manual task, bounce, response rate."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Triage the replies to your campaigns

## What this does

Reads the replies your campaigns received, sorts them by what the person actually
wants, writes a draft answer for each one in the voice of the person who sent the
campaign, and handles the opt outs immediately and without asking. It writes
everything to `outreach/replies.md` and stops there.

**The perimeter is the replies to your campaigns, read from two places.** The activity
feed of a campaign says who replied, when, and to which step: it is the work list. The
Emelia Inbox (the **Inbox** tab of the app, fed by the mailboxes connected to Emelia)
holds the emails themselves: the whole thread, a reply sent from another address, one
that landed in spam. Emelia opens that inbox to code in two ways: the inbox tools of the
MCP server (`list_mailboxes`, `list_emails`, `search_emails`, `get_thread`,
`draft_reply`, `send_draft` and others), and the Emelia Inbox API at
`https://api.emelia.io/inbox/api/v1`, with the same API key. This skill uses the inbox to
read and answer what your campaigns received. It does not sort the rest of the mailbox:
newsletters, invoices and internal mail stay out of `replies.md`. Say that to the user
the first time.

**It prepares, you send.** No message reaches a real person without an explicit yes
from you, one message at a time. The only action taken without asking is honouring an
unsubscribe, because that is an obligation, not a decision.

## When to use it

Run it daily while a campaign is running, and once more a week after it ends: late
replies are often the good ones.

Use a different skill when you want the numbers rather than the messages
(`outreach-audit` gives rates per step and per variant), when you want to fix the copy
that produced these replies (`outreach-write`), or when the campaign is not sending at
all, which is a deliverability question.

Do not reach for it to sort a whole mailbox. Labels, views, inbox filters and AI label
rules have their own tools (the `inbox_settings` category of the MCP server) and their own
routes in the Inbox API. This skill reads the inbox only to handle what your campaigns
received.

## Inputs

- **A campaign.** The `emelia.campaignId` in `outreach/campaign.json`, or a name to
  resolve. Without either, `list_campaigns` (MCP) or `GET /advanced/campaigns` lists them
  with their id, name and status, so ask the user which one. Replies are read per
  campaign: there is no "all my replies" call, so a user running four campaigns gets
  four passes.
- **`outreach/sequence.md`.** The drafts must sound like the campaign, not like a
  chatbot. Read the copy before writing a single answer.
- **`EMELIA_API_KEY`**, or the Emelia MCP server. Without either there is nothing to read
  and nothing to send: say so rather than producing an empty triage.
- **The Emelia Inbox**, strongly recommended. With MCP, look for a tool whose name ends in
  `__search_emails` or `__list_mailboxes`. The inbox tools appear only once the Inbox has
  been opened in Emelia: if they are missing, tell the user to open the **Inbox** tab of
  the app once, wait a few minutes and reconnect the server. With the key, call
  `GET https://api.emelia.io/inbox/api/v1/mailboxes`: it lists the mailboxes the inbox
  reads. Without the inbox the skill still works from the activity feed, but it cannot
  read a thread, and its answers go out as new emails rather than replies in the
  conversation (section 7).
- **The sender's calendar link**, if there is one. Ask once, reuse it in every draft. Do
  not invent a booking URL.

## How to do it

### 1. Know what you can actually read

The campaign side tells you who replied:

| What | MCP tool | REST, `https://api.emelia.io` |
|---|---|---|
| The activity feed of one campaign, replies included | `get_campaign_activities`, first page only | `GET /advanced/campaigns/{id}/activities`, 30 per page |
| Every reply of a campaign in one call | `export_campaign` with `type: "replies"` | `GET /advanced/campaigns/{id}/export?type=replies`, a CSV |
| Blacklist an address or a domain, and undo it | `add_to_blacklist`, `remove_from_blacklist` with `type: "email"` | `POST` and `DELETE /emails/blacklists/contact` |
| Answer without the inbox | none | `POST /emails/reply` |

The inbox side holds the emails. The MCP tools appear once the Inbox has been opened in
Emelia; the Inbox API takes the same key and has its own quotas, 60 requests a minute and
10,000 a month per account:

| What | MCP tool | Inbox API, `https://api.emelia.io/inbox/api/v1` |
|---|---|---|
| The mailboxes the inbox reads | `list_mailboxes` | `GET /mailboxes` |
| Find the reply of a contact | `search_emails` | `GET /emails/search?q=...` |
| Browse new mail | `list_emails`, `get_unread_counts` | `GET /emails`, cursor pagination |
| Read the whole thread | `get_thread` | `GET /emails/{emailId}/body` |
| Prepare an answer in the conversation, nothing sent | `draft_reply` | `POST /drafts` with `inReplyTo` and `references` |
| Send it, after a yes | `send_draft` | `POST /drafts/send` |

If a user asks for "everything in my inbox", that is the inbox tools on their own, not
this skill: this skill starts from the campaigns.

### 2. Pull the replies, page by page

With MCP, for a small campaign:

```
get_campaign_activities { "campaignId": "6612f0a9b1c2d3e4f5a6b7c8", "type": "MAIL_REPLIED" }
```

Repeat for `LINKEDIN_REPLIED`, `UNSUBSCRIBED` and `BOUNCED`. The full event list is
`VISITED`, `INVITED`, `ACCEPTED`, `MESSAGE_SENT`, `INMAIL_SENT`, `LINKEDIN_REPLIED`,
`MAIL_REPLIED`, `RE_REPLY_EMAIL`, `RE_REPLY_LINKEDIN`, `FOLLOWED`, `LIKED`, `SENT`,
`BOUNCED`, `OPENED`, `UNSUBSCRIBED`, `CLICKED`, `TASK_COMPLETED`.

**The feed is paginated 30 at a time and the MCP tool does not expose the page**, so
above 30 replies `get_campaign_activities` silently gives you the first page and nothing
else. With MCP alone, take every reply at once with
`export_campaign { "campaignId": "...", "type": "replies" }`: it returns the CSV as text,
cut at 100,000 characters with a note giving the number of lines shown, so pass `start`
and `end` to split a large campaign into date ranges. With the key, loop over REST:

```bash
page=0
while : ; do
  body=$(curl -s -H "Authorization: $EMELIA_API_KEY" \
    "https://api.emelia.io/advanced/campaigns/$CAMPAIGN_ID/activities?type=MAIL_REPLIED&page=$page")
  n=$(printf '%s' "$body" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["activities"]))')
  printf '%s\n' "$body" >> outreach/.replies-raw.jsonl
  [ "$n" -lt 30 ] && break
  page=$((page + 1))
done
```

Four things about this loop:

- `page` starts at 0, and the response is `{"activities": [...]}`.
- Stop on a **short** page, not only on an empty one. A last page of 12 is the end;
  waiting for a page of 0 costs one extra call, which is harmless but slower.
- `types` takes a comma separated list, so `types=MAIL_REPLIED,LINKEDIN_REPLIED`
  fetches both in one pass. `type` takes one value.
- `query` filters by contact but only accepts a full valid email address, anything
  else is ignored silently. `search` is the free text one.

For a campaign with hundreds of replies, skip the loop entirely:

```bash
curl -s -H "Authorization: $EMELIA_API_KEY" \
  "https://api.emelia.io/advanced/campaigns/$CAMPAIGN_ID/export?type=replies&start=2026-03-01" \
  -o outreach/replies-export.csv
```

One call, every reply, with an optional `start` and `end` range. Use it for the first
run on an old campaign, and the paginated loop for the daily pass.

Record the last page you read and the date of the newest activity, so tomorrow's run
starts there instead of re-reading everything.

### 3. What a reply looks like

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

### 4. Sort by intent

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
recontactez plus", "supprimez mes données". Handle it in section 5, first, before you
draft anything else.

**Negative.** "not interested", "we already have one", "pas intéressé", and everything
hostile. Draft at most one line acknowledging it, and only when the tone allows. Never
argue, never send a "just to be sure" follow up. A hostile reply that mentions spam or
legal action gets blacklisted, not answered.

### 5. Unsubscribes, immediately and without asking

An opt out is honoured on the same run it is detected. Do not queue it, do not batch it
for later, do not ask the user whether they agree.

```bash
curl -s -X POST https://api.emelia.io/emails/blacklists/contact \
  -H "Authorization: $EMELIA_API_KEY" -H "Content-Type: application/json" \
  -d '{"email":"claire.fontaine@nexora.fr"}'
```

With MCP: `add_to_blacklist { "type": "email", "value": "claire.fontaine@nexora.fr" }`.

- The `email` field (`value` with MCP) also accepts a bare domain in the form
  `domain.ltd`, which blacklists everyone there. Use it when someone answers for their whole company, and only then. Ask
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

### 6. Draft in the sender's voice

Read two or three messages from `outreach/sequence.md` first, then hold to these rules:

- Match the length of their reply. A two line answer gets a two line answer.
- Match the language of their reply, not the language of the campaign.
- One question per message, at most.
- No attachment, no new pitch, no second call to action.
- No fabricated facts. If you do not know the price, the draft says the sender will
  confirm it, it does not invent a number.
- Never paste the signature into the body: Emelia adds the signature of the mailbox. With
  `draft_reply`, add no closing and no name either, the sender block is added for you.
  With `POST /emails/reply`, sign with the sender's name.
- Quote nothing. `draft_reply` quotes the original by itself, and so does
  `POST /emails/reply` when it has a `messageId`.

Write each draft into `outreach/replies.md`. That file is the deliverable, and it is
the deliverable even when the user is in a hurry: the drafts wait there until a human
approves them one by one.

### 7. Send, one at a time, only on an explicit yes

Show the draft, ask, wait for a yes for that specific message. A yes on one draft is
not a yes on the next one, and "send them all" is a request to show them all first.

**With the inbox, answer in the conversation.** Find the email of the reply, read the
thread, and leave a draft in the inbox, under her message:

```
search_emails { "query": "claire.fontaine@nexora.fr", "folder": "INBOX" }
get_thread    { "emailId": "<id of her reply>", "bodyFormat": "clean_text" }
draft_reply   { "emailId": "<id of her reply>", "body": { "text": "Bonjour Claire,\n\nSur un parc ..." } }
```

- Pick the email in the mailbox of `customData.repliedTo` (its `mailboxId` comes from
  `list_mailboxes`) and dated like the activity. A contact who replied twice has two.
- `draft_reply` sets the subject, the recipients, the threading headers and the quoted
  original, and sends nothing. It returns the draft and a link to review it in the Emelia
  inbox: put that link in `replies.md`.
- On the yes, `send_draft { "draftId": "...", "idempotencyKey": "<a new random string>",
  "confirm": true }`. `confirm: true` only after the user approved that exact email. If
  the call times out, retry with the same key, never with a new draft. The user can also
  send it from the inbox with the link.
- `DRAFT_ALREADY_EXISTS` means a draft already answers that email, often an AI auto-draft.
  Show it to the user; overwrite it (`replaceExistingDraft: true`) only if they agree.

With the key and no MCP, the same through the Inbox API:

```bash
INBOX=https://api.emelia.io/inbox/api/v1
curl -s -H "Authorization: $EMELIA_API_KEY" \
  "$INBOX/emails/search?q=claire.fontaine@nexora.fr&folderType=INBOX"
```

Each item carries `id`, `mailboxId`, `messageId`, `references` and `subject`. Read the
thread with `GET $INBOX/emails/{id}/body`, then `POST $INBOX/drafts` with `mailboxId`,
`to`, `subject` (`Re: ` and hers), `inReplyTo` set to her `messageId`, `references` set to
her `references` followed by her `messageId`, and `body` (`text`, `html` or both). The
draft waits in the inbox. `POST $INBOX/drafts/send` takes the same body and sends at once:
only on the yes, always with an `Idempotency-Key` header.

**Without the inbox, `POST /emails/reply`.** It sends a new email from the right mailbox,
which is still a correct answer, but usually not in the same conversation:

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
   references and appends the quoted history. It is the Message-ID of the email you
   answer, and the activity feed does not carry it. When you can read the inbox, answer
   through the inbox as above rather than through this route.
3. **Without `messageId` you must supply `to` and `subject` yourself.** The call has
   nothing to inherit from. That is the shape shown above.
4. With a `messageId` that Emelia cannot find, the call fails with
   `Original message not found`. Retry without it, adding `to` and `subject`.

`content` is HTML. Use `<br>` for line breaks, not `\n`. `cc`, `bcc` and `attachments`
(`[{ "name": ..., "url": ... }]`) exist if you need them, and you almost never do.

### 8. LinkedIn conversations

LinkedIn conversations have inbox routes of their own, apart from the email inbox
above, and no MCP tool. These routes were
verified on 9 September 2026 and are **not in the public specification**, so treat
them exactly like the campaign build routes in the dispatcher: use them, and tell the
user they are not contractual yet and may change without notice.

| Method and path | What it does |
|---|---|
| `GET /linkedin-inbox/chats` | Merged conversation list across the connected accounts. Query: `accounts` (comma separated auth ids), `cursor`, `limit` up to 100, `unread`, `after`, `before` as ISO dates |
| `GET /linkedin-inbox/chats/{chatId}` | One conversation |
| `GET /linkedin-inbox/chats/{chatId}/messages` | Its messages, `cursor` and `limit` up to 250 |
| `POST /linkedin-inbox/chats/{chatId}/messages` | Send a message in that conversation, multipart, `text` and up to 10 `attachments` |
| `POST /linkedin-inbox/chats` | Start a conversation, multipart, `accountId` and `attendeeProviderId` required |
| `PATCH /linkedin-inbox/chats/{chatId}/read` | Mark read or unread, body `{"value": true}` |
| `GET /linkedin-inbox/search` | Search conversations by participant name, `q` of at least 2 characters |

Pagination here is cursor based, not page based: read `cursor` from the response and
pass it back. The same rule applies as everywhere else in this skill: draft, show,
wait for a yes, then post. A LinkedIn message is a message to a real person.

If the user has no LinkedIn account connected, these calls return nothing useful.
Draft the LinkedIn answers in the file and tell them to send from the app.

### 9. Manual tasks

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
step to someone who never got the previous one. Without MCP, the same two things are in
the public reference: `GET /advanced/campaigns/{id}/manual-tasks` lists the tasks
(optional `stepId`), and `POST /advanced/campaigns/{id}/manual-tasks/status` closes one,
with `{"contactId": "...", "taskId": "...", "status": "ok"}`. A task can be closed only
once. Pausing the campaign deletes the pending tasks; they come back after the next start,
when the contacts reach the task step again.

## Output

`outreach/replies.md`, rewritten on every run, newest first.

```markdown
# Replies, Q4 SaaS founders, run of 2026-03-18

Source: campaign activity feed, 3 pages read (74 activities), newest 2026-03-18 09:12.
Threads read in the Emelia inbox. Only the replies to this campaign are here: the rest
of the mailbox was not sorted.

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

Draft ready in the Emelia inbox, in her conversation (draft_reply), from paul@get-acme.com.
Review: <link returned by draft_reply>
Send with: send_draft after your yes, or from the inbox with the link.

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

- The file says where the replies came from (the feed, the inbox, or both) and that the
  rest of the mailbox was not sorted. A user must never think a reply was handled when it
  was only read.
- The feed was paginated to the end, or the file says at which page you stopped and
  why. Exactly 30 replies is a page boundary, not a total: check it.
- Every reply pulled is in the file with a bucket and the phrase that decided it. No
  reply is silently dropped.
- Every unsubscribe was blacklisted **before** the file was written, and the file says so
  with a timestamp.
- No draft contains a fact that is not in the reply, in the sequence, or given by the
  user. No invented price, no invented calendar link, no invented case study.
- Nothing was sent without a yes for that specific message. The file records what was
  sent and what is still waiting.
- Manual tasks marked `ok` were actually done by a human who said so.

## Failure modes

- **A reply is missing from the feed.** The prospect wrote from another address, or
  Emelia could not attach the message to a contact. Search the inbox by domain
  (`search_emails { "query": "nexora.fr" }`) or by the subject of the step. Without the
  inbox, it is visible only in the Emelia app: say so.
- **The inbox tools are not there.** The Inbox was never opened in Emelia. Ask the user to
  open the **Inbox** tab once, wait a few minutes and reconnect the server. Until then,
  work from the feed and answer with `POST /emails/reply`, which needs the key: with the
  MCP server alone, the drafts wait in `replies.md` and the user sends them from the app.
- **Only 30 replies come back.** That is one page. The MCP tool cannot ask for the
  next one: use `export_campaign` with `type: "replies"`, or loop on `page` over REST.
- **`POST /drafts/send` answers 500.** The reference warns that the email may have left
  anyway, and that the idempotency key is then released. Look in the `SENT` folder before
  retrying, or the prospect gets it twice.
- **A reply is attached to the wrong contact.** Emelia matches a reply by sender address,
  message id or thread id. A reply from a colleague's address on a forwarded thread lands
  on the original contact. Read `reply.senderName` and the text before answering by name.
- **Out of office answers counted as replies.** `ignoreAutoReplies` is off in the campaign
  settings. Turn it on: otherwise every auto responder stops the sequence for that contact
  and inflates your reply rate.
- **`Original message not found`.** The `messageId` is not in the merged inbox any more.
  Send without it, with `to` and `subject`.
- **`Provider not found`.** The `providerId` does not belong to the account, or the
  `senderEmail` is not a connected mailbox. Re-read `list_email_providers`.
- **The reply arrives with the signature twice.** The signature was pasted into `content`
  and Emelia appended the mailbox one. Remove it from the body.
- **You blacklisted a whole domain by mistake.** `DELETE /emails/blacklists/contact` with
  the same value undoes it. Say what happened, do not fix it quietly.
- **No replies at all after several days.** Check the campaign is `RUNNING` and that mail
  is actually going out, then look at deliverability. An empty feed is rarely a triage
  problem.

## Limits

This skill handles the replies to your campaigns. Once the Inbox is set up in Emelia it
reads their threads and answers in them, through the inbox tools of the MCP server or the
Inbox API. It does not sort the rest of the mailbox, and it does not touch labels, views,
inbox filters or rules: those have their own tools. Without the Inbox, it sees only what
the activity feed carries, and its answers start a new email.

The LinkedIn conversation routes are not in the public specification: use them, and
expect them to change.

It cannot book a meeting or touch a calendar, cannot see whether your reply landed in
spam, and cannot judge a reply that says nothing (a bare "ok" is ambiguous and it will
say so rather than guess).

It drafts, it does not decide: the answer that goes out is yours, one yes at a time.
