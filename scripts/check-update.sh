#!/usr/bin/env bash
# Says whether this checkout is behind the published repository, in one line.
# Cheap: one network call to the remote, nothing is fetched or written.
# Prints "up to date", "behind by N commits ..." or "unknown: <reason>".
set -u

dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$dir" 2>/dev/null || { echo "unknown: cannot reach the plugin directory"; exit 0; }

command -v git >/dev/null 2>&1 || { echo "unknown: git is not installed"; exit 0; }
git rev-parse --git-dir >/dev/null 2>&1 || {
  echo "unknown: installed without git, reinstall to get updates"; exit 0; }

local_sha="$(git rev-parse HEAD 2>/dev/null)"
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
[ "$branch" = "HEAD" ] && branch=main

remote_sha="$(git ls-remote origin "refs/heads/$branch" 2>/dev/null | cut -f1)"
[ -z "$remote_sha" ] && remote_sha="$(git ls-remote origin HEAD 2>/dev/null | cut -f1)"
[ -z "$remote_sha" ] && { echo "unknown: the remote did not answer"; exit 0; }

[ "$local_sha" = "$remote_sha" ] && { echo "up to date ($(cat VERSION 2>/dev/null))"; exit 0; }

# How far behind, when the object is already known locally; otherwise just say it differs.
if git cat-file -e "$remote_sha" 2>/dev/null; then
  n="$(git rev-list --count "HEAD..$remote_sha" 2>/dev/null || echo '?')"
  echo "behind by $n commits, run: git -C $dir pull"
else
  echo "behind, run: git -C $dir pull"
fi
