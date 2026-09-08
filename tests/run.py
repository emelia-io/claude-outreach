#!/usr/bin/env python3
"""Structural checks for every skill and agent in this repository.

Run from the repo root: python3 tests/run.py
Exits non zero when something is wrong, so it works as a CI gate.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_SECTIONS = [
    "What this does",
    "When to use it",
    "Inputs",
    "How to do it",
    "Output",
    "Checks before finishing",
    "Failure modes",
    "Limits",
]
DASHES = {"—": "em dash", "–": "en dash"}

failures: list[str] = []
checked = 0


def fail(where: Path, message: str) -> None:
    failures.append(f"{where.relative_to(ROOT)}: {message}")


def frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    block, out, key = text[4:end], {}, None
    for line in block.split("\n"):
        m = re.match(r"^([a-zA-Z-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            out[key] = m.group(2).strip()
        elif key and line.startswith(" "):
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


def check_skill(path: Path) -> None:
    global checked
    checked += 1
    text = path.read_text(encoding="utf-8")
    fm = frontmatter(text)
    if fm is None:
        fail(path, "no YAML frontmatter")
        return
    name = fm.get("name", "").strip("\"'")
    if not name:
        fail(path, "frontmatter has no name")
    elif name != path.parent.name:
        fail(path, f"name {name!r} does not match directory {path.parent.name!r}")
    desc = fm.get("description", "").strip("\"'")
    if len(desc) < 120:
        fail(path, "description is too short to be a useful trigger")
    if "Triggers on:" not in desc and name != "outreach":
        fail(path, "description has no 'Triggers on:' trigger word list")
    if fm.get("license", "").strip("\"'") != "MIT":
        fail(path, "license must be MIT")

    body = text[text.find("\n---\n", 4) + 5 :]
    if name != "outreach":  # the dispatcher has its own shape
        for section in REQUIRED_SECTIONS:
            if not re.search(rf"^#+\s+.*{re.escape(section)}", body, re.I | re.M):
                fail(path, f"missing section: {section}")

    for char, label in DASHES.items():
        if char in body:
            line = body[: body.index(char)].count("\n") + 1
            fail(path, f"{label} in prose, line {line} of the body")

    for target in re.findall(r"\]\((?!https?:|#|mailto:)([^)]+)\)", body):
        resolved = (path.parent / target.split("#")[0]).resolve()
        if not resolved.exists() and not (ROOT / target.split("#")[0]).exists():
            fail(path, f"broken relative link: {target}")


def main() -> int:
    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    if not skills:
        print("no skills found, nothing to check")
        return 1
    names = [p.parent.name for p in skills]
    for duplicate in {n for n in names if names.count(n) > 1}:
        failures.append(f"duplicate skill name: {duplicate}")
    for path in skills:
        check_skill(path)

    for path in sorted((ROOT / "agents").glob("*.md")):
        global checked
        checked += 1
        fm = frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            fail(path, "no YAML frontmatter")
        elif not fm.get("description"):
            fail(path, "agent has no description")

    print(f"checked {checked} files")
    if failures:
        print(f"\n{len(failures)} problem(s):")
        for f in failures:
            print(f"  {f}")
        return 1
    print("all good")
    return 0


if __name__ == "__main__":
    sys.exit(main())
