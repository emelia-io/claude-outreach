#!/usr/bin/env python3
"""Read a campaign back from Emelia and check it can actually send.

Every finding here comes from a campaign that was really built wrong: a step body in
plain text so the whole email arrived as one block, a variable spelled in a way no
contact carries so it rendered empty, a list that was never attached, a follow-up with
no opt out. The API accepts all of it and says 200.

    EMELIA_API_KEY=... python3 scripts/preflight-campaign.py <campaignId>

Exit code 0 when nothing blocks, 1 when something does.
"""
import json
import os
import re
import ssl
import sys
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
# custom variables, then to the linked company. Mirrors CONTACT_ROOT_VARS in the
# sending engine: a field that exists on the contact but is not here renders empty.
ROOT_VARS = {
    "firstName", "lastName", "fullName", "email", "secondaryEmail", "phone",
    "mobilePhone", "jobTitle", "seniority", "department", "gender", "age", "language",
    "linkedinUrlProfile", "twitterUrl", "country", "region", "city", "postalCode",
    "address", "timezone", "yearsOfExperience", "education", "bio", "companyName",
}
# Filled by Emelia at send time, never by the list.
ENGINE_VARS = {"signature", "unsubscribe_link", "unique_id"}
COMPANY_VARS = {"companyDomain", "websiteUrl", "logoUrl", "industry", "companySize",
                "employeeCount", "foundedYear", "annualRevenue", "linkedinCompanyUrl",
                "companyCity", "companyCountry", "notes", "tags"}

VAR = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
LIQUID = re.compile(r"\{%|\{#")
# The activity record casts stepId to an ObjectId. Anything else raises after the
# message has already been sent, so the send is not logged and gets planned again.
OBJECT_ID = re.compile(r"^[0-9a-fA-F]{24}$")


def call(key: str, path: str):
    req = urllib.request.Request(BASE + path, method="GET")
    req.add_header("Authorization", key)
    try:
        with urllib.request.urlopen(req, timeout=60, context=TLS) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode(errors="replace")[:300]}


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
    steps = list(walk(c.get("steps")))
    for st, _ in steps:
        sid = str(st.get("_id") or "")
        if st.get("stepType") == "START":
            continue
        if not OBJECT_ID.match(sid):
            blocking.append(f"step {st.get('stepType')} has _id {sid!r}, which is not a "
                            f"24 character ObjectId: its sends will not be logged and "
                            f"the step will be replanned and sent again")
        for v in st.get("versions") or []:
            vid = str(v.get("_id") or "")
            if vid and not OBJECT_ID.match(vid):
                warnings.append(f"version _id {vid!r} on a {st.get('stepType')} step is "
                                f"not an ObjectId: per variant statistics are lost")
    emails = [(s, n) for s, n in steps if s.get("stepType") == "EMAIL"]
    print(f"steps     {len(steps) - 1} after START, {len(emails)} email")
    for s, n in emails:
        for v in s.get("versions") or []:
            msg = v.get("message") or ""
            subj = v.get("subject") or ""
            used |= set(VAR.findall(msg)) | set(VAR.findall(subj))
            if not msg.strip():
                blocking.append(f"email step {n}: a version has an empty body")
            elif "<p" not in msg:
                blocking.append(f"email step {n}: the body carries no <p>, it will "
                                f"arrive as a single block")
            if "\\n" in msg or "\n" in msg:
                warnings.append(f"email step {n}: the body contains a newline, which "
                                f"renders as nothing. Paragraphs are <p>")
            if LIQUID.search(msg):
                warnings.append(f"email step {n}: the body uses Liquid. It works, but "
                                f"a default value hides a column you should have filled")
            if n == 1 and not subj.strip():
                blocking.append("email step 1 has no subject, the first email needs one")
            if n > 1 and "unsubscribe_link" not in msg.lower():
                warnings.append(f"email step {n}: no opt out link, so no "
                                f"List-Unsubscribe header on this step")
        if len(s.get("versions") or []) > 1 and s.get("stepType") != "EMAIL":
            blocking.append("several versions on a LinkedIn step: they are all sent, "
                            "one after another, this is not an A/B test")

    # 4. Do the variables resolve
    engine = {v for v in used if v.lower() in ENGINE_VARS}
    need = sorted(used - engine)
    print(f"variables {', '.join(sorted(used)) or 'none'}")

    columns, missing_counts = set(), {}
    for l in lists:
        st, rows = call(key, f"/lists/list/{l['_id']}/rows?page=1&pageSize=100")
        if st != 200:
            warnings.append(f"cannot read the contacts of {l.get('name')}: HTTP {st}")
            continue
        columns |= {v["technicalName"] for v in rows.get("customVariables") or []}
        for item in rows.get("items") or []:
            flat = dict(item)
            for cf in item.get("customFields") or []:
                flat[cf["technicalName"]] = cf.get("value")
            flat.update(item.get("company") or {})
            for v in need:
                if not str(flat.get(v) or "").strip():
                    missing_counts[v] = missing_counts.get(v, 0) + 1

    sampled = min(100, total)
    for v in need:
        known = v in ROOT_VARS or v in columns or v in COMPANY_VARS
        empty = missing_counts.get(v, 0)
        if not known:
            blocking.append(f"{{{{{v}}}}} is not a contact field and no list carries a "
                            f"column of that name: it renders empty on everyone")
        elif empty == sampled and sampled:
            blocking.append(f"{{{{{v}}}}} is empty on all {sampled} contacts sampled")
        elif empty:
            warnings.append(f"{{{{{v}}}}} is empty on {empty} of the {sampled} contacts "
                            f"sampled, those emails will have a hole in them")

    if "signature" not in {v.lower() for v in used}:
        warnings.append("no {{signature}} in any step, the emails go out unsigned")

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
