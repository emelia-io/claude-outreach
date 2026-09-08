# Skill conventions

Every sub-skill in this repository follows the same shape. If you are adding one,
copy an existing skill and keep these rules.

## File layout

```
skills/outreach-<name>/
  SKILL.md            required, the whole skill
  references/*.md     optional, long reference material read on demand
  templates/*         optional, files the skill writes or fills
```

One skill, one directory, one `SKILL.md`. No code lives in a skill unless it is a
script the skill actually runs; shared scripts go in `scripts/` at the repo root.

## Frontmatter

```yaml
---
name: outreach-find-email
description: "One paragraph in English. What the skill does, what it needs, what it
  produces, then a list of trigger words. This is the only thing Claude reads when
  deciding whether to load the skill, so it must contain the words a user would type."
license: MIT
metadata:
  author: Emelia
  version: "0.1.0"
  category: sales
---
```

`name` matches the directory name exactly. `description` is one string, no line
breaks that break YAML, and it ends with `Triggers on: word, word, word.`

Only the dispatcher skill (`outreach`) is `user-invokable: true`. Sub-skills are
loaded by the dispatcher or by trigger words, not called with a slash command.

## Writing style

Write for a colleague who knows sales but not this codebase. Short sentences.
Second person. No marketing voice, no exclamation marks, no emoji.

State numbers with their source and date. "Reply rates above 5% are good" is
useless; "across Emelia campaigns in 2025, a 3 to 5% reply rate is the median for
cold B2B email, above 8% is top decile" is usable. If you do not have a source,
say the number is a rule of thumb.

Never use an em dash or an en dash in prose. Use a comma, a colon or parentheses.

Every skill says what it does **not** do, and what it costs the user when it costs
something.

## Required sections

1. **What this does** in two or three sentences.
2. **When to use it** and when to use a different skill instead.
3. **Inputs**: the files, keys and arguments it needs, and what to do when one is
   missing (ask, or degrade gracefully, never guess silently).
4. **How to do it**: the actual procedure, with the exact tool names, endpoints,
   field names and parameters. This is the body of the skill.
5. **Output**: the file it writes, with a real example of its content.
6. **Checks before finishing**: what must be true for the step to count as done.
7. **Failure modes**: what commonly goes wrong and what to do about it.
8. **Limits**: what this skill cannot do.

## Working with the user's money and reputation

Anything that consumes Emelia credits states the cost before running and waits for
a yes. Anything that sends a message to a real person waits for a yes. Anything
that could harm sender reputation (unverified list, no warmup, volume spike) stops
and explains, rather than proceeding with a warning.

## Referencing the platform

Emelia access is either the MCP server (`https://mcp.emelia.io/mcp`, preferred) or
the REST API (`https://api.emelia.io`, documented at https://docs.emelia.io). Use
the exact MCP tool names listed in `skills/outreach/SKILL.md`. Never invent an
endpoint: if you need one that does not exist, say so and offer the closest path.

French B2B data comes from the Basile API (`api.basile.cc`). Anything else comes
from a CSV the user provides.

## Tests

`tests/` checks that every skill has valid frontmatter, a unique name matching its
directory, all eight required sections, no em dashes, and no broken relative links.
Run `python3 tests/run.py` before opening a pull request.
