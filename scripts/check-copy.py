#!/usr/bin/env python3
"""Mechanical checks on outreach/sequence.md, run by the outreach-write skill.

Usage: python3 scripts/check-copy.py outreach/sequence.md outreach/leads.csv
Exits 1 when a FAIL is found, so it works as a gate before a launch.
"""
import csv, re, sys
SEQ, LEADS = sys.argv[1], sys.argv[2]
ROOT_VARS = set("""firstName lastName fullName email secondaryEmail phone mobilePhone jobTitle
seniority department gender age language linkedinUrlProfile twitterUrl country region city
postalCode address timezone yearsOfExperience education bio companyName companyCity
companyCountry unsubscribe_link UNIQUE_ID""".split())
SPAM = """free,100% free,risk free,no cost,guarantee,guaranteed,act now,urgent,limited time,
last chance,don't miss,expires,order now,buy now,cheap,discount,cash,earn,make money,prize,
winner,congratulations,revolutionary,game-changing,breakthrough,amazing,incredible,best-in-class,
world-class,cutting-edge,supercharge,skyrocket,10x,unleash,no-brainer,dear sir,dear friend,
to whom it may concern,this is not spam,click here,click below,apply now,call now,increase sales,
boost your,quick win,exclusive offer,special promotion,earn extra,double your""".replace("\n","")
SPAM = [w.strip() for w in SPAM.split(",") if w.strip()]
text = open(SEQ, encoding="utf-8").read()
cols = set(next(csv.reader(open(LEADS, encoding="utf-8"))))
steps, cur = [], None
for line in text.splitlines():
    h = re.match(r"^##\s+Step\s+(\d+)", line)
    if h:
        cur = {"n": int(h.group(1)), "subject": "", "body": [], "infence": False}
        steps.append(cur)
        continue
    if cur is None: continue
    s = re.match(r"^\*\*Subject:\*\*\s*(.*)$", line)
    if s: cur["subject"] = s.group(1).strip(); continue
    if line.startswith("```"): cur["infence"] = not cur["infence"]; continue
    if cur["infence"]: cur["body"].append(line)
for s in steps: s["body"] = "\n".join(s["body"]).strip()
out, hard = [], 0
def say(level, step, msg):
    global hard
    if level == "FAIL": hard += 1
    out.append(f"{level:4} step {step}: {msg}")
strip = lambda t: re.sub(r"\{[^}]*\}", " ", t)
words = lambda t: re.findall(r"[A-Za-zÀ-ÿ']+", strip(t))
stems = lambda t: {w.lower() for w in words(t) if len(w) > 3}
prev = None
for s in steps:
    n, sub, body = s["n"], s["subject"], s["body"]
    if sub:
        if len(sub) > 60: say("FAIL", n, f"subject is {len(sub)} chars, rewrite under 45")
        elif len(sub) > 45: say("WARN", n, f"subject is {len(sub)} chars, aim for 30 to 45")
        if len(sub) > 35: say("WARN", n, f"mobile shows about '{sub[:35]}', check it stands alone")
        caps_words = [w for w in sub.split() if w[:1].isupper()]
        if len(caps_words) > max(1, len(sub.split()) * 0.5):
            say("WARN", n, "Title Case subject reads like a newsletter, use sentence case")
        if [w for w in sub.split() if len(w) > 2 and w.isupper()]:
            say("FAIL", n, "shouting in the subject")
        shits = [t for t in SPAM if t in sub.lower()]
        if shits: say("FAIL", n, f"spam trigger in the subject: {', '.join(shits)}")
    elif n == 1: say("FAIL", n, "step 1 has no subject")
    w = len(words(body))
    if n == 1 and not (50 <= w <= 125): say("FAIL", n, f"{w} words, step 1 must be 50 to 125")
    if n > 1 and w > 90: say("FAIL", n, f"{w} words, a follow-up must stay under 90")
    links = len(re.findall(r"https?://", body))
    if n == 1 and links > 1: say("FAIL", n, f"{links} links in step 1, keep 0 or 1")
    if links > 2: say("FAIL", n, f"{links} links, keep 1 per step")
    if re.search(r"<img|!\[", body): say("FAIL", n, "image in the body, the open pixel is already one")
    for v in set(re.findall(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}", body + " " + sub)):
        if v not in cols and v not in ROOT_VARS:
            say("FAIL", n, f"variable {v} is not a column of leads.csv nor an Emelia field")
    for v in set(re.findall(r"\{#\s*([A-Za-z0-9_]+)", body + " " + sub)):
        if v not in cols and v not in ROOT_VARS: say("FAIL", n, f"Liquid variable {v} does not exist")
    if "{{" in sub and "|" not in sub and "{#" not in sub:
        say("WARN", n, "variable in the subject with no fallback, empty values leave a gap")
    low = body.lower()
    hits = [t for t in SPAM if t in low]
    if len(hits) >= 3: say("FAIL", n, f"spam trigger stack: {', '.join(hits)}")
    elif hits: say("WARN", n, f"spam trigger word: {', '.join(hits)}")
    if body.count("!") > 0: say("WARN", n, "exclamation mark, cold email does not need one")
    if body.count("?") > 1: say("FAIL", n, f"{body.count('?')} questions, ask one thing")
    caps = [t for t in re.findall(r"\b[A-Z]{4,}\b", body) if t not in ("SPF","DKIM","DMARC","SAAS")]
    if caps: say("WARN", n, f"shouted words: {', '.join(caps)}")
    if re.search(r"\b\d+ ?(%|x)\b", body) and not re.search(r"(from|to|over|in|of) ", low):
        say("WARN", n, "a number with no base, give the before and after or drop it")
    if prev:
        a, b = stems(prev), stems(body)
        if a and b and len(a & b) / len(a | b) > 0.4:
            say("FAIL", n, "this follow-up repeats the previous step, give it something new")
    prev = body
alltext = " ".join(s["body"] for s in steps).lower()
if "unsubscribe_link" not in alltext and "reply with" not in alltext and "let me know" not in alltext:
    say("FAIL", 0, "no opt-out anywhere in the sequence")
if len(steps) > 5: say("WARN", 0, f"{len(steps)} steps, past 4 you mostly buy unsubscribes")
total = sum(len(words(s["body"])) for s in steps)
if total > 400: say("WARN", 0, f"{total} words across the sequence, trim to under 400")
print("\n".join(out) if out else "no findings")
print(f"\n{len(steps)} steps, {total} words, {hard} blocking")
sys.exit(1 if hard else 0)
