---
name: outreach-sequence
description: "Designs the multichannel flow of a campaign, starting from one of Emelia's five real campaign templates (Pure Cold Email, Pure Linkedin basic, Pure Linkedin Premium with InMail, LinkedIn then Email, Email then LinkedIn) rather than from a blank tree, and picking the template mechanically from the email and LinkedIn coverage the enrichment actually produced. Then: which steps exist in Emelia (email, LinkedIn visit, invitation, message, InMail, manual call task), how conditions and branches work (invitation accepted, email bounced, link clicked, reply received, contact fields such as the email and the LinkedIn profile URL), the delays that work and why, a clean A/B test with a sample size that makes the result mean something, what goes in the body of an email step (the message or its custom variable, then the signature, then a real unsubscribe link from step 2 on), and the conditions that stop a contact or stop the campaign. Produces outreach/campaign.json, the spec that outreach-campaign turns into a real campaign. Triggers on: sequence, flow, cadence, steps, template, campaign template, which template, pure cold email, pure linkedin, linkedin then email, email then linkedin, smart multi channel, sales navigator, InMail, multichannel, multicanal, delays, wait, condition, branch, if accepted, if bounced, A/B test, split test, variant, variants, sample size, stop condition, stop the sequence, campaign design, campaign structure, LinkedIn plus email, unsubscribe link, opt out, signature, step body."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Design the sequence flow

## What this does

Turns approved copy into a step tree: which channel touches the prospect, in which
order, after how long, under which condition, and when the whole thing stops. It starts
from one of Emelia's five campaign templates, chosen from what the enrichment actually
found rather than from preference, then adapts it. It writes `outreach/campaign.json`,
which is both the spec `outreach-campaign` consumes and the build sheet a human follows
in the Emelia app.

## When to use it

Use it after [outreach-write](../outreach-write/SKILL.md) has produced approved copy,
and before anything is created in Emelia. Use it again when a campaign runs and one step is
carrying it: cutting a step is a flow decision, not a copy decision. Use it as well when
the only question is "which template do I pick", because the answer comes from the list
and section 1 computes it in one command.

Use a different skill when: you are writing the text of the steps
([outreach-write](../outreach-write/SKILL.md)), filling variables per contact
([outreach-personalize](../outreach-personalize/SKILL.md)), or checking whether the
mailboxes can carry the volume this schedule implies (`outreach-deliverability`).

## Inputs

| Input | Where it comes from | If it is missing |
|---|---|---|
| The copy, step by step | `outreach/sequence.md` | Stop, design a flow around copy that exists |
| Contact count and segments | `outreach/leads.csv` | Ask, the count drives the A/B decision |
| Email and LinkedIn coverage on the contactable rows | `outreach/leads.csv`, counted as in section 1 | Count it yourself, do not ask. It is what picks the template |
| Sending identities | the user, or `list_email_providers` on the MCP server | Ask for the mailbox addresses and the LinkedIn account |
| Channels the user actually has | the user | Email only is a valid design, say so and drop the LinkedIn steps |
| InMail credits on the LinkedIn seat | the user | Assume none, and cut the InMail step rather than designing a branch that cannot fire |
| Timezone of the recipients | `outreach/icp.json` or the user | Default `Europe/Paris` for a French list and say you defaulted |

Read the honest constraint first, and tell the user before designing: **the API creates
a campaign name and nothing else.** `POST /advanced/campaigns` takes `name`. The step
tree, the schedule and the sending accounts are built once in the Emelia app. This file
is what makes that build fast and repeatable, and after it exists the skills feed the
attached list, so every contact added enters the running campaign on its own.

The good news about that build: you do not do it from a blank canvas. Emelia offers five
campaign templates, section 1 says which one your list picks, and the tree it drops in is
most of the work. Everything after section 1 is how you adapt it.

## How to do it

### 1. Start from a template, not from a blank tree

**How long a sequence should be, before you look at any template.** On email, four or
five steps. On LinkedIn, one connection request and then **three messages at most**:
LinkedIn quotas cap your daily volume anyway, and someone who has not answered after
three is not going to answer at the fourth. Users will adjust afterwards, and that is
fine, but this is where you start.

**LinkedIn delays are longer than email delays, on purpose.** Not everyone lives on
LinkedIn. Someone who signs in once a fortnight must not open the app and find three
messages waiting, break-up included, because that reads as a machine and not as a
person. Treat the delays that come with the templates as a floor rather than a target,
and stretch them when the audience is one that checks LinkedIn rarely: founders of small
companies, technical roles, anyone outside sales and recruiting.

Emelia ships five campaign templates, and one of them is nearly always closer to the
right answer than a tree you invent. Their trees are reproduced in this
skill, delays and conditions already wired, so you build one by pushing it through
`PATCH /advanced/campaigns/{id}/steps` rather than by clicking. You then cut what you do not need, paste
the copy in, and record what you changed. Design from scratch only when none of the five
fits, and write the reason into `campaign.json`.

The five, as they are in the product on 9 September 2026. The `id` is what you write into
`campaign.json`, the name is what the app shows you.

| `id` | Name in the app | Channel | Shape | What it assumes you have |
|---|---|---|---|---|
| `pure-cold-email` | Pure Cold Email | Email only | 5 emails, 43 days | A verified address for everybody |
| `pure-linkedin` | Pure Linkedin (for basic account) | LinkedIn only | Invitation, message, message, like, message, 11 days | A profile URL for everybody, and no InMail credits |
| `linkedin-premium-or-sales-navigator` | Pure Linkedin (for Premium Account) | LinkedIn only | Invitation, then messages if accepted, InMail if not | A profile URL for everybody, plus Premium or Sales Navigator with InMail credits |
| `linkedin-email` | LinkedIn then Email | Multichannel | LinkedIn first, email later for the rows that have an address | A profile URL for everybody, an address for some |
| `smart-multi-channel` | Email then LinkedIn | Multichannel | Email first, LinkedIn later for the rows that have a profile | An address for everybody, a profile URL for some |

A template hands you the tree and nothing else. Every step comes back with empty
`versions` and empty `identities`, and every `_id` is regenerated, so the words are still
yours to write and the sending accounts still yours to attach.

#### The choice follows from the enrichment, not from taste

The template is decided by two numbers, and you can read both off `outreach/leads.csv`
once `outreach-enrich` has run. Count them on the rows you are actually going to contact,
which is `send_decision` equal to `send`.

```bash
python3 - <<'PY'
import csv
rows = [r for r in csv.DictReader(open('outreach/leads.csv'))
        if (r.get('send_decision') or 'send') == 'send']
n = len(rows) or 1
email = sum(1 for r in rows if r.get('email'))
li = sum(1 for r in rows if r.get('linkedin_url'))
print(f"{len(rows)} contactable rows, email {email} ({email/n:.0%}), "
      f"linkedin {li} ({li/n:.0%})")
PY
```

Read the two percentages into three bands. They are rules of thumb, not thresholds
measured on anything: **near everyone** above 90%, **some** between 40 and 90%, **few**
below 40%.

| Email coverage | LinkedIn coverage | Template | Why |
|---|---|---|---|
| Near everyone | Few | `pure-cold-email` | There is no second channel to switch to |
| Few | Near everyone, basic account | `pure-linkedin` | The invitation is the only door you have |
| Few | Near everyone, Premium or Sales Navigator | `linkedin-premium-or-sales-navigator` | The InMail is what reaches the rows that never accept |
| Some | Near everyone | `linkedin-email` | Start where everyone is, switch to email for the rows that have one |
| Near everyone | Some | `smart-multi-channel` | Start where everyone is, add LinkedIn for the rows that have a profile |
| Near everyone | Near everyone | either multichannel | Both work. Pick the channel this segment answers on, and write down which you picked and why |
| Few | Few | none | Go back to `outreach-enrich`. A list with no channel is not a campaign |

Say the numbers to the user before naming a template: "312 contactable rows, 96% have an
address, 41% have a LinkedIn profile, so this is Email then LinkedIn." That sentence is
the whole justification, and it also tells them what enrichment would have to improve for
a different template to become available.

#### `linkedin-email`, when LinkedIn is the channel everyone has

Use it when you have the profile URL of everybody and the address of only part of the
list. It opens on LinkedIn, because that is the channel that reaches the whole list, and
switches to email only for the contacts whose address exists. Both branches check
`$email` before they try to send one, so a row with no address never falls into a dead
email step: it either ends or gets an InMail.

```
START                                            day 0
CONNECTION            the invitation             +0
CONDITION   ACCEPTED == true                     window 5 days
  yes   MESSAGE                                  +1 hour
        MESSAGE                                  +5 days
        LIKE                                     +8 days
        MESSAGE                                  +1 hour
        CONDITION   $email IS_NOT_EMPTY          window 3 days
          yes   EMAIL                            +1 day
                EMAIL                            +5 days
                EMAIL                            +20 days
                END_OF_CAMPAIGN                  +1 day
          no    END_OF_CAMPAIGN                  +1 day
  no    CONDITION   $email IS_NOT_EMPTY          window 1 day
          yes   EMAIL                            +1 day
                EMAIL                            +5 days
                EMAIL                            +10 days
          no    INMAIL                           +1 day
```

Three things to notice. The accepted branch talks on LinkedIn for two weeks before it
touches email at all, so email is the second act, not a parallel channel. The InMail at
the bottom right is the only path for a contact who neither accepted nor has an address,
and it costs a credit, so cut that step if the account has none. And both arms end
explicitly, which is the template telling you that branches never rejoin.

Do not pick it when your LinkedIn coverage is partial: everyone whose profile URL is
missing sits at the first step with an invitation that cannot be sent. Coverage on
LinkedIn is what this template spends, so it has to be near total.

#### `smart-multi-channel`, when email is the channel everyone has

The mirror image, and it is the one to use when you have the address of everybody and the
profile of only part of the list. It opens on email, then adds LinkedIn for the rows whose
profile exists. It is also the only template that reads a bounce as a signal: a contact
whose first email bounced is routed to LinkedIn immediately rather than being sent three
more emails to an address that does not exist.

```
START                                                     day 0
EMAIL                 email 1                             +0
CONDITION   BOUNCED == true                               window 1 day
  yes   CONDITION   $linkedinUrlProfile IS_NOT_EMPTY      window 1 day
          yes   CONNECTION                                +1 day
                MESSAGE                                   +1 day
          no    nothing, the contact stops here
  no    EMAIL           email 2                           +1 day
        EMAIL           email 3                           +5 days
        CONDITION   $linkedinUrlProfile IS_EMPTY          window 1 day
          yes   EMAIL   email 4                           +1 day
          no    CONNECTION                                +2 days
                MESSAGE                                   +1 day
                MESSAGE                                   +5 days
```

Read the second condition carefully, because its polarity is the opposite of the first
one: it tests `IS_EMPTY`, so the `yes` branch is "no LinkedIn profile, send a fourth
email" and the `no` branch is "there is a profile, go to LinkedIn". Getting that backwards
sends your LinkedIn sequence to the rows that have no profile, and Emelia will not warn
you: the invitation simply never fires.

The `no` branch of the first condition is empty in the template. A contact whose email
bounced and who has no LinkedIn profile stops there, silently, with no
`END_OF_CAMPAIGN`. That is the correct outcome, but add the `END_OF_CAMPAIGN` yourself so
the report reads as a decision rather than as a step that failed.

Do not pick it when your email coverage is partial: the first step is an email, so every
row without an address is dead on arrival. If that is your list, you wanted
`linkedin-email`.

#### What the templates get right, and the five things to fix in them

1. **`pure-cold-email` ships five email steps.** [outreach-write](../outreach-write/SKILL.md)
   section 8 writes four and explains why a fifth mostly buys unsubscribes. Delete the
   last step, or decide deliberately to write a fifth and say so. Do not leave an empty
   step in the tree: an email step with no body is an email step that sends nothing and
   still counts as a touch in the stats.
2. **The condition windows park everybody.** The 5 day window on `ACCEPTED` in the three
   LinkedIn templates means every contact who has not accepted waits 5 days before the
   fallback runs. That is the design, and it is the right default, but say the number out
   loud: on a 500 row list nothing at all happens on the email side for the first week.
3. **The "~N days" on the template card is a label, not the span.** It is a hand written
   approximation in the product, and on the branching templates it understates. The real
   span is the sum of the delays along the branch a contact takes, condition windows
   included: the accepted arm of `linkedin-email` runs about 48 days, not 15. Compute the
   branch, do not repeat the card.
4. **The last message of `pure-linkedin` fires one minute after the like.** A like and a
   message landing in the same minute reads as one automated action, which is the thing
   section 5 says to avoid everywhere else. Raise it to a few hours unless you have a
   reason not to.
5. **The templates carry no stop conditions and no schedule.** They are a tree. The
   `eventToStop` list, the timezone, the daily volumes and the tracking flags are settings
   you still have to set, in section 5 and section 7 below.

#### The trap that decides whether the multichannel branches work at all

Both multichannel templates branch on contact fields, and those are Emelia's field names,
not your CSV headers:

| Condition field | Emelia contact field | What has to land in it |
|---|---|---|
| `$email` | `email` | the address from `outreach/leads.csv` |
| `$linkedinUrlProfile` | `linkedinUrlProfile` | the profile URL from `outreach/leads.csv` |

If the LinkedIn URL is imported into a custom field called `linkedin_url` or `linkedin`,
`$linkedinUrlProfile` is empty on every row. The condition then routes the whole list down
one branch, no error is raised, and you find out when the invitations never fire. Check
the mapping on the import screen, and check one contact in the app after the load, before
you start the campaign.

#### The `campaign.json` for each template

Same schema as the Output section below: these blocks give `template`, `channels` and
`steps`, and everything else in the file (`goal`, `identities`, `recipients`, `schedule`,
`ab_test`, `stop_rules`, `emelia`) is written as shown there. Keep the `template` field
even when you have edited the tree, and list what you changed in `template_changes`, so
six weeks later you can tell a deliberate cut from a mistake.

`pure-cold-email`:

```json
{
  "template": "pure-cold-email",
  "template_changes": ["dropped the fifth email, outreach-write writes four"],
  "channels": ["email"],
  "steps": {
    "_id": "START", "stepType": "START", "identities": [], "delay": {"amount": 0, "unit": "DAYS"},
    "next": {
      "_id": "e1", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 0, "unit": "DAYS"},
      "versions": [{"_id": "e1-v", "subject": "status page vs reality", "message": "sequence.md step 1, then {{signature}}, no opt out link", "disabled": false}],
      "next": {
        "_id": "e2", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 3, "unit": "DAYS"},
        "versions": [{"_id": "e2-v", "subject": "", "message": "sequence.md step 2, then {{signature}}, then the opt out anchor", "disabled": false}],
        "next": {
          "_id": "e3", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 5, "unit": "DAYS"},
          "versions": [{"_id": "e3-v", "subject": "who gets paged", "message": "sequence.md step 3, then {{signature}}, then the opt out anchor", "disabled": false}],
          "next": {
            "_id": "e4", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 10, "unit": "DAYS"},
            "versions": [{"_id": "e4-v", "subject": "", "message": "sequence.md step 4, the break up, then {{signature}}, then the opt out anchor", "disabled": false}]
          }
        }
      }
    }
  }
}
```

`pure-linkedin`:

```json
{
  "template": "pure-linkedin",
  "template_changes": ["last message moved from 1 minute after the like to 4 hours"],
  "channels": ["linkedin"],
  "steps": {
    "_id": "START", "stepType": "START", "identities": [], "delay": {"amount": 0, "unit": "DAYS"},
    "next": {
      "_id": "invite", "stepType": "CONNECTION", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 0, "unit": "DAYS"},
      "versions": [{"_id": "invite-v", "message": ""}],
      "next": {
        "_id": "dm1", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 1, "unit": "DAYS"},
        "versions": [{"_id": "dm1-v", "message": "sequence.md LinkedIn message 1"}],
        "next": {
          "_id": "dm2", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 3, "unit": "DAYS"},
          "versions": [{"_id": "dm2-v", "message": "sequence.md LinkedIn message 2"}],
          "next": {
            "_id": "like", "stepType": "LIKE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 7, "unit": "DAYS"},
            "next": {
              "_id": "dm3", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 4, "unit": "HOURS"},
              "versions": [{"_id": "dm3-v", "message": "sequence.md LinkedIn break up"}]
            }
          }
        }
      }
    }
  }
}
```

`linkedin-premium-or-sales-navigator`:

```json
{
  "template": "linkedin-premium-or-sales-navigator",
  "template_changes": [],
  "channels": ["linkedin"],
  "steps": {
    "_id": "START", "stepType": "START", "identities": [], "delay": {"amount": 0, "unit": "DAYS"},
    "next": {
      "_id": "invite", "stepType": "CONNECTION", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 0, "unit": "DAYS"},
      "versions": [{"_id": "invite-v", "message": ""}],
      "next": {
        "_id": "accepted", "stepType": "CONDITION", "identities": [], "delay": {"amount": 5, "unit": "DAYS"},
        "conditions": {"field": "ACCEPTED", "operator": "EQUAL", "value": "true"},
        "yes": {
          "_id": "dm1", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 2, "unit": "HOURS"},
          "versions": [{"_id": "dm1-v", "message": "sequence.md LinkedIn message 1"}],
          "next": {
            "_id": "dm2", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 5, "unit": "DAYS"},
            "versions": [{"_id": "dm2-v", "message": "sequence.md LinkedIn message 2"}],
            "next": {
              "_id": "dm3", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 10, "unit": "DAYS"},
              "versions": [{"_id": "dm3-v", "message": "sequence.md LinkedIn break up"}]
            }
          }
        },
        "no": {
          "_id": "inmail", "stepType": "INMAIL", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 1, "unit": "DAYS"},
          "versions": [{"_id": "inmail-v", "subject": "who owns response monitoring", "message": "sequence.md InMail body"}],
          "next": {
            "_id": "like", "stepType": "LIKE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 2, "unit": "DAYS"},
            "next": {
              "_id": "dm4", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 5, "unit": "DAYS"},
              "versions": [{"_id": "dm4-v", "message": "sequence.md LinkedIn last message"}]
            }
          }
        }
      }
    }
  }
}
```

`linkedin-email`:

```json
{
  "template": "linkedin-email",
  "template_changes": [
    "dropped the InMail, the account has no credits",
    "third message moved from 1 hour after the like to 4 hours"
  ],
  "channels": ["linkedin", "email"],
  "steps": {
    "_id": "START", "stepType": "START", "identities": [], "delay": {"amount": 0, "unit": "DAYS"},
    "next": {
      "_id": "invite", "stepType": "CONNECTION", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 0, "unit": "DAYS"},
      "versions": [{"_id": "invite-v", "message": ""}],
      "next": {
        "_id": "accepted", "stepType": "CONDITION", "identities": [], "delay": {"amount": 5, "unit": "DAYS"},
        "conditions": {"field": "ACCEPTED", "operator": "EQUAL", "value": "true"},
        "yes": {
          "_id": "dm1", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 1, "unit": "HOURS"},
          "versions": [{"_id": "dm1-v", "message": "sequence.md LinkedIn message 1"}],
          "next": {
            "_id": "dm2", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 5, "unit": "DAYS"},
            "versions": [{"_id": "dm2-v", "message": "sequence.md LinkedIn message 2"}],
            "next": {
              "_id": "like", "stepType": "LIKE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 8, "unit": "DAYS"},
              "next": {
                "_id": "dm3", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 4, "unit": "HOURS"},
                "versions": [{"_id": "dm3-v", "message": "sequence.md LinkedIn message 3"}],
                "next": {
                  "_id": "has-email-yes", "stepType": "CONDITION", "identities": [], "delay": {"amount": 3, "unit": "DAYS"},
                  "conditions": {"field": "$email", "operator": "IS_NOT_EMPTY", "value": ""},
                  "yes": {
                    "_id": "e1", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 1, "unit": "DAYS"},
                    "versions": [{"_id": "e1-v", "subject": "status page vs reality", "message": "sequence.md step 1, then {{signature}}, no opt out link", "disabled": false}],
                    "next": {
                      "_id": "e2", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 5, "unit": "DAYS"},
                      "versions": [{"_id": "e2-v", "subject": "", "message": "sequence.md step 2, then {{signature}}, then the opt out anchor", "disabled": false}],
                      "next": {
                        "_id": "e3", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 20, "unit": "DAYS"},
                        "versions": [{"_id": "e3-v", "subject": "", "message": "sequence.md step 3, then {{signature}}, then the opt out anchor", "disabled": false}],
                        "next": {"_id": "end1", "stepType": "END_OF_CAMPAIGN", "identities": [], "delay": {"amount": 1, "unit": "DAYS"}}
                      }
                    }
                  },
                  "no": {"_id": "end2", "stepType": "END_OF_CAMPAIGN", "identities": [], "delay": {"amount": 1, "unit": "DAYS"}}
                }
              }
            }
          }
        },
        "no": {
          "_id": "has-email-no", "stepType": "CONDITION", "identities": [], "delay": {"amount": 1, "unit": "DAYS"},
          "conditions": {"field": "$email", "operator": "IS_NOT_EMPTY", "value": ""},
          "yes": {
            "_id": "e4", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 1, "unit": "DAYS"},
            "versions": [{"_id": "e4-v", "subject": "status page vs reality", "message": "sequence.md step 1, then {{signature}}, no opt out link", "disabled": false}],
            "next": {
              "_id": "e5", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 5, "unit": "DAYS"},
              "versions": [{"_id": "e5-v", "subject": "", "message": "sequence.md step 2, then {{signature}}, then the opt out anchor", "disabled": false}],
              "next": {
                "_id": "e6", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 10, "unit": "DAYS"},
                "versions": [{"_id": "e6-v", "subject": "who gets paged", "message": "sequence.md step 3, then {{signature}}, then the opt out anchor", "disabled": false}],
                "next": {"_id": "end3", "stepType": "END_OF_CAMPAIGN", "identities": [], "delay": {"amount": 1, "unit": "DAYS"}}
              }
            }
          },
          "no": {"_id": "end4", "stepType": "END_OF_CAMPAIGN", "identities": [], "delay": {"amount": 1, "unit": "DAYS"}}
        }
      }
    }
  }
}
```

The InMail of the stock template sat where `end4` is. Keep it instead of the
`END_OF_CAMPAIGN` when the account has credits, as an `INMAIL` step with a
`versions[0].subject` and a `versions[0].message`.

`smart-multi-channel`:

```json
{
  "template": "smart-multi-channel",
  "template_changes": ["added END_OF_CAMPAIGN on the bounced with no profile branch"],
  "channels": ["email", "linkedin"],
  "steps": {
    "_id": "START", "stepType": "START", "identities": [], "delay": {"amount": 0, "unit": "DAYS"},
    "next": {
      "_id": "e1", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 0, "unit": "DAYS"},
      "versions": [{"_id": "e1-v", "subject": "status page vs reality", "message": "sequence.md step 1, then {{signature}}, no opt out link", "disabled": false}],
      "next": {
        "_id": "bounced", "stepType": "CONDITION", "identities": [], "delay": {"amount": 1, "unit": "DAYS"},
        "conditions": {"field": "BOUNCED", "operator": "EQUAL", "value": "true"},
        "yes": {
          "_id": "has-li", "stepType": "CONDITION", "identities": [], "delay": {"amount": 1, "unit": "DAYS"},
          "conditions": {"field": "$linkedinUrlProfile", "operator": "IS_NOT_EMPTY", "value": ""},
          "yes": {
            "_id": "invite1", "stepType": "CONNECTION", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 1, "unit": "DAYS"},
            "versions": [{"_id": "invite1-v", "message": ""}],
            "next": {
              "_id": "dm1", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 1, "unit": "DAYS"},
              "versions": [{"_id": "dm1-v", "message": "sequence.md LinkedIn message 1"}]
            }
          },
          "no": {"_id": "end1", "stepType": "END_OF_CAMPAIGN", "identities": [], "delay": {"amount": 0, "unit": "DAYS"}}
        },
        "no": {
          "_id": "e2", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 1, "unit": "DAYS"},
          "versions": [{"_id": "e2-v", "subject": "", "message": "sequence.md step 2, then {{signature}}, then the opt out anchor", "disabled": false}],
          "next": {
            "_id": "e3", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 5, "unit": "DAYS"},
            "versions": [{"_id": "e3-v", "subject": "who gets paged", "message": "sequence.md step 3, then {{signature}}, then the opt out anchor", "disabled": false}],
            "next": {
              "_id": "no-li", "stepType": "CONDITION", "identities": [], "delay": {"amount": 1, "unit": "DAYS"},
              "conditions": {"field": "$linkedinUrlProfile", "operator": "IS_EMPTY", "value": ""},
              "yes": {
                "_id": "e4", "stepType": "EMAIL", "identities": ["niels@emelia.io"], "delay": {"amount": 1, "unit": "DAYS"},
                "versions": [{"_id": "e4-v", "subject": "", "message": "sequence.md step 4, the break up, then {{signature}}, then the opt out anchor", "disabled": false}]
              },
              "no": {
                "_id": "invite2", "stepType": "CONNECTION", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 2, "unit": "DAYS"},
                "versions": [{"_id": "invite2-v", "message": ""}],
                "next": {
                  "_id": "dm2", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 1, "unit": "DAYS"},
                  "versions": [{"_id": "dm2-v", "message": "sequence.md LinkedIn message 1"}],
                  "next": {
                    "_id": "dm3", "stepType": "MESSAGE", "identities": ["linkedin:niels-mathieu"], "delay": {"amount": 5, "unit": "DAYS"},
                    "versions": [{"_id": "dm3-v", "message": "sequence.md LinkedIn message 2"}]
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

The LinkedIn steps in both multichannel trees carry the copy written by the LinkedIn
prompt, not the email copy translated. A LinkedIn message is unsigned, has no subject and
ends on a question:
[outreach-write](../outreach-write/SKILL.md) section 1, under "Mode A on LinkedIn".

### 2. The steps that exist

These are Emelia's real step types. Use these exact values in `campaign.json`.

| `stepType` | Channel | Needs | Notes |
|---|---|---|---|
| `START` | none | nothing | The entry point, always the root, `delay` 0 |
| `EMAIL` | email | an email identity, `versions[].subject` and `versions[].message` | `message` is the whole body, assembled as in section 4. Leave the subject empty to stay in the thread: Emelia reuses the last subject, prefixes it with `Re: `, and quotes the history underneath |
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

### 3. Conditions and branches

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
from `outreach-audit`.

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

### 4. What goes in the body of an email step

`versions[].message` is the whole body of that email, and it is three blocks separated by
a blank line, in this order. [outreach-write](../outreach-write/SKILL.md) section 10 has
the detail and the reasoning, this is the part the flow has to get right.

1. **The copy.** Either the written text (Mode B) or the custom variable that holds the
   message written for that contact (Mode A, usually `{{message}}`, and nothing else
   around it).
2. **`{{signature}}`**, on its own line. Lowercase only: `{{Signature}}` silently renders
   nothing. It pulls the signature of the identity that sends, so the same step signs
   correctly from every mailbox you attach.
3. **The opt out link**, from step 2 on, as a real anchor and never a bare variable:

```html
<p><a href="{{unsubscribe_link}}">Unsubscribe</a></p>
```

Four flow level consequences:

- **Step 1 carries no opt out link, every later email step does.** That is the default in
  this repository. The reasoning is in [outreach-write](../outreach-write/SKILL.md)
  section 10, along with what it costs and how to override it with `Opt-out: every step`.
  Record the choice in `campaign.json` under `opt_out` so `outreach-campaign` builds what
  you decided rather than what it assumes.
- **The opt out link is exempt from `trackLinks`.** Every other `href` is rewritten as a
  redirect. This one keeps its own URL, so it does not spend the one link a step is
  allowed and it does not look like a redirect to a filter.
- **`{{unsubscribe_link}}` is what sets the `List-Unsubscribe` header**, per step. A step
  without the variable goes out without the header, which is exactly what the step 1 rule
  means in practice. Say that to the user rather than letting them find out.
- **Every A/B version of a step needs all three blocks.** Versions are separate bodies:
  a signature or an opt out link added to version A only is a bug you will read as a
  result.

### 5. Delays that work, and why

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
| `eventToStop` | empty | See section 7 |

On LinkedIn volume: keep new invitations well under the platform's weekly ceiling. A
widely used rule of thumb is around 100 invitations per week on an established account,
and far less on a new one, so 15 to 20 a day established and 5 to 10 a day on a young
account. That is a rule of thumb, not a documented limit, and the cost of being wrong
is the account.

Emelia draws the same line in its own cadence screen, and the thresholds are worth
knowing because you will see them: with an invitation step in the tree,
`dailyLinkedinAdded` above 20 raises a warning and above 40 an error; without one, so a
LinkedIn track made of visits, likes and messages only, the warning starts at 40; above
80 it is an error whatever the tree contains. Read that as the product's own opinion of
what is safe, and treat 20 a day with invitations as the ceiling rather than the target.

### 6. A clean A/B test

**Email only. There is no A/B test on LinkedIn, and getting this wrong sends every
variant to the same person.** The product uses the same `versions` array on both, for
two opposite behaviours, verified in the sending code on 9 September 2026:

| Step | What `versions` means | What the sender does |
|---|---|---|
| `EMAIL` | A/B variants | The job carries one `versionId`. Each contact receives **one** version |
| `MESSAGE` on LinkedIn | Sub-messages | The sender loops over **every** version and sends them **all**, 3.5 to 6.2 seconds apart |

Sub-messages exist to look like someone typing in several goes. So three "variants" on a
LinkedIn step means one person receives three messages back to back, in about fifteen
seconds. Never put variants on a LinkedIn step.

When a user asks for an A/B test on LinkedIn, explain rather than refuse flatly: a test
only says something with volume. On email you send a thousand a day, so two hundred per
variant, and after a few days a gap means something. On LinkedIn the quotas put you at a
handful of touches a day, and comparing five people to five people measures noise, not
copy. Test on email, then carry what wins over to LinkedIn.

**The mechanism, on email.** An email step holds `versions`, an array. Each version has
its own `_id`, `subject`, `message` and `disabled` flag. Emelia splits the contacts
across the enabled versions, and the activity feed accepts a `versionId` filter, so
results are attributable per version. Spintax is not: do not confuse the two.

**Up to five variants.** Two is the usual case, five is the ceiling worth running. More
variants means more angles tested at once, which is the right move in exactly two
situations: you have no per row data so personalization is off the table, and you have
so much volume that writing one message per contact would cost more than it returns.
Nobody writes a hundred thousand personalized emails. Five angles across a hundred
thousand contacts, on the other hand, teaches you which one to keep. You can also split
variants by company size rather than at random, and read each band separately.

**Test approaches, not synonyms.** Two versions that say the same thing in different
words cost a full send and teach you nothing. A variant is worth running when a win
changes what you write next: a different angle, a different promise, a different ask, a
different kind of proof. The table of what to vary, and what a win in each case actually
tells you, is in [outreach-write](../outreach-write/SKILL.md) section 1, under "Mode B".
Write both versions there, and bring them here as `versions[]`.

**One variable at a time.** If A and B differ in the subject and the body, a win tells
you nothing you can reuse. Test in this order, because this is the order of effect
size: the angle, then the ask, then the proof, then the subject, then the send time.

**In Mode A there is no A/B test on the body.** Every contact gets a different message,
so there is nothing to hold constant and nothing to attribute. You can still test the
subject line, the delays or the channel mix. Say that rather than declaring a test that
cannot be read.

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

### 7. Stop conditions

Two layers. The first is Emelia's, in `schedule.eventToStop`: the events that take a
contact out of the campaign. A sane default for email plus LinkedIn is
`["MAIL_REPLIED", "LINKEDIN_REPLIED", "UNSUBSCRIBED", "BOUNCED"]`. Add `CLICKED` only
when a click means a human takes over. Never add `OPENED`.

The second layer is yours, and it stops the campaign rather than a contact. Write these
into `stop_rules` and check them in `outreach-audit`:

| Signal | Threshold | What you do |
|---|---|---|
| Bounce rate on a running campaign | above 3% | Pause. The list was not verified properly, and every further send costs reputation |
| Unsubscribe rate | above 1.5% | Pause. This is a targeting problem, not a copy problem |
| Reply rate after 300 sends | under 1% | Pause. The offer or the segment is wrong, and a fourth variant will not fix it |
| Spam complaints | any | Stop. This is the domain, not the campaign |
| A step producing more unsubscribes than replies | any | Cut that step |

### 8. Write the file, then show what will be built

Write `outreach/campaign.json`, then print the step tree as an indented list in the
conversation, with the delays, so the user can read the sequence before anything is
pushed. Name the template you started from and the changes you made to it. Then flag the
three things that are easy to get wrong: the timezone, `dailyEmailAdded`, and the
condition windows.

`outreach-campaign` reads this file and pushes it with
`PATCH /advanced/campaigns/{id}/steps`. The user reads the tree here, not in the
interface, so this printout is their last look before it exists.

Nothing is created in Emelia by this skill. `outreach-campaign` does that, and it asks
before it does.

## Output

`outreach/campaign.json`. Everything under `schedule` and `steps` uses Emelia's own
field names and values, so it can be read straight into the app or into a future API.
The blocks outside them (`goal`, `template`, `ab_test`, `stop_rules`, `emelia`) are this
repository's, and carry the decisions the platform does not store.

```json
{
  "spec_version": "1",
  "name": "FR SaaS CTOs, response monitoring, Q4",
  "copy_source": "outreach/sequence.md",
  "list_source": "outreach/leads.csv",
  "template": "smart-multi-channel",
  "template_changes": [
    "branch on ACCEPTED rather than BOUNCED: the list is verified, bounces are near zero",
    "profile visit added before the invitation",
    "call task added on the clicked branch",
    "END_OF_CAMPAIGN added where the stock tree stopped silently"
  ],
  "coverage_at_design_time": { "contactable": 1000, "with_email": 0.96, "with_linkedin": 0.41 },
  "channels": ["email", "linkedin", "call"],
  "goal": { "metric": "replies", "target_rate": 0.05, "contacts": 1000 },
  "copy_mode": "B",
  "opt_out": { "placement": "from_step_2", "wording": "Unsubscribe from these emails" },
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
        { "_id": "v-a", "subject": "status page vs reality", "message": "sequence.md step 1, variant A, ends with {{signature}}, no opt out link", "disabled": false },
        { "_id": "v-b", "subject": "status page vs reality", "message": "sequence.md step 1, variant B, ends with {{signature}}, no opt out link", "disabled": false }
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
              "versions": [{ "_id": "v-s2", "subject": "", "message": "sequence.md step 2, then {{signature}}, then the opt out anchor" }],
              "next": {
                "_id": "s7-email3",
                "stepType": "EMAIL",
                "identities": ["niels@emelia.io"],
                "delay": { "amount": 5, "unit": "DAYS" },
                "versions": [{ "_id": "v-s3", "subject": "who gets paged", "message": "sequence.md step 3, then {{signature}}, then the opt out anchor" }],
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
                    "versions": [{ "_id": "v-s4", "subject": "", "message": "sequence.md step 4, then {{signature}}, then the opt out anchor" }],
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
- `template` names one of the five ids, or is `null` with a written reason, and the two
  coverage percentages that led to that choice were said out loud to the user.
- `template_changes` lists every deviation from the stock tree, including the deletions.
  An empty array means the tree really is the template, not that nobody checked.
- If the template is `linkedin-email` or `smart-multi-channel`, the conditions use
  `$email` and `$linkedinUrlProfile`, and you told the user those are Emelia contact
  fields that the import has to fill.
- No `INMAIL` step survives unless the user confirmed the seat has InMail credits.
- No step is left with an empty `versions[0].message` where the template had a
  placeholder.
- Every `stepType` is one of the values in the table, and every `CONDITION` has both a
  `yes` and a `no`.
- Every message step has at least one version with a non-empty `message`, and every
  `EMAIL` step that starts a new thread has a subject.
- Every version of every `EMAIL` step ends with `{{signature}}`, lowercase, and every
  version of the same step carries the same blocks as its sibling.
- The opt out link matches `opt_out.placement`: absent from the first email step and
  present on every later one by default, or present everywhere if that was the choice.
  It is an `<a href="{{unsubscribe_link}}">` with a short text, never a bare variable.
- `python3 scripts/check-copy.py outreach/sequence.md outreach/leads.csv` exits 0 on the
  copy this tree points at.
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

**The whole list goes down one branch of a multichannel template.** The condition tests
`$linkedinUrlProfile` or `$email`, and the import put the value somewhere else, so the
field is empty on every row. Nothing errors. Open one contact in the app, check the
field is the standard one and not a custom field with a similar name, and reload the
list rather than editing the tree.

**The LinkedIn half of the campaign never fires.** Check the polarity of the condition
before anything else. In `smart-multi-channel` the second condition is
`$linkedinUrlProfile IS_EMPTY`, so LinkedIn hangs off the `no` branch. Copying that step
into another tree and reading it as "has a profile" inverts your whole audience.

**The template was picked from the campaign name rather than the data.** "LinkedIn then
Email" on a list where 30% have a profile means 70% of the contacts stop at step one. Run
the count in section 1 first, every time, even when the user names a template.

**Nothing happens for a week and the user thinks it is broken.** The `ACCEPTED` condition
window in the LinkedIn templates is 5 days, and every contact who has not accepted waits
it out before the fallback runs. Say the number when you hand over the build sheet.

**The campaign is much longer than the card said.** The "~15 days" on a template card is
an approximation written in the product, not the sum of the branch. Add the delays along
the branch the contact actually takes, condition windows included, and quote that.

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

**One A/B version has a footer and the other does not.** Versions are separate bodies, so
a block added to one is missing from the other. Whatever wins, you cannot say why. Diff
the two versions block by block before the launch.

**Recipients complain there is no way out.** The opt out link is on steps 2 and later by
design, so a contact who only ever received step 1 never saw one. That is the accepted
cost of the rule, and the reply path still works. If the user is not comfortable with it,
switch to `Opt-out: every step` rather than arguing.

## Limits

This skill does not create anything in Emelia and does not send anything: it writes a
file and a build sheet, and `outreach-campaign` does the rest with an explicit
confirmation. The five templates are the ones the product shipped on 9 September 2026,
read from its own template file: if the app shows a sixth, or different delays, trust the
app and say the skill is behind. It cannot build the step tree through the API, because that endpoint does
not exist, and it will say so rather than pretending. It does not know your mailbox
capacity: the daily numbers here are proposals that `outreach-deliverability` has the
final word on. The delay and volume figures are rules of thumb from common practice, not
measurements from your account, and `outreach-audit` is what replaces them with yours.
