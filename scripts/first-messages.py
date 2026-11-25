#!/usr/bin/env python3
"""Build the prospect cards, check the messages written per contact, merge them.

The recommended way of writing in this repository: the first message of a campaign is
written for every contact, in batches of about eight, in three paragraphs (an
observation, the offer, one question); each follow up is either shared by the target or
written per contact too, as the user chose. This script does the mechanical part around
the model:

    python3 scripts/first-messages.py cards  outreach/leads.csv --out outreach/copy
    python3 scripts/first-messages.py check  outreach/copy/out-01.json \
        --cards outreach/copy/cards-01.json --header outreach/copy/header.md \
        --channel email --report outreach/copy/check-01.json
    python3 scripts/first-messages.py followups outreach/copy/followups.json \
        --header outreach/copy/header.md --channel email
    python3 scripts/first-messages.py followups outreach/copy/fu-01.json \
        --cards outreach/copy/cards-01.json --first outreach/copy/out-01.json \
        --header outreach/copy/header.md --channel email --report outreach/copy/fucheck-01.json
    python3 scripts/first-messages.py merge  outreach/leads.csv --kind first \
        --cards 'outreach/copy/cards-*.json' --out 'outreach/copy/out-*.json' --lang fr
    python3 scripts/first-messages.py merge  outreach/leads.csv --kind followups \
        --cards 'outreach/copy/cards-*.json' --out 'outreach/copy/fu-*.json' --lang fr

cards      one JSON file per batch, with what the model may read about each contact and
           nothing else: never the last name, the address, the website or the profile URL.
           Half emojis and broken characters are removed before anything reaches a model.
check      the first messages of a batch: grave faults (the message is not kept), light
           faults (it is retried once), the batch faults (same openings, repeated
           sequences of words), and the messages over the maximum, to shorten.
followups  shared follow ups, or with --cards the follow ups written per contact, which
           also keep the rules of the first message and take another angle than it.
merge      writes greeting, subject_line, message, subject_line_3, message_2 to message_4
           (li_ on LinkedIn), message_sources and message_date into leads.csv for what has
           no grave fault left, and counts a failed attempt for the rest: at the third,
           the contact is marked dropped and never sent anything.
Every command but merge exits 1 when a grave fault is left.
"""
import argparse
import csv
import glob
import html
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Lengths, counted on the body: observation, offer and question joined by a blank line,
# without the greeting and without the signature. The prompt aims lower, because a model
# overshoots by 10 to 25% even when told the number.
# ---------------------------------------------------------------------------
# (min, max, hard cap). By email the table is the one of scripts/audit-emails.py, read
# from there so the two never disagree; LinkedIn has its own.
def _email_lengths():
    src = Path(__file__).parent / "audit-emails.py"
    m = re.search(r"^LENGTH\s*=\s*(\{.+?\})", src.read_text(encoding="utf-8"), re.S | re.M) \
        if src.exists() else None
    try:
        return eval(m.group(1)) if m else {}
    except Exception:
        return {}


EMAIL_LENGTH = _email_lengths() or {1: (260, 480, 504), 2: (90, 220, 280),
                                    3: (180, 380, 400), 4: (80, 200, 260)}
LINKEDIN_LENGTH = {1: (150, 300, 315), 2: (80, 200, 210), 3: (120, 280, 294), 4: (80, 200, 210)}
LENGTHS = {"email": EMAIL_LENGTH, "linkedin": LINKEDIN_LENGTH}
GRAVE_UNDER = 0.60
QUESTION_MAX = 90
SUBJECT_SOFT_WORDS, SUBJECT_SOFT_CHARS, SUBJECT_HARD_CHARS = 7, 48, 80
MESSAGE_MAX, SUBJECT_MAX = 2000, 150      # our own cap on a variable, see outreach-campaign
LINK_MIN, VOCAB_MIN = 2, 15               # the observation and offer link check
ATTEMPTS_MAX = 3

# What the card may carry, in this order, with the column of leads.csv and the cut.
CARD_FIELDS = [
    ("First name", "first_name", None),
    ("Title", "job_title", None),
    ("LinkedIn headline", "x_headline", 200),
    ("Role description", "x_role_description", 600),
    ("LinkedIn summary, in their words", "x_linkedin_summary", 400),
    ("Skills", "x_skills", 250),
    ("Career, latest first", "x_experiences", 500),
    ("Company (NEVER name it)", "company_name", None),
    ("City", "city", None),
    ("Headcount", "company_headcount", None),
    ("Industry", "company_industry", None),
    ("What their company does", "x_company_description", 700),
    ("Recent signal", "signal", 200),
]
# Never sent to a model: they give it nothing to write with, and an address or a URL in
# the prompt is one that can end up quoted in the message.
NEVER = {"last_name", "full_name", "email", "phone", "linkedin_url", "company_website",
         "company_domain", "company_linkedin_url"}

STOP = set("""
a an and are as at be been but by can could did do does for from had has have how i if
in into is it its may more most much must no not of on or our out over so some such
than that the their them then there these they this those to too under up very was we
were what when where which while who why will with would you your yours
un une des les le la de du et en est sont pour par sur dans avec sans plus moins tres
qui que quoi dont ou mais donc car ce cet cette ces se sa son ses leur leurs nous vous
votre vos notre nos il elle ils elles on au aux ne pas peu bien tout tous toute toutes
often rarely usually every year years company companies business team teams people
souvent rarement parfois chaque annee annees entreprise entreprises societe equipe
equipes personne personnes moment temps fois meme autre autres aussi encore deja
""".split())

GENERIC_COMPANY = set("""
group groupe holding france paris europe international conseil consulting consultants
services service solutions solution agency agence cabinet studio company societe
partners partenaires associes associates industries industrie technologies technology
digital sas sasu sarl eurl ltd llc inc corp gmbh the les des
""".split())

NUMBER_WORDS = set("""
two three four five six seven eight nine ten eleven twelve twenty thirty forty fifty
hundred hundreds thousand thousands dozen dozens million millions
deux trois quatre cinq six sept huit neuf dix onze douze vingt trente quarante cinquante
soixante cent cents mille dizaine dizaines douzaine douzaines vingtaine trentaine
quarantaine cinquantaine centaine centaines millier milliers million millions
""".split())


def pats(*words):
    return [re.compile(w, re.I) for w in words]


# Each list holds the English and the French forms. The prompt carries the same lists,
# in two blocks, in skills/outreach-write/references/first-message-prompt.md section 5.
FLATTERY = pats(r"\bimpressi", r"\bremarkabl", r"\bremarquabl", r"\badmirabl",
                r"\bbravo\b", r"\bcongrat", r"\bf[ée]licit", r"\bbrillian", r"\bbrillant",
                r"\bexceptional", r"\bexceptionnel", r"\bpassionnant", r"\binspir",
                r"\bbel(le)? (parcours|r[ée]ussite)", r"\bgreat (career|track record)",
                r"\bhats off\b", r"\bchapeau\b",
                r"\b(agency|firm|company|startup|award|employer) of the year\b",
                r"\b(agence|cabinet|entreprise|start-?up|prix|troph[ée]e|employeur)s? de l'ann[ée]e\b",
                r"\branked among\b", r"\bclass[ée]e? parmi\b")
WORN_IMAGES = pats(r"\bjuggl", r"\bjongl", r"\bmany hats\b", r"\bcasquettes?\b",
                   r"\bbehind the scenes\b", r"\bin the shadows?\b", r"\bdans l'ombre\b",
                   r"\ben coulisses?\b", r"\blifeblood\b", r"\bnerf de la guerre\b",
                   r"\bcore business\b", r"\bc(oe|œ)ur de m[ée]tier\b", r"\bday[- ]to[- ]day\b",
                   r"\bau quotidien\b", r"\bcornerstone\b", r"\bpierre angulaire\b",
                   r"\bunicorn hire\b", r"\bmouton [àa] cinq pattes\b", r"\bmental load\b",
                   r"\bcharge mentale\b", r"\blike yours\b", r"\bcomme (la|le) v[ôo]tre\b")
ABSOLUTES = pats(r"\bno one( else)?\b", r"\bnobody\b", r"\beveryone\b", r"\beverybody\b",
                 r"\bpersonne( d'autre)? ne\b", r"\btout le monde\b")
SAID_SOURCE = pats(r"\bi (saw|noticed|read)\b", r"\byour profile\b", r"\bwhile (browsing|reading)\b",
                   r"\bj'ai (vu|lu|remarqu[ée])\b", r"\bvotre profil\b", r"\ben parcourant\b",
                   r"\ben lisant\b")
FAMILIAR = pats(r"\bsounds good\b", r"\bfancy a\b", r"\bhop on a call\b", r"\bcool\b",
                r"\bawesome\b", r"\bsuper\b", r"\bça colle\b", r"\bon s'appelle\b",
                r"\bça vous dit\b", r"\bça vous tente\b", r"\bsympa\b", r"\btop\b")
SET_UP = pats(r"\bfrom (the address of )?your (web)?site\b", r"\bwe would (propose|suggest|define)\b",
              r"\bfor example\b", r"\bfor instance\b", r"\b[àa] partir de (l'adresse de )?votre site\b",
              r"\bpropos(er|erions|erait|erons) une cible\b", r"\bnous d[ée]finir(ions|ons)\b",
              r"\bpar exemple\b")
WORN_FORMULAS = pats(r"\baims to take .* off your\b", r"\btake care of (this|that) (part|search)\b",
                     r"\bvise [àa] vous retirer\b", r"\bprendre? en charge cette (partie|part|recherche)\b")
CLOSINGS = pats(r"\bbest regards\b", r"\bkind regards\b", r"\bregards\b", r"\bbest wishes\b",
                r"\bsincerely\b", r"\bcheers\b", r"\bhave a (great|nice|good) day\b",
                r"\bthanks in advance\b", r"\bthank you in advance\b", r"\btalk soon\b",
                r"\bbien [àa] vous\b", r"\bcordialement\b", r"\bbien cordialement\b",
                r"\bbelle journ[ée]e\b", r"\bbonne journ[ée]e\b", r"\b[àa] bient[ôo]t\b",
                r"\bmerci d'avance\b")
OPENINGS = pats(r"^\s*i hope\b", r"^\s*allow me\b", r"^\s*i am reaching out\b", r"^\s*i'?m reaching out\b",
                r"^\s*i am\b", r"^\s*i'm\b", r"^\s*my name is\b",
                r"^\s*j'esp[èe]re\b", r"^\s*je me permets\b", r"^\s*je vous contacte\b",
                r"^\s*je suis\b")
EMAIL_WORDS = pats(r"\be-?mails?\b", r"\bmails?\b", r"\bmailbox(es)?\b", r"\binbox(es)?\b",
                   r"\bcourriels?\b", r"\bbo[îi]tes? (aux lettres|mail|e-?mail)\b", r"\bmessagerie\b")
EMAIL_CHANNEL = pats(r"\b(by|via) e-?mail\b", r"\b(this|my|our) e-?mail\b", r"\breply to this (e-?)?mail\b",
                     r"\b(par|via) e-?mail\b", r"\b(ce|cet|mon|ma|notre) e-?mail\b", r"\bbo[îi]te mail\b",
                     r"\br[ée]pondre [àa] ce (e-?)?mail\b")
DATES = pats(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
             r"\b\d{1,2}(st|nd|rd|th)? (january|february|march|april|may|june|july|august|september|october|november|december) \d{4}\b",
             r"\b\d{1,2} (janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|d[ée]cembre) \d{4}\b",
             r"\b(in|en) (19|20)\d\d\b", r"\b(noted|recorded|dated) on\b", r"\b(relev[ée]|dat[ée]) (le|du)\b")
STRUCK_PRICE = pats(r"\binstead of \S*\d", r"\bau lieu de \S*\d")
# Follow ups only.
FOLLOWUP_OPENINGS = pats(r"^\s*(one point that matters|another angle|quick reminder|just a reminder|"
                         r"i am following up|i'm following up|following up|to complete|following my|"
                         r"as agreed|for your information|i wanted|i wished)\b",
                         r"^\s*(un point qui compte|autre angle|petit rappel|je reviens vers vous|"
                         r"pour compl[ée]ter|suite [àa]|comme convenu|pour information|je voulais|"
                         r"je souhaitais)\b")
FOLLOWUP_CLICHES = pats(r"\bmy door (is|remains) open\b", r"\bi won'?t insist\b", r"\bclos(e|ing) this thread\b",
                        r"\bclutter your inbox\b", r"\blast attempt\b", r"\bdon'?t hesitate\b",
                        r"\bwithout (a )?reply from you\b", r"\bcircle back later\b", r"\bnot to disturb you\b",
                        r"\bleave you alone\b", r"\bat your disposal\b", r"\blook(ing)? forward to (talking|hearing)\b",
                        r"\bas i wrote\b", r"\bmy previous (e-?mail|message)\b",
                        r"\bma porte reste ouverte\b", r"\bje n'insiste pas\b", r"\bje ne vais pas insister\b",
                        r"\bje clos ce fil\b", r"\bencombrer votre bo[îi]te\b", r"\bderni[èe]re tentative\b",
                        r"\bn'h[ée]sitez pas\b", r"\bsans r[ée]ponse de votre part\b",
                        r"\bje me permets une derni[èe]re\b", r"\brevenir vers vous plus tard\b",
                        r"\bne pas vous d[ée]ranger\b", r"\bje vous laisse tranquille\b",
                        r"\bje reste [àa] votre disposition\b", r"\bau plaisir d'[ée]changer\b",
                        r"\bcomme je vous l'[ée]crivais\b", r"\bsuite [àa] mon message\b",
                        r"\bmon pr[ée]c[ée]dent (e-?mail|message)\b")
PRESUMPTION = pats(r"\byou (feel|know that|must be|probably feel)\b", r"\bas you know\b",
                   r"\bvous vous sentez\b", r"\bvous savez que\b", r"\bcomme vous le savez\b")
PROMISE = pats(r"\bguarantee", r"\byou will (get|gain|win|save)\b", r"\bnever again\b",
               r"\bgaranti", r"\bvous obtiendrez\b", r"\bvous gagnerez\b", r"\bplus jamais\b")
TESTIMONIAL = pats(r"\b(says|reports|testifies|cite[s]?|rapporte|t[ée]moigne)\b", r"[«\"]\s*\d")

WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿ]+)?")
SURROGATE = re.compile("[\ud800-\udfff\ufffd]")


def safe_text(s):
    """Remove half emojis (lone surrogates) and replacement characters, which make a model
    API refuse the whole request, then collapse the spaces."""
    s = SURROGATE.sub("", str(s or ""))
    return re.sub(r"[ \t]+", " ", s).strip()


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


def words(s):
    return WORD.findall(s or "")


def stems(s):
    out = set()
    for w in words(s):
        f = fold(w)
        if len(f) >= 4 and f not in STOP and not f.isdigit():
            out.add(f[:5])
    return out


def numbers(s):
    found = set(re.findall(r"\d+(?:[.,]\d+)?", s or ""))
    found |= {fold(w) for w in words(s) if fold(w) in NUMBER_WORDS}
    return found


def hits(patterns, text):
    return [p.pattern for p in patterns if p.search(text or "")]


def read_header(path):
    text = Path(path).read_text(encoding="utf-8") if path else ""
    return text


def load_json(pattern):
    out = []
    for path in sorted(glob.glob(pattern)) or [pattern]:
        data = json.load(open(path, encoding="utf-8"))
        out.append((path, data))
    return out


# ---------------------------------------------------------------------------
# cards
# ---------------------------------------------------------------------------
def build_cards(args):
    rows = list(csv.DictReader(open(args.leads, encoding="utf-8", errors="replace")))
    segments = sorted({r.get("segment", "") for r in rows if r.get("segment")})
    several = len(segments) > 1
    todo = []
    for r in rows:
        if (r.get("writing_status") or "") == "dropped":
            continue
        if args.skip_done and (r.get("message") or r.get("li_message")):
            continue
        todo.append(r)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    batches = [todo[i:i + args.batch] for i in range(0, len(todo), args.batch)]
    for b, batch in enumerate(batches, 1):
        cards = []
        for i, r in enumerate(batch):
            summary = safe_text(r.get("x_linkedin_summary"))
            lines = []
            for label, col, cut in CARD_FIELDS:
                v = safe_text(r.get(col))
                if not v:
                    continue
                if col == "x_headline" and fold(v) == fold(safe_text(r.get("job_title"))):
                    continue
                if col == "x_role_description" and summary:
                    cut = 400
                if col == "x_company_description" and summary:
                    cut = 500
                if cut and len(v) > cut:
                    v = v[:cut].rsplit(" ", 1)[0]
                lines.append(f"{label}: {v}")
            if several and r.get("segment"):
                lines.append(f"Their target: {r['segment']}")
            cards.append({"index": i, "lead_id": r.get("lead_id") or r.get("email"),
                          "company": safe_text(r.get("company_name")),
                          "trade_name": safe_text(r.get("x_trade_name")),
                          "city": safe_text(r.get("city")),
                          "card": "\n".join(lines)})
        path = out_dir / f"cards-{b:02d}.json"
        json.dump(cards, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(todo)} contacts in {len(batches)} batch(es) of up to {args.batch}, in {out_dir}")
    print("never sent to the model: " + ", ".join(sorted(NEVER)))
    return 0


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------
def company_named(text, card):
    names = [n for n in (card.get("company"), card.get("trade_name")) if n]
    low = fold(text)
    for n in names:
        if len(n) >= 3 and re.search(r"\b" + re.escape(fold(n)) + r"\b", low):
            return n
    common = {fold(w) for w in words(card.get("card", "")) if w[:1].islower()}
    city = fold(card.get("city") or "")
    for n in names:
        for tok in words(n):
            f = fold(tok)
            if (len(f) < 4 or f in STOP or f in GENERIC_COMPANY or f == city or f in common
                    or not tok[:1].isupper()):
                continue
            if re.search(r"\b" + re.escape(tok) + r"\b", text):
                return tok
    return None


def check_message(m, card, header_text, target_text, channel, email_is_product):
    grave, light = [], []
    obs, offer, q = ((m.get(k) or "").strip() for k in ("observation", "offer", "question"))
    subj = (m.get("subject") or "").strip()
    body = "\n\n".join(x for x in (obs, offer, q) if x)
    full = body + "\n" + subj
    card_text = card.get("card", "")

    for part, name in ((obs, "observation"), (offer, "offer"), (q, "question")):
        if not part:
            grave.append(f"the {name} is empty")
    lo, hi, cap = LENGTHS[channel][1]
    n = len(body)
    if n > cap or n < lo * GRAVE_UNDER:
        grave.append(f"{n} characters, the bounds are {lo} to {hi}")
    elif n > hi or n < lo:
        light.append(f"{n} characters, the bounds are {lo} to {hi}")
    if "?" not in body:
        grave.append("no question")
    invented = numbers(obs) - numbers(card_text)
    if invented:
        grave.append(f"a number in the observation the card does not give: {', '.join(sorted(invented))}")
    if channel == "linkedin":
        bad = hits(EMAIL_CHANNEL if email_is_product else EMAIL_WORDS, body)
        if bad:
            grave.append("an email word on LinkedIn")
        if subj:
            light.append("a subject on LinkedIn, leave it empty")
    else:
        if not subj:
            grave.append("no subject")
        elif len(subj) > SUBJECT_HARD_CHARS:
            grave.append(f"subject of {len(subj)} characters")
        else:
            if len(subj.split()) > SUBJECT_SOFT_WORDS or len(subj) > SUBJECT_SOFT_CHARS:
                light.append("subject too long, 3 to 6 words and 45 characters")
            sub_stems = {fold(w)[:5] for w in words(subj) if len(w) >= 4}
            acronyms = [w for w in words(subj) if len(w) >= 2 and w.isupper()]
            if (sub_stems and not (sub_stems & stems(body))) or any(a not in body for a in acronyms):
                light.append("the subject shares no word with the observation")
    if hits(CLOSINGS, body):
        grave.append("a closing formula, the message ends on its last useful sentence")
    if re.search("[\u2013\u2014]", full):
        grave.append("an em dash or an en dash")
    named = company_named(full, card)
    if named:
        grave.append(f"the recipient's company is named: {named}")
    if re.search(r"[{}]|https?://|\bwww\.", full):
        grave.append("a variable, a brace or a link")
    if hits(DATES, full) or hits(STRUCK_PRICE, full):
        grave.append("a date or a struck price")

    if re.search(r"\b(you|your|yours)\b", obs, re.I) or re.search(r"\b(vous|votre|vos)\b", obs, re.I):
        light.append("'you' in the observation, it talks about the problem, not about them")
    head_stems = stems(header_text)
    if len(head_stems) >= VOCAB_MIN:
        own = stems(obs) - stems(card_text) - stems(target_text)
        if len(own & (stems(offer) | head_stems)) < LINK_MIN:
            light.append("the observation has no link with the offer: read alone, it must let "
                         "the reader guess what the sender sells")
    rest = body[: body.rfind(q)] if q and q in body else body
    if "?" in rest or "!" in body:
        light.append("a question mark or an exclamation mark outside the final question")
    if q.count("?") > 1 or (q and not q.rstrip().endswith("?")):
        light.append("one question, at the end")
    if len(q) > QUESTION_MAX:
        light.append(f"question of {len(q)} characters, {QUESTION_MAX} at most")
    for patterns, label in ((SET_UP, "set up talk"), (WORN_FORMULAS, "worn formula"),
                            (FAMILIAR, "familiarity"), (FLATTERY, "flattery"),
                            (WORN_IMAGES, "worn image"), (ABSOLUTES, "absolute"),
                            (SAID_SOURCE, "says where it read about them")):
        if hits(patterns, body):
            light.append(label)
    if hits(OPENINGS, obs):
        light.append("forbidden opening")
    profile_figures = [x for x in re.findall(r"\d+(?:[.,]\d+)?", body) if x in header_text]
    if len(profile_figures) > 1:
        light.append("more than one figure from the sender block")
    card_low = " ".join(fold(card_text).split())
    for s in m.get("sources") or []:
        if " ".join(fold(s).split()) not in card_low:
            light.append(f"source not found on the card: {s[:60]}")
    return grave, light, n > hi


def first_words(s, k):
    return tuple(fold(w) for w in words(s)[:k])


def ngrams(s, k, exclude):
    ws = [fold(w) for w in words(s)]
    out = set()
    for i in range(len(ws) - k + 1):
        g = ws[i:i + k]
        if not any(w[:5] in exclude for w in g if len(w) >= 4):
            out.add(tuple(g))
    return out


def check_batch(msgs, header_text, target_text):
    """Light faults on the second and later messages that repeat an earlier one."""
    faults = {m.get("index"): [] for m in msgs}
    exclude = stems(header_text) | stems(target_text)
    seen = {"obs3": {}, "off3": {}, "q2": {}, "s2": {}, "obs1": {}}
    for m in msgs:
        i = m.get("index")
        for key, field, k in (("obs3", "observation", 3), ("off3", "offer", 3),
                              ("q2", "question", 2), ("s2", "subject", 2)):
            fw = first_words(m.get(field) or "", k)
            if fw and fw in seen[key]:
                faults[i].append(f"{field} starts like message {seen[key][fw]}")
            elif fw:
                seen[key][fw] = i
        f1 = first_words(m.get("observation") or "", 1)
        seen["obs1"].setdefault(f1, []).append(i)
        if f1 and len(seen["obs1"][f1]) > 2:
            faults[i].append("more than two observations open on the same word")
    for field, k in (("observation", 4), ("offer", 3)):
        count = {}
        for m in msgs:
            for g in ngrams(m.get(field) or "", k, exclude):
                count.setdefault(g, []).append(m.get("index"))
        for g, idx in count.items():
            for i in idx[2:]:
                faults[i].append(f"the {field} repeats '{' '.join(g)}' from two others")
    return faults


def run_check(args):
    header_text = read_header(args.header)
    target_text = args.target or ""
    cards = {c["index"]: c for c in json.load(open(args.cards, encoding="utf-8"))}
    data = json.load(open(args.file, encoding="utf-8"))
    msgs = data.get("messages", data) if isinstance(data, dict) else data
    report, grave_left = {}, 0
    missing = sorted(set(cards) - {m.get("index") for m in msgs})
    batch = check_batch(msgs, header_text, target_text)
    for m in msgs:
        i = m.get("index")
        card = cards.get(i)
        if card is None:
            print(f"index {i}: no card with that index, ignored")
            continue
        grave, light, too_long = check_message(m, card, header_text, target_text,
                                               args.channel, args.email_is_product)
        light += batch.get(i, [])
        grave_left += bool(grave)
        report[i] = {"lead_id": card.get("lead_id"), "grave": grave, "light": light,
                     "shorten": too_long and not [g for g in grave if "characters" in g]}
        state = "GRAVE" if grave else ("RETRY" if light else "KEEP")
        if too_long and state == "KEEP":
            state = "SHORTEN"
        print(f"index {i:>2}  {state:7}  " + "; ".join(grave + light))
    for i in missing:
        print(f"index {i:>2}  MISSING  the model did not write this one, ask again")
        report[i] = {"lead_id": cards[i].get("lead_id"), "grave": ["missing"], "light": [],
                     "shorten": False}
        grave_left += 1
    if args.report:
        json.dump(report, open(args.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(msgs)} message(s), {grave_left} with a grave fault")
    return 1 if grave_left else 0


# ---------------------------------------------------------------------------
# followups
# ---------------------------------------------------------------------------
def followup_faults(f, channel, email_is_product, header_text):
    """The rules every follow up keeps, shared or personalised."""
    step, text, subj = f.get("step"), (f.get("body") or "").strip(), (f.get("subject") or "").strip()
    grave, light = [], []
    if re.search(r"[{}]|https?://|\bwww\.", text + subj):
        grave.append("a variable, a brace or a link: the greeting is added for you")
    lo, hi, cap = LENGTHS[channel].get(step, (80, 280, 300))
    n = len(text)
    if n > cap or n < lo * GRAVE_UNDER:
        grave.append(f"{n} characters, the bounds are {lo} to {hi}")
    elif n > hi or n < lo:
        light.append(f"{n} characters, the bounds are {lo} to {hi}")
    sentences = [x for x in re.split(r"(?<=[.?!])\s+", text) if x.strip()]
    if text.count("?") != 1 or not sentences or not sentences[-1].rstrip().endswith("?"):
        grave.append("exactly one question mark, on the last sentence")
    if "!" in text:
        light.append("an exclamation mark")
    if re.search("[\u2013\u2014]", text + subj):
        grave.append("an em dash or an en dash")
    figures = [x for x in re.findall(r"\d+(?:[.,]\d+)?", text) if x != "15"]
    if [x for x in figures if x not in header_text]:
        grave.append("a figure the sender block does not give")
    if len([x for x in figures if x in header_text]) > 1:
        light.append("more than one figure from the sender block")
    if re.search(r"\b\d+\s*min", text) and step != 3:
        light.append("only follow up 3 asks for the conversation")
    if channel == "email":
        if step in (2, 4) and subj:
            light.append("follow ups 2 and 4 stay in the thread: empty subject")
        if step == 3 and not subj:
            grave.append("follow up 3 starts a new thread and needs a subject")
    elif subj:
        light.append("a subject on LinkedIn")
    if channel == "linkedin" and hits(EMAIL_CHANNEL if email_is_product else EMAIL_WORDS, text):
        grave.append("an email word on LinkedIn")
    if hits(CLOSINGS, text):
        grave.append("a closing formula")
    for patterns, label in ((FOLLOWUP_OPENINGS, "forbidden opening"), (OPENINGS, "forbidden opening"),
                            (FOLLOWUP_CLICHES, "cliche, or a reference to an earlier message"),
                            (PRESUMPTION, "presumption about the reader"), (PROMISE, "promise"),
                            (TESTIMONIAL, "testimonial plastered in"),
                            (FAMILIAR, "familiarity"), (WORN_IMAGES, "worn image")):
        if hits(patterns, text):
            light.append(label)
    if re.search(r"^[^\n.?!]{2,60}:\s", text):
        light.append("an announcement followed by a colon")
    if header_text:
        hw = [fold(w) for w in words(header_text)]
        grams = {tuple(hw[i:i + 5]) for i in range(len(hw) - 4)}
        tw = [fold(w) for w in words(text)]
        if any(tuple(tw[i:i + 5]) in grams for i in range(len(tw) - 4)):
            light.append("five words copied from the sender block: a feature, not an argument")
    return grave, light


def run_followups(args):
    header_text = read_header(args.header)
    target_text = args.target or ""
    data = json.load(open(args.file, encoding="utf-8"))
    graves = 0
    if not args.cards:                                 # shared: one set for the target
        items = data.get("followups", data) if isinstance(data, dict) else data
        starts = {}
        for f in items:
            grave, light = followup_faults(f, args.channel, args.email_is_product, header_text)
            fw = first_words(f.get("body") or "", 2)
            if fw in starts:
                light.append(f"starts like follow up {starts[fw]}")
            starts.setdefault(fw, f"{f.get('step')}{f.get('version') or ''}")
            graves += bool(grave)
            state = "GRAVE" if grave else ("RETRY" if light else "KEEP")
            print(f"follow up {f.get('step')}{f.get('version') or ''}  {state:5}  " + "; ".join(grave + light))
        return 1 if graves else 0

    # personalised: one set per contact, with the rules of the first message as well
    cards = {c["index"]: c for c in json.load(open(args.cards, encoding="utf-8"))}
    firsts = {}
    if args.first:
        fd = json.load(open(args.first, encoding="utf-8"))
        firsts = {m.get("index"): m for m in (fd.get("messages", fd) if isinstance(fd, dict) else fd)}
    msgs = data.get("messages", data) if isinstance(data, dict) else data
    report = {}
    by_step = {}
    for m in msgs:
        for f in m.get("followups") or []:
            by_step.setdefault(f.get("step"), []).append(
                {"index": m.get("index"), "observation": f.get("body") or "", "subject": f.get("subject") or ""})
    batch = {}
    for step, items in by_step.items():
        for i, faults in check_batch(items, header_text, target_text).items():
            batch.setdefault((i, step), []).extend(
                x.replace("observation", f"follow up {step}") for x in faults)
    for m in msgs:
        i = m.get("index")
        card = cards.get(i)
        if card is None:
            print(f"index {i}: no card with that index, ignored")
            continue
        first = firsts.get(i) or {}
        common = stems(card.get("card", "")) | stems(header_text) | stems(target_text)
        first_grams = ngrams(first.get("observation") or "", 4, common)
        report[i] = {"lead_id": card.get("lead_id"), "steps": {}}
        angles = set()
        for f in m.get("followups") or []:
            step, text = f.get("step"), (f.get("body") or "").strip()
            grave, light = followup_faults(f, args.channel, args.email_is_product, header_text)
            named = company_named(text + " " + (f.get("subject") or ""), card)
            if named:
                grave.append(f"the recipient's company is named: {named}")
            digits = set(re.findall(r"\d+(?:[.,]\d+)?", text)) - {"15"}
            invented = digits - numbers(card.get("card", "")) - numbers(header_text)
            if invented:
                grave.append(f"a number neither the card nor the sender block gives: "
                             f"{', '.join(sorted(invented))}")
            if hits(DATES, text) or hits(STRUCK_PRICE, text):
                grave.append("a date or a struck price")
            for patterns, label in ((FLATTERY, "flattery"), (ABSOLUTES, "absolute"),
                                    (SAID_SOURCE, "says where it read about them"),
                                    (SET_UP, "set up talk"), (WORN_FORMULAS, "worn formula")):
                if hits(patterns, text):
                    light.append(label)
            head_stems = stems(header_text)
            if len(head_stems) >= VOCAB_MIN:
                own = stems(text) - stems(card.get("card", "")) - stems(target_text)
                if len(own & head_stems) < LINK_MIN:
                    light.append("no link with the offer")
            if first_grams & ngrams(text, 4, common):
                light.append("repeats the observation of the first message: take another angle")
            angle = fold(f.get("angle") or "")
            if angle and angle in angles:
                light.append(f"the same angle as another follow up: {angle}")
            angles.add(angle)
            light += batch.get((i, step), [])
            graves += bool(grave)
            report[i]["steps"][str(step)] = {"grave": grave, "light": light}
            state = "GRAVE" if grave else ("RETRY" if light else "KEEP")
            print(f"index {i:>2} follow up {step}  {state:5}  " + "; ".join(grave + light))
    if args.report:
        json.dump(report, open(args.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 1 if graves else 0


# ---------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------
GREETINGS = {"en": ("Hello {first},", "Hello,"), "fr": ("Bonjour {first},", "Bonjour,"),
             "de": ("Guten Tag {first},", "Guten Tag,"), "es": ("Hola {first},", "Hola,"),
             "it": ("Buongiorno {first},", "Buongiorno,"), "pt": ("Olá {first},", "Olá,"),
             "nl": ("Hallo {first},", "Hallo,")}


def clean_value(s):
    s = safe_text_keep_lines(s)
    s = re.sub(r"[{}|]", "", s)
    return re.sub("\\s*[\u2013\u2014]\\s*", ", ", s)


def safe_text_keep_lines(s):
    s = SURROGATE.sub("", str(s or ""))
    return "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in s.split("\n")).strip()


def count_failure(r):
    n = int(r.get("writing_attempts") or 0) + 1
    r["writing_attempts"] = str(n)
    r["writing_status"] = "dropped" if n >= ATTEMPTS_MAX else "failed"
    return r["writing_status"]


def run_merge(args):
    leads_path = Path(args.leads)
    rows = list(csv.DictReader(open(leads_path, encoding="utf-8", errors="replace")))
    fields = list(rows[0].keys()) if rows else []
    key = lambda r: r.get("lead_id") or r.get("email")
    by_id = {key(r): r for r in rows}
    hello, bare = GREETINGS.get(args.lang, GREETINGS["en"])
    if args.greeting:
        hello, bare = args.greeting.split("|", 1)
    email = args.channel == "email"
    prefix = "" if email else "li_"
    cards = {}
    for path, data in load_json(args.cards):
        for c in data:
            cards[(Path(path).stem.replace("cards-", ""), c["index"])] = c
    stem_out, stem_report = ("out-", "check-") if args.kind == "first" else ("fu-", "fucheck-")
    counts = {"kept": 0, "failed": 0, "dropped": 0}
    new_cols = set()

    def greet(r):
        first = safe_text(r.get("first_name"))
        g = hello.format(first=first) if first else bare
        return html.escape(g, quote=False) if email else g

    def body(text):
        text = clean_value(text)
        return html.escape(text, quote=False) if email else text

    for path, data in load_json(args.out):
        batch = Path(path).stem.replace(stem_out, "")
        report_path = Path(path).with_name(f"{stem_report}{batch}.json")
        if not report_path.exists():
            print(f"{path}: no {report_path.name}, run the check with --report first")
            return 2
        report = json.load(open(report_path, encoding="utf-8"))
        msgs = data.get("messages", data) if isinstance(data, dict) else data
        for m in msgs:
            card = cards.get((batch, m.get("index")))
            r = by_id.get(card.get("lead_id")) if card else None
            if r is None:
                continue
            verdict = report.get(str(m.get("index"))) or {}
            if args.kind == "first":
                if verdict.get("grave"):
                    counts[count_failure(r)] += 1
                    continue
                text = "\n\n".join(body(m.get(k)) for k in ("observation", "offer", "question"))
                value = f"{greet(r)}\n\n{text}"
                subject = " ".join(clean_value(m.get("subject")).split())
                if len(value) > MESSAGE_MAX or len(subject) > SUBJECT_MAX:
                    print(f"{key(r)}: over {MESSAGE_MAX} characters, or a subject over {SUBJECT_MAX}: not merged")
                    continue
                r["greeting"], r[f"{prefix}message"] = greet(r), value
                new_cols |= {"greeting", f"{prefix}message"}
                if email:
                    r["subject_line"] = subject
                    new_cols.add("subject_line")
            else:
                steps = m.get("followups") or []
                values = {f.get("step"): f"{greet(r)}\n\n{body(f.get('body'))}" for f in steps}
                graves = [f.get("step") for f in steps
                          if (verdict.get("steps") or {}).get(str(f.get("step")), {}).get("grave", ["unchecked"])]
                if graves or any(len(v) > MESSAGE_MAX for v in values.values()):
                    counts[count_failure(r)] += 1
                    continue
                for f in steps:
                    step, value = f.get("step"), values[f.get("step")]
                    r["greeting"], r[f"{prefix}message_{step}"] = greet(r), value
                    new_cols |= {"greeting", f"{prefix}message_{step}"}
                    if email and step == 3:
                        r["subject_line_3"] = " ".join(clean_value(f.get("subject")).split())
                        new_cols.add("subject_line_3")
            r["message_sources"] = " | ".join(clean_value(x) for x in m.get("sources") or [])
            r["message_date"] = date.today().isoformat()
            r["writing_status"] = "ok"
            counts["kept"] += 1
    new_cols |= {"message_sources", "message_date", "writing_attempts", "writing_status"}
    order = ["greeting", "subject_line", "message", "subject_line_3", "message_2", "message_3",
             "message_4", "li_message", "li_message_2", "li_message_3", "li_message_4",
             "message_sources", "message_date", "writing_attempts", "writing_status"]
    fields += [c for c in order if c in new_cols and c not in fields]
    with open(leads_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    print(f"{counts['kept']} contact(s) merged, {counts['failed']} to write again, "
          f"{counts['dropped']} dropped after {ATTEMPTS_MAX} attempts")
    no_first = sum(1 for r in rows if r.get("writing_status") == "ok" and not safe_text(r.get("first_name")))
    if no_first:
        print(f"{no_first} contact(s) without a first name, greeted with '{bare}'")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cards")
    c.add_argument("leads")
    c.add_argument("--out", default="outreach/copy")
    c.add_argument("--batch", type=int, default=8)
    c.add_argument("--skip-done", action="store_true")
    k = sub.add_parser("check")
    k.add_argument("file")
    k.add_argument("--cards", required=True)
    k.add_argument("--header", required=True)
    k.add_argument("--target", help="the text of the target(s) and their why")
    k.add_argument("--channel", choices=["email", "linkedin"], default="email")
    k.add_argument("--email-is-product", action="store_true")
    k.add_argument("--report")
    f = sub.add_parser("followups")
    f.add_argument("file")
    f.add_argument("--header", required=True)
    f.add_argument("--cards", help="personalised follow ups: the cards of the batch")
    f.add_argument("--first", help="personalised follow ups: the first messages of the batch")
    f.add_argument("--target", help="the text of the target(s) and their why")
    f.add_argument("--channel", choices=["email", "linkedin"], default="email")
    f.add_argument("--email-is-product", action="store_true")
    f.add_argument("--report")
    m = sub.add_parser("merge")
    m.add_argument("leads")
    m.add_argument("--cards", required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--kind", choices=["first", "followups"], default="first")
    m.add_argument("--channel", choices=["email", "linkedin"], default="email")
    m.add_argument("--lang", default="en")
    m.add_argument("--greeting", help="'Hello {first},|Hello,': with a first name, then without")
    args = ap.parse_args()
    return {"cards": build_cards, "check": run_check, "followups": run_followups,
            "merge": run_merge}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
