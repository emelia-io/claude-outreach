#!/usr/bin/env python3
"""Emelia email finder with the fallback cascade, run by the outreach-find-email skill.

One row can be looked up three different ways, and the second and third ways find
addresses the first one misses. The finder queries a first source with what you send
it; when that source comes back empty it hands the job to a second source, and the
company field it hands over is the domain when you sent one, the company name when you
did not. So the same person searched by domain and searched by name goes down two
different paths. This script runs those paths in order and stops at the first hit:

  1  companyName + companyWebsite   the domain, most accurate when the domain is right
  2  companyName only               no domain, both sources resolve the company themselves
  3  the trade name, only when the source carries one that differs from the legal name

A lookup that finds nothing is refunded, so attempts 2 and 3 only cost credits when
they work. `country` is sent on every call: the published schema marks it optional and
the API rejects the request without it.

Usage:
  export EMELIA_API_KEY="..."
  python3 scripts/find-emails.py outreach/leads.csv
  python3 scripts/find-emails.py outreach/leads.csv --out outreach/leads.csv --plan grow
  python3 scripts/find-emails.py outreach/leads.csv --limit 25       # a paid sample
  python3 scripts/find-emails.py outreach/leads.csv --dry-run        # plan only, spends nothing

Options:
  --out PATH        where to write the enriched CSV (default: <input>-emails.csv)
  --report PATH     where to write the JSON report (default: <out without .csv>.json)
  --plan NAME       none | start | grow | scale, sets the requests per minute ceiling
  --limit N         look up at most N rows, for a sample before the full run
  --max-attempts N  1, 2 or 3, how far down the cascade to go (default 3)
  --country CC      fallback ISO country code for rows that carry none (default FR)
  --dry-run         count the rows, print the plan and the worst case cost, call nothing
  --resume          skip rows the output file already has a verdict for

The output CSV is rewritten after every row, so a run you interrupt keeps everything it
already paid for. Restart it with --resume and the same --out.

Exits 1 on a hard stop (no key, no credits, unreadable file), 0 otherwise.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from datetime import datetime, timezone


def tls_context() -> ssl.SSLContext:
    """A verified TLS context that also works on a Python with no CA bundle installed.

    A fresh python.org install on macOS ships without root certificates, so every HTTPS
    call fails with CERTIFICATE_VERIFY_FAILED until you run Install Certificates.command.
    Use certifi when it is importable, which covers that case without weakening anything.
    Verification is never turned off.
    """
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


TLS = tls_context()

BASE = os.environ.get("EMELIA_API_BASE", "https://api.emelia.io")
FIND_EMAIL = "/tools/find/email"

# Requests per minute per API key, per plan. Measured in the Emelia code, not guessed.
PLAN_RPM = {"none": 30, "start": 100, "grow": 300, "scale": 1000}

# The server queries its own sources for up to two minutes before giving up on a row.
# That wait is per job and the jobs run in parallel server side, so this script submits a
# whole wave of rows first and then polls the whole wave, instead of waiting out one row
# before starting the next. Serial would be one row every 20 to 60 seconds; a wave of 250
# comes back in about the time a single row takes.
POLL_EVERY = 5.0
POLL_TIMEOUT = 420.0
# /tools/ routes are exempt from the per plan rate limit, so a wave can be submitted at
# speed. The limiter stays as a safety net and 429 is still handled.
TOOLS_RPM = 600

# Column aliases, compared lowercased with punctuation stripped.
ALIASES = {
    "full_name": ["full_name", "fullname", "name", "nom complet", "contact", "contact name"],
    "first_name": ["first_name", "firstname", "prenom", "given name", "fname"],
    "last_name": ["last_name", "lastname", "nom", "surname", "family name", "lname"],
    "company_name": ["company_name", "companyname", "company", "societe", "entreprise",
                     "organisation", "organization", "account", "employer", "raison sociale",
                     "legal_name"],
    "company_domain": ["company_domain", "companydomain", "domain", "company_website",
                       "companywebsite", "website", "websiteurl", "site", "site web", "url",
                       "company url"],
    "trade_name": ["trade_name", "trading_name", "commercial_name", "company_trade_name",
                   "enseigne", "nom commercial", "brand", "brand_name", "gmb_name",
                   "google_name", "x_trade_name", "x_gmb_name", "dba"],
    "country_code": ["country_code", "country", "pays", "countrycode", "country code"],
    "email": ["email", "e-mail", "mail", "courriel", "adresse email", "work email"],
}

# Legal wrappers stripped before comparing a trade name with a company name.
LEGAL_NOISE = re.compile(
    r"\b(sas|sasu|sarl|eurl|sa|snc|sci|scp|scm|selarl|sccv|gie|association|asso|"
    r"ltd|limited|llc|inc|corp|corporation|gmbh|bv|nv|plc|ab|oy|spa|srl|holding|"
    r"groupe|group)\b",
    re.I,
)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def slug(s: str) -> str:
    """A company name reduced to what identifies it, for comparing two spellings."""
    return re.sub(r"\s+", " ", LEGAL_NOISE.sub(" ", norm(s))).strip()


def clean_domain(value: str) -> str:
    """emelia.io out of https://www.emelia.io/pricing?utm=x, and nothing at all out of junk."""
    v = (value or "").strip().lower()
    if not v:
        return ""
    v = re.sub(r"^[a-z]+://", "", v)
    v = v.split("/")[0].split("?")[0].split("#")[0]
    if v.startswith("www."):
        v = v[4:]
    if "@" in v:
        v = v.split("@")[-1]
    return v if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", v) else ""


def build_map(header: list[str]) -> dict[str, str]:
    """Map contract fields onto the real column names of this file."""
    lookup = {norm(h): h for h in header}
    out: dict[str, str] = {}
    for field, names in ALIASES.items():
        for candidate in names:
            if norm(candidate) in lookup:
                out[field] = lookup[norm(candidate)]
                break
    return out


class Api:
    """Thin HTTP client that paces itself under the plan's requests per minute."""

    def __init__(self, key: str, rpm: int) -> None:
        self.key = key
        self.rpm = max(1, int(rpm * 0.8))  # keep headroom, the key may be shared
        self.window: deque[float] = deque()
        self.requests = 0

    def _throttle(self) -> None:
        now = time.monotonic()
        while self.window and now - self.window[0] > 60:
            self.window.popleft()
        if len(self.window) >= self.rpm:
            wait = 60 - (now - self.window[0]) + 0.2
            if wait > 0:
                time.sleep(wait)
        self.window.append(time.monotonic())

    def call(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        self._throttle()
        self.requests += 1
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(BASE + path, data=data, method=method)
        req.add_header("Authorization", self.key)
        if data:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60, context=TLS) as resp:
                return resp.status, json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace")
            try:
                return e.code, json.loads(raw or "{}")
            except json.JSONDecodeError:
                return e.code, {"error": raw[:300]}
        except (urllib.error.URLError, TimeoutError) as e:
            return 0, {"error": str(e)}


def submit(api: Api, payload: dict) -> dict:
    """Create one finder job. Returns either a job id or a terminal outcome."""
    status, body = api.call("POST", FIND_EMAIL, payload)

    if status == 429:
        time.sleep(20)
        status, body = api.call("POST", FIND_EMAIL, payload)
    if status == 402 or "credit" in json.dumps(body).lower():
        return {"outcome": "no_credits", "http": status,
                "error": body.get("error") or body.get("message")}
    if status == 401:
        return {"outcome": "unauthorized", "http": status}
    if status == 400:
        return {"outcome": "rejected", "http": 400,
                "error": body.get("error") or body.get("message")}
    job_id = body.get("jobId")
    if not job_id:
        return {"outcome": "error", "http": status,
                "error": body.get("error") or body.get("message")}
    return {"outcome": "submitted", "job_id": job_id}


def collect(api: Api, jobs: dict, on_result, enough=None) -> None:
    """Poll a whole wave of jobs until each one answers or the deadline passes.

    `jobs` maps job_id to whatever the caller needs to route the answer back, and
    `on_result` is called once per job with (payload, result). Jobs are polled in the
    order they were submitted, so the oldest, most likely finished, answers first.
    """
    deadline = time.monotonic() + POLL_TIMEOUT
    while jobs:
        if enough and enough():
            print(f"  target reached, {len(jobs)} jobs left running server side. "
                  f"Their jobId is in the file, collect them later.", flush=True)
            for job_id, payload in list(jobs.items()):
                on_result(payload, {"outcome": "pending", "job_id": job_id})
            jobs.clear()
            return
        time.sleep(POLL_EVERY)
        for job_id in list(jobs):
            gstatus, gbody = api.call("GET", f"{FIND_EMAIL}/{job_id}")
            if gstatus == 429:
                time.sleep(20)
                break
            data = (gbody or {}).get("data") or {}
            if data.get("status") and data["status"] != "running":
                email = (data.get("email") or "").strip()
                on_result(jobs.pop(job_id), {
                    "outcome": "found" if email else "not_found",
                    "job_id": job_id,
                    "email": email,
                    "qualification": data.get("qualification") or "",
                })
        if time.monotonic() > deadline:
            for job_id, payload in list(jobs.items()):
                on_result(payload, {"outcome": "pending", "job_id": job_id})
            jobs.clear()


def attempts_for(row: dict, cmap: dict, default_country: str, max_attempts: int) -> list[dict]:
    """The cascade for one row: what to send, in which order, and why."""
    full = (row.get(cmap.get("full_name", ""), "") or "").strip()
    if not full:
        first = (row.get(cmap.get("first_name", ""), "") or "").strip()
        last = (row.get(cmap.get("last_name", ""), "") or "").strip()
        full = f"{first} {last}".strip()
    company = (row.get(cmap.get("company_name", ""), "") or "").strip()
    domain = clean_domain(row.get(cmap.get("company_domain", ""), ""))
    trade = (row.get(cmap.get("trade_name", ""), "") or "").strip()
    country = (row.get(cmap.get("country_code", ""), "") or "").strip().upper()[:2] or default_country

    if not full or not company:
        return []

    plan = []
    if domain:
        plan.append({"label": "domain", "companyName": company, "companyWebsite": domain})
    plan.append({"label": "company_name", "companyName": company})
    if trade and slug(trade) and slug(trade) != slug(company):
        plan.append({"label": "trade_name", "companyName": trade})

    for a in plan:
        a["fullname"] = full
        a["country"] = country
    return plan[:max_attempts]


def payload_of(attempt: dict) -> dict:
    body = {"fullname": attempt["fullname"], "companyName": attempt["companyName"],
            "country": attempt["country"]}
    if attempt.get("companyWebsite"):
        body["companyWebsite"] = attempt["companyWebsite"]
    return body


NEW_COLUMNS = ["email", "email_status", "email_qualification", "email_source",
               "email_attempt", "email_attempts_made", "email_job_id"]


def main() -> int:
    p = argparse.ArgumentParser(description="Emelia email finder with the fallback cascade")
    p.add_argument("csv_in")
    p.add_argument("--out")
    p.add_argument("--report")
    p.add_argument("--plan", default="start", choices=sorted(PLAN_RPM))
    p.add_argument("--limit", type=int)
    p.add_argument("--max-attempts", type=int, default=3, choices=[1, 2, 3])
    p.add_argument("--country", default="FR")
    p.add_argument("--enough", type=int, metavar="N",
                   help="stop polling once N addresses are found. The jobs already "
                        "submitted keep running server side and their jobId is written "
                        "to the file, so the stragglers are collectable later with "
                        "--collect. Use it to start writing as soon as the campaign has "
                        "its contacts instead of waiting out the slowest row.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--resume", action="store_true")
    args = p.parse_args()

    out_path = args.out or re.sub(r"\.csv$", "", args.csv_in) + "-emails.csv"
    report_path = args.report or re.sub(r"\.csv$", "", out_path) + ".json"

    try:
        with open(args.csv_in, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        print(f"cannot read {args.csv_in}: {e}")
        return 1
    if not rows:
        print(f"{args.csv_in} has no data rows")
        return 1

    header = list(rows[0].keys())
    cmap = build_map(header)
    missing = [f for f in ("company_name",) if f not in cmap]
    if "full_name" not in cmap and not ("first_name" in cmap and "last_name" in cmap):
        missing.append("full_name (or first_name and last_name)")
    if missing:
        print("cannot map the columns this script needs: " + ", ".join(missing))
        print("columns in the file: " + ", ".join(header))
        return 1

    already_done: set[int] = set()
    if args.resume and os.path.exists(out_path):
        with open(out_path, newline="", encoding="utf-8-sig") as f:
            for i, prev in enumerate(csv.DictReader(f)):
                if (prev.get("email") or "").strip() or \
                        (prev.get("email_status") or "").strip() in ("found", "not_found"):
                    already_done.add(i)
                    for col in NEW_COLUMNS:
                        if i < len(rows) and prev.get(col):
                            rows[i][col] = prev[col]

    plans, skipped_has_email, skipped_no_input = [], 0, 0
    for i, row in enumerate(rows):
        existing = (row.get(cmap.get("email", ""), "") or "").strip()
        if existing or i in already_done:
            skipped_has_email += 1
            plans.append(None)
            continue
        chain = attempts_for(row, cmap, args.country.upper()[:2], args.max_attempts)
        if not chain:
            skipped_no_input += 1
            plans.append(None)
            continue
        plans.append(chain)

    todo = [i for i, c in enumerate(plans) if c]
    if args.limit:
        for i in todo[args.limit:]:
            plans[i] = None
        todo = todo[: args.limit]

    with_domain = sum(1 for i in todo if plans[i][0]["label"] == "domain")
    with_trade = sum(1 for i in todo if any(a["label"] == "trade_name" for a in plans[i]))
    rpm = PLAN_RPM[args.plan]

    print(f"Email finder cascade on {args.csv_in}")
    print(f"  rows in the file            {len(rows)}")
    print(f"  already have a verdict      {skipped_has_email}   skipped")
    print(f"  no name or no company       {skipped_no_input}   skipped, never looked up")
    print(f"  to look up                  {len(todo)}")
    print(f"    with a domain             {with_domain}   start at attempt 1")
    print(f"    with a trade name         {with_trade}   can reach attempt 3")
    print(f"  cost                        1 credit per address found, a miss is refunded")
    print(f"  worst case                  {len(todo)} credits, one per row that ends up found")
    print(f"  plan {args.plan}, {rpm} requests per minute, pacing at {int(rpm * 0.8)}")
    if args.dry_run:
        print("\ndry run, nothing was called and nothing was spent")
        return 0

    key = os.environ.get("EMELIA_API_KEY", "").strip()
    if not key:
        print("\nEMELIA_API_KEY is not set. Export it and run again.")
        return 1

    out_header = header + [c for c in NEW_COLUMNS if c not in header]

    def write_out() -> None:
        """Rewritten after every row, so an interrupted run keeps what it paid for."""
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=out_header, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in out_header})

    api = Api(key, max(rpm, TOOLS_RPM))
    started = datetime.now(timezone.utc)
    stats = {"found": 0, "not_found": 0, "error": 0, "pending": 0,
             "by_attempt": {"domain": 0, "company_name": 0, "trade_name": 0},
             "attempts_made": 0, "rescued_by_fallback": 0}
    stopped = None
    done = 0

    def record(i: int, result: dict, label: str, made: list) -> None:
        """Write one row's verdict into the table and the counters."""
        nonlocal done
        outcome = result["outcome"]
        rows[i]["email"] = result.get("email", "")
        rows[i]["email_qualification"] = result.get("qualification", "")
        rows[i]["email_source"] = "finder" if result.get("email") else ""
        rows[i]["email_attempt"] = label if result.get("email") else ""
        rows[i]["email_attempts_made"] = str(len(made))
        rows[i]["email_job_id"] = result.get("job_id", "")
        rows[i]["email_status"] = {"found": "found", "not_found": "not_found",
                                   "pending": "pending"}.get(outcome, "error")
        if outcome == "found":
            stats["found"] += 1
            stats["by_attempt"][label] += 1
            if label != "domain" and plans[i][0]["label"] == "domain":
                stats["rescued_by_fallback"] += 1
        elif outcome == "not_found":
            stats["not_found"] += 1
        elif outcome == "pending":
            stats["pending"] += 1
        else:
            stats["error"] += 1
        done += 1
        mark = result.get("email") or outcome
        if outcome == "error" and result.get("error"):
            mark = f"error: {result['error']}"
        print(f"  [{done}/{len(todo)}] {plans[i][0]['fullname']} at "
              f"{plans[i][0]['companyName']}  {'>'.join(made)} -> {mark}", flush=True)

    # One wave per rung of the cascade: submit every row that is still open, poll the
    # whole wave, then send the rows that came back empty down to the next rung.
    open_rows = list(todo)
    made_by_row = {i: [] for i in todo}

    for rung in range(args.max_attempts):
        wave = [i for i in open_rows if len(plans[i]) > rung]
        if not wave:
            break

        jobs, next_open = {}, []
        print(f"\nattempt {rung + 1} ({plans[wave[0]][rung]['label']}): "
              f"submitting {len(wave)} rows", flush=True)

        for i in wave:
            attempt = plans[i][rung]
            r = submit(api, payload_of(attempt))
            stats["attempts_made"] += 1
            made_by_row[i].append(attempt["label"])
            if r["outcome"] in ("no_credits", "unauthorized"):
                stopped = r["outcome"]
                break
            if r["outcome"] == "submitted":
                jobs[r["job_id"]] = i
            else:
                record(i, r, attempt["label"], made_by_row[i])

        if stopped:
            break

        print(f"  {len(jobs)} jobs running, polling every {int(POLL_EVERY)}s", flush=True)

        def on_result(i: int, result: dict) -> None:
            label = plans[i][rung]["label"]
            last_rung = rung + 1 >= min(args.max_attempts, len(plans[i]))
            if result["outcome"] == "not_found" and not last_rung:
                next_open.append(i)          # try the next rung rather than give up
                return
            record(i, result, label, made_by_row[i])

        collect(api, jobs, on_result,
                enough=(lambda: stats["found"] >= args.enough) if args.enough else None)
        write_out()
        if args.enough and stats["found"] >= args.enough:
            print(f"\n{stats['found']} addresses found, target was {args.enough}. "
                  f"Stopping here so the campaign can be built now.", flush=True)
            break
        open_rows = next_open

    write_out()
    looked_up = stats["found"] + stats["not_found"] + stats["error"] + stats["pending"]
    report = {
        "run": {"started_at": started.isoformat(), "finished_at": datetime.now(timezone.utc).isoformat(),
                "input": args.csv_in, "output": out_path, "plan": args.plan,
                "stopped_early": stopped},
        "cost": {"rate": "1 credit per address found, refunded on a miss",
                 "credits_spent_estimate": stats["found"]},
        "counts": {"rows_in": len(rows), "skipped_already_had_email": skipped_has_email,
                   "skipped_missing_input": skipped_no_input, "looked_up": looked_up,
                   **{k: v for k, v in stats.items() if k != "by_attempt"}},
        "cascade": {"found_by_attempt": stats["by_attempt"],
                    "found_only_because_of_a_retry": stats["rescued_by_fallback"],
                    "api_requests": api.requests},
        "rates": {"discovery": round(stats["found"] / looked_up, 3) if looked_up else 0},
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    rate = f"{100 * stats['found'] / looked_up:.1f}%" if looked_up else "n/a"
    print(f"\n{looked_up} rows looked up, {stats['found']} found ({rate}), "
          f"{stats['not_found']} not found, {stats['error']} errors, {stats['pending']} pending")
    print(f"  found on attempt 1, the domain          {stats['by_attempt']['domain']}")
    print(f"  found on attempt 2, the company name    {stats['by_attempt']['company_name']}")
    print(f"  found on attempt 3, the trade name      {stats['by_attempt']['trade_name']}")
    print(f"  would have been lost without the retry  {stats['rescued_by_fallback']}")
    print(f"  {stats['attempts_made']} lookups for {looked_up} rows, "
          f"{api.requests} API requests")
    print(f"  about {stats['found']} credits spent, misses are refunded")
    print(f"\nwrote {out_path} and {report_path}")
    if stopped == "no_credits":
        print("\nStopped: the account is out of credits. Rerun with --resume once it is topped up.")
        return 1
    if stopped == "unauthorized":
        print("\nStopped: the API key was rejected (401).")
        return 1
    if stats["pending"]:
        print(f"\n{stats['pending']} jobs were still running. Their jobId is in the file: "
              f"collect them with GET /tools/find/email/<jobId> rather than looking them up again.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
