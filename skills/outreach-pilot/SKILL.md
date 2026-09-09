---
name: outreach-pilot
description: "Guided first outbound campaign on exactly 100 contacts, with a numbered checkpoint at every step. Asks who you sell to, builds and cleans a small list, verifies every address, writes the sequence with you, gates on deliverability, launches only on an explicit yes, then reads the results at day 3, day 7 and day 14 and tells you whether to scale, rewrite the message or change the target. Use it for a first campaign, a new market, a new offer, or a sending domain that has never carried cold email. Triggers on: pilot, first campaign, getting started, test campaign, try outreach, small batch, 100 contacts, new market, guided setup, walkthrough, onboarding, dry run."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Pilot: a first campaign on 100 contacts

## What this does

Walks you through one complete outbound campaign, from "who do we sell to" to
"here is what the numbers say", on a deliberately small list of 100 contacts. It
runs the other skills in order and stops at every step so you can look at what was
produced before anything costs money or reaches a person. At the end it gives you
one decision: scale, change the message, or change the target.

## When to use it

Use it when you have never run a campaign with this repository, when you are opening
a market you have not sold to, when you are testing a new offer, or when the sending
domain is new. Use it also when someone else set up a campaign and you want to see
the whole chain once, slowly.

Do not use it when you already know the market and the copy works: run
[`outreach`](../outreach/SKILL.md) with `full` instead, which does the same steps
without stopping at each one. Do not use it to fix a campaign that is already
running: that is [`outreach-audit`](../outreach-audit/SKILL.md).

## Inputs

| Input | Required | If missing |
|---|---|---|
| A sentence about who you sell to and what you sell | yes | ask for it, do not guess |
| The country or countries you will email | yes | ask, the rules differ by market |
| `EMELIA_API_KEY` in the environment | for enrichment and sending | offer dry run: every file is still produced, nothing is sent, nothing is charged |
| A source of contacts (Basile key, a Sales Navigator search URL, or a CSV) | yes | ask which one, a CSV always works |
| A sending domain with SPF, DKIM and DMARC, and warmup running | before launch only | say it at step 1, not at step 8, so the user can start warmup today |
| An Emelia campaign whose steps are already built in the app | before launch only | explain the split at step 1 (see step 8), it surprises everyone once |

`BASILE_API_KEY` is optional and only used if the list comes from Basile. The MCP
server is optional too: the pilot uses the REST API by default and reaches for MCP
only where REST has no equivalent (campaign statistics, warmup status, sending
accounts, list management). Check whether it is configured, never assume.

Write nothing outside `outreach/` in the current directory.

## How to do it

### What it costs you, before you start

Time, if the sending domain is already warmed:

| Phase | Your attention | Elapsed |
|---|---|---|
| Steps 1 to 3 (target, rules, list) | 10 to 15 min | same day |
| Steps 4 to 6 (verify, copy, sequence) | 15 to 25 min | same day |
| Step 7 (deliverability gate) | 5 min | same day |
| Step 8 (launch) | 2 min | same day |
| Step 9 (read the results) | three check-ins of 5 min | 14 days |

If the domain is **not** warmed, add two to three weeks before step 8. Warmup cannot
be compressed, and starting it is free, which is why step 7 is announced at step 1.

Credits, on 100 contacts:

| What | How many jobs | Skipped when |
|---|---|---|
| Find email | one per contact with no email, at most 100 | the row already carries an address |
| Verify email | one per address, so about 100 | never, verification is not optional here |
| Find phone | zero | the pilot is email only |

Each job consumes Emelia credits, and the price per job depends on your plan: read it
in the Emelia app before you answer yes. This skill states the count and waits for an
explicit yes before spending anything. On the Start plan the API accepts 100 requests
per minute (300 on Grow, 1,000 on Scale, 30 with no subscription), and each enrichment
is one call to start the job plus one or more to poll it, so a 100 row run takes a few
minutes. That is normal. Do not retry in a loop when you see a rate limit.

### Why 100 and not 1,000

1. **It answers the only question a first campaign has.** Not "which subject line
   wins", but "is anything here alive". Three replies out of 100 means the chain
   works end to end. Zero replies means something is broken, and you find out for the
   price of 100 contacts.
2. **It is not enough to compare two things, and that is fine.** With 100 sends, an
   observed 5% reply rate carries a 95% interval of roughly 2% to 11%. Telling a 3%
   message apart from a 6% message at normal confidence takes around 750 contacts per
   variant (standard two proportion sample size, so a rule of thumb, not a promise).
   The pilot therefore runs **one** message, not an A/B test. A/B testing comes later,
   with volume.
3. **It protects the domain.** A domain that has never sent cold email and suddenly
   pushes 1,000 messages gets throttled, foldered or blocked, and reputation takes
   weeks to rebuild. 100 messages across ten working days is ten a day, which a warmed
   mailbox carries without a bump.
4. **Mistakes stay cheap.** A merge variable that renders empty, a link that 404s, a
   first line that reads as a template: on 100 contacts you burn 100 contacts. You do
   not get to email the same person again with the better version and expect a
   different answer.
5. **The bounce rate stays survivable.** Three bounces out of 100 is a visible 3% and
   a reason to stop. Thirty bounces out of 1,000 is the same rate with ten times the
   damage already done.

### The nine steps

Run them in order. After each one, show the user what was produced and wait. Record
the decision in `outreach/pilot.md` before moving on.

**Step 1. Say who you are targeting.**
Run [`outreach-icp`](../outreach-icp/SKILL.md).
Produces `outreach/icp.json`: titles, industries, headcount, geography, exclusions.
*Check before continuing:* read it back. Could you name one real company that fits?
Are the exclusions written down (existing customers, competitors, students, agencies)?
If the titles list runs past six entries, that is a wish, not a spec: cut it.

**Step 2. Sharpen what you sell.**
Produces `outreach/offer.md`, and the block the writing prompt will consume.
*Check before continuing:* what you sell is specific enough that a competitor could not
put their logo on the same sentence. If it still reads like a category description, the
messages will read like everyone else's and the pilot will not tell you much.

**Step 3. Source about 500, cut to about 250, enrich those.**
Run [`outreach-leads`](../outreach-leads/SKILL.md) with a target of 150, then
[`outreach-filter`](../outreach-filter/SKILL.md).
Produces `outreach/leads.csv`, source column kept.
Source 150 and not 100: filtering removes duplicates, current customers, blacklisted
domains and rows too thin to personalize. Sourcing exactly 100 leaves you with 70.
*Check before continuing:* open the file and read ten rows at random. For each one,
could you write the first line of an email to that person without inventing anything?
If the answer is no for three of the ten, the list is the problem. Go back to step 1.

**Step 4. Find the missing addresses, and verify only the ones you brought yourself.**
Run [`outreach-enrich`](../outreach-enrich/SKILL.md).
Produces `outreach/enrichment.json`: found, not found, verification result, cost.
Filter first (step 3), enrich second. Never the other way round: credits spent on rows
you are about to delete are gone.
*Check before continuing:* the run reports found and not found separately, as
percentages. Keep the rows the finder returned as `valid`, plus the ones you brought that the verifier confirmed. Drop catch-all
and unknown rows from the pilot rather than "trying them anyway", because on 100
contacts you cannot afford their bounce risk. If you end up below 80 usable rows,
source more before launching: a pilot on 60 contacts answers nothing.

**Step 5. Write the sequence.**
Run [`outreach-write`](../outreach-write/SKILL.md).
Produces `outreach/sequence.md`: subject, first email, two follow ups.
One angle, one ask, no A/B at this size.
*Check before continuing:* read the first email as if it landed in your own inbox on a
Tuesday morning. Is every claim in it true? Do all the variables fill correctly on your
first three rows? Is the ask small enough to answer in one line? If the email needs a
paragraph to explain what you do, the offer is not ready and no sequence will fix it.

**Step 6. Design the flow.**
Run [`outreach-sequence`](../outreach-sequence/SKILL.md).
Produces the campaign spec in `outreach/campaign.json`.
For a pilot: three email steps over about twelve working days, stop on reply, no
condition branches, no A/B versions.
*Check before continuing:* the flow stops when someone replies, the delays are in
working days, and there is no fourth step. A fourth step buys a few replies and costs
more unsubscribes than it is worth at this size.

**Step 7. The deliverability gate.**
Run [`outreach-deliverability`](../outreach-deliverability/SKILL.md).
This step is allowed to stop the pilot, and it should.
It must confirm: SPF, DKIM and DMARC published on the sending domain; warmup running
with a healthy score; the sending domain is not the domain your invoices come from;
a daily cap of ten to twenty per mailbox; a custom tracking domain if link tracking is
on. Anything missing means no launch today.
*Check before continuing:* you can state each of those five out loud. This is the step
people skip, and it is the most common reason a first campaign returns nothing.

**Step 8. Launch.**
Run [`outreach-campaign`](../outreach-campaign/SKILL.md). It waits for an explicit yes.
Before you give it: send yourself a test of all three steps and read them on a phone.
Be honest with the user about the split of work, and say it now if you have not
already. `POST /advanced/campaigns` creates a campaign with a name and nothing else:
the three steps, the delays, the schedule and the sending identities are built once in
the Emelia app, on that campaign, and the user starts it there. From then on it is
programmable: contacts added to the list attached to the campaign enter the running
campaign on their own, so the last action of the pilot is pushing your 100 verified
contacts into that list.
*Check before continuing:* `outreach/campaign.json` holds the campaign id, the list id
and a contact count that matches the number you verified at step 4. If those counts
differ, do not launch, find the missing rows first.

**Step 9. Read what happened.**
Run [`outreach-audit`](../outreach-audit/SKILL.md) three times, at day 3, day 7 and
day 14. Produces `outreach/report.md`.

### The three read points

**Day 3, once the first email has reached everyone.** One question only: is it being
delivered?

- Bounces above 3% of sent: pause the campaign now and go back to step 4. Nothing else
  matters until that is fixed.
- Two or more unsubscribes already: the list or the first line is wrong, pause.
- Zero sent: the campaign never actually started. Check the campaign status (a campaign
  left in `DRAFT` sends nothing) and the sending mailboxes (a disconnected provider
  sends nothing either).
- Anything else: keep going and change nothing. It is far too early to judge the copy.

**Day 7, after the second step.** Record the numbers, read every reply in full, answer
the ones that deserve an answer. The only changes allowed today are answering replies
and pausing on a deliverability signal. Follow ups carry a large share of the replies,
so judging the copy now will make you throw away a message that was about to work.

**Day 14, sequence complete.** Decide, using the table below.

### The decision at day 14

Per 100 contacts actually contacted, not per 100 sourced:

| What you see | What it means | What you do |
|---|---|---|
| 4 or more replies, at least one asking for a call, a price or a demo | list and offer both work | **Scale.** Same sequence, same ICP, 500 to 1,000 contacts, ramp the daily volume, keep verifying every address |
| 4 or more replies, none positive, mostly "not for us" or "wrong person" | the message reaches people, they are the wrong people | **Change the target.** Back to step 1, tighten titles and company size, keep the copy |
| 1 to 3 replies, mixed, bounces under 2% | targeting is plausible, the message is weak | **Change the message.** Keep `icp.json` and the source, rewrite the first email around a different problem, run a second pilot on 100 fresh contacts |
| 0 replies, bounces under 2%, mail clearly going out | nobody cares, or the ask is too big | **Change the message and the ask** before touching the list |
| 0 replies with bounces above 3%, or almost nothing sent | delivery, not copy | **Stop and go back to step 7.** Rewriting now teaches you nothing |
| Replies are mostly "how did you get my data", or unsubscribes above 2% | source or tone problem | **Back to step 2, then step 1** |

Two rules that matter more than the table. Never scale a pilot that produced zero
replies by sending more of the same. And never change two things at once: change the
target **or** the message, then run another 100. That is the whole point of running
100.

## Output

`outreach/pilot.md`, the run log. Every other file is written by the skill that owns
it (`icp.json`, `leads.csv`, `enrichment.json`, `sequence.md`, `campaign.json`,
`report.md`). Real example, mid run:

```markdown
# Pilot run, started 2026-09-08

Target market: France. Offer: API monitoring for SaaS teams.

| # | Step | Status | Result | Decided |
|---|------|--------|--------|---------|
| 1 | ICP | done | CTO / VP Eng, French SaaS, 20 to 200 people, excl. agencies | 2026-09-08 |
| 3 | List | done | 152 sourced (Basile), 104 after filtering | 2026-09-08 |
| 4 | Enrich | done | 104 rows: 71 emails found (68%), 66 verified valid, 5 dropped | 2026-09-08 |
| 5 | Copy | done | angle: "your status page lies", one ask: 15 min | 2026-09-08 |
| 6 | Sequence | done | 3 emails, day 0 / day 4 / day 11, stop on reply | 2026-09-08 |
| 7 | Deliverability | BLOCKED | DMARC missing on mail.acme-outbound.com | 2026-09-08 |
| 8 | Launch | pending | waiting on step 7 | |
| 9 | Read | pending | day 3 / day 7 / day 14 | |

## Spend
- Find email: 104 jobs, approved by user 2026-09-08 14:02
- Verify email: 71 jobs, approved by user 2026-09-08 14:19
- Find phone: not used

## Open items
- Publish the DMARC record (p=none to start), then re-run step 7.
- 66 verified contacts is below the 100 target. Decision: launch on 66 and treat
  4 replies as the scale threshold, rather than delay two weeks to source more.
```

Note in the log what you did **not** do. "71 emails found out of 104" is the useful
line. "List enriched" is not.

## Checks before finishing

- Every step has a line in `outreach/pilot.md` with a status and a date.
- No credit was spent without a recorded yes from the user, with the count stated
  first.
- The contacts attached to the campaign are only addresses that verified `valid`.
- The deliverability gate passed on its own terms, and you can name SPF, DKIM, DMARC,
  warmup and the daily cap.
- The user typed a yes for the launch itself, separately from the yes for spending.
- Every number reported to the user is a real count, with its denominator named.
- The day 14 report ends with exactly one recommendation, not a list of options.

## Failure modes

**"Skip the pilot, load 2,000 contacts."** Say what the pilot buys: a cheap answer and
an intact domain. If the user still wants volume, do not refuse the work, but require
the ramp plan from `outreach-deliverability` and a fully verified list, and say plainly
that the first campaign on a cold domain is the one that decides the next six months of
deliverability.

**No Emelia key.** Say it at step 1. Steps 1 to 6 run fine in dry run and produce every
file. Steps 4, 8 and 9 cannot run. Discovering this at step 8 wastes the user's hour.

**Not enough leads at step 3.** The ICP is too narrow, or the source does not cover
that market. Widen the geography before widening the titles: a broader title list
degrades the message faster than a broader map.

**Fewer than 60 emails found out of 100.** That is a signal about the list, not a tool
failure: the companies are too small, too new or too obscure for any finder. Report the
percentage and offer to change the source. Never fill the gap with guessed patterns
like `firstname.lastname@domain`, they bounce and they cost you the domain.

**Warmup is off and the user wants to launch anyway.** Refuse, and offer something
better: start warmup now, keep the campaign in draft, and schedule the launch for the
date warmup completes. Everything else in the pilot is already done by then.

**The copy is edited after step 7 and before step 8.** Re-run the checks. One added
line can introduce a link, a spam trigger word or a variable that does not exist in
the list, and the gate you passed no longer applies to what you are about to send.

**Zero activity at day 3.** Look at the campaign status before anything else. A
campaign that was created but never started stays in `DRAFT` and sends nothing, and a
disconnected sending mailbox produces the same silence.

## Limits

This skill cannot tell you which of two subject lines is better: 100 contacts cannot
resolve a difference smaller than roughly a factor of two. It cannot validate an offer
nobody has bought yet: if three different messages to three fresh lists of 100 all
return nothing, the problem is upstream of outreach and more sending will not find it.
It does not place calls and it does not run LinkedIn steps unless that integration is
already connected. It cannot build the campaign steps through the API: it produces the
spec and the copy, and verifies that what was configured in the app matches. And the
100 contacts it uses are spent: re-emailing the same people with a better message is a
worse test than emailing 100 new ones.
