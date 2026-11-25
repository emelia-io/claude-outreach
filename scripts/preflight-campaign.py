#!/usr/bin/env python3
"""Read a campaign back from Emelia and check it can actually send.

Every finding here comes from a campaign that was really built wrong: a step body in
plain text so the whole email arrived as one block, a variable spelled in a way no
contact carries so it rendered empty, a list that was never attached, a follow-up with
no opt out. The API accepts all of it and says 200.

Variables are counted on every contact, page after page, never on a sample: the custom
values come from the campaign's own contacts, which is what the engine sends, and the
standard and company fields from every row of the attached lists. A step whose body is a
single variable (Mode A) blocks as soon as one contact has it empty.

    EMELIA_API_KEY=... python3 scripts/preflight-campaign.py <campaignId>

Exit code 0 when nothing blocks, 1 when something does.
"""
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("EMELIA_API_BASE", "https://api.emelia.io")


def tls_context() -> ssl.SSLContext:
    """Verified TLS that also works on a Python shipped without a CA bundle."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


TLS = tls_context()

# Resolved from the contact itself. Anything outside this list falls through to the
# custom variables, then to the linked company. Mirrors the list of root fields the
# sending engine reads: a field that exists on the contact but is not here renders empty.
ROOT_VARS = {
    "firstName", "lastName", "fullName", "email", "secondaryEmail", "phone",
    "mobilePhone", "jobTitle", "seniority", "department", "gender", "age", "language",
    "linkedinUrlProfile", "twitterUrl", "country", "region", "city", "postalCode",
    "address", "timezone", "yearsOfExperience", "education", "bio", "companyName",
}
# Filled by Emelia at send time, never by the list. {{signature}} is lowercase only; the
# opt out and the unique id resolve in any case.
ENGINE_VARS = {"signature", "unsubscribe_link", "unique_id"}
# The root fields the campaign contact listing returns next to `custom`.
CAMPAIGN_SIDE = {"firstName", "lastName", "email", "phone", "linkedinUrlProfile"}
# Steps whose versions carry a message.
MESSAGE_STEPS = {"EMAIL", "MESSAGE", "INMAIL", "CONNECTION"}
COMPANY_VARS = {"companyDomain", "websiteUrl", "logoUrl", "industry", "companySize",
                "employeeCount", "foundedYear", "annualRevenue", "linkedinCompanyUrl",
                "companyCity", "companyCountry", "notes", "tags"}

VAR = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
LIQUID = re.compile(r"\{%|\{#")
# {{ firstName | default: "" }} is not Liquid and does not work. Liquid itself runs after
# the double braces are substituted, with {# #} as its output tag and the usual {% %} tags.
# On a standard or company field it depends on the version of the sending engine: recent
# ones read the field, older ones read it as empty. A warning, not a block.
LIQUID_VAR = re.compile(r"\{#\s*([A-Za-z0-9_]+)|\{%-?\s*(?:if|unless|elsif)\s+([A-Za-z0-9_]+)")
FILTER_IN_BRACES = re.compile(r"\{\{[^{}]*(?:\||\bdefault\s*:)[^{}]*\}\}")
# A condition field is an activity, or a contact field when it starts with $. Anything
# else is read as an unknown activity and answers "no" for every contact.
ACTIVITIES = {"ACCEPTED", "LINKEDIN_REPLIED", "MAIL_REPLIED", "OPENED", "CLICKED",
              "UNSUBSCRIBED", "BOUNCED", "TASK_COMPLETED"}
# Step and version ids are MongoDB ObjectIds written as 24 lowercase hex characters. The
# API saves any string, and a step whose id is not one is never recorded as done: an
# email or an invitation never goes out, a LinkedIn message goes out again at every pass.
# Uppercase hex and 12 character labels are converted on the way in and no longer match
# the tree, which ends the same way.
OBJECT_ID = re.compile(r"^[0-9a-f]{24}$")


def call(key: str, path: str):
    for attempt in range(4):
        req = urllib.request.Request(BASE + path, method="GET")
        req.add_header("Authorization", key)
        try:
            with urllib.request.urlopen(req, timeout=60, context=TLS) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                wait = int(e.headers.get("Retry-After") or 60)
                print(f"  rate limited, waiting {wait} s")
                time.sleep(wait)
                continue
            return e.code, {"error": e.read().decode(errors="replace")[:300]}
    return 429, {"error": "rate limited"}


def campaign_contacts(key: str, cid: str):
    """Every contact of the campaign, as the engine holds them. `page` is zero based."""
    out, page, count = [], 0, None
    while True:
        st, body = call(key, f"/advanced/campaign/contacts?id={cid}&page={page}&perPage=1000")
        if st != 200:
            return None, f"HTTP {st}"
        batch = body.get("list") or []
        count = body.get("count") or 0
        out.extend(batch)
        if not batch or len(out) >= count:
            return out, None
        page += 1


def list_rows(key: str, list_id: str):
    """Every row of a list, 100 per page, plus the custom variables it shows."""
    out, columns, page = [], set(), 1
    while True:
        st, body = call(key, f"/lists/list/{list_id}/rows?page={page}&pageSize=100")
        if st != 200:
            return None, columns, f"HTTP {st}"
        columns |= {v["technicalName"] for v in body.get("customVariables") or []}
        items = body.get("items") or []
        out.extend(items)
        if not items or len(out) >= (body.get("total") or 0):
            return out, columns, None
        page += 1


def carrier(text: str):
    """The variable a body is made of, when it is made of one variable and nothing else."""
    rest = re.sub(r"<a\b[^>]*unsubscribe_link[^>]*>.*?</a>", " ", text, flags=re.I | re.S)
    rest = re.sub(r"\{\{\s*signature\s*\}\}", " ", rest)
    rest = re.sub(r"<[^>]+>|&nbsp;", " ", rest)
    m = re.fullmatch(r"\s*\{\{\s*([A-Za-z0-9_]+)\s*\}\}\s*", rest)
    return m.group(1) if m else None


def walk(step, depth=0, n=0):
    """Yield every step of the tree, in send order, numbered by email step."""
    if not step:
        return
    if step.get("stepType") == "EMAIL":
        n += 1
    yield step, n
    for branch in ("next", "yes", "no"):
        for s, m in walk(step.get(branch), depth + 1, n):
            yield s, m


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    key = os.environ.get("EMELIA_API_KEY", "").strip()
    if not key:
        print("EMELIA_API_KEY is not set")
        return 2
    cid = sys.argv[1]

    status, body = call(key, f"/advanced/campaigns/{cid}")
    if status != 200:
        print(f"cannot read the campaign: HTTP {status} {body.get('error', '')}")
        return 2
    c = body.get("campaign") or body

    blocking, warnings = [], []
    print(f"campaign  {c.get('name')}  [{c.get('status')}]")

    # 1. Who sends
    ids = c.get("identities") or []
    print(f"senders   {len(ids)}")
    if not ids:
        blocking.append("no identity attached, the campaign cannot send")
    for i in ids:
        print(f"            {i.get('name')}")

    # 2. Who receives
    lists = (c.get("recipients") or {}).get("lists") or []
    total = sum(l.get("contactCount") or 0 for l in lists)
    print(f"recipients {total} contacts in {len(lists)} list(s)")
    for l in lists:
        print(f"            {l.get('name')}  {l.get('contactCount')}")
    if not lists:
        blocking.append("no list attached, the campaign has nobody to send to")
    elif total == 0:
        blocking.append("the attached list(s) hold no contact")

    # 3. The steps
    used = set()
    bounce_branch = False
    steps = list(walk(c.get("steps")))
    seen_ids = {}
    for st, _ in steps:
        sid = str(st.get("_id") or "")
        if st.get("stepType") == "START":
            continue
        if not OBJECT_ID.match(sid):
            blocking.append(f"step {st.get('stepType')} has _id {sid!r}, not 24 lowercase "
                            f"hex characters: Emelia never records it as done, so an email "
                            f"or an invitation never goes out and a LinkedIn message goes "
                            f"out again. Repair it as outreach-sequence section 2 says")
        elif sid in seen_ids:
            blocking.append(f"steps {seen_ids[sid]} and {st.get('stepType')} share the _id "
                            f"{sid!r}: Emelia treats them as one step")
        else:
            seen_ids[sid] = st.get("stepType")
        for v in st.get("versions") or []:
            vid = str(v.get("_id") or "")
            if vid and not OBJECT_ID.match(vid):
                warnings.append(f"version _id {vid!r} on a {st.get('stepType')} step is "
                                f"not 24 lowercase hex characters: per variant statistics "
                                f"are lost")
            for text in (v.get("message") or "", v.get("subject") or ""):
                for bad in sorted(set(FILTER_IN_BRACES.findall(text))):
                    blocking.append(f"{st.get('stepType')} step: {bad} puts a filter inside "
                                    f"double braces, which does not work. A default is "
                                    f"written in Liquid on a custom variable, "
                                    f"{{# name | default: \"...\" #}}")
                for a, b in sorted(set(LIQUID_VAR.findall(text))):
                    name = a or b
                    if (name in ROOT_VARS or name in COMPANY_VARS
                            or name.lower() in ENGINE_VARS):
                        warnings.append(f"{st.get('stepType')} step: Liquid reads {name}, "
                                        f"which is not a custom variable. Some versions of "
                                        f"the sending engine read it as empty, and then its "
                                        f"default always prints and an if on it is always "
                                        f"false. Put the value in a custom variable, which "
                                        f"works either way, or check it in a test email")
                for bad in sorted(set(re.findall(r"\{\{\s*(signature)\s*\}\}", text, re.I))):
                    if bad != "signature":
                        blocking.append(f"{st.get('stepType')} step: {{{{{bad}}}}} is not "
                                        f"lowercase and renders nothing. Write {{{{signature}}}}")
        if st.get("stepType") == "MESSAGE" and len(st.get("versions") or []) > 1:
            warnings.append("several versions on a LinkedIn MESSAGE step: they are all "
                            "sent, one after another, as sub-messages. Fine if that is "
                            "what you want, but it is not an A/B test")
        if st.get("stepType") == "CONDITION":
            conds = st.get("conditions") or {}
            for cond in (conds if isinstance(conds, list) else [conds]):
                field = str((cond or {}).get("field") or "")
                bounce_branch = bounce_branch or field == "BOUNCED"
                if field and not field.startswith("$") and field not in ACTIVITIES:
                    blocking.append(f"condition on {field!r}: neither an activity nor a "
                                    f"contact field written with a leading $, so it "
                                    f"answers no for every contact")

    # A stop event is checked before every action, LinkedIn included, so BOUNCED in
    # eventToStop kills any branch that a BOUNCED condition routes to.
    stops = (c.get("schedule") or {}).get("eventToStop") or []
    if "BOUNCED" in stops and bounce_branch:
        warnings.append("eventToStop holds BOUNCED while a condition branches on BOUNCED: "
                        "a bounced contact is stopped before that branch runs")
    emails = [(s, n) for s, n in steps if s.get("stepType") == "EMAIL"]
    print(f"steps     {len(steps) - 1} after START, {len(emails)} email")
    carriers = {}
    for s, n in steps:
        if s.get("stepType") not in MESSAGE_STEPS:
            continue
        label = f"email step {n}" if s.get("stepType") == "EMAIL" else f"{s.get('stepType')} step"
        for v in s.get("versions") or []:
            msg, subj = v.get("message") or "", v.get("subject") or ""
            used |= set(VAR.findall(msg)) | set(VAR.findall(subj))
            # An empty invitation note still sends the invitation: not a carrier.
            if s.get("stepType") == "CONNECTION":
                continue
            for text, what in ((msg, "body"), (subj, "subject")):
                name = carrier(text)
                if name and name.lower() not in ENGINE_VARS:
                    carriers.setdefault(name, f"the {what} of {label}")
    for s, n in emails:
        for v in s.get("versions") or []:
            msg = v.get("message") or ""
            subj = v.get("subject") or ""
            if not msg.strip():
                blocking.append(f"email step {n}: a version has an empty body")
            elif "<p" not in msg:
                blocking.append(f"email step {n}: the body carries no <p>, it will "
                                f"arrive as a single block")
            if "\\n" in msg or "\n" in msg:
                warnings.append(f"email step {n}: the body contains a newline, which "
                                f"renders as nothing. Paragraphs are <p>")
            if LIQUID.search(msg):
                warnings.append(f"email step {n}: the body uses Liquid. A malformed tag "
                                f"silently deletes every Liquid block of the message, so "
                                f"look at it in a test email, and a default value hides a "
                                f"column you should have filled")
            if n == 1 and not subj.strip():
                blocking.append("email step 1 has no subject, the first email needs one")
            if n > 1 and "unsubscribe_link" not in msg.lower():
                warnings.append(f"email step {n}: no opt out link, so no "
                                f"List-Unsubscribe header on this step")

    # 4. Do the variables resolve, on every contact
    engine = {v for v in used if v.lower() in ENGINE_VARS}
    need = sorted(used - engine)
    print(f"variables {', '.join(sorted(used)) or 'none'}")
    if carriers:
        print(f"carriers  {', '.join(sorted(carriers))}")

    # The campaign side: the custom values the engine will actually send.
    contacts, err = campaign_contacts(key, cid)
    if contacts is None:
        warnings.append(f"cannot read the contacts of the campaign ({err}): custom "
                        f"variables are counted on the lists instead")
    elif not contacts and total:
        warnings.append("the campaign holds no contact yet while its lists do: the "
                        "recipients are still being set up. Run this again in a minute, "
                        "custom variables are counted on the lists meanwhile")
        contacts = None
    custom_keys = set()
    for c in contacts or []:
        custom_keys |= set((c.get("custom") or {}).keys())

    # The list side: every row, for the fields the campaign listing does not return.
    rows, columns = [], set()
    if need:
        for l in lists:
            got, cols, err = list_rows(key, l["_id"])
            columns |= cols
            if got is None:
                warnings.append(f"cannot read the contacts of {l.get('name')}: {err}")
                continue
            rows.extend(got)

    def flat_row(item):
        flat = dict(item)
        for cf in item.get("customFields") or []:
            flat[cf["technicalName"]] = cf.get("value")
        flat.update(item.get("company") or {})
        return flat

    flat_rows = [flat_row(r) for r in rows]
    print(f"read      {len(contacts or [])} campaign contacts, {len(flat_rows)} list rows")

    for v in need:
        on_campaign = contacts is not None and (v in CAMPAIGN_SIDE or v in custom_keys or (
            v not in ROOT_VARS and v not in COMPANY_VARS))
        if on_campaign:
            pool = contacts
            empty = sum(1 for c in pool if not str(
                (c.get(v) if v in CAMPAIGN_SIDE else (c.get("custom") or {}).get(v)) or "").strip())
            where = "campaign contacts"
        else:
            pool = flat_rows
            empty = sum(1 for r in pool if not str(r.get(v) or "").strip())
            where = "list rows"
        known = (v in ROOT_VARS or v in COMPANY_VARS or v in columns or v in custom_keys)
        size = len(pool)
        if not known:
            blocking.append(f"{{{{{v}}}}} is not a contact field and no contact carries a "
                            f"variable of that name: it renders empty on everyone")
        elif size and empty == size:
            hint = ("" if on_campaign else ", or its column is hidden in the list table of "
                    "the app: the API only returns the visible columns")
            blocking.append(f"{{{{{v}}}}} is empty on all {size} {where}{hint}")
        elif empty and v in carriers:
            blocking.append(f"{{{{{v}}}}} is {carriers[v]}, a carrier, and it is empty on "
                            f"{empty} of {size} {where}: {empty} contact(s) would get an empty message. "
                            f"Write those rows or remove those contacts before the launch")
        elif empty:
            warnings.append(f"{{{{{v}}}}} is empty on {empty} of {size} {where}, "
                            f"those messages will have a hole in them")

    if "signature" not in used and emails:
        warnings.append("no {{signature}} in any email step, the emails go out unsigned")

    print()
    for m in blocking:
        print(f"  BLOCK  {m}")
    for m in warnings:
        print(f"  WARN   {m}")
    if not blocking and not warnings:
        print("  nothing to fix")
    print()
    print(f"{len(blocking)} blocking, {len(warnings)} to look at")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
