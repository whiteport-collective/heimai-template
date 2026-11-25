#!/usr/bin/env python3
"""Check every agent and capability in an agents folder against Heim's conventions.

Errors: no front matter, missing keys, a guardrail without evals, a path into WDS's agents
folder, something that looks like a secret, a reference to an object that does not exist.
Warnings: a skill description without trigger phrases, size above the guidance, BMad
markers, shouted rules, dead links, a passed review date, links that disagree in the two
directions. It never requires XML or a fixed step format. Reads only; fixes nothing.
See tool.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "capability-catalog"))
import catalog  # type: ignore  # noqa: E402

REQUIRED = {
    "skills": ("name", "description", "used_by", "version"),
    "tools": ("used_by", "skills"),
    "guardrails": ("name", "applies_to"),
    "agents": ("name", "description", "skills", "guardrails"),
    "dependencies": ("name", "for"),
    "apps": ("name",),
}
SIZE = {"skills": 150, "agents": 80}          # lines in the main file before a warning
REFERENCE_SIZE = 250
TRIGGER = re.compile(r"\bUse (when|whenever|at|for|after|before|if)\b|[\"“(][^\"”)]{3,}[\"”)]", re.IGNORECASE)
BMAD = re.compile(r"<workflow\b|<step\b|<activation\b|<constraints>|\{output_folder\}|\{project-root\}")
SHOUT = re.compile(r"\b(MUST|CRITICAL|MANDATORY|NEVER|ALWAYS)\b|No exceptions")
SECRET = re.compile(r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|\bsk-[A-Za-z0-9-]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}"
                    r"|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----")
LINK = re.compile(r"\]\(([^)\s]+)\)")
CATALOG_KINDS = {"missing-reference": "error", "guardrail-without-evals": None, "mentions-wds-path": None,
                 "asymmetric": "warning", "front-matter-not-yaml": "warning", "used-by-names-a-skill": "warning",
                 "no-front-matter": None, "unknown-agent": None}


def check(c: catalog.Catalog, only: str | None) -> list[dict]:
    today = dt.date.today()
    out: list[dict] = []

    def add(o, level, rule, msg, path: Path | None = None, line: int = 0):
        p = path or o.main or o.path
        out.append({"object": o.id, "level": level, "rule": rule, "message": msg, "line": line,
                    "path": p.relative_to(c.folder).as_posix() if p.is_relative_to(c.folder) else str(p)})

    for oid in sorted(c.objects):
        o = c.objects[oid]
        if only and only not in oid:
            continue
        fm, layer = o.fm, o.layer
        if layer in REQUIRED and o.main is not None:
            if not fm and not o.fm_error:
                add(o, "error", "front-matter", "no front matter")
            else:
                miss = [k for k in REQUIRED[layer]
                        if not fm.get(k) and not (k == "used_by" and fm.get("owner"))
                        and not (layer == "tools" and k == "used_by" and fm.get("tool"))]
                if layer == "tools" and not (fm.get("tool") or fm.get("name")):
                    miss.insert(0, "tool")
                if miss:
                    add(o, "error" if layer != "tools" else "warning", "required-keys", "missing: " + ", ".join(miss))
            nm = fm.get("name") or fm.get("tool")
            if nm and layer in ("skills", "tools", "agents", "guardrails") and str(nm) != o.name:
                add(o, "warning", "name-matches-folder", f"name: {nm}, but the object is {o.name}")
        if layer == "guardrails" and not catalog.has_evals(o.text):
            add(o, "error", "guardrail-evals", "a guardrail without evals is a wish: add ## Evals with at least one case")
        if layer == "skills":
            desc = str(fm.get("description") or "")
            if desc and not TRIGGER.search(desc):
                add(o, "warning", "trigger-phrases", "the description says what, but not when (\"Use when …\", or the words people say)")
        if layer in SIZE and o.text:
            n = o.text.count("\n") + 1
            if n > SIZE[layer]:
                add(o, "warning", "size", f"{n} lines; guidance is about {SIZE[layer]}: move detail to references/ or a tool")
        def review_by(meta: dict, path: Path | None) -> None:
            rb = meta.get("review_by")
            if not rb:
                return
            try:
                d = rb if isinstance(rb, dt.date) else dt.date.fromisoformat(str(rb))
                if d < today:
                    add(o, "warning", "review-by-passed", f"review_by {d} has passed: the content may be out of date", path)
            except ValueError:
                add(o, "warning", "review-by-passed", f"review_by '{rb}' is not a date (YYYY-MM-DD)", path)

        review_by(fm, None)
        for f in o.files:
            if f.suffix.lower() not in catalog.TEXT:
                continue
            text = catalog.read(f)
            if f.suffix == ".md":
                if f != o.main and layer != "templates":
                    review_by(catalog.front_matter(text)[0], f)
                if f != o.main and f.name.lower() not in ("tool.md",):
                    n = text.count("\n") + 1
                    if n > REFERENCE_SIZE and layer in ("skills", "agents"):
                        add(o, "warning", "size", f"{n} lines in a reference; guidance is under {REFERENCE_SIZE}", f)
                prose_lines, fenced = [], False
                for line in text.splitlines():
                    if line.strip().startswith("```"):
                        fenced = not fenced
                    prose_lines.append("" if fenced else re.sub(r"`[^`]*`", "", line))
                for i, line in enumerate(prose_lines, 1):
                    if BMAD.search(line):
                        add(o, "warning", "bmad-markers", f"BMad workflow marker: {BMAD.search(line).group(0)}", f, i)
                shouts = SHOUT.findall(" ".join(prose_lines))
                if len(shouts) >= 3:
                    add(o, "warning", "calm-rules", f"{len(shouts)} shouted words (MUST, NEVER, ALWAYS …): write the rule and its reason", f)
                in_code = False
                for i, line in enumerate(text.splitlines(), 1):
                    if line.strip().startswith("```"):
                        in_code = not in_code
                    if in_code:
                        continue
                    for target in LINK.findall(line):
                        t = target.split("#", 1)[0]
                        if not t or re.match(r"^[a-z]+:", t) or t.startswith(("<", "{")):
                            continue
                        if not (f.parent / t).exists():
                            add(o, "warning", "dead-link", f"link to {target} leads nowhere", f, i)
            for i, line in enumerate(text.splitlines(), 1):
                if SECRET.search(line):
                    add(o, "error", "secret", "this looks like a secret: burn it and name the Bitwarden item instead", f, i)
                if catalog.WDS_PATH in line:
                    add(o, "error", "wds-path", "points into WDS's agents folder; point into the Heim instead", f, i)
    for fd in c.findings:
        level = CATALOG_KINDS.get(fd["kind"])
        if fd["kind"] == "mentions-wds-path" and not fd["object"]:
            level = "error"                      # a source file that belongs to no object
        if level and (not only or only in fd["object"]):
            out.append({"object": fd["object"], "level": level, "rule": fd["kind"], "message": fd["detail"],
                        "line": 0, "path": fd["path"]})
    out.sort(key=lambda x: (x["object"], 0 if x["level"] == "error" else 1, x["rule"], x["path"], x["line"]))
    return out


def main() -> int:
    catalog.utf8()
    ap = argparse.ArgumentParser(description="Check agents and capabilities against Heim's conventions (see tool.md).")
    ap.add_argument("folder", nargs="?", help="an agents folder, or one source in it (default: the Heim's)")
    ap.add_argument("--heim")
    ap.add_argument("--only", help="check only objects whose id contains this (e.g. heim/skills/governance)")
    ap.add_argument("--errors", action="store_true", help="show only errors")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        folder = Path(a.folder).resolve() if a.folder else catalog.default_folder(a.heim)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    c = catalog.scan(folder)
    res = check(c, a.only)
    if a.errors:
        res = [r for r in res if r["level"] == "error"]
    errors = sum(1 for r in res if r["level"] == "error")
    if a.json:
        print(json.dumps({"schema": "heim-capability-lint/1", "folder": folder.as_posix(),
                          "errors": errors, "warnings": len(res) - errors, "results": res},
                         ensure_ascii=False, indent=2))
        return 1 if errors else 0
    current = None
    for r in res:
        if r["object"] != current:
            current = r["object"]
            print(f"\n{current or '(source files)'}")
        loc = r["path"] + (f":{r['line']}" if r["line"] else "")
        print(f"  {r['level']:<7} {r['rule']:<20} {r['message']}  ({loc})")
    checked = sum(1 for oid in c.objects if not a.only or a.only in oid)
    print(f"\n{checked} objects checked: {errors} errors, {len(res) - errors} warnings.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
