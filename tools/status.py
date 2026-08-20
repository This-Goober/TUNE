#!/usr/bin/env python3
"""tools/status.py — print what is ACTUALLY in this repo, so PROJECT.md can be checked
against reality instead of trusted.

PROJECT.md's "Current state" section is hand-maintained and rots. Run this first:

    python tools/status.py

It reports what exists on disk, what git thinks, and what looks stale. It asserts nothing
about findings — it only shows the ground truth a human or a model should reconcile the
docs against.
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STALE_AFTER_DAYS = 21


def sh(*args: str) -> str:
    """Run a git command in the repo; return stripped stdout, or '' on failure."""
    try:
        out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=20)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def rule(title: str) -> None:
    print(f"\n\033[1m{title}\033[0m\n" + "-" * len(title))


def days_since(ts: float) -> int:
    return (datetime.now(timezone.utc) - datetime.fromtimestamp(ts, timezone.utc)).days


# --------------------------------------------------------------- experiments on disk
def experiments() -> None:
    rule("EXPERIMENTS ON DISK")
    exp = ROOT / "experiments"
    if not exp.is_dir():
        print("  no experiments/ directory")
        return
    folders = sorted(p for p in exp.iterdir() if p.is_dir() and p.name != "lib")
    if not folders:
        print("  none")
        return
    width = max(len(p.name) for p in folders)
    for p in folders:
        scripts = sorted(p.glob("*.py"))
        results = sorted(list(p.glob("RESULTS*.md")) + list(p.glob("README.md")))
        if results:
            newest = max(r.stat().st_mtime for r in results)
            age = days_since(newest)
            stamp = datetime.fromtimestamp(newest).strftime("%Y-%m-%d")
            mark = "\033[32m✓\033[0m"
            note = f"{', '.join(r.name for r in results)}  ({stamp}, {age}d ago)"
        else:
            mark = "\033[31m✗\033[0m"
            note = "\033[31mNO RESULTS FILE — findings exist only in chat/journal\033[0m"
        print(f"  {mark} {p.name:<{width}}  {len(scripts):>2} scripts   {note}")


# --------------------------------------------------------------- audio
def audio() -> None:
    rule("AUDIO")
    aud = ROOT / "audio"
    if not aud.is_dir():
        print("  no audio/ directory")
        return
    exts = {".wav", ".m4a", ".mp3", ".flac", ".mp4", ".mov", ".aiff"}
    for p in sorted(x for x in aud.iterdir() if x.is_dir()):
        takes = [f for f in p.rglob("*") if f.suffix.lower() in exts]
        if takes:
            mb = sum(f.stat().st_size for f in takes) / 1e6
            print(f"  \033[32m✓\033[0m {p.name:<24} {len(takes):>3} files ({mb:.0f} MB)")
        else:
            print(f"  \033[33m—\033[0m {p.name:<24} \033[33mEMPTY — session not recorded\033[0m")


# --------------------------------------------------------------- git
def git() -> None:
    rule("GIT")
    if not (ROOT / ".git").exists():
        print("  not a git repo")
        return

    if (ROOT / ".git" / "index.lock").exists():
        print("  \033[31m! .git/index.lock present — an interrupted git operation is "
              "blocking commands. Remove it.\033[0m")

    branch = sh("git", "rev-parse", "--abbrev-ref", "HEAD") or "?"
    upstream = sh("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    print(f"  branch:   {branch}")
    print(f"  upstream: {upstream or chr(27) + '[31mNONE SET — plain `git push` will not work' + chr(27) + '[0m'}")

    last = sh("git", "log", "-1", "--format=%h  %cd  %s", "--date=short")
    print(f"  last commit: {last or '(none)'}")

    sh("git", "fetch", "--quiet", "origin")
    if upstream:
        counts = sh("git", "rev-list", "--left-right", "--count", f"{upstream}...HEAD")
        if counts:
            behind, ahead = (counts.split() + ["?", "?"])[:2]
            flag = "" if ahead == "0" else "  \033[33m<- UNPUBLISHED WORK\033[0m"
            print(f"  ahead of remote:  {ahead}{flag}")
            print(f"  behind remote:    {behind}"
                  + ("" if behind == "0" else "  \033[33m<- remote has commits you lack\033[0m"))

    dirty = sh("git", "status", "--porcelain")
    if dirty:
        lines = dirty.splitlines()
        print(f"  \033[33muncommitted changes: {len(lines)}\033[0m")
        for line in lines[:12]:
            print(f"      {line}")
        if len(lines) > 12:
            print(f"      ... and {len(lines) - 12} more")
    else:
        print("  working tree clean")


# --------------------------------------------------------------- doc freshness
def docs() -> None:
    rule("DOC FRESHNESS")
    proj = ROOT / "PROJECT.md"
    if not proj.is_file():
        print("  no PROJECT.md")
        return
    text = proj.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Last verified:\s*(\d{4}-\d{2}-\d{2})", text)
    if not m:
        print("  \033[31mPROJECT.md has no 'Last verified:' stamp — cannot tell if it is "
              "current.\033[0m")
        return
    stamped = datetime.strptime(m.group(1), "%Y-%m-%d").date()
    age = (datetime.now().date() - stamped).days
    if age > STALE_AFTER_DAYS:
        print(f"  \033[31mPROJECT.md §Current state last verified {stamped} "
              f"({age} days ago) — TREAT AS STALE.\033[0m")
    else:
        print(f"  \033[32mPROJECT.md §Current state verified {stamped} ({age}d ago).\033[0m")

    priv = ROOT / "_private"
    if priv.is_dir():
        ignored = sh("git", "check-ignore", "_private")
        if ignored:
            print("  \033[32m_private/ is gitignored.\033[0m")
        else:
            print("  \033[31m! _private/ EXISTS AND IS NOT IGNORED — do not push.\033[0m")


def main() -> int:
    print(f"\033[1mTUNE repo status\033[0m — {ROOT}")
    print(f"generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    experiments()
    audio()
    git()
    docs()
    print("\nReconcile the above against PROJECT.md §Current state before trusting it.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
