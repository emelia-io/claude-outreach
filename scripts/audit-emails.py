#!/usr/bin/env python3
"""Content audit of an outreach sequence, run by the outreach-audit skill.

It answers one question per email: what in this text costs you replies.
It does not look at open rates, click rates or any campaign statistic.

Usage:
  python3 scripts/audit-emails.py outreach/sequence.md
  python3 scripts/audit-emails.py outreach/campaign-raw.json   # GET /advanced/campaigns/{id}

Exits 1 when a step gets a FAIL, so it works as a gate before a launch.
"""
from __future__ import annotations

import html as htmlmod
import json
import math
import os
import re
import sys

# ---------------------------------------------------------------------------
# THRESHOLDS  (provisional, see "Pending: the reference screenshot" in SKILL.md)
# One rendered line on a phone is about 45 characters. Everything below is
# derived from that single number, so changing CHARS_PER_LINE moves the whole
# table in one edit.
# ---------------------------------------------------------------------------
CHARS_PER_LINE = 45

# Reference email, measured from the Emelia editor: 74 chars, then 148, then 74.
# Body 300 chars, 47 words, three paragraphs, the last one a question.
# step number -> (min body chars, target max body chars, hard cap)
LENGTH = {
    1: (220, 300, 380),
    2: (90, 220, 280),
    3: (150, 300, 380),
    4: (80, 200, 260),
}
LENGTH_DEFAULT = (90, 260, 340)

# The reference shape: three paragraphs, medium, long, short, the last one an ask.
SHAPE_PARAGRAPHS = (2, 4)      # fewer than 2 is a block of text, more than 4 is a page
SHAPE_LONGEST_RATIO = 3.0      # the long paragraph should not dwarf the others
SHAPE_LAST_MAX = 140           # the closing paragraph carries the ask and stays short

# what a variable is worth when we estimate the rendered length
VAR_SENTENCE = 65   # an icebreaker variable renders as a whole sentence
VAR_WORD = 10       # a first name, a company name, a city
SENTENCE_VARS = re.compile(
    r"icebreaker|opener|opening|intro|accroche|personalis|personaliz|"
    r"custom_message|message|ligne|phrase|hook",
    re.I,
)

MAX_SENTENCE_WORDS = 25          # past this the reader re-reads the sentence
MARKUP_RATIO_WARN = 2.0          # len(html) / len(text)
MARKUP_RATIO_FAIL = 4.0

# ---------------------------------------------------------------------------
# Word lists
# ---------------------------------------------------------------------------

def load_spam_list() -> list[str]:
    """Reuse the list in scripts/check-copy.py rather than keeping a second one."""
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "check-copy.py")
    try:
        text = open(src, encoding="utf-8").read()
    except OSError:
        return []
    block = re.search(r"^SPAM = \"\"\".*?^SPAM = \[[^\]]*\]", text, re.S | re.M)
    if not block:
        return []
    ns: dict = {}
    exec(compile(block.group(0), src, "exec"), ns)  # noqa: S102, the source is ours
    return list(ns.get("SPAM", []))


SPAM_EXTRA = [
    "dear valued", "as per my last email", "just checking in", "just following up",
    "circling back", "touching base", "per my previous", "any update on this",
    "hope you are well", "hope this email finds you", "i wanted to reach out",
    "unlock", "no obligation", "money back", "credit card", "satisfaction guaranteed",
    "offre exceptionnelle", "gratuit", "sans engagement", "profitez", "cliquez ici",
]

JARGON = [
    "synergy", "synergies", "holistic", "paradigm", "ecosystem", "seamless",
    "frictionless", "end-to-end", "best-in-class", "best in class", "turnkey",
    "disruptive", "empower", "streamline", "robust", "scalable solution",
    "value proposition", "low-hanging fruit", "move the needle", "boil the ocean",
    "north star", "secret sauce", "silver bullet", "deep dive", "circle back",
    "touch base", "bandwidth", "in the weeds", "mission-critical", "best of breed",
    "drive growth", "unlock value", "leverage our", "leverage your", "operationalize",
    "actionable insights", "thought leader", "next-gen", "solutioning", "ideate",
]

METAPHOR = [
    "think of it as", "picture this", "imagine a world", "the uber of", "the airbnb of",
    "the netflix of", "swiss army knife", "tip of the iceberg", "needle in a haystack",
    "moving parts under the hood", "drinking from the firehose", "rocket ship",
    "like a well-oiled", "the glue that holds", "a single pane of glass",
    "connect the dots", "raise the bar", "at the end of the day", "peel the onion",
]

CALENDAR = re.compile(
    r"calendly\.com|cal\.com|savvycal|zcal\.co|lemcal|hubspot\.com/meetings|"
    r"meetings\.hubspot|youcanbook|chilipiper|book a (call|time|slot)|"
    r"grab a slot|my calendar|pick a time",
    re.I,
)
CLICK_ASK = re.compile(
    r"\b(have a look at|check (it |this )?out|take a look at|see (the|our) "
    r"(page|site|demo|deck)|read more|download|watch the|sign up|try it|"
    r"create (a|your) (free )?account|start (your )?free trial)\b",
    re.I,
)
HARD_QUESTION = re.compile(
    r"(what do you (think|currently)|how (do|are) you (currently )?"
    r"(handle|handling|manage|managing|solve|solving|deal|dealing)|"
    r"what (are|is) your (biggest|current|main|top)|which of these|"
    r"tell me (about|more about)|walk me through|what does your .{0,30}look like)",
    re.I,
)
SCHEDULE_ASK = re.compile(
    r"((let me know|send me|share) (your |you )?(availability|availabilities|calendar)|"
    r"what time works|which (day|slot|time) (works|suits)|"
    r"(monday|tuesday|wednesday|thursday|friday) or (monday|tuesday|wednesday|thursday|friday)|"
    r"do any of these (times|slots)|pick a slot|propose (a few |some )?(times|slots))",
    re.I,
)
EASY_QUESTION = re.compile(
    r"^(is|are|was|were|do|does|did|would|will|should|can|could|have|has|any|"
    r"worth|open to|interested|who|shall|makes sense|want|ok if|"
    r"am i|right person)\b",
    re.I,
)
LEGALESE = re.compile(
    r"confidential|disclaimer|this (e-?mail|message) and any|privileged|"
    r"\bgdpr\b|\brgpd\b|\bsiret\b|\bsiren\b|\brcs\b|tva intracom|"
    r"registered (office|in england)|company number|please consider the environment|"
    r"do not print this",
    re.I,
)
SOCIAL = re.compile(r"linkedin\.com/(in|company)|twitter\.com|x\.com/|instagram\.com|facebook\.com", re.I)
ATTACH_WORDS = re.compile(
    r"\b(attached|attachment|i(?:'ve| have) attached|find enclosed|see the pdf|"
    r"ci-joint|pi[eè]ce jointe|en pj)\b", re.I,
)
GREETING = re.compile(r"^\s*(hi|hey|hello|dear|bonjour|salut|good (morning|afternoon))\b", re.I)
SIGNOFF = re.compile(
    r"^\s*(best|best regards|regards|cheers|thanks|thank you|kind regards|"
    r"all the best|sincerely|bien [àa] vous|cordialement|merci)\b[,.]?\s*$", re.I,
)
UNSUB = re.compile(
    r"unsubscribe|d[ée]sabonn|se d[ée]sinscrire|opt out|opt-out|stop these emails|"
    r"no more emails|remove me from|take me off", re.I,
)
VAR = re.compile(r"\{\{\s*([A-Za-z0-9_.|\s\"'-]+?)\s*\}\}|\{#\s*([A-Za-z0-9_]+)")

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def html_to_text(s: str) -> str:
    s = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", s)
    s = re.sub(r"(?i)</\s*(p|div|tr|li|h[1-6])\s*>", "\n\n", s)
    s = re.sub(r"(?i)<\s*(script|style)[^>]*>.*?</\s*\1\s*>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    s = htmlmod.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def parse_markdown(path: str) -> list[dict]:
    """Read the sequence.md shape written by outreach-write."""
    steps, cur, fence = [], None, False
    for line in open(path, encoding="utf-8").read().splitlines():
        h = re.match(r"^##\s+Step\s+(\d+)", line)
        if h:
            cur = {"n": int(h.group(1)), "subject": "", "raw": [], "attachments": [],
                   "raw_html": False, "version": "single"}
            steps.append(cur)
            fence = False
            continue
        if cur is None:
            continue
        m = re.match(r"^\*\*Subject:\*\*\s*(.*)$", line)
        if m:
            cur["subject"] = m.group(1).strip()
            continue
        if line.startswith("```"):
            fence = not fence
            continue
        if fence:
            cur["raw"].append(line)
    for s in steps:
        s["raw"] = "\n".join(s["raw"]).strip()
        s["text"] = html_to_text(s["raw"]) if "<" in s["raw"] else s["raw"]
    return steps


def parse_campaign(path: str) -> list[dict]:
    """Walk the step tree of GET /advanced/campaigns/{id}: START then next / yes / no."""
    data = json.load(open(path, encoding="utf-8"))
    root = data.get("campaign", data).get("steps") or data.get("steps")
    if isinstance(root, list):  # tolerate a flat array
        nodes = root
    else:
        nodes, queue = [], [root]
        while queue:
            node = queue.pop(0)
            if not isinstance(node, dict):
                continue
            nodes.append(node)
            for key in ("next", "yes", "no"):
                if node.get(key):
                    queue.append(node[key])
    steps, n = [], 0
    for node in nodes:
        if node.get("stepType") != "EMAIL":
            continue
        n += 1
        for i, v in enumerate(node.get("versions") or [{}]):
            if v.get("disabled"):
                continue
            steps.append({
                "n": n,
                "version": chr(65 + i) if len(node.get("versions") or []) > 1 else "single",
                "subject": (v.get("subject") or "").strip(),
                "raw": v.get("message") or "",
                "text": html_to_text(v.get("message") or ""),
                "attachments": v.get("attachments") or [],
                "raw_html": bool(v.get("rawHtml")),
            })
    return steps

# ---------------------------------------------------------------------------
# Measuring
# ---------------------------------------------------------------------------

def expand_vars(text: str) -> str:
    def sub(m):
        name = (m.group(1) or m.group(2) or "").split("|")[0].strip()
        return "x" * (VAR_SENTENCE if SENTENCE_VARS.search(name) else VAR_WORD)
    return VAR.sub(sub, text)


def body_only(text: str) -> str:
    """Drop greeting, sign-off, signature and opt-out: keep the sentences."""
    lines = text.split("\n")
    out, hit_signoff = [], False
    for i, line in enumerate(lines):
        bare = line.strip()
        if not bare:
            out.append("")
            continue
        if i < 2 and GREETING.match(bare):
            continue
        if SIGNOFF.match(bare) or UNSUB.search(bare) or "{{signature}}" in bare.lower():
            hit_signoff = True
        if hit_signoff:
            continue
        out.append(line)
    body = "\n".join(out).strip()
    # a lone name on the last line is the sign-off
    tail = body.split("\n")
    while tail and (not tail[-1].strip() or len(tail[-1].split()) <= 3 and tail[-1].strip()[:1].isupper()
                    and not tail[-1].strip().endswith((".", "?", "!"))):
        tail.pop()
    return "\n".join(tail).strip()


def measure(body: str) -> dict:
    expanded = expand_vars(body)
    paras = [p.strip() for p in re.split(r"\n\s*\n", expanded) if p.strip()]
    lines = sum(max(1, math.ceil(len(p) / CHARS_PER_LINE)) for p in paras)
    lines += max(0, len(paras) - 1)  # the blank line between paragraphs
    return {
        "chars": len(re.sub(r"\s+", " ", expanded).strip()),
        "words": len(re.findall(r"[A-Za-zÀ-ÿ0-9'’-]+", expanded)),
        "paragraphs": len(paras),
        "lines": lines,
    }


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

# ---------------------------------------------------------------------------
# The nine checks
# ---------------------------------------------------------------------------
WEIGHT = {"cta": 100, "length": 80, "attachments": 70, "images": 60,
          "html": 50, "signature": 40, "spam": 30, "jargon": 20}
_SHARED_SPAM = load_spam_list()
if not _SHARED_SPAM:
    print("warning: could not read the SPAM list out of scripts/check-copy.py, "
          "spam checks run on the extension list only", file=sys.stderr)
SPAM = _SHARED_SPAM + SPAM_EXTRA


def audit_step(step: dict) -> list[tuple]:
    """Return [(level, criterion, message)] for one step."""
    f, n = [], step["n"]
    text, raw, subject = step["text"], step["raw"], step["subject"]
    body = body_only(text)
    m = measure(body)
    step["measure"] = m
    lo, hi, cap = LENGTH.get(n, LENGTH_DEFAULT)

    # 9. one email, one call to action  (checked first, it decides the verdict)
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', raw, re.I)
    bare = re.findall(r"(?<![\"'=])\bhttps?://[^\s<>\")\]]+", text)
    urls = [u for u in hrefs + bare if not UNSUB.search(u) and "unsubscribe_link" not in u.lower()]
    urls = list(dict.fromkeys(urls))
    asks = set()
    if CALENDAR.search(text) or any(CALENDAR.search(u) for u in urls):
        asks.add("book a meeting")
    if CLICK_ASK.search(body) or (urls and not CALENDAR.search(text)):
        asks.add("go to a page")
    if SCHEDULE_ASK.search(body):
        asks.add("pick a slot")
    if "?" in body:
        asks.add("reply")
    if len(asks) > 1:
        f.append(("FAIL", "cta", f"{len(asks)} asks in one email ({', '.join(sorted(asks))}). "
                                 "Pick one, delete the others"))
    elif not asks:
        f.append(("FAIL", "cta", "no ask at all, the reader has nothing to answer"))
    else:
        f.append(("OK", "cta", f"one ask: {asks.pop()}"))

    if len(urls) > 1:
        f.append(("FAIL", "cta", f"{len(urls)} links besides the opt-out, they compete with the reply"))
    elif urls and n == 1:
        f.append(("WARN", "cta", "a link in step 1, a click here is a reply you did not get"))
    elif urls:
        f.append(("OK", "cta", "1 link"))
    else:
        f.append(("OK", "cta", "no link besides the opt-out"))

    # 8. is the ask answerable in one line
    qs = [s for s in sentences(body) if s.rstrip().endswith("?")]
    if len(qs) > 1:
        f.append(("FAIL", "cta", f"{len(qs)} questions, the reader answers none of them"))
    if SCHEDULE_ASK.search(body):
        f.append(("FAIL", "cta", "the ask makes the reader choose a slot, which is work. "
                                 "Ask a question their thumb can answer instead"))
    for q in qs:
        head = re.sub(r"^[^A-Za-z]*", "", q.strip())
        tail_clause = re.sub(r"^[^A-Za-z]*", "", q.split(",")[-1].strip())
        stem = head if EASY_QUESTION.match(head) else tail_clause
        if HARD_QUESTION.search(q) or HARD_QUESTION.search(body):
            f.append(("FAIL", "cta", f"the question needs a paragraph to answer: \"{q[:70]}\""))
        elif len(q.split()) > 18:
            f.append(("WARN", "cta", f"{len(q.split())} word question, cut it to under 12"))
        elif EASY_QUESTION.match(stem):
            f.append(("OK", "cta", "the question takes a yes or a no"))
        else:
            f.append(("WARN", "cta", f"open question, not answerable with one word: \"{q[:70]}\""))

    # 1. length
    if m["chars"] > cap:
        f.append(("FAIL", "length", f"{m['chars']} characters, {m['words']} words, "
                                    f"about {m['lines']} lines on a phone. Cap for step {n} is {cap}"))
    elif m["chars"] > hi:
        f.append(("WARN", "length", f"{m['chars']} characters, target for step {n} is {lo} to {hi}"))
    elif m["chars"] < lo and m["chars"] > 0:
        f.append(("WARN", "length", f"{m['chars']} characters, shorter than the {lo} floor, "
                                    "check it still says something"))
    else:
        f.append(("OK", "length", f"{m['chars']} characters, {m['words']} words, "
                                  f"about {m['lines']} lines on a phone"))
    # the shape, which matters as much as the total: medium, long, short with the ask
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    lo_p, hi_p = SHAPE_PARAGRAPHS
    if len(paras) > hi_p:
        f.append(("WARN", "length", f"{len(paras)} paragraphs, the reference shape is three: "
                                    "one medium, one long, one short that carries the ask"))
    elif len(paras) < lo_p and m["chars"] > 120:
        f.append(("WARN", "length", "one block of text, break it into a medium paragraph, "
                                    "a long one, and a short one with the ask"))
    if len(paras) >= 2:
        lens = [len(x) for x in paras]
        if min(lens) and max(lens) / min(lens) > SHAPE_LONGEST_RATIO:
            f.append(("WARN", "length", f"one paragraph is {max(lens)} characters against "
                                        f"{min(lens)} for the shortest, even them out"))
        if len(paras[-1]) > SHAPE_LAST_MAX:
            f.append(("WARN", "length", f"the closing paragraph is {len(paras[-1])} characters, "
                                        "the ask lands better in one short line"))
        elif paras[-1].rstrip().endswith("?"):
            f.append(("OK", "length", "three parts and the ask closes on a question"))
    for s in sentences(body):
        if len(s.split()) > MAX_SENTENCE_WORDS:
            f.append(("WARN", "jargon", f"{len(s.split())} word sentence, the reader re-reads it: "
                                        f"\"{s[:60]}...\""))

    # 2. HTML
    if step.get("raw_html"):
        f.append(("FAIL", "html", "the step is flagged rawHtml, it was pasted from a template"))
    tags = re.findall(r"<\s*([a-zA-Z]+)", raw)
    heavy = [t.lower() for t in tags if t.lower() in
             {"table", "tr", "td", "tbody", "font", "center", "colgroup", "th"}]
    styles = len(re.findall(r'style\s*=\s*["\']', raw, re.I))
    if heavy:
        f.append(("FAIL", "html", f"layout markup in the body: {len(heavy)} of "
                                  f"{', '.join(sorted(set(heavy)))}"))
    if styles > 2:
        f.append(("FAIL", "html", f"{styles} inline styles, a person writing an email does not do that"))
    elif styles:
        f.append(("WARN", "html", f"{styles} inline style(s), drop them"))
    if raw and text:
        ratio = len(raw) / max(1, len(text))
        if ratio >= MARKUP_RATIO_FAIL:
            f.append(("FAIL", "html", f"{ratio:.1f} characters of markup per character of text"))
        elif ratio >= MARKUP_RATIO_WARN:
            f.append(("WARN", "html", f"{ratio:.1f} characters of markup per character of text"))
    if not heavy and styles == 0 and not step.get("raw_html"):
        f.append(("OK", "html", "paragraphs and links only"))

    # 3. spam trigger words
    low = body.lower()
    hits = sorted({t for t in SPAM if t and t in low})
    subject_hits = sorted({t for t in SPAM if t and t in subject.lower()})
    if subject_hits:
        f.append(("FAIL", "spam", f"spam trigger in the subject: {', '.join(subject_hits)}"))
    if len(hits) >= 3:
        f.append(("FAIL", "spam", f"a stack of {len(hits)}: {', '.join(hits)}"))
    elif hits:
        f.append(("WARN", "spam", f"trigger word: {', '.join(hits)}"))
    else:
        f.append(("OK", "spam", "no trigger word"))

    # 4. metaphors and hollow jargon
    jhits = sorted({t for t in JARGON if t in low})
    mhits = sorted({t for t in METAPHOR if t in low})
    if mhits:
        f.append(("FAIL", "jargon", f"metaphor the reader has to decode: {', '.join(mhits)}"))
    if len(jhits) >= 3:
        f.append(("FAIL", "jargon", f"{len(jhits)} hollow terms: {', '.join(jhits)}"))
    elif jhits:
        f.append(("WARN", "jargon", f"hollow term: {', '.join(jhits)}"))
    if not jhits and not mhits:
        f.append(("OK", "jargon", "plain words"))

    # 5. images
    imgs = re.findall(r"<\s*img\b", raw, re.I) + re.findall(r"!\[[^\]]*\]\(", raw)
    bg = re.findall(r"background-image\s*:", raw, re.I) + re.findall(r"\bcid:", raw, re.I)
    if imgs or bg:
        f.append(("FAIL", "images", f"{len(imgs) + len(bg)} image(s) in the body. "
                                    "The open pixel is already one, a second one reads as a newsletter"))
    else:
        f.append(("OK", "images", "no image"))

    # 6. signature
    sig_zone = text[text.lower().find("{{signature}}"):] if "{{signature}}" in text.lower() else ""
    tail = text[len(body):] if body and text.startswith(body[:40]) else text.split("\n\n")[-1]
    zone = sig_zone + "\n" + tail
    if "{{signature}}" in text.lower():
        f.append(("NOTE", "signature", "the signature is stored in Emelia, not in this text. "
                                       "Read it in a test email before you sign this off"))
    sig_bad = []
    if re.search(r"<\s*img\b", zone, re.I):
        sig_bad.append("an image or a logo")
    if LEGALESE.search(zone):
        sig_bad.append("legal boilerplate")
    if len(SOCIAL.findall(zone)) > 1:
        sig_bad.append("several social links")
    if re.search(r"^\s*[\"“].{20,}[\"”]\s*$", zone, re.M):
        sig_bad.append("a quote")
    sig_lines = [l for l in zone.split("\n") if l.strip()]
    if len(sig_lines) > 4:
        sig_bad.append(f"{len(sig_lines)} lines")
    if sig_bad:
        f.append(("FAIL", "signature", "the signature carries " + ", ".join(sig_bad) +
                                       ". Name, company, one line, nothing else"))
    elif not sig_zone:
        f.append(("OK", "signature", "light"))

    # 7. attachments
    if step.get("attachments"):
        names = ", ".join(a.get("name", "?") for a in step["attachments"])
        f.append(("FAIL", "attachments", f"{len(step['attachments'])} attachment(s) ({names}). "
                                         "Worse than an image: filters open them, people do not"))
    elif ATTACH_WORDS.search(text):
        f.append(("WARN", "attachments", "the text mentions an attachment"))
    else:
        f.append(("OK", "attachments", "none"))

    # the opt-out, which is the one link that belongs there
    has_unsub = bool(UNSUB.search(raw))
    if n == 1 and has_unsub:
        f.append(("WARN", "cta", "opt-out link in step 1. The rule here is step 2 onward"))
    if n > 1 and not has_unsub:
        f.append(("WARN", "cta", "no opt-out from step 2 onward, and no List-Unsubscribe header "
                                 "without it"))
    if has_unsub and re.search(r">\s*https?://[^<]*<", raw):
        f.append(("WARN", "cta", "the opt-out shows a raw URL, give it words instead"))
    return f

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    steps = parse_campaign(path) if path.endswith(".json") else parse_markdown(path)
    if not steps:
        print(f"no email step found in {path}")
        return 2

    worst, totals = {}, {"FAIL": 0, "WARN": 0}
    verdicts = []
    for step in steps:
        findings = audit_step(step)
        label = f"step {step['n']}" + ("" if step["version"] == "single" else f" version {step['version']}")
        fails = [x for x in findings if x[0] == "FAIL"]
        warns = [x for x in findings if x[0] == "WARN"]
        totals["FAIL"] += len(fails)
        totals["WARN"] += len(warns)
        verdict = "REWRITE" if fails else ("FIX" if warns else "SHIP")
        verdicts.append((label, verdict, len(fails), len(warns)))
        print(f"\n{label}: {verdict}")
        m = step["measure"]
        print(f"  {m['chars']} chars, {m['words']} words, {m['paragraphs']} paragraphs, "
              f"about {m['lines']} rendered lines on a phone")
        for level, crit, msg in findings:
            if level == "OK":
                continue
            if level == "NOTE":
                print(f"  NOTE {crit:12} {msg}")
                continue
            print(f"  {level:4} {crit:12} {msg}")
            w = WEIGHT.get(crit, 10) + (100 if level == "FAIL" else 0)
            if w > worst.get("w", -1):
                worst = {"w": w, "crit": crit, "msg": msg, "step": label}

    print("\n" + "=" * 72)
    for label, verdict, nf, nw in verdicts:
        print(f"  {label:24} {verdict:8} {nf} blocking, {nw} to fix")
    overall = "REWRITE" if totals["FAIL"] else ("FIX" if totals["WARN"] else "SHIP")
    print(f"\noverall: {overall}   {totals['FAIL']} blocking, {totals['WARN']} to fix, "
          f"{len(steps)} email step(s)")
    if worst:
        print(f"\npriority: {worst['step']}, {worst['crit']} -> {worst['msg']}")
    return 1 if totals["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
