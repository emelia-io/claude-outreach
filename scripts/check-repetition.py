#!/usr/bin/env python3
"""Find the sentences your per contact copy repeats across contacts.

When a hundred sequences are written by ten agents in parallel, no agent can see what
the others wrote, so the same closing question comes back twenty times. Each recipient
only ever reads their own email, so this is not a delivery problem: it is a sign that
the personalisation stopped at the opening line and that the ask, which is the part
that earns the reply, was written from a template.

    python3 scripts/check-repetition.py outreach/copy/*.json

Reads the same JSON the writing agents produce: a list of objects carrying `lead_id`
and `emailNsubject` / `emailNmessage`. Exits 1 when something crosses the threshold.
"""
import argparse
import glob
import json
import re
import sys
from collections import defaultdict

SENTENCE = re.compile(r"(?<=[.?!])\s+")
# A line short enough to be an unavoidable turn of phrase, "Merci." or "Bonjour Marc,".
SHORT = 35


def load(paths):
    rows, seen = [], set()
    for pattern in paths:
        for path in sorted(glob.glob(pattern)) or [pattern]:
            try:
                data = json.load(open(path, encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as e:
                print(f"cannot read {path}: {e}")
                continue
            for c in data:
                if c.get("lead_id") in seen:
                    continue
                seen.add(c.get("lead_id"))
                rows.append((path, c))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--max-repeats", type=int, default=2,
                    help="how many contacts may share one sentence (default 2)")
    args = ap.parse_args()

    rows = load(args.files)
    if not rows:
        print("no contact read")
        return 2

    where = defaultdict(list)          # sentence -> [(lead_id, step)]
    for _, c in rows:
        for n in (1, 2, 3, 4):
            for s in SENTENCE.split(c.get(f"email{n}message") or ""):
                s = " ".join(s.split())
                if len(s) > SHORT:
                    where[s].append((c.get("lead_id"), n))
    subjects = defaultdict(list)
    for _, c in rows:
        for n in (1, 3):
            s = (c.get(f"email{n}subject") or "").strip()
            if s:
                subjects[s].append(c.get("lead_id"))

    over = sorted(((len(v), k, v) for k, v in where.items() if len(v) > args.max_repeats),
                  reverse=True)
    subj_over = sorted(((len(v), k) for k, v in subjects.items()
                        if len(v) > args.max_repeats), reverse=True)

    print(f"{len(rows)} contacts, {len(where)} distinct sentences over {SHORT} characters")
    print(f"threshold: a sentence may be shared by at most {args.max_repeats} contacts")
    print()

    if over:
        print("sentences reused too widely, most shared first:")
        for n, s, hits in over[:25]:
            steps = sorted({str(step) for _, step in hits})
            print(f"  {n:3}x  step {'/'.join(steps)}  {s[:100]}")
        if len(over) > 25:
            print(f"  and {len(over) - 25} more")
        print()
    if subj_over:
        print("subject lines reused too widely:")
        for n, s in subj_over[:15]:
            print(f"  {n:3}x  {s[:100]}")
        print()

    worst = over[0][0] if over else 0
    print(f"{len(over)} sentence(s) and {len(subj_over)} subject(s) over the threshold, "
          f"worst shared by {worst} contacts")
    if over or subj_over:
        print("Rewrite them per contact, or re-run those slices with an instruction to "
              "vary the ask. Do not fix a hundred messages by hand.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
