#!/usr/bin/env python3
"""Mechanical checks on outreach/sequence.md, run by the outreach-write skill.

Usage: python3 scripts/check-copy.py outreach/sequence.md outreach/leads.csv
Exits 1 when a FAIL is found, so it works as a gate before a launch.

One directive is read from the file header, and it is optional:
  Opt-out: every step  puts the unsubscribe link on every email step instead of
                       the default, which is none on step 1 and one from step 2 on.
A Mode A step, whose body is a carrier variable holding the whole message, is detected
from the body itself: the copy checks are skipped there and reported as skipped.
"""
import csv, re, sys
SEQ, LEADS = sys.argv[1], sys.argv[2]
ROOT_VARS = set("""firstName lastName fullName email secondaryEmail phone mobilePhone jobTitle
seniority department gender age language linkedinUrlProfile twitterUrl country region city
postalCode address timezone yearsOfExperience education bio companyName companyCity
companyCountry websiteUrl unsubscribe_link signature UNIQUE_ID""".split())
# checked by their own rule below, so the generic "unknown variable" rule leaves them alone
CASE_FREE = {"unsubscribe_link", "unique_id", "signature"}
SPAM = """free,100% free,risk free,no cost,guarantee,guaranteed,act now,urgent,limited time,
last chance,don't miss,expires,order now,buy now,cheap,discount,cash,earn,make money,prize,
winner,congratulations,revolutionary,game-changing,breakthrough,amazing,incredible,best-in-class,
world-class,cutting-edge,supercharge,skyrocket,10x,unleash,no-brainer,dear sir,dear friend,
to whom it may concern,this is not spam,click here,click below,apply now,call now,increase sales,
boost your,quick win,exclusive offer,special promotion,earn extra,double your""".replace("\n","")
SPAM = [w.strip() for w in SPAM.split(",") if w.strip()]
# <a href="{{unsubscribe_link}}">Se desabonner</a>, in any case, over any number of lines
UNSUB_ANCHOR = re.compile(
    r"<a\b[^>]*?href\s*=\s*(['\"])\s*\{\{\s*unsubscribe_link\s*\}\}\s*\1[^>]*>(.*?)</a>",
    re.I | re.S)
UNSUB_VAR = re.compile(r"\{\{\s*unsubscribe_link\s*\}\}", re.I)
SIGNATURE = re.compile(r"\{\{\s*signature\s*\}\}")          # lowercase only, on purpose
NOT_EMAIL = ("linkedin", "whatsapp", "call", "task", "visit", "invitation",
             "connection", "inmail", "audio", "voice", "sms")
text = open(SEQ, encoding="utf-8").read()
cols = set(next(csv.reader(open(LEADS, encoding="utf-8"))))
m = re.search(r"^Opt-?out:\s*(.+)$", text, re.M | re.I)
optout_every = bool(m) and "every" in m.group(1).lower()
steps, cur = [], None
for line in text.splitlines():
    h = re.match(r"^##\s+Step\s+(\d+)(.*)$", line)
    if h:
        head = h.group(2).lower()
        cur = {"n": int(h.group(1)), "subject": "", "body": [], "infence": False,
               "email": not any(k in head for k in NOT_EMAIL)}
        steps.append(cur)
        continue
    if cur is None: continue
    s = re.match(r"^\*\*Subject:\*\*\s*(.*)$", line)
    if s: cur["subject"] = s.group(1).strip(); continue
    if line.startswith("```"): cur["infence"] = not cur["infence"]; continue
    if cur["infence"]: cur["body"].append(line)
for s in steps: s["body"] = "\n".join(s["body"]).strip()
emails = [s for s in steps if s["email"]]
# a one email sequence has no step 2 to carry the opt out, so it carries it itself
if len(emails) < 2: optout_every = True
out, hard = [], 0
def say(level, step, msg):
    global hard
    if level == "FAIL": hard += 1
    out.append(f"{level:4} step {step}: {msg}")
strip = lambda t: re.sub(r"\{[^}]*\}", " ", re.sub(r"<[^>]*>", " ", t))
words = lambda t: re.findall(r"[A-Za-zÀ-ÿ']+", strip(t))
stems = lambda t: {w.lower() for w in words(t) if len(w) > 3}
prev = None
for s in steps:
    n, sub, body, is_email = s["n"], s["subject"], s["body"], s["email"]
    # the opt out block is plumbing, not copy: it never counts as words or as a link
    copy = UNSUB_ANCHOR.sub(" ", body)
    w = len(words(copy))
    # a Mode A step is one carrier variable: there is no copy here to measure yet
    carrier = w < 5 and re.search(r"\{\{\s*[A-Za-z0-9_]+\s*\}\}", copy) is not None
    if sub:
        if len(sub) > 60: say("FAIL", n, f"subject is {len(sub)} chars, rewrite under 45")
        elif len(sub) > 45: say("WARN", n, f"subject is {len(sub)} chars, aim for 30 to 45")
        if len(sub) > 35: say("WARN", n, f"mobile shows about '{sub[:35]}', check it stands alone")
        caps_words = [w2 for w2 in sub.split() if w2[:1].isupper()]
        if len(caps_words) > max(1, len(sub.split()) * 0.5):
            say("WARN", n, "Title Case subject reads like a newsletter, use sentence case")
        if [w2 for w2 in sub.split() if len(w2) > 2 and w2.isupper()]:
            say("FAIL", n, "shouting in the subject")
        shits = [t for t in SPAM if t in sub.lower()]
        if shits: say("FAIL", n, f"spam trigger in the subject: {', '.join(shits)}")
    elif n == 1: say("FAIL", n, "step 1 has no subject")
    if carrier:
        say("INFO", n, "carrier step, the message is in a variable. Run the copy checks "
                       "on the rendered sample, not on this file")
    else:
        if n == 1 and not (50 <= w <= 125): say("FAIL", n, f"{w} words, step 1 must be 50 to 125")
        if n > 1 and w > 90: say("FAIL", n, f"{w} words, a follow-up must stay under 90")
    links = len(re.findall(r"https?://", copy))
    if n == 1 and links > 1: say("FAIL", n, f"{links} links in step 1, keep 0 or 1")
    if links > 2: say("FAIL", n, f"{links} links, keep 1 per step")
    if re.search(r"<img|!\[", body): say("FAIL", n, "image in the body, the open pixel is already one")
    for v in set(re.findall(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}", body + " " + sub)):
        if v not in cols and v not in ROOT_VARS and v.lower() not in CASE_FREE:
            say("FAIL", n, f"variable {v} is not a column of leads.csv nor an Emelia field")
    for v in set(re.findall(r"\{#\s*([A-Za-z0-9_]+)", body + " " + sub)):
        if v not in cols and v not in ROOT_VARS: say("FAIL", n, f"Liquid variable {v} does not exist")
    if "{{" in sub and "|" not in sub and "{#" not in sub:
        say("WARN", n, "variable in the subject with no fallback, empty values leave a gap")
    if is_email:
        # the signature block, lowercase only: {{Signature}} silently renders nothing
        if not SIGNATURE.search(body):
            if re.search(r"\{\{\s*signature\s*\}\}", body, re.I):
                say("FAIL", n, "{{signature}} is capitalised, only the lowercase form resolves")
            else:
                say("FAIL", n, "no {{signature}} in the body, the sender block is missing")
        anchors = UNSUB_ANCHOR.findall(body)
        bare = UNSUB_VAR.search(copy) is not None
        if bare:
            say("FAIL", n, 'unsubscribe variable pasted bare, it renders a raw URL. Wrap it: '
                           '<a href="{{unsubscribe_link}}">Unsubscribe</a>')
        for _, label in anchors:
            label = re.sub(r"<[^>]*>", " ", label).strip()
            if not label:
                say("FAIL", n, "the unsubscribe link has no text")
            elif "http" in label.lower() or "{{" in label:
                say("FAIL", n, "the unsubscribe link shows a URL, use a word instead")
            elif "?" in label:
                say("FAIL", n, "a question mark in the unsubscribe link, keep the one question for the ask")
            elif len(label.split()) > 6:
                say("WARN", n, f"unsubscribe wording is {len(label.split())} words, one to four is enough")
            junk = [x for x in SPAM if x in label.lower()]
            if junk: say("FAIL", n, f"spam trigger in the unsubscribe wording: {', '.join(junk)}")
        has_unsub = bool(anchors) or bare
        if optout_every and not has_unsub:
            why = ("the header asks for one on every step" if m
                   else "a one email sequence has no step 2 to carry it")
            say("FAIL", n, f"no unsubscribe link, {why}")
        elif not optout_every:
            if n == 1 and has_unsub:
                say("FAIL", n, "unsubscribe link in step 1, it belongs from step 2 on. "
                               "Write 'Opt-out: every step' in the header to override")
            if n > 1 and not has_unsub:
                say("FAIL", n, "no unsubscribe link, every step after the first carries one")
    low = copy.lower()
    hits = [t for t in SPAM if t in low]
    if len(hits) >= 3: say("FAIL", n, f"spam trigger stack: {', '.join(hits)}")
    elif hits: say("WARN", n, f"spam trigger word: {', '.join(hits)}")
    if carrier: prev = None; continue
    if copy.count("!") > 0: say("WARN", n, "exclamation mark, cold email does not need one")
    if copy.count("?") > 1: say("FAIL", n, f"{copy.count('?')} questions, ask one thing")
    caps = [t for t in re.findall(r"\b[A-Z]{4,}\b", copy) if t not in ("SPF","DKIM","DMARC","SAAS")]
    if caps: say("WARN", n, f"shouted words: {', '.join(caps)}")
    if re.search(r"\b\d+ ?(%|x)\b", copy) and not re.search(r"(from|to|over|in|of) ", low):
        say("WARN", n, "a number with no base, give the before and after or drop it")
    if prev:
        a, b = stems(prev), stems(copy)
        if a and b and len(a & b) / len(a | b) > 0.4:
            say("FAIL", n, "this follow-up repeats the previous step, give it something new")
    prev = copy
if emails and not any(UNSUB_VAR.search(s["body"]) for s in emails):
    say("FAIL", 0, "no opt out anywhere in the sequence")
if len(steps) > 5: say("WARN", 0, f"{len(steps)} steps, past 4 you mostly buy unsubscribes")
total = sum(len(words(UNSUB_ANCHOR.sub(" ", s["body"]))) for s in steps)
if total > 400: say("WARN", 0, f"{total} words across the sequence, trim to under 400")
print("\n".join(out) if out else "no findings")
print(f"\n{len(steps)} steps, {total} words, {hard} blocking")
sys.exit(1 if hard else 0)
