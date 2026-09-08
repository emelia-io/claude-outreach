---
name: outreach-sequence
description: "Designs the multichannel flow of a campaign: which steps exist in Emelia (email, LinkedIn visit, invitation, message, InMail, manual call task), how conditions and branches work (invitation accepted, email opened, link clicked, reply received, unsubscribed, task done), the delays that work and why, a clean A/B test with a sample size that makes the result mean something, and the conditions that stop a contact or stop the campaign. Produces outreach/campaign.json, the spec that outreach-campaign turns into a real campaign. Triggers on: sequence, flow, cadence, steps, multichannel, multicanal, delays, wait, condition, branch, if accepted, A/B test, split test, variant, sample size, stop condition, stop the sequence, campaign design, campaign structure, LinkedIn plus email."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Design the sequence flow

## What this does

Turns approved copy into a step tree: which channel touches the prospect, in which
order, after how long, under which condition, and when the whole thing stops. It writes
`outreach/campaign.json`, which is both the spec `outreach-campaign` consumes and the
build sheet a human follows in the Emelia app.

## When to use it

Use it after [outreach-write](../outreach-write/SKILL.md) has produced approved copy,
and before anything is created in Emelia. Use it again when a campaign runs and one step is
carrying it: cutting a step is a flow decision, not a copy decision.

Use a different skill when: you are writing the text of the steps
([outreach-write](../outreach-write/SKILL.md)), filling variables per contact
([outreach-personalize](../outreach-personalize/SKILL.md)), or checking whether the
mailboxes can carry the volume this schedule implies (`outreach-deliverability`).

## Inputs

| Input | Where it comes from | If it is missing |
|---|---|---|
| The copy, step by step | `outreach/sequence.md` | Stop, design a flow around copy that exists |
| Contact count and segments | `outreach/leads.csv` | Ask, the count drives the A/B decision |
| Sending identities | the user, or `list_email_providers` on the MCP server | Ask for the mailbox addresses and the LinkedIn account |
| Channels the user actually has | the user | Email only is a valid design, say so and drop the LinkedIn steps |
| Timezone of the recipients | `outreach/icp.json` or the user | Default `Europe/Paris` for a French list and say you defaulted |

Read the honest constraint first, and tell the user before designing: **the API creates
a campaign name and nothing else.** `POST /advanced/campaigns` takes `name`. The step
tree, the schedule and the sending accounts are built once in the Emelia app. This file
is what makes that build fast and repeatable, and after it exists the skills feed the
attached list, so every contact added enters the running campaign on its own.

## How to do it

### 1. The steps that exist

These are Emelia's real step types. Use these exact values in `campaign.json`.

| `stepType` | Channel | Needs | Notes |
|---|---|---|---|
| `START` | none | nothing | The entry point, always the root, `delay` 0 |
| `EMAIL` | email | an email identity, `versions[].subject` and `versions[].message` | Leave the subject empty to stay in the thread: Emelia reuses the last subject, prefixes it with `Re: `, and quotes the history underneath |
| `VISIT` | LinkedIn | a LinkedIn identity | A profile view. Costs nothing, notifies the prospect, warms an invitation |
| `CONNECTION` | LinkedIn | a LinkedIn identity | The invitation. `versions[].message` is the note, and an empty note usually gets accepted more often than a pitched one |
| `MESSAGE` | LinkedIn | an accepted connection | The direct message. Useless before an acceptance |
| `INMAIL` | LinkedIn | InMail credits on the account | Paid, use it on the rows the invitation did not reach |
| `LIKE`, `FOLLOW` | LinkedIn | a LinkedIn identity | Light touches, low value on their own, fine as a warm up |
| `AUDIO` | LinkedIn | a LinkedIn identity | A voice note. High reply rate, does not scale, keep it for a short list |
| `WHATSAPP` | WhatsApp | a connected number | Only where the market expects it |
| `TASK` | human | nothing | The manual step, and this is the call step. Its name is `versions[0].subject` |
| `CONDITION` | none | `conditions` plus `yes` and `no` | The branch, see below |
| `API_CALL` | none | a URL | Fires a webhook, use it to write into your CRM |
| `END_OF_CAMPAIGN` | none | nothing | Ends the sequence for this contact |
| `WAIT` | none | nothing | A pure delay. Rarely needed, every step already carries its own `delay` |

Every step carries `_id`, `stepType`, `identities`, `delay` and a link to what comes
next. The tree is chained through `next`, and a `CONDITION` chains through `yes` and
`no` instead.

The manual call task is worth its own line. A `TASK` step parks the contact and shows
up in the Emelia app as a pending task with the name you gave it. When the MCP server
is configured, `list_manual_tasks` lists them and `complete_manual_task` closes one
with `ok` or `ko`. Write the task name as an instruction, not a label: "Call the
mobile, ask who owns response monitoring" beats "Call".

### 2. Conditions and branches

A `CONDITION` step holds `conditions` with three fields, plus a `yes` branch and a `no`
branch:

```json
{ "field": "ACCEPTED", "operator": "EQUAL", "value": "true" }
```

There are two families.

**Activity conditions.** The field is an event name in capitals and the value is
`"true"`. Available: `ACCEPTED`, `MAIL_REPLIED`, `LINKEDIN_REPLIED`, `OPENED`,
`CLICKED`, `UNSUBSCRIBED`, `BOUNCED`, `TASK_COMPLETED`.

**Contact field conditions.** The field starts with a dollar sign and names a contact
field or a custom variable, for example `$jobTitle` or `$icebreaker`. Operators:
`EQUAL`, `DOES_NOT_EQUAL`, `GREATER`, `LOWER`, `CONTAINS`, `DOES_NOT_CONTAIN`,
`IS_EMPTY`, `IS_NOT_EMPTY`. This is how you route rows that have an icebreaker down one
path and rows that do not down another.

**The trap that catches everyone: the condition's `delay` is the waiting window, and it
counts from the originating action, not from the condition.** Each activity has an
originating action: `ACCEPTED` counts from the invitation, `MAIL_REPLIED`, `OPENED`,
`CLICKED`, `UNSUBSCRIBED` and `BOUNCED` count from the send, `LINKEDIN_REPLIED` counts
from the message or InMail, `TASK_COMPLETED` counts from the task. Until that window
expires, the contact sits pending and nothing else happens to them. So a 7 day window
on "invitation accepted" holds every unaccepted contact for 7 days before the `no`
branch runs. Choose the window as the amount of time you are willing to lose, not as a
generous guess.

Two more mechanical facts: a `delay.amount` of zero or less is treated as one unit, and
a `TASK_COMPLETED` condition is forced to a 30 day window whatever you write.

**Do not branch on `OPENED`.** Apple Mail Privacy Protection pre-fetches images, so a
recorded open does not mean a human read anything, and a contact who never saw your
email will take the "opened" branch. Branch on `CLICKED`, on a reply, on `ACCEPTED`, or
on a contact field. This is also why `trackOpens` is set to `false` in the schedule
below: an inflated open rate is worse than no open rate, because it hides the truth
from `outreach-analyze`.

**Branches never rejoin.** The tree has no merge. Anything that must happen after both
arms has to be written twice, once in each arm. Keep branches short for that reason.

Branches worth building, in order of usefulness:

1. Invitation accepted or not: LinkedIn message on `yes`, email follow-up on `no`.
2. Call task done or not: on `ko` the contact goes back into the email path.
3. Clicked but no reply: change the ask, not the angle. They are interested and the
   question was wrong.
4. Bounced: end the campaign for that contact, and blacklist the domain if several rows
   from it bounce.
5. Icebreaker empty or not, when the copy has an opener that only works with one.

### 3. Delays that work, and why

| Between | Delay | Why |
|---|---|---|
| Email 1 and email 2 | 3 business days | Under 2 days the first is often still unread. Past 5 it has left the first screen |
| Email 2 and email 3 | 4 to 5 business days | Long enough to be a new conversation, short enough to be remembered |
| Email 3 and the break-up | 6 to 8 business days | The break-up works because time passed |
| Profile visit and invitation | 12 to 24 hours | The view must register before the invitation, or it looks like one automated burst |
| Invitation accepted and first message | at least 24 hours | Messaging within minutes of an acceptance reads as a bot, and it is the fastest way to get reported |
| Any LinkedIn action and the next one | 1 day minimum | LinkedIn rate limits per account, not per campaign |

A four step email sequence therefore spans 14 to 21 calendar days. Longer sequences do
not earn more meetings, they earn unsubscribes.

The unit is `MINUTES`, `HOURS` or `DAYS`, and the delay is spent against the campaign's
open days and hours: a 3 `DAYS` delay on a Monday to Friday schedule lands on the next
open day, not on a Saturday.

Schedule fields and their defaults in Emelia, so you know what you are changing:

| Field | Default | What to do |
|---|---|---|
| `timeZone` | `Europe/Brussels` | Set it to the recipients' timezone, not yours |
| `days` | `[0,1,2,3,4]` where 0 is Monday | Keep Monday to Friday |
| `start`, `end` | `08:00` and `17:00` | Match a working day in the recipients' timezone |
| `dailyEmailAdded` | 20 | New contacts entering the email track each day. This is the ramp dial |
| `dailyEmailLimit` | 500 | All emails sent per day, follow-ups included. Set it from what the mailboxes can carry, which `outreach-deliverability` decides |
| `dailyLinkedinAdded` | 20 | New contacts entering the LinkedIn track each day |
| `trackOpens` | true | Turn it off unless you need it: it adds a pixel to a cold email and the number it produces cannot be trusted |
| `trackLinks` | true | Leave on if you need click data, and accept that your links become redirects |
| `excludeAlreadyMessaged` | off | Turn it on whenever the list overlaps a previous campaign |
| `ignoreAutoReplies` | false | Turn it on, otherwise every out of office counts as a reply and stops the contact |
| `eventToStop` | empty | See section 5 |

On LinkedIn volume: keep new invitations well under the platform's weekly ceiling. A
widely used rule of thumb is around 100 invitations per week on an established account,
and far less on a new one, so 15 to 20 a day established and 5 to 10 a day on a young
account. That is a rule of thumb, not a documented limit, and the cost of being wrong
is the account.

### 4. A clean A/B test

**The mechanism.** A message step holds `versions`, an array. Each version has its own
`_id`, `subject`, `message` and `disabled` flag. Emelia splits the contacts across the
enabled versions, and the activity feed accepts a `versionId` filter, so results are
attributable per version. Spintax is not: do not confuse the two.

**One variable at a time.** If A and B differ in the subject and the body, a win tells
you nothing you can reuse. Test in this order, because this is the order of effect
size: the angle, then the ask, then the proof, then the subject, then the send time.

**Sample size, so the result means something.** These are the contacts needed per
version to detect a difference at the usual 95% confidence and 80% power. They come
from the standard two proportion formula, not from anyone's dashboard.

| Difference you want to detect | Contacts per version |
|---|---|
| 5% against 6% replies | about 8,200 |
| 5% against 7% replies | about 2,200 |
| 5% against 10% replies | about 435 |
| 3% against 6% replies | about 750 |
| 50% against 55% opens | about 1,600 |
| 50% against 60% opens | about 390 |

Read the top row again: on a list of 1,000 you cannot detect a one point difference in
reply rate, and no amount of staring at the dashboard changes that. So on a small list,
either test something big enough to move the rate by half again, or do not run a test:
run one version, call it a learning campaign, and say so.

**Duration.** Cold email replies mostly arrive within the first 3 business days after a
send. Do not read a step's result until every contact in the test has had at least 5
business days past that step. A step 1 test is not final until the follow-ups have run,
because a weak first email can be rescued by the second.

**No peeking.** Write the sample size and the metric into `campaign.json` before the
launch and hold to them. Checking a 5% base rate repeatedly and stopping at the first
gap produces a "winner" by chance often enough that the habit is worse than not testing.

**The metric is replies, then positive replies.** Not opens, for the Apple reason above.

### 5. Stop conditions

Two layers. The first is Emelia's, in `schedule.eventToStop`: the events that take a
contact out of the campaign. A sane default for email plus LinkedIn is
`["MAIL_REPLIED", "LINKEDIN_REPLIED", "UNSUBSCRIBED", "BOUNCED"]`. Add `CLICKED` only
when a click means a human takes over. Never add `OPENED`.

The second layer is yours, and it stops the campaign rather than a contact. Write these
into `stop_rules` and check them in `outreach-analyze`:

| Signal | Threshold | What you do |
|---|---|---|
| Bounce rate on a running campaign | above 3% | Pause. The list was not verified properly, and every further send costs reputation |
| Unsubscribe rate | above 1.5% | Pause. This is a targeting problem, not a copy problem |
| Reply rate after 300 sends | under 1% | Pause. The offer or the segment is wrong, and a fourth variant will not fix it |
| Spam complaints | any | Stop. This is the domain, not the campaign |
| A step producing more unsubscribes than replies | any | Cut that step |

### 6. Write the file, then hand over the build sheet

Write `outreach/campaign.json`, then print the step tree as an indented list in the
conversation, with the delays, so the user can build it in the app in one pass. Say the
three things that are easy to get wrong there: the timezone, `dailyEmailAdded`, and the
condition windows.

Nothing is created in Emelia by this skill. `outreach-campaign` does that, and it asks
before it does.

## Output

`outreach/campaign.json`. Everything under `schedule` and `steps` uses Emelia's own
field names and values, so it can be read straight into the app or into a future API.
The blocks outside them (`goal`, `ab_test`, `stop_rules`, `emelia`) are this
repository's, and carry the decisions the platform does not store.

```json
{
  "spec_version": "1",
  "name": "FR SaaS CTOs, response monitoring, Q4",
  "copy_source": "outreach/sequence.md",
  "list_source": "outreach/leads.csv",
  "channels": ["email", "linkedin", "call"],
  "goal": { "metric": "replies", "target_rate": 0.05, "contacts": 1000 },
  "identities": ["niels@emelia.io", "linkedin:niels-mathieu"],
  "recipients": {
    "list_name": "FR SaaS CTOs Q4",
    "lists": [],
    "excludedLists": ["Customers", "Open opportunities"]
  },
  "schedule": {
    "timeZone": "Europe/Paris",
    "days": [0, 1, 2, 3, 4],
    "start": "08:30",
    "end": "17:30",
    "dailyEmailAdded": 30,
    "dailyEmailLimit": 200,
    "dailyLinkedinAdded": 15,
    "trackOpens": false,
    "trackLinks": true,
    "excludeAlreadyMessaged": true,
    "ignoreAutoReplies": true,
    "eventToStop": ["MAIL_REPLIED", "LINKEDIN_REPLIED", "UNSUBSCRIBED", "BOUNCED"]
  },
  "steps": {
    "_id": "START",
    "stepType": "START",
    "identities": [],
    "delay": { "amount": 0, "unit": "DAYS" },
    "next": {
      "_id": "s1-email",
      "stepType": "EMAIL",
      "identities": ["niels@emelia.io"],
      "delay": { "amount": 0, "unit": "DAYS" },
      "versions": [
        { "_id": "v-a", "subject": "status page vs reality", "message": "sequence.md step 1, variant A", "disabled": false },
        { "_id": "v-b", "subject": "status page vs reality", "message": "sequence.md step 1, variant B", "disabled": false }
      ],
      "next": {
        "_id": "s2-visit",
        "stepType": "VISIT",
        "identities": ["linkedin:niels-mathieu"],
        "delay": { "amount": 1, "unit": "DAYS" },
        "next": {
          "_id": "s3-invite",
          "stepType": "CONNECTION",
          "identities": ["linkedin:niels-mathieu"],
          "delay": { "amount": 1, "unit": "DAYS" },
          "versions": [{ "_id": "v-invite", "message": "" }],
          "next": {
            "_id": "s4-accepted",
            "stepType": "CONDITION",
            "identities": [],
            "delay": { "amount": 5, "unit": "DAYS" },
            "conditions": { "field": "ACCEPTED", "operator": "EQUAL", "value": "true" },
            "yes": {
              "_id": "s5-dm",
              "stepType": "MESSAGE",
              "identities": ["linkedin:niels-mathieu"],
              "delay": { "amount": 1, "unit": "DAYS" },
              "versions": [{ "_id": "v-dm", "message": "sequence.md step 2, LinkedIn wording" }]
            },
            "no": {
              "_id": "s6-email2",
              "stepType": "EMAIL",
              "identities": ["niels@emelia.io"],
              "delay": { "amount": 3, "unit": "DAYS" },
              "versions": [{ "_id": "v-s2", "subject": "", "message": "sequence.md step 2" }],
              "next": {
                "_id": "s7-email3",
                "stepType": "EMAIL",
                "identities": ["niels@emelia.io"],
                "delay": { "amount": 5, "unit": "DAYS" },
                "versions": [{ "_id": "v-s3", "subject": "who gets paged", "message": "sequence.md step 3" }],
                "next": {
                  "_id": "s8-clicked",
                  "stepType": "CONDITION",
                  "identities": [],
                  "delay": { "amount": 3, "unit": "DAYS" },
                  "conditions": { "field": "CLICKED", "operator": "EQUAL", "value": "true" },
                  "yes": {
                    "_id": "s9-call",
                    "stepType": "TASK",
                    "identities": [],
                    "delay": { "amount": 1, "unit": "DAYS" },
                    "versions": [{ "_id": "v-task", "subject": "Call the mobile, ask who owns response monitoring" }]
                  },
                  "no": {
                    "_id": "s10-breakup",
                    "stepType": "EMAIL",
                    "identities": ["niels@emelia.io"],
                    "delay": { "amount": 7, "unit": "DAYS" },
                    "versions": [{ "_id": "v-s4", "subject": "", "message": "sequence.md step 4" }],
                    "next": {
                      "_id": "s11-end",
                      "stepType": "END_OF_CAMPAIGN",
                      "identities": [],
                      "delay": { "amount": 0, "unit": "DAYS" }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  },
  "ab_test": {
    "step_id": "s1-email",
    "variable": "the ask",
    "versions": { "v-a": "question about ownership", "v-b": "interest based, the two minute version" },
    "metric": "replies",
    "min_contacts_per_version": 435,
    "min_days_after_last_entry": 5,
    "decision_rule": "read it only when both versions have 435 contacts and 5 quiet days, then take the higher reply rate. No peeking before that."
  },
  "stop_rules": {
    "bounce_rate_above": 0.03,
    "unsubscribe_rate_above": 0.015,
    "reply_rate_below_after_300_sends": 0.01,
    "spam_complaints_above": 0,
    "action": "pause and report, do not continue"
  },
  "emelia": {
    "campaignId": null,
    "listId": null,
    "status": "draft",
    "built_in_app": false,
    "note": "POST /advanced/campaigns creates the name only. The tree above is the build sheet for the Emelia app. outreach-campaign creates the campaign and the list, then pushes contacts into the list, and each contact added enters the running campaign."
  }
}
```

In this example the accepted branch deliberately ends after the LinkedIn message: they
are a connection now, and the rest happens by hand. That is also the only honest way to
handle a branch, since branches never rejoin.

## Checks before finishing

- The file is valid JSON, the tree has exactly one `START` root, and every `_id` is
  unique.
- Every `stepType` is one of the values in the table, and every `CONDITION` has both a
  `yes` and a `no`.
- Every message step has at least one version with a non-empty `message`, and every
  `EMAIL` step that starts a new thread has a subject.
- Every step's copy exists in `outreach/sequence.md`, and no step references copy that
  was never written.
- The condition windows are deliberate, and you told the user how long each one parks a
  contact.
- `dailyEmailAdded` times the number of days is not larger than the list, and the daily
  volume matches what `outreach-deliverability` allows.
- `eventToStop` contains at least the replies, unsubscribes and bounces, and does not
  contain `OPENED`.
- If an A/B test is declared, `min_contacts_per_version` times the number of versions is
  at most the list size. If it is not, say the test is underpowered and offer to run one
  version instead.
- The user has seen the indented tree and said yes.

## Failure modes

**The flow is longer than the list can feed.** Ten steps over 30 days on 200 contacts
produces a trickle and no signal. Fewer steps on more contacts beats the opposite.

**The condition never fires and everyone is stuck.** The window was set on the
condition but counts from the originating action, and that action never happened for
those contacts: no invitation sent means no `ACCEPTED` to wait for. Check that the step
before the condition is the one that produces the originating event.

**The LinkedIn steps are designed and there is no LinkedIn account.** Ask before you
design, not after. Email only is a perfectly good sequence.

**Both A/B versions win, depending on the day.** That is what an underpowered test looks
like. Go back to the sample size table and either wait or stop calling it a test.

**The campaign is built in the app but contacts do not enter it.** They were added to a
list that is not the one attached to the campaign. Check the attached list id before
pushing anything.

**Opens look great and there are no replies.** If `trackOpens` was left on, part of that
number is Apple pre-fetching images. Turn it off, and read the reply rate instead.

## Limits

This skill does not create anything in Emelia and does not send anything: it writes a
file and a build sheet, and `outreach-campaign` does the rest with an explicit
confirmation. It cannot build the step tree through the API, because that endpoint does
not exist, and it will say so rather than pretending. It does not know your mailbox
capacity: the daily numbers here are proposals that `outreach-deliverability` has the
final word on. The delay and volume figures are rules of thumb from common practice, not
measurements from your account, and `outreach-analyze` is what replaces them with yours.
