#!/usr/bin/env python3
"""See a Heim's projects, and start a new one from the templates once the person has confirmed it.

    scan   [--heim DIR]
    create <slug> --name "Name" [--what ...] [--client ...] [--builds ...] [--goal ...] [--constraints ...]
           [--language ...] [--milestone ...] [--code app/|repo|undecided] [--sources ...]
           [--projects-folder X] [--heim DIR] [--yes]

A project is <projects>/<slug>/ with feature.yaml and 01-brief/00-intake.md
(decision 26). Without --yes, create only prints what it would write. It never
overwrites and refuses a folder that exists. Folders come from the floor plan
(../heim-floor/floor.py); templates from <tool dir>/../../templates/project/. See tool.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "heim-floor"))
import floor  # noqa: E402

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WDS_FOLDER = re.compile(r"^[A-G]-[A-Za-z]")       # A-Product-Brief, B-Trigger-Map, ...
OPEN = {"open", "öppen", "oppen"}
FIELDS = {   # intake field: what [needed] asks when it was not given
    "what": "what it is, in one sentence",
    "client": "who it is for",
    "builds": "what is built or made",
    "goal": "what it should achieve",
    "constraints": "time, budget and other hard walls",
    "language": "the languages, the first one first",
    "milestone": "the first date that matters",
    "code": "app/, its own repo, or undecided",
    "sources": "where the intake comes from: the conversation, documents",
}


def front_matter(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            if f.readline().strip() != "---":
                return {}
            text = []
            for line in f:
                if line.strip() == "---":
                    break
                text.append(line)
        return floor.parse_flat_yaml("".join(text))
    except OSError:
        return {}


def as_list(v) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v if x]
    return [v] if isinstance(v, str) and v else []


def open_handovers(sessions: Path | None) -> list[tuple[Path, list[str], dict]]:
    out = []
    if not sessions or not sessions.is_dir():
        return out
    for dirpath, dirs, files in os.walk(sessions):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in sorted(files):
            if not name.lower().endswith(".md"):
                continue
            p = Path(dirpath) / name
            fm = front_matter(p)
            if str(fm.get("status", "")).strip().lower() in OPEN:
                projects = as_list(fm.get("projects"))
                if projects:
                    out.append((p, projects, fm))
    return out


def describe(folder: Path) -> str:
    card = folder / "feature.yaml"
    if card.is_file():
        try:
            d, note = floor.read_card(card)
        except floor.FloorError as e:
            return f"feature.yaml unreadable ({e})"
        name = d.get("feature") or folder.name
        return f"{name} · {d.get('status', '?')} · {d.get('version', '?')}" + (f"  (feature.yaml {note})" if note else "")
    try:
        children = [c.name for c in folder.iterdir() if c.is_dir()]
    except OSError:
        children = []
    if any(WDS_FOLDER.match(c) for c in children):
        return "WDS layout (" + ", ".join(sorted(c for c in children if WDS_FOLDER.match(c))) + ")"
    return "no feature.yaml"


def cmd_scan(a) -> int:
    f = floor.load(heim=a.heim)
    print(f"Heim: {f.name}")
    print(f"Root: {f.root}  (floor plan {f.rel(f.plan)})")
    handovers = open_handovers(f.sessions)
    known = set()
    for pf in f.projects:
        print(f"\nProjects folder: {f.rel(pf)}" + ("" if pf.is_dir() else "  (missing)"))
        if not pf.is_dir():
            continue
        folders = sorted(d for d in pf.iterdir() if d.is_dir() and not d.name.startswith((".", "_")))
        if not folders:
            print("  (no projects)")
        for d in folders:
            known.add(d.name)
            print(f"  {d.name:<28} {describe(d)}")
            for p, _projects, fm in handovers:
                if d.name in _projects:
                    print(f"      open handover → {fm.get('to', '?')}: {f.rel(p)}")
    others = [(p, pr, fm) for p, pr, fm in handovers if not set(pr) & known]
    if others:
        print("\nOpen handovers naming a project that is not a folder here:")
        for p, pr, fm in others:
            print(f"  [{', '.join(pr)}] → {fm.get('to', '?')}: {f.rel(p)}")
    print(f"\n{len(known)} projects, {len(handovers)} open handovers naming a project"
          + ("" if f.sessions and f.sessions.is_dir() else " (no sessions folder)") + ".")
    return 0


def yaml_quoted(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def one_line(s: str | None) -> str | None:
    return " ".join(s.split()) if s else s


def pick_projects_folder(f, choice: str | None) -> Path:
    if not choice:
        return f.projects[0]
    # as the floor plan writes it (heimai: 2 from the root, heim: 1 inside heimdocs), then from the root, then from here
    base = f.root if f.format == 2 else f.heimdocs
    for candidate in ((base / choice).resolve(), (f.root / choice).resolve(), Path(choice).resolve()):
        if candidate in f.projects:
            return candidate
    raise floor.FloorError(f"{choice} is not a projects folder in the floor plan; choose one of: "
                           + ", ".join(f.rel(p) for p in f.projects))


def cmd_create(a) -> int:
    if not SLUG.match(a.slug):
        print(f"Error: the slug {a.slug!r} must be lowercase letters, digits and hyphens (e.g. sjobod-site)",
              file=sys.stderr)
        return 2
    f = floor.load(heim=a.heim)
    pf = pick_projects_folder(f, a.projects_folder)
    tpl = floor.templates_dir(__file__) / "project"
    if not (tpl / "feature.yaml").is_file() or not (tpl / "00-intake.md").is_file():
        print(f"Error: no project templates at {tpl}", file=sys.stderr)
        return 2
    target = pf / a.slug
    if target.exists():
        try:
            inside = sorted(c.name + ("/" if c.is_dir() else "") for c in target.iterdir())
        except OSError:
            inside = []
        print(f"Refused: {f.rel(target)} already exists; nothing written.")
        print("  It holds: " + (", ".join(inside[:20]) + (" …" if len(inside) > 20 else "") if inside else "(empty)"))
        return 1

    values = {"name": one_line(a.name), "date": dt.date.today().isoformat(),
              "next": "[needed: the next step]"}
    for k, ask in FIELDS.items():
        values[k] = one_line(getattr(a, k)) or f"[needed: {ask}]"
    card = (tpl / "feature.yaml").read_text(encoding="utf-8")
    for k, v in values.items():
        card = card.replace("{{" + k + "}}", yaml_quoted(v))
    intake = (tpl / "00-intake.md").read_text(encoding="utf-8")
    for k, v in values.items():
        intake = intake.replace("{{" + k + "}}", v)

    print(f"Heim: {f.name}  ({f.root})")
    print(f"{'Writing' if a.yes else 'Would write'} in {f.rel(pf)}/:")
    print(f"  {a.slug}/\n    feature.yaml\n    01-brief/\n      00-intake.md")
    if not a.yes:
        print("\n--- feature.yaml ---\n" + card.rstrip())
        print("\n--- 01-brief/00-intake.md ---\n" + intake.rstrip())
        print("\nNothing written: add --yes after the person has confirmed the summary.")
        return 0

    target.mkdir(parents=True, exist_ok=False)
    written = []
    for rel, text in (("feature.yaml", card), ("01-brief/00-intake.md", intake)):
        p = target / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("x", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        written.append(p)
    for p in written:
        print(f"  wrote    {f.rel(p)}")
    open_fields = [k for k, v in values.items() if v.startswith("[needed")]
    if open_fields:
        print("Still [needed]: " + ", ".join(open_fields))
    return 0


def main() -> int:
    floor.utf8_stdout()
    ap = argparse.ArgumentParser(description="See a Heim's projects, or start a new one (see tool.md).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="the Heim, its projects and the open handovers naming them")
    s.add_argument("--heim")
    c = sub.add_parser("create", help="print, or with --yes write, a new project from the templates")
    c.add_argument("slug")
    c.add_argument("--name", required=True)
    for k in FIELDS:
        if k == "code":
            c.add_argument("--code", choices=["app/", "repo", "undecided"])
        else:
            c.add_argument(f"--{k}")
    c.add_argument("--projects-folder", help="which projects folder, when the floor plan names several")
    c.add_argument("--heim")
    c.add_argument("--yes", action="store_true", help="write; only after the person has confirmed the summary")
    a = ap.parse_args()
    try:
        return cmd_scan(a) if a.cmd == "scan" else cmd_create(a)
    except (OSError, floor.FloorError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
