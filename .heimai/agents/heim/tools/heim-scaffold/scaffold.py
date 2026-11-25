#!/usr/bin/env python3
"""Create a new Heim's floor plan and folders from templates/heim/, or add a person to one.

Shows what it would write and writes nothing without --yes. Never overwrites: a file
that exists is kept and reported. See tool.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "heim-floor"))
try:
    import floor  # type: ignore
except ImportError:  # heim-floor not beside this tool: a minimal stand-in
    floor = None

TEMPLATES = (HERE / ".." / ".." / "templates" / "heim").resolve()
AGENTS_SOURCE = (HERE / ".." / "..").resolve()          # agents/heim/ (or the source's delivery folder)
CODE_MARKERS = ("package.json", "pyproject.toml", "Cargo.toml", "go.mod", "composer.json", "src")
GITIGNORE_NEEDS = (".heim-notify.txt", ".heimai/machine/notify.txt")  # the machine folder itself is in git (the Watchdog)


def utf8() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def fill(text: str, values: dict) -> str:
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(values.get(m.group(1), m.group(0))), text)


def template(rel: str) -> str:
    return (TEMPLATES / rel).read_text(encoding="utf-8")


def persona_line(agent: str) -> str:
    """The first sentence of an agent's persona description, for the agents table."""
    p = AGENTS_SOURCE / "agents" / agent / "persona.md"
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return "(not in this source)"
    m = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    if not m:
        return ""
    first = re.split(r"(?<=\.)\s", m.group(1).strip(), maxsplit=1)[0]
    return first.rstrip(".")


def slug(text: str) -> str:
    t = text.lower().replace("å", "a").replace("ä", "a").replace("ö", "o")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


class Plan:
    def __init__(self, root: Path):
        self.root = root
        self.items: list[tuple[Path, str | None, str]] = []   # (path, content or None for a note, note)

    def add(self, rel: str, content: str) -> None:
        self.items.append((self.root / rel, content, ""))

    def note(self, rel: str, text: str) -> None:
        self.items.append((self.root / rel, None, text))

    def show_and_write(self, write: bool) -> int:
        new = kept = 0
        for path, content, note in self.items:
            rel = path.relative_to(self.root).as_posix()
            if content is None:
                print(f"  note   {rel}: {note}")
                continue
            if path.exists():
                kept += 1
                print(f"  kept   {rel}  (exists, not changed)")
                continue
            new += 1
            print(f"  {'wrote ' if write else 'new   '} {rel}")
            if write:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
        if not write:
            print(f"\n{new} new, {kept} kept. Nothing written: run again with --yes to write.")
        else:
            print(f"\n{new} written, {kept} kept.")
        return 0


def existing_heim(folder: Path) -> Path | None:
    for p in (folder / ".heimai" / "heimai.yaml", folder / "heim.yaml", folder / "heimai.yaml"):
        if p.is_file():
            return p
    return None


def cmd_create(a) -> int:
    root = Path(a.into or ".").resolve()
    found = existing_heim(root)
    if found:
        print(f"Refused: {root} is already a Heim ({found.relative_to(root).as_posix()}). Nothing written.")
        print("Show it with heim-status; a Heim is never scaffolded twice.")
        return 3
    if a.kind == "private" and a.governance:
        print("Refused: a private Heim has no governance (decision 15). Nothing written.")
        return 2
    code = [m for m in CODE_MARKERS if (root / m).exists()]
    heimdocs = a.heimdocs or ("heimdocs/" if code else ".")
    hd = "" if heimdocs in (".", "./") else heimdocs.rstrip("/") + "/"
    agents = [x.strip() for x in (a.agents or "idun").split(",") if x.strip()]
    today = a.date or dt.date.today().isoformat()
    org_line = f"organization: {a.organization}\n" if a.organization else ""
    gov_line = ("# governance: governance-compliance/   # added by governance-init when the business wants a policy"
                if a.kind == "business" else "")
    if a.inherits:
        inherits = "inherits:\n" + "".join(
            f"  - from: {src}\n    take: [agents/heim]\n" for src in a.inherits)
    else:
        inherits = ("# inherits:                  # what is copied in, and from where; each copy gets a .source\n"
                    "#   - from: github:<owner>/HeimAI\n#     take: [agents/heim]\n")
    if a.kind == "private":
        policy = ("A private Heim has no governance: the person's soul files are the rules, and Heim's defaults "
                  "are offered as advice with the reason first.")
    else:
        policy = ("The policy is read in the order of `governance-compliance/policies.md` once it is set up; "
                  "until then Heim's defaults are offered as advice.")
    values = {
        "name": a.name, "description": a.description or f"{a.name}'s Heim", "kind": a.kind,
        "organization_line": org_line, "language": a.lang, "heimdocs": heimdocs,
        "governance_line": gov_line, "agents": ", ".join(agents), "inherits_block": inherits,
        "agents_table": "\n".join(f"| {x.capitalize()} | heim | {persona_line(x)} | `/{x}` |" for x in agents),
        "policy_line": policy, "person": a.person or "the owner", "date": today,
    }
    plan = Plan(root)
    plan.add("heim.yaml", fill(template("heim.yaml"), values))
    plan.add("AGENTS.md", fill(template("agents-md.md"), values))
    plan.add("CLAUDE.md", template("claude-md.md"))
    gi = root / ".gitignore"
    if gi.exists():
        have = gi.read_text(encoding="utf-8", errors="replace")
        missing = [x for x in GITIGNORE_NEEDS if x not in have]
        if missing:
            plan.note(".gitignore", f"exists; add by hand: {', '.join(missing)}")
    else:
        plan.add(".gitignore", template("gitignore.txt"))
    plan.add(f"{hd}00-decisions.md", fill(template("decisions.md"), values))
    plan.add(f"{hd}06-sessions/README.md", template("sessions-readme.md"))
    plan.add(f"{hd}users/README.md", template("users/README.md"))
    for f in ("user.md", "soul.md", "objectives.md"):
        plan.add(f"{hd}users/_template/{f}", template(f"users/_template/{f}"))
    plan.add(f"{hd}tasks/inbox.md", template("inbox.md"))
    if a.user:
        pv = dict(values, person=a.person or a.user, github=a.github or a.user)
        for f in ("user.md", "soul.md", "objectives.md"):
            plan.add(f"{hd}users/{a.user}/{f}", fill(template(f"users/_template/{f}"), pv))
    print(f"Heim: {a.name}  ({a.kind})  at {root}")
    print(f"heimdocs: {heimdocs}" + (f"  (code found: {', '.join(code)}, so the Heim's folders go in heimdocs/)" if code and not a.heimdocs else ""))
    print(f"agents woken: {', '.join(agents)}\n")
    return plan.show_and_write(a.yes)


def people_folder(f) -> Path:
    cfg = f.config
    if f.format == 2:
        return (f.root / str(cfg.get("users") or cfg.get("people") or ".heimai/users/")).resolve()
    return (f.heimdocs / str(cfg.get("people") or "users/")).resolve()


def cmd_add_person(a) -> int:
    if floor is None:
        print("Error: heim-floor is not beside this tool.", file=sys.stderr)
        return 2
    try:
        f = floor.load(heim=a.heim)
    except floor.FloorError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    user = slug(a.user)
    if user != a.user:
        print(f"The id is written in lowercase with hyphens: {user}")
    folder = people_folder(f) / user
    if folder.exists():
        print(f"Refused: {f.rel(folder)} exists. Nothing written. It holds:")
        for p in sorted(folder.iterdir()):
            print(f"  {p.name}")
        return 3
    values = {"person": a.name or user, "github": a.github or user}
    plan = Plan(f.root)
    for name in ("user.md", "soul.md", "objectives.md"):
        plan.add(f"{f.rel(folder)}/{name}", fill(template(f"users/_template/{name}"), values))
    print(f"Heim: {f.name}  ({f.root})\nPerson: {user}\n")
    return plan.show_and_write(a.yes)


def main() -> int:
    utf8()
    ap = argparse.ArgumentParser(description="Create a Heim, or add a person to one (see tool.md).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create", help="a new Heim's heim.yaml and folders")
    c.add_argument("--name", required=True)
    c.add_argument("--kind", choices=["private", "business", "project"], required=True)
    c.add_argument("--into", help="the folder (default: here)")
    c.add_argument("--description")
    c.add_argument("--organization")
    c.add_argument("--heimdocs", help="'.' (default) or heimdocs/ (default when the folder holds code)")
    c.add_argument("--agents", help="the agents to wake, comma-separated (default: idun)")
    c.add_argument("--inherits", action="append", help="a source to inherit from, e.g. github:<owner>/HeimAI")
    c.add_argument("--lang", default="en")
    c.add_argument("--person", help="who the Heim is set up with, for the first decision")
    c.add_argument("--user", help="also make this person's folder in users/")
    c.add_argument("--github")
    c.add_argument("--governance", action="store_true", help=argparse.SUPPRESS)
    c.add_argument("--date")
    c.add_argument("--yes", action="store_true", help="write (default: only show)")
    p = sub.add_parser("add-person", help="a person's folder from users/_template/")
    p.add_argument("user")
    p.add_argument("--name")
    p.add_argument("--github")
    p.add_argument("--heim")
    p.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    return cmd_create(a) if a.cmd == "create" else cmd_add_person(a)


if __name__ == "__main__":
    sys.exit(main())
