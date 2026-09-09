---
name: outreach-campaign
description: "Creates the campaign in Emelia and gets it launched: finds or creates the contact list, loads the contacts in bulk with their custom variables, creates the email or LinkedIn campaign, attaches the list so new contacts flow in automatically, sets the cadence, the sending window and the sending accounts, runs a pre-flight checklist (deliverability green, list verified, unsubscribe link present, every variable resolved, test email read), asks for an explicit yes, then starts it. Writes outreach/campaign.json with the real Emelia identifiers. Triggers on: campaign, launch, launch campaign, create campaign, start sending, send the sequence, go live, attach list, contact list, cadence, daily limit, sending accounts, identities, schedule, pre-flight, sequence steps, multichannel campaign."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Create and launch the campaign

## What this does

Turns the files produced by the earlier steps into a live Emelia campaign: a list that
holds the contacts, a campaign that holds the sequence, the two wired together, the
cadence set, and the launch done only after you say yes in plain words.

It records every real identifier in `outreach/campaign.json` so the next steps
(`outreach-replies`, `outreach-audit`) can find the campaign without asking you again.

## When to use it

Run it when the list is verified and the copy is written, as step 9 of a full run. It
calls the deliverability gate first and stops if the answer is BLOCKED.

Use a different skill when you want to design the sequence rather than create it
(`outreach-sequence`), write or fix the copy (`outreach-write`), add contacts to a
campaign that is already running (come back here, section 3, the list is the way in), or
read what happened after the launch (`outreach-audit`).

## Inputs

- **`outreach/deliverability.md`.** Read the `## Verdict` line first. If it is missing,
  run `outreach-deliverability` now. If it says BLOCKED, stop and show the fix list.
- **`outreach/leads.csv`.** One row per contact, verified. Must carry at least `email`
  for an email campaign, or `linkedinUrlProfile` for a LinkedIn campaign. If the
  verification column is missing, stop: sending to an unverified list is a refusal.
- **`outreach/sequence.md`.** The copy, step by step, with the variables.
- **`outreach/campaign.json`.** The sequence spec written by `outreach-sequence`. If it
  does not exist, build it here from `sequence.md` and confirm it with the user.
- **`EMELIA_API_KEY`**, or the Emelia MCP server. Without either, produce every file and
  the exact calls it would have made, and say plainly that nothing was created.

## How to do it

### 0. The gate

```bash
grep -A2 '^## Verdict' outreach/deliverability.md
```

BLOCKED means stop. Not "warn and continue". Show the blockers and the fix list, and
offer to re-run the audit once they are fixed.

READY WITH LIMITS means continue with the daily cap that file states, and carry that
number into the cadence in section 6 rather than the one the user asked for.

### 1. Find or create the list

Contacts do not live in a campaign. They live in a list, and a list is attached to one or
more campaigns. Get this right and the rest of the product makes sense.

Read the existing lists first, then create one if you need it:

```bash
curl -s https://api.emelia.io/lists/list -H "Authorization: $EMELIA_API_KEY"

curl -s -X POST https://api.emelia.io/lists/list \
  -H "Authorization: $EMELIA_API_KEY" -H "Content-Type: application/json" \
  -d '{"name":"Q4 SaaS founders"}'
```

The create returns `{"success": true, "listId": "...", "name": "..."}`. Keep the campaign
name and the list name identical, it saves an hour later. That `listId` is the same id
the campaign routes take, there is no import step between the two.

**Read the columns of the lists you did not build.** Every list in the `GET` above carries
a `columnPreferences` array, and that array is the list of variables the copy can use. A
key that starts with `custom` is a custom variable: strip that prefix and lowercase the
next letter to get the name the message uses, so `customEmail1subject` is
`{{email1subject}}`. A list that already carries `customEmail1subject`,
`customEmail1message` and their followers has been written for a previous campaign, and
those columns are the carriers to reuse. Writing new ones next to them means the campaign
sends the old copy or the new one depending on which name the steps reference, and a wrong
name renders empty with no error. Read the columns, then name the carriers to match.

Never reuse a list that already feeds another running campaign unless that is what the
user asked for: every contact in it would enter the new campaign too.

### 2. Load the contacts in bulk

One call carries up to 100 contacts:

```bash
curl -s -X POST "https://api.emelia.io/lists/list/<listId>/contacts/batch?updateIfExists=true" \
  -H "Authorization: $EMELIA_API_KEY" -H "Content-Type: application/json" \
  -d '{"contacts":[
    {"firstName":"Claire","lastName":"Fontaine","email":"claire.fontaine@nexora.fr",
     "companyName":"Nexora","companyDomain":"nexora.fr",
     "linkedinUrlProfile":"https://www.linkedin.com/in/clairefontaine",
     "icebreaker":"your migration to Postgres 16 last month"}
  ]}'
```

- **100 contacts per call, maximum**, and **1 MB per request body**. Split the CSV into
  chunks of 100, and clip long text fields to about 4,000 characters before sending. A
  hundred rows each carrying a full LinkedIn bio crosses the megabyte, and the refusal
  fails the whole batch, not the offending row.
- The payload is a flat object. `firstName`, `lastName`, `email`, `phone`,
  `linkedinUrlProfile`, `companyName`, `websiteUrl` are recognised fields. **Any other
  key creates a custom variable automatically**, which is how `icebreaker` above becomes
  `{{icebreaker}}` in the copy. Spell the keys exactly as the copy spells the variables.
- `updateIfExists: true` turns a duplicate into an update. Without it, a contact already
  in the list is left as it is and reported as a duplicate, not re-created.
- The response reports `created`, `duplicates`, `updated` and `failed` counts plus a per
  row result, indexed on the position in the array you sent, so each result maps back to
  its row. It also returns `createdCustomVariables`, where `technicalName` is the name to
  put in the copy. **Read the failed rows and report them.** Never say "1,180 contacts
  loaded" when 41 rows failed on a malformed address.
- **The LinkedIn field is `linkedinUrlProfile`.** Not `linkedinUrl`, not `linkedin`. A
  wrong name raises no error: it silently becomes a custom variable, and every LinkedIn
  branch of the campaign then finds an empty profile and never fires.
- **An unknown key is matched against the standard field names first, in several
  languages, before it becomes a custom variable.** `"Secteur"` lands in the company
  industry, `"Prénom"` in `firstName`, `"Société"` in `companyName`. If you want a real
  custom variable, give it a name that resembles no standard field.
- Reading back is not symmetric with writing: you send a flat object, and
  `GET /lists/list/<listId>/rows?page=1&pageSize=50` returns the company nested under
  `company` and the custom variables in a `customFields` array. `pageSize` caps at 100.

There is also a single contact route, `POST /advanced/lists/contacts` with
`{"id":"<listId>","contact":{...}}`. Use it to add one row to a list that already feeds a
running campaign, never to load a file: at one call per contact it burns the rate limit of
the plan for nothing. Three traps on that one, all of which fail a row rather than the
batch:

1. The contact needs **either** an email **or** a LinkedIn profile URL. The published
   schema lists both as required; the server accepts one. Sending neither fails.
2. A contact already in that list returns an error, it is not silently skipped. Treat that
   error as a duplicate, not as a failure to retry.
3. A Sales Navigator URL (`linkedin.com/sales/lead/...`) is converted to a
   `linkedin.com/in/...` URL when it can be. Anything else that is not a
   `linkedin.com/in/` URL is rejected.

Pace the loop. Rate limits are per key per minute: 30 without a subscription, 100 on
Start, 300 on Grow, 1000 on Scale. A 1,200 row list is 1,200 REST calls, so on Start that
is 12 minutes of sending at a steady rate. With MCP it is 12 calls.

### 3. The mechanic to explain to the user, once

**A list attached to a running campaign feeds it continuously.** Add a contact to that
list tomorrow and the contact enters the campaign tomorrow, at step 1, without touching
the campaign. That is how you keep a campaign alive: you add to the list, never to the
campaign.

The consequences, all of which surprise people the first time:

- Deleting a contact from the list removes it from the campaigns using that list.
- A list attached to two campaigns feeds both. Someone would get both sequences.
- Excluding people is done with an exclusion list on the campaign, not by trimming the
  main list.
- `POST /advanced/campaign/contacts` with `{ "id": "<campaignId>", "contact": {...} }`
  does exist and pushes one contact straight into a campaign. Use it only for a one off
  addition: those contacts are not in a reusable list, so you cannot re-target them
  later without rebuilding them.

Say this out loud the first time you create a campaign for someone. It is the single
thing that makes the rest programmable.

### 4. Create the campaign

Email or multichannel:

```bash
curl -s -X POST https://api.emelia.io/advanced/campaigns \
  -H "Authorization: $EMELIA_API_KEY" -H "Content-Type: application/json" \
  -d '{"name":"Q4 SaaS founders"}'
# {"success":true,"campaignId":"6612f0a9b1c2d3e4f5a6b7c8"}
```

LinkedIn only campaign: `POST https://api.emelia.io/linkedin/campaigns` with the same
`{"name":"..."}` body; it returns the whole campaign object rather than just the id. With
MCP, `create_campaign` with `{ name }` does the same thing.

**The campaign is created empty**, with a default schedule and empty steps. `name` is
the only field that endpoint takes, but everything else is set right after, by API.

### 5. Push the steps, from campaign.json

`PATCH /advanced/campaigns/{campaignId}/steps` with the tree wrapped in an object:
`{"steps": { ... }}`, not an array. Read the campaign back first with
`GET /advanced/campaigns/{campaignId}` so you change what you mean to change, then push,
then read it back again and compare it to `outreach/campaign.json`.

The tree is a linked structure, not a list: it starts at a `START` node and each node
carries the next one, with `yes` and `no` branches on a condition. The five shipped
templates in `outreach-sequence` are the reference for what a valid tree looks like.

**Every PATCH on this API replaces the whole block, and there is no partial update.**
Not for steps, not for recipients, not for identities, not for settings. What you send
becomes the block, and what you leave out is gone. Sending only the step you wanted to
change deletes the rest of the sequence. Sending one list in `lists` detaches all the
others. So the only correct shape is read, modify, send back:

```
GET   /advanced/campaigns/{id}          the whole object
                                        change the one field, in the object you just read
PATCH /advanced/campaigns/{id}/steps    send the entire tree back
```

On a campaign that has already sent something, keep the `_id` of every step and every
version you are not changing: activities, per version statistics and each contact's
position in the sequence hang off those ids, and new ids restart people mid sequence.
The server generates ids that are missing, so a brand new tree can omit them entirely,
but an existing tree must keep the ones it has.

And a campaign that is `RUNNING` refuses every one of these calls with
`You must pause your campaign before updating it`. Pause, patch, start again.

**What goes in an email step, verbatim.** Subject and body are the carrier variables,
never the written text:

```
subject: {{email1subject}}
body:    <p>{{email1message}}</p><p></p><p>{{signature}}</p>
```

From step 2 the opt out link is appended, as a real anchor:

```
<p></p><p><a target="_blank" rel="noopener noreferrer" href="{{unsubscribe_link}}">Se désabonner</a></p>
```

The body is HTML. Paragraphs are `<p>`, an empty line is `<p></p>`, and a `\n` typed in
the body renders as nothing, which turns the whole email into one block.

**Inside a variable's value it is the opposite: a `\n` becomes a paragraph break.** The
sending engine converts `\n\n` to `</p><p></p><p>` and `\n` to `</p><p>` when it
substitutes a value. That is exactly why the carrier pattern works: you write the message
into `email1message` as plain text with ordinary line breaks, and it comes out as
paragraphs. Write HTML in the body, plain text with `\n` in the variable, and never the
other way round.

Variables are double braces. A name that does not resolve renders empty, silently, with
no error and no default, so the campaign sends "Bonjour ," rather than failing. Guarantee
the data instead of guarding the template: every variable a step uses must be filled on
every contact of the list, which is what the pre-flight below checks.

Only a fixed set of contact fields resolve at the root: `firstName`, `lastName`,
`fullName`, `email`, `secondaryEmail`, `phone`, `mobilePhone`, `jobTitle`, `seniority`,
`department`, `gender`, `age`, `language`, `linkedinUrlProfile`, `twitterUrl`, `country`,
`region`, `city`, `postalCode`, `address`, `timezone`, `yearsOfExperience`, `education`,
`bio` and `companyName`. Resolution then falls through to your custom variables, then to
the linked company, where `companyCity` and `companyCountry` reach the company's own
fields since the bare names belong to the contact. A field that exists on the contact but
is not in that list, `birthDate` or `skills` for instance, renders empty in a message
even though the API accepted it on import.

The shapes Emelia uses:

- `stepType` is one of `START`, `EMAIL`, `CONNECTION`, `MESSAGE`, `INMAIL`, `VISIT`,
  `LIKE`, `FOLLOW`, `AUDIO`, `TASK`, `API_CALL`, `CONDITION`, `END_OF_CAMPAIGN`. The
  LinkedIn ones carry no `LINKEDIN_` prefix, and there is no `WAIT` step: waiting is the
  `delay` of the next step.
- `delay` is `{ "amount": 3, "unit": "DAYS" }`, and `unit` is `DAYS`, `HOURS` or
  `MINUTES`. The delay is counted from the previous step, not from the start.
- A message step carries `versions`, one per A/B variant, each with `subject`, `message`
  and `disabled`.
- A `CONDITION` step branches on a field with an operator among `EQUAL`, `GREATER`,
  `LOWER`, `CONTAINS`, `IS_EMPTY`, `DOES_NOT_CONTAIN`, `DOES_NOT_EQUAL`, `IS_NOT_EMPTY`.

Four rules Emelia enforces when you press Launch, so check them now rather than there:

1. Every email step needs at least one active version.
2. Every active version needs content. An empty body fails, an image only body passes the
   check but see `outreach-deliverability` for why it should not.
3. **The first email of a branch needs a subject.** The following emails inherit the
   thread and can leave it empty, which is what makes a follow up land in the same thread.
4. A LinkedIn message step with an audio note needs the audio actually uploaded.

Variables, exactly as the engine resolves them:

- `{{firstName}}`, `{{lastName}}`, `{{fullName}}`, `{{email}}`, `{{phone}}`,
  `{{jobTitle}}`, `{{companyName}}`, `{{city}}`, `{{country}}`, `{{linkedinUrlProfile}}`
  and the rest of the contact fields, plus every custom key you loaded in section 2.
- `{{unsubscribe_link}}` renders the opt out URL and feeds the `List-Unsubscribe` header.
  Put it from step 2 onwards, not on step 1: the first touch stays as short as
  possible. Note the trade off, the `List-Unsubscribe` header is only set when the
  variable is in that step's body, so step 1 goes out without it.
- `{{SENDER}}` is not resolved by the sending engine and renders empty. Write your own
  name in the copy instead.
- Resolution order is contact field, then custom variable, then company field. A custom
  variable named `city` will never win over the contact's own `city`.

### 6. Cadence, sending accounts and recipients

Three more calls, all by API:

- `PATCH /advanced/campaigns/{id}/settings` with `{"settings": { ... }}`. Note that
  `trackLinks`, `trackOpens` and `blacklistUnsub` are **required** inside that object,
  so send them even when you are not changing them.
- `PATCH /advanced/campaigns/{id}/recipients` with `{"recipients": {"lists_id": [...]}}`
  and `excludedLists` when you have exclusions.
- `PATCH /advanced/campaigns/{id}/identities` with `{"identities": [...]}`, each entry
  carrying a `name` and at least one of `email` or `linkedin`, using the
  ids collected by `outreach-deliverability`.

The settings fields, with the values the product accepts:

| Setting | Accepted | What to set for cold outreach |
|---|---|---|
| `dailyEmailAdded` / `dailyEmailLimit` | 1 to 500 | The number from the deliverability ramp, per mailbox. Not 500. |
| `dailyLinkedinAdded` | 1 to 80 | 40 maximum when the sequence contains a connection request, 80 otherwise. Emelia rejects the launch above that. |
| `days` | 0 to 6 | Monday to Friday only |
| `start` / `end` | `HH:MM` | The recipient's working hours, not yours |
| `timeZone` | IANA name | The recipient's zone |
| `trackOpens` | boolean | Off. Apple already broke the number. |
| `trackLinks` | boolean | Off on a cold first touch |
| `blacklistUnsub` | boolean | On. An unsubscribe click blacklists the address account wide. |
| `ignoreAutoReplies` | boolean | On. Out of office answers stop counting as replies and stop stopping the sequence. |
| `excludeAlreadyMessaged` | boolean | On, unless you deliberately want a second campaign to reach the same people |
| `eventToStop` | list of events | At minimum the reply events, so a person who answers stops receiving follow ups |
| `bcc` | address | Your CRM dropbox if you have one |

**Sending accounts** are called identities: one email mailbox, optionally paired with a
LinkedIn account. Attach as many as the ramp plan requires. Every identity must have an
email provider attached when the campaign has an email step, and a campaign with a
LinkedIn step needs either one shared LinkedIn account or one per identity.

Get the real identifiers rather than guessing them:

| What you need | Where it comes from |
|---|---|
| Email mailbox id | `GET /email-providers`, field `_id` on each provider |
| LinkedIn account id | `GET /linkedin-scrappers/authes`, field `_id`, only entries whose `status` is `valid` |
| Tracking domain status | `GET /domains`, a domain counts only when its `status` is `OK` |

`outreach-deliverability` already collects all three when it runs, so read its output
before calling these again. The LinkedIn response also carries a live session token:
read the id and the status, and never print or store the rest.

Then `PATCH /advanced/campaigns/{id}/identities` with `{"identities": [...]}`, where
each entry carries a `name` and at least one of `email` or `linkedin`.

**Recipients**: attach the list from section 1. Confirm the contact count Emelia shows
matches the rows you loaded. A campaign is capped at 15,000 recipients.

### 7. Pre-flight, all of it, before you ask anything

| Check | How | Pass condition |
|---|---|---|
| Deliverability | `## Verdict` in `outreach/deliverability.md` | READY, or READY WITH LIMITS and the cadence set to that cap |
| List verified | the verification column in `outreach/leads.csv` | every row verified, invalid rows removed |
| Unsubscribe | grep the copy | `{{unsubscribe_link}}` present from step 2 onwards, as a link and not a bare variable |
| Variables resolved | count blanks per variable across the CSV | 0 blanks, or a fallback written into the copy |
| Test email | send one from the campaign to your own address | received, read on a phone, every variable filled, links working |
| Subject on step 1 | `GET /advanced/campaigns/{id}` | not empty |
| Body is HTML | `GET /advanced/campaigns/{id}` | every step body contains `<p>`, and no raw `\n` |
| Variable syntax | `GET /advanced/campaigns/{id}` | only `{{name}}`, no `{#`, no `|`, no `default:` |
| Carrier columns | `get_list_contacts` on one row | every `emailNsubject` and `emailNmessage` the steps reference exists and is filled |
| Greeting | one rendered sample | the message opens with a greeting, not with the first sentence |
| Subscription | Emelia account | active, the product refuses to start a campaign without one |
| Identities | `GET /advanced/campaigns/{id}` | at least one, none disconnected or expired |
| Recipients | `get_campaign` | above 0, at most 15,000, and at least one contact reachable on each channel the sequence uses |
| Schedule | `GET /advanced/campaigns/{id}` | set, with days and hours |

A blank variable is the most common way a good campaign embarrasses someone. Count them
per variable and show the count. If `{{icebreaker}}` is empty on 34 rows, either write
those 34 or cut them from this campaign.

### 8. Ask, then launch

Show the summary and stop:

```
Campaign     Q4 SaaS founders (6612f0a9b1c2d3e4f5a6b7c8)
List         Q4 SaaS founders (65f1a2b3c4d5e6f7a8b9c0d1), 1,139 contacts loaded, 41 rejected
Sequence     3 steps (2 emails, 1 LinkedIn visit), 4 days end to end
Mailboxes    paul@get-acme.com, lea@get-acme.com
Cadence      20 per mailbox per day, Mon to Fri, 09:00 to 17:00 Europe/Paris
First send   tomorrow 09:00
Ends around  2026-04-24
Tracking     opens off, links off, unsubscribe link present in both email steps

Launch? This sends real email to 1,139 people.
```

Wait for an explicit yes. Not "ok next", not silence. Then the user presses Launch in the
app: the API does not expose starting a campaign. Confirm it took with `get_campaign` and
check that `status` is `RUNNING`. Then update `outreach/campaign.json` with the real
identifiers before you report back.

## Output

`outreach/campaign.json`, enriched in place. The `emelia` block is what the later skills
read.

```json
{
  "name": "Q4 SaaS founders",
  "channel": "email",
  "emelia": {
    "campaignId": "6612f0a9b1c2d3e4f5a6b7c8",
    "listId": "65f1a2b3c4d5e6f7a8b9c0d1",
    "status": "RUNNING",
    "startedAt": "2026-03-13T08:00:00.000Z",
    "identities": ["paul@get-acme.com", "lea@get-acme.com"]
  },
  "contacts": { "loaded": 1139, "duplicates": 12, "failed": 41, "source": "outreach/leads.csv" },
  "schedule": {
    "dailyEmailAdded": 20,
    "days": [1, 2, 3, 4, 5],
    "start": "09:00",
    "end": "17:00",
    "timeZone": "Europe/Paris",
    "trackOpens": false,
    "trackLinks": false,
    "blacklistUnsub": true,
    "ignoreAutoReplies": true
  },
  "steps": [
    { "stepType": "EMAIL", "delay": { "amount": 0, "unit": "DAYS" },
      "versions": [{ "subject": "{{companyName}} + Postgres 16", "message": "Hi {{firstName}}, ..." }] },
    { "stepType": "EMAIL", "delay": { "amount": 3, "unit": "DAYS" },
      "versions": [{ "subject": "", "message": "Following up, {{firstName}}. ... {{unsubscribe_link}}" }] },
    { "stepType": "VISIT", "delay": { "amount": 1, "unit": "DAYS" }, "versions": [] }
  ],
  "preflight": {
    "deliverability": "READY WITH LIMITS",
    "listVerified": true,
    "blankVariables": { "icebreaker": 0, "companyName": 0 },
    "testEmailSentTo": "paul@get-acme.com",
    "confirmedBy": "user, 2026-03-12T18:41:00Z"
  }
}
```

## Checks before finishing

- `campaignId` and `listId` are real values returned by the API, never placeholders.
- The contact count Emelia reports matches the rows you loaded, or the difference is
  explained in `contacts.failed` and `contacts.duplicates`.
- The deliverability verdict is recorded in the file, with the date it was produced.
- Every pre-flight row passed, and the failures were fixed rather than waived.
- The launch confirmation is recorded with a timestamp. No confirmation means no launch,
  and the file says `status: "DRAFT"`.
- The user has been told, in words, that adding to the list is how they add to the
  campaign from now on.

## Failure modes

- **The campaign shows 0 recipients after you attached the list.** Emelia materialises the
  recipients asynchronously; `recipients.processing` is true while it does. Wait and read
  `get_campaign` again before doing anything else.
- **"none of your contacts has an email address".** The column mapping is wrong: the CSV
  column was loaded into a custom variable instead of `email`. Check one contact with
  `get_list_contacts` using `{ listId, email: "..." }` and fix the keys, then reload.
- **"You cannot have more than 15,000 recipients".** Split into several campaigns by
  segment. Do not trim the list at random.
- **"Your email provider has been disconnected".** Reconnect it in the app. It is not
  something the API can do, and the campaign will not start until it is done.
- **"You must have a subscription to start a campaign".** The account is on trial or
  expired. Everything up to the launch still works, so finish the setup and say what is
  blocking.
- **The LinkedIn cadence is rejected.** The cap drops from 80 to 40 as soon as a
  connection request exists in the sequence, and it is re-checked at launch. Lower the
  number, do not remove the step.
- **A rate limit error while loading contacts.** Stop, wait a minute, resume at the row
  that failed. Do not restart the batch: the rows already loaded would come back as
  duplicates.
- **The test email arrives with `{{firstName}}` in it.** The variable name in the copy does
  not match a key on the contact. Compare them character by character, they are case
  sensitive.

## Limits

This skill does not write the copy and does not judge whether the sequence is any good.
It cannot create the steps, the schedule or the sending accounts through the API, and it
cannot press Launch for you: those happen once in the Emelia app, and the skill tells you
exactly what to set there. It does not verify email addresses (`outreach-verify` does),
does not create A/B variants through the API. It will
not launch on a BLOCKED verdict, on an unverified list, or without an explicit yes, and
no phrasing of the request changes that.
