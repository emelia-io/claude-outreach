---
name: outreach-compliance
description: "What the law lets you do when you send cold B2B email, market by market. Covers France and the European Union (GDPR, legitimate interest, the information duty at first contact, the right to object, the CNIL position on B2B prospecting), the United Kingdom (PECR and UK GDPR), the United States (CAN-SPAM and state privacy law), Canada (CASL, which is much stricter), and the general principle everywhere else. States what a message must contain, what is never allowed, how long you may keep the data, what you must be able to prove, and how to handle opt-outs in Emelia. Writes outreach/compliance.md with an operational checklist for your market. Not legal advice. Triggers on: compliance, legal, GDPR, RGPD, CNIL, legitimate interest, ePrivacy, PECR, ICO, CAN-SPAM, CASL, LGPD, consent, opt-in, opt-out, unsubscribe, data retention, privacy notice, is cold email legal, can I email."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---

# Compliance for cold B2B email

**This is not legal advice.** It is an operational summary written by people who send
email, not lawyers. Laws change and regulators publish new guidance. For anything with
real money or real risk attached, have a qualified lawyer in the target market read
your sequence and your data flow.

## What this does

Tells you, for the market you are about to email, whether you may write to someone who
has never heard of you, what the message must contain, how long you may keep the data,
and what you must be able to show if someone asks. Produces a checklist you can hand to
whoever writes the copy.

## When to use it

Run it before sourcing a list in a market you have not sold to, before a first campaign
of any kind, when a recipient asks how you got their address, when you inherit a list
whose origin you cannot document, and any time a campaign crosses a border.

It is a gate, not a chapter: if the market is consent first and you have no consent, the
answer changes the campaign, so run it before
[`outreach-leads`](../outreach-leads/SKILL.md), not after.

Technical sending rules (SPF, DKIM, DMARC, the Gmail and Yahoo bulk sender
requirements) are not law and live in
[`outreach-deliverability`](../outreach-deliverability/SKILL.md).

## Inputs

| Input | Required | If missing |
|---|---|---|
| The countries the recipients are in | yes | ask. Not where you are, where **they** are |
| Whether recipients are named people or generic addresses | yes | assume named people, it is the stricter case |
| Where the list came from, and when | yes | if the user cannot answer, that is itself the finding: say the list is not usable until the source is documented |
| Your company's legal name, address and privacy notice URL | for the message | ask, these go in the email |
| Whether an existing relationship exists (customer, inquiry, event) | no | it can change the answer in Canada and the United States |

## How to do it

### 1. The two questions that decide everything

**Opt-in or opt-out market?** Opt-in means permission before the first message (Canada,
Germany, Italy). Opt-out means you may write first as long as you identify yourself and
offer a working way to stop (United States, United Kingdom for corporate recipients,
France under conditions).

**Natural person or organisation?** `marie.dupont@societe.fr` identifies a human being,
so privacy law applies on top of the marketing rule. `contact@societe.fr` usually
identifies nobody and several regimes treat it more lightly. Sole traders and
unincorporated partnerships count as natural persons in most places, which is the case
people get wrong.

### 2. France and the European Union

Two texts apply at the same time, and confusing them is the usual mistake.

- **The GDPR** (Regulation (EU) 2016/679) governs the personal data: whether you may
  hold the address at all, what you must tell the person, and what rights they have.
- **The ePrivacy Directive** (2002/58/EC, article 13) governs the act of sending
  unsolicited electronic marketing. It requires consent for natural persons and left
  the business to business case to each member state, which is why the answer changes
  at the border inside the same union.

**France.** Article L.34-5 of the Code des postes et des communications electroniques
requires prior consent for marketing email to a natural person. The CNIL's published
position on commercial prospecting treats professional prospecting differently: you may
write to a person at their professional address without prior consent when the message
relates to the profession of the person you are writing to. Software for accountants to
a finance director is in scope; a gym membership to the same person is not. Two
conditions come with it: the person is informed when the address is collected or at the
latest at the first contact, and can object simply and free of charge from the message
itself. Generic addresses such as `contact@` or `info@` are treated as the company's
address rather than an individual's personal data.

**Your legal basis is legitimate interest** (article 6(1)(f)), and it is not a
checkbox. It requires a balancing test you write down once per campaign type and keep:
your interest (finding customers for something relevant to their job), the necessity
(is there a less intrusive way to reach that role), and their reasonable expectations
(would a finance director be surprised to receive this at work). If you cannot honestly
write the third paragraph, you do not have the basis, and no amount of unsubscribe link
repairs it.

**Information at first contact.** Article 14 covers data you did not collect from the
person themselves, which is every cold list. You must tell them who you are, why you
have their data, **where you got it**, the legal basis, how long you keep it, and their
rights, at the latest at the first communication. In practice that is two or three
lines at the bottom of the first email plus a link to your privacy notice. The line
about where you got it is the one everybody omits and the one recipients actually ask
about.

**The right to object** (article 21(2)) is absolute for direct marketing. No
justification, no delay, no counter-offer. You stop, permanently, and you keep enough
of a record to keep stopping.

**Retention.** The CNIL's reference framework for commercial management recommends
keeping prospect data no longer than three years from the last contact coming from the
prospect, and keeping the record of an objection at least three years so you can honour
it. Those are recommendations, not statute, but a regulator that publishes a number uses
it as a yardstick. Put a deletion date on the list the day you create it.

**The union is not one market.** Starting points only, verify locally before a first
send:

| Market | First cold email to a named business address | Where it comes from |
|---|---|---|
| France | allowed without prior consent when the message relates to the person's job, with information and an opt-out | CNIL position on B2B prospecting |
| Germany | consent required, including business to business | UWG section 7, narrow existing customer exception |
| Italy | consent required | Codice privacy article 130, soft opt-in for existing customers only |
| Spain | consent required unless there is a prior contractual relationship for similar products | LSSI article 21 |
| Netherlands | lighter opt-out regime for legal persons, opt-in for individuals | Telecommunicatiewet article 11.7 |
| Belgium | consent required, with an exception for impersonal addresses of legal persons | Code de droit economique, book XII |
| Ireland, Nordics, central Europe | varies | national transposition, check before sending |

Germany and Italy are the two that surprise people who assume business to business is
fine everywhere in Europe. It is not.

### 3. United Kingdom

PECR (the Privacy and Electronic Communications Regulations 2003), regulation 22,
requires consent for unsolicited marketing email to **individual subscribers**, which
the ICO reads as individuals, sole traders and, in England, Wales and Northern Ireland,
unincorporated partnerships. **Corporate subscribers**, meaning limited companies, LLPs
and public bodies, sit outside that consent rule, so you may write to a named person at
a limited company without prior consent.

Two things still apply. You must not conceal your identity and you must give a valid
address for opt-out requests. And UK GDPR governs the employee's personal data
independently of PECR: legal basis, the article 14 information duty, and the right to
object all still bind you. The Data (Use and Access) Act 2025 raised PECR penalties to
UK GDPR levels, so the old reasoning that PECR fines were small no longer holds.

### 4. United States

**CAN-SPAM** (15 U.S.C. chapter 103, FTC rule 16 CFR part 316) is an opt-out regime:
no consent is needed before the first message. What is mandatory:

- Accurate header information. The From, To, Reply-To and routing data must identify
  who is actually sending, and the domain must not be misleading.
- A subject line that does not misrepresent the content.
- The message identifiable as an advertisement, clearly and conspicuously. This can be
  done in the body, it does not have to be in the subject.
- A valid **physical postal address** for the sender. A post box or a registered agent
  address you genuinely receive mail at is fine. An invented one is not.
- A clear explanation of how to opt out, with a mechanism that keeps working for at
  least 30 days after the message was sent.
- Opt-outs honoured within 10 business days.
- No fee, no information beyond an email address, and no more than one page to click
  through in order to opt out.
- You remain responsible when another company sends on your behalf.

Penalties are assessed per email and adjusted for inflation each year, currently above
USD 50,000 per message, so one careless campaign is not a rounding error.

State privacy law applies to the data on top of CAN-SPAM. California's CCPA as amended
by the CPRA has covered business contact data since 1 January 2023, so a California
resident you prospect can ask what you hold and ask you to delete it. Several other
states have comparable laws with their own thresholds. Practically: be able to answer a
deletion request, and honour it.

### 5. Canada

**CASL** (S.C. 2010, c. 23) is the strictest of the four regimes here, and it is the
one people breach without noticing. You need consent, express or implied, **before**
sending a commercial electronic message.

- **Express consent**: they asked to hear from you, and you can show when and how.
- **Implied consent** is the route cold outreach uses, and it has exactly three
  conditions that must all hold at once:
  - **conspicuous publication**: the address was published publicly (a company website,
    a professional directory),
  - the publication carries **no statement** refusing unsolicited commercial messages,
  - and your message is **relevant to that person's business role or functions**.
- Implied consent also arises from an existing business relationship (a purchase within
  two years, an inquiry within six months) or from an address handed to you directly,
  with the same relevance condition.

Every message must identify the sender and anyone on whose behalf it is sent, carry
contact information valid for at least 60 days, and provide an unsubscribe mechanism
valid for 60 days and honoured within 10 business days. Penalties reach CAD 1,000,000
for an individual and CAD 10,000,000 for an organisation per violation.

What this means in practice: buying a generic list and mailing Canada is not compliant.
Building a list where each row records **the public URL the address came from**, and
writing only to people whose role matches the offer, is the compliant path, and you
have to keep that URL. If your source cannot give you a per row provenance, do not send
to Canada from it.

### 6. Everywhere else

Assume the strict version until you have checked. Australia's Spam Act 2003 works like
CASL (consent inferred from a conspicuously published work address, a relevance
condition, sender identification, an unsubscribe honoured within 5 business days), and
newer privacy laws such as Brazil's LGPD and India's DPDP Act copy the GDPR structure.
Six behaviours satisfy nearly all of them at once:

1. Write only to a role that could plausibly care.
2. Say who you are, with a real company name and a real address.
3. Be able to say where you got the address, and say it unprompted at first contact.
4. Give a one click opt-out, and honour it immediately.
5. Keep the source and the collection date of every row.
6. Delete on a schedule you set in advance.

### 7. What is never allowed, anywhere

- A false or disguised sender name, a lookalike domain, a reply-to nobody reads.
- A subject line that misdescribes the message: `Re:` on a first contact, `invoice`,
  `your account`, a fake forward.
- An opt-out that does not work, requires a login, asks for more than an email address,
  or is buried behind several pages.
- Emailing someone who already objected. The first time is a mistake, the second is the
  violation.
- Prospecting a bought list whose origin you cannot name. "A data broker" is not a
  source you can put in an article 14 notice.
- Hiding a commercial purpose behind a fake survey, a fake job offer or a fake
  introduction.
- Fabricated personalization ("loved your post on X" when there is no post). Not
  illegal on its own in most places, but it is a misrepresentation, and it destroys the
  only thing outbound runs on.

### 8. Handling opt-outs, operationally

1. **Put `{{unsubscribe_link}}` in the body**, at minimum in the first email and
   preferably in every step. In Emelia the `List-Unsubscribe` header is added to a
   message only when that variable is present in the body: no variable, no header, and
   no one click unsubscribe button in Gmail or Outlook. A line saying "reply STOP" is
   not a substitute. `{{UNSUBSCRIBE_LINK}}` works too, the name is case insensitive.
2. **When someone asks to be removed in a reply**, blacklist them yourself rather than
   relying on them clicking:
   `POST https://api.emelia.io/emails/blacklists/contact` with
   `{"email": "marie.dupont@societe.fr"}` and the header `Authorization: <key>`. The
   same endpoint accepts a bare domain (`societe.fr`) when a company asks you to stop
   contacting anyone there. `DELETE` on the same path reverses it, which you should
   almost never do.
3. **Keep your own suppression list**, in a file outside Emelia, so it survives an
   account or tool change. Attach it to campaigns as an excluded list, which is what
   `recipients.excludedLists` on a campaign is for.
4. **Record the date and the wording** of every request. That record is the proof, and
   it is the one thing you keep after deleting everything else about that person.
5. **Never re-permission an opt-out** by emailing to ask whether they really meant it.
   That email is itself the violation.

### 9. What you must be able to prove

For any contact, within about a month of being asked: where the address came from (the
exact source and date, not "the internet"), why you contacted that person (the role,
and how the message relates to it), your legal basis and the balancing test behind it,
what you sent and when, and whether they objected and what you did about it.

Keep the first two in `outreach/leads.csv` as `source` and `collected_at` columns, the
next two in `outreach/compliance.md`, and the last in your suppression list. If someone
asks and you need more than a day to answer, you do not have a process.

### 10. The operational checklist, per market

**France and the European Union.** Opt-out for France and, for legal persons, the
Netherlands. Consent first for Germany, Italy, Spain and Belgium.

- [ ] Recipients are named professionals and the message relates to their job
- [ ] Consent first markets filtered out of the list, or consent proven per row
- [ ] Balancing test written in three paragraphs and filed
- [ ] Source and collection date recorded on every row
- [ ] Sender's real name plus the company's legal name in the message
- [ ] Article 14 notice in the first email: who, why, **where the address came from**,
      retention, rights, link to the privacy notice
- [ ] `{{unsubscribe_link}}` in every step
- [ ] Objections honoured immediately and permanently, blacklisted and logged
- [ ] Deletion date set: three years from the last contact coming from the prospect

**United Kingdom.**

- [ ] Recipient is a corporate subscriber (limited company, LLP, public body), not a
      sole trader or an unincorporated partnership
- [ ] Sender identity not concealed, and a valid address given for opt-out requests
- [ ] UK GDPR article 14 notice in the first email, including the source
- [ ] `{{unsubscribe_link}}` in every step, objections honoured immediately
- [ ] Retention period written down and actually enforced

**United States.**

- [ ] From, Reply-To and routing information accurate, subject line not misleading
- [ ] Message identifiable as an advertisement, clearly and conspicuously
- [ ] Valid physical postal address in every message
- [ ] Opt-out working for at least 30 days after the send, with no fee, no login and
      nothing asked beyond an email address
- [ ] Opt-outs honoured within 10 business days
- [ ] Able to answer an access or deletion request from a California resident

**Canada.**

- [ ] Every row records the public URL the address was published on, and the date
- [ ] That page carried no statement refusing unsolicited commercial messages
- [ ] The message is relevant to that person's role, checked per segment
- [ ] Sender identified, plus anyone on whose behalf the message is sent
- [ ] Contact information valid 60 days, unsubscribe valid 60 days, honoured within
      10 business days
- [ ] Nothing sent to a Canadian address whose provenance you cannot show

**Anywhere else.**

- [ ] Checked whether the market is consent first **before** sourcing the list
- [ ] The six behaviours in section 6 applied
- [ ] Local counsel consulted when the campaign carries real money or real risk

## Output

`outreach/compliance.md`, the checklist for this campaign's market. Real example:

```markdown
# Compliance, campaign "Q4 SaaS founders", market: France

Not legal advice. Reviewed 2026-09-08. Re-check before a new market.

## Verdict
Allowed without prior consent. Named people at professional addresses, message
relates to their job (engineering leaders, monitoring tooling). Legal basis:
legitimate interest, GDPR art. 6(1)(f).

## Balancing test (art. 6(1)(f)), kept on file
1. Our interest: reach engineering leaders who buy monitoring tools, a product
   category they already budget for.
2. Necessity: no less intrusive channel reaches this role at this scale. We write
   once, with two follow ups, and stop on reply or objection.
3. Their expectations: a VP Engineering at a 20 to 200 person SaaS company expects
   vendor contact at work. We do not write to personal addresses, we do not write
   to anyone outside that role.

## Data source
Basile, exported 2026-09-04. Per row: `source=basile`, `collected_at=2026-09-04`.
Public company data plus professional contact data. No consumer addresses.

## Checklist (France and EU, section 10)
- [x] Sender's real name and the company legal name
- [x] Article 14 notice at the bottom of email 1, including where the address came from
- [x] `{{unsubscribe_link}}` present in steps 1, 2 and 3, verified in sequence.md
- [x] Postal address in the signature
- [ ] Subject line reviewed for anything misleading: pending copy review

## Retention
Delete on 2029-09-04 (3 years, CNIL guidance) or 3 years after the last contact from
the prospect, whichever is later. Suppression records kept at least 3 years.

## Opt-outs
Click goes through Emelia. Replies asking to stop: blacklist by hand via
POST /emails/blacklists/contact within the working day, then add to
suppression-list.csv. Both logged with date and wording.

## Not covered by this file
Recipients outside France. This campaign is filtered to FR only. Any expansion to
DE, IT or CA needs a new review: those are consent first markets.
```

## Checks before finishing

- The market of the **recipients** is established, not the market of the sender.
- Every country in the list is covered by the verdict, or the list is filtered down to
  the countries that are.
- For a legitimate interest market, the balancing test is written in three paragraphs,
  not asserted.
- The first email carries the article 14 information where that duty applies, including
  the source of the address.
- `{{unsubscribe_link}}` is present in the body of the steps that need it, verified by
  reading `outreach/sequence.md`, not assumed.
- A retention date is written down, not "as long as useful".
- `outreach/leads.csv` carries a source and a collection date per row.
- The words "not legal advice" appear in the file you produce.

## Failure modes

**"It is B2B so GDPR does not apply."** It does. GDPR governs personal data, and a
named person's work address is personal data. What changes for business to business is
the ePrivacy consent rule, not the GDPR.

**"We bought the list, the broker said it was GDPR compliant."** You must be able to
name the source in your own notice, and you carry the obligation, not the broker. If
provenance per row does not exist, treat the list as unusable and say so plainly.

**One campaign, several countries.** The strictest market in the list sets the rule
unless you split the campaign. Splitting is almost always the better answer: filter the
list by country and run one campaign per regime.

**Generic addresses treated as a loophole.** `contact@` is lighter on the privacy side,
but several countries' marketing rules still apply and the reply rate is far worse. It
is not a way around a consent market.

**A recipient asks how you got their address.** Answer directly, name the source, offer
deletion, and do not turn it into a sales conversation. If several people ask the same
question, that is a signal about the source, not about them.

**Canada or Germany appears in the list at step 3 of a pilot.** Stop and filter them
out rather than proceeding and hoping. In both markets the default answer to a cold
message is no consent, no send.

**The unsubscribe link was left out of follow up steps.** Common, because people add it
to email 1 and forget the rest. Check every step, and remember that in Emelia the
absence of the variable also removes the `List-Unsubscribe` header from that message.

## Limits

This is a starting point written by practitioners, not legal advice, and it creates no
lawyer relationship and no guarantee. It does not cover consumer marketing, telephone
prospecting, SMS, postal mail, or the sector rules (finance, health, public
procurement) that add obligations on top. It does not cover international data
transfers or the contracts you need with your processors. It states positions taken by
regulators, which change. And it cannot make a list compliant retroactively: if you
cannot say where a row came from, no message design fixes that.
