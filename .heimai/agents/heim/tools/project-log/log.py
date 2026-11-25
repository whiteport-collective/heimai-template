#!/usr/bin/env python3
"""Keep a project's design log and its card (feature.yaml).

    append <project> --agent saga --text "..."
    status <project> [--status X] [--next "..."] [--version X.Y.Z]

<project> is a slug under the Heim's projects folder(s), a path, or `heim` for
the Heim's own log under heimdocs. The log is <project>/05-progress/00-design-log.md.
status edits top-level keys line by line, so the rest of feature.yaml and its
comments stay as they are. Folders come from the floor plan (../heim-floor/floor.py).
See tool.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "heim-floor"))
import floor  # noqa: E402

AGENT = re.compile(r"^[a-z][a-z0-9-]*$")
VERSION = re.compile(r"^\d+\.\d+\.\d+$")
PLAIN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._/()+-]*$")   # safe to write without quotes


class Refused(Exception):
    pass


def resolve(f, arg: str) -> tuple[Path, str, bool]:
    """(the project's folder, its name, whether it is the Heim itself)."""
    if arg == "heim":
        return f.heimdocs, f.name, True
    for pf in f.projects:
        if (pf / arg).is_dir():
            folder = pf / arg
            break
    else:
        p = Path(arg)
        if not p.is_dir():
            raise Refused(f"no project {arg!r} in {', '.join(f.rel(p) for p in f.projects)}, and no such folder")
        folder = p.resolve()
    name = folder.name
    card = folder / "feature.yaml"
    if card.is_file():
        name = str(floor.read_card(card)[0].get("feature") or name)
    return folder, name, False


def cmd_append(f, a) -> int:
    if not AGENT.match(a.agent):
        raise Refused(f"the agent {a.agent!r} must be a lowercase name, like saga")
    text = " ".join((a.text or "").split())
    if not text:
        raise Refused("--text is empty")
    folder, name, _ = resolve(f, a.project)
    log = folder / "05-progress" / "00-design-log.md"
    stamp = getattr(a, "session", None)   # a handover gives its session id and recipient: the heading the log already uses
    who = f"{a.agent} → {a.to}" if getattr(a, "to", None) else a.agent
    heading, bullet = f"### {stamp or dt.date.today().isoformat()} ({who})", f"- {text}"
    log.parent.mkdir(parents=True, exist_ok=True)
    if not log.exists():
        with log.open("x", encoding="utf-8", newline="\n") as fh:
            fh.write(f"# Design log: {name}\n\nThe project's timeline, with the latest at the top.\n\n## Log\n")
        print(f"created  {f.rel(log)}")
    raw = log.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.splitlines()
    at = next((i for i, ln in enumerate(lines) if ln.strip() == "## Log"), None)
    if at is None:   # a plain log: its old lines stay above, the newest-first part starts here
        lines += ["", "## Log"]
        at = len(lines) - 1
    first = at + 1
    while first < len(lines) and not lines[first].strip():
        first += 1
    if first < len(lines) and lines[first].strip() == heading:
        lines.insert(first + 1, bullet)          # same day and agent as the top entry: join it
        shown = [heading, bullet]
    else:
        lines[at + 1:first] = ["", heading, bullet, ""] if first < len(lines) else ["", heading, bullet]
        shown = [heading, bullet]
    with log.open("w", encoding="utf-8", newline="") as fh:
        fh.write(nl.join(lines) + nl)
    print(f"added at the top of {f.rel(log)}:\n  " + "\n  ".join(shown))
    return 0


def scalar(value: str, quote: bool = False) -> str:
    if not quote and PLAIN.match(value) and not value.lower() in ("yes", "no", "true", "false", "null", "on", "off"):
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def set_key(lines: list[str], key: str, value: str) -> tuple[str | None, str]:
    """Replace a top-level `key:` line (and its indented continuation lines) keeping its comment;
    append the key when it is missing. Returns (the old line(s), the new line)."""
    pat = re.compile(rf"^{re.escape(key)}\s*:(.*)$")
    for i, line in enumerate(lines):
        m = pat.match(line)
        if not m:
            continue
        rest = m.group(1)
        val = floor.strip_comment(rest)
        tail = rest[len(val):]
        new = f"{key}: {value}"
        if tail.strip().startswith("#"):
            comment = tail.strip()
            col = len(line) - len(rest) + len(val) + (len(tail) - len(tail.lstrip()))
            new = new.ljust(col) if len(new) < col else new + "  "
            new += comment
        j = i + 1
        while j < len(lines) and lines[j].strip() and lines[j][:1] in (" ", "\t"):
            j += 1
        old = "\n".join(lines[i:j])
        lines[i:j] = [new]
        return old, new
    new = f"{key}: {value}"
    lines.append(new)
    return None, new


def cmd_status(f, a) -> int:
    folder, _name, is_heim = resolve(f, a.project)
    card = folder / "feature.yaml"
    if not card.is_file():
        raise Refused(f"{f.rel(card)} does not exist" + (" (the Heim has no card; give a project)" if is_heim else ""))
    raw = card.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    changes = []
    if a.version is not None and not VERSION.match(a.version):
        raise Refused(f"the version {a.version!r} must be X.Y.Z")
    if a.status is not None:
        changes.append(("status", scalar(" ".join(a.status.split()))))
    if a.version is not None:
        changes.append(("version", a.version))
    if a.next is not None:
        changes.append(("next", scalar(" ".join(a.next.split()), quote=True)))

    print(f"{f.rel(card)}:")
    if not changes:
        print(raw.rstrip())
        note = floor.read_card(card)[1]
        if note:
            print(f"\nNote: feature.yaml is {note}.")
        return 0
    lines = raw.splitlines()
    for key, value in changes:
        old, new = set_key(lines, key, value)
        print(f"  before: {old if old is not None else '(no ' + key + ': line)'}")
        print(f"  after:  {new}")
    text = nl.join(lines) + nl
    if text != raw:
        with card.open("w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print("updated.")
    else:
        print("no change.")
    note = floor.read_card(card)[1]
    if note:
        print(f"Note: feature.yaml is still {note}; another key needs quotes.")
    return 0


def main() -> int:
    floor.utf8_stdout()
    ap = argparse.ArgumentParser(description="Keep a project's design log and feature.yaml (see tool.md).")
    ap.add_argument("--heim", help="the Heim (default: the nearest at or above here)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("append", help="add a dated line to the project's design log")
    p.add_argument("project", help="a slug under projects, a path, or heim")
    p.add_argument("--agent", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--session", help="a session id for the heading, YYYY-MM-DD_HH-MM-<user> (the handover tool gives it)")
    p.add_argument("--to", help="with --session: the recipient, so the heading reads (agent → to)")
    p.add_argument("--heim", dest="heim_sub")
    s = sub.add_parser("status", help="print feature.yaml, or update status, next and version in it")
    s.add_argument("project", help="a slug under projects, or a path")
    s.add_argument("--status")
    s.add_argument("--next")
    s.add_argument("--version")
    s.add_argument("--heim", dest="heim_sub")
    a = ap.parse_args()
    try:
        f = floor.load(heim=a.heim_sub or a.heim)
        return cmd_append(f, a) if a.cmd == "append" else cmd_status(f, a)
    except Refused as e:
        print(f"Refused: {e}", file=sys.stderr)
        return 1
    except (OSError, floor.FloorError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
