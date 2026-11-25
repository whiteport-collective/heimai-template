#!/usr/bin/env python3
"""Walk an agents folder and list every object per source and layer, with what uses it and
what it uses, from the objects' own front matter.

Flags references to objects that do not exist, guardrails without an `## Evals` section,
links that disagree in the two directions, and any file that points into WDS's agents
folder. Prints tables, or `--json` in the stable form the glass's Agents pages read
(schema heim-capability-catalog/1, documented in tool.md). Reads only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "heim-floor"))
try:
    import floor  # type: ignore
except ImportError:
    floor = None
try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

SCHEMA = "heim-capability-catalog/1"
LAYERS = ("agents", "skills", "tools", "templates", "apps", "automations", "dependencies", "guardrails")
MAIN_FILE = {"agents": ("persona.md", "instructions.md"), "skills": ("SKILL.md",), "tools": ("tool.md",),
             "apps": ("app.md",), "automations": ("automation.md", "README.md"), "templates": ("README.md",)}
REF_FIELDS = {"skills": "skills", "tools": "tools", "templates": "templates", "guardrails": "guardrails",
              "apps": "apps"}
NEEDS_FRONT_MATTER = ("agents", "skills", "tools", "apps", "dependencies", "guardrails")
TEXT = {".md", ".py", ".yaml", ".yml", ".json", ".js", ".mjs", ".cjs", ".ts", ".ps1", ".sh", ".txt",
        ".html", ".css", ".toml"}
WDS_PATH = "agents/" + "wds/"          # written in two parts so this file does not flag itself
SKIP_DIRS = {"__pycache__", "node_modules", ".git"}
EVERYONE = {"all", "every agent", "everyone", "*"}


@dataclass
class Obj:
    source: str
    layer: str
    name: str
    path: Path                      # the folder or file of the object
    main: Path | None               # the file its front matter is read from
    fm: dict = field(default_factory=dict)
    fm_error: str = ""
    text: str = ""
    files: list[Path] = field(default_factory=list)
    uses: dict = field(default_factory=dict)            # field -> [ids]
    agents: set = field(default_factory=set)
    referenced_by: set = field(default_factory=set)

    @property
    def id(self) -> str:
        return f"{self.source}/{self.layer}/{self.name}"


@dataclass
class Catalog:
    folder: Path
    sources: list[dict]
    objects: dict[str, Obj]
    findings: list[dict]


def utf8() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def front_matter(text: str) -> tuple[dict, str]:
    """(keys, error). Empty keys and no error when there is no front matter."""
    if not text.startswith("---"):
        return {}, ""
    end = text.find("\n---", 3)
    if end < 0:
        return {}, "front matter not closed"
    block = text[3:end].strip("\n")
    if yaml is not None:
        try:
            data = yaml.safe_load(block) or {}
            return (data, "") if isinstance(data, dict) else ({}, "front matter is not a map")
        except yaml.YAMLError as e:
            first = str(e).splitlines()[0]
            data = {}
            for line in block.splitlines():          # keep what can be read line by line
                m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
                if m:
                    data[m.group(1)] = m.group(2)
            return data, f"front matter is not valid YAML ({first})"
    data = {}
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            v = m.group(2).strip()
            data[m.group(1)] = [x.strip() for x in v.strip("[]").split(",") if x.strip()] if v.startswith("[") else v
    return data, ""


def as_list(v) -> list[str]:
    if v is None or v == "":
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    s = str(v).strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    return [x.strip() for x in s.split(",") if x.strip()]


def files_under(p: Path) -> list[Path]:
    if p.is_file():
        return [p]
    out = []
    for f in sorted(p.rglob("*")):
        if f.is_file() and not any(part in SKIP_DIRS for part in f.relative_to(p).parts):
            out.append(f)
    return out


def find_sources(folder: Path) -> list[Path]:
    if any((folder / layer).is_dir() for layer in LAYERS):
        return [folder]
    return sorted(d for d in folder.iterdir()
                  if d.is_dir() and not d.name.startswith(".") and any((d / l).is_dir() for l in LAYERS))


def objects_in(src: Path) -> list[Obj]:
    out = []
    for layer in LAYERS:
        d = src / layer
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            if p.name.startswith((".", "_")) or p.name in SKIP_DIRS:
                continue
            if p.is_dir():
                main = next((p / n for n in MAIN_FILE.get(layer, ()) if (p / n).is_file()), None)
                if main is None and layer not in ("templates",):
                    mds = sorted(p.glob("*.md"))
                    main = mds[0] if mds else None
                name = p.name
            else:
                main, name = p, p.stem
            o = Obj(source=src.name, layer=layer, name=name, path=p, main=main, files=files_under(p))
            if main is not None:
                o.text = read(main)
                if main.suffix == ".md" or layer != "templates":
                    o.fm, o.fm_error = front_matter(o.text)
            out.append(o)
    return out


def resolve(ref: str, default_layer: str, src: str, sources: set[str]) -> tuple[str, str, str]:
    r = ref.strip().strip("`").replace("\\", "/")
    for suffix in ("/tool.md", "/SKILL.md", "/persona.md", "/app.md"):
        if r.endswith(suffix):
            r = r[: -len(suffix)]
    r = re.sub(r"\.(md|ya?ml|html|txt)$", "", r)
    parts = [x for x in r.split("/") if x]
    source = src
    if len(parts) > 1 and (parts[0] in sources or parts[0] in ("heim", "wds", "taste", "bmad")):
        source, parts = parts[0], parts[1:]
    layer = default_layer
    if len(parts) > 1 and parts[0] in LAYERS:
        layer, parts = parts[0], parts[1:]
    return source, layer, (parts[0] if parts else "")


def has_evals(text: str) -> bool:
    m = re.search(r"^##\s+Evals\b.*$", text, re.MULTILINE)
    if not m:
        return False
    rest = text[m.end():]
    nxt = re.search(r"^##\s", rest, re.MULTILINE)
    body = rest[: nxt.start()] if nxt else rest
    rows = [l for l in body.splitlines() if l.strip().startswith("|") and not re.match(r"^\|[\s:|-]+\|$", l.strip())]
    return len(rows) >= 2          # a header and at least one case


def scan(folder: Path) -> Catalog:
    srcs = find_sources(folder)
    names = {s.name for s in srcs}
    objs: dict[str, Obj] = {}
    for s in srcs:
        for o in objects_in(s):
            objs[o.id] = o
    agents = {o.name for o in objs.values() if o.layer == "agents"}
    findings: list[dict] = []

    def find(kind, severity, o: Obj | None, detail, path: Path | None = None):
        p = path or (o.main or o.path if o else folder)
        findings.append({"kind": kind, "severity": severity, "object": o.id if o else "",
                         "path": p.relative_to(folder).as_posix() if p.is_relative_to(folder) else str(p),
                         "detail": detail})

    # references
    for o in objs.values():
        if o.fm_error and o.layer != "templates":      # a template's front matter is part of its content
            find("front-matter-not-yaml", "warning", o, o.fm_error + "; quote values that hold ': '")
        if o.layer in NEEDS_FRONT_MATTER and o.main is not None and not o.fm and not o.fm_error:
            find("no-front-matter", "warning", o, "no front matter, so the catalog cannot say what uses it")
        if o.layer == "agents":
            o.agents.add(o.name)
        for f, layer in REF_FIELDS.items():
            if o.layer == "tools" and f == "skills":
                continue                     # a tool's skills: names who uses it; checked below
            ids = []
            for ref in as_list(o.fm.get(f)):
                src, lay, nm = resolve(ref, layer, o.source, names)
                rid = f"{src}/{lay}/{nm}"
                if rid in objs:
                    ids.append(rid)
                    objs[rid].referenced_by.add(o.id)
                else:
                    where = "" if src in names else f" (source {src} is not in this folder)"
                    find("missing-reference", "error", o, f"{f}: {ref} does not exist{where}")
            if ids:
                o.uses[f] = sorted(set(ids))
        for a in as_list(o.fm.get("used_by")):
            if a.lower() in EVERYONE:
                o.agents.add("*")
                continue
            if a not in agents and f"{o.source}/skills/{a}" in objs:
                find("used-by-names-a-skill", "warning", o,
                     f"used_by names the skill {a}; used_by names agents, and a tool names its skills in skills:")
                continue
            o.agents.add(a)
            if a not in agents:
                find("unknown-agent", "info", o, f"used_by names {a}, who is not an agent in this folder")
        if o.layer == "guardrails" and not has_evals(o.text):
            find("guardrail-without-evals", "error", o, "no ## Evals table with at least one case")

    # what each agent reaches: persona -> its skills, guardrails, apps; skill -> its tools, templates, guardrails
    for o in objs.values():
        if o.layer == "agents":
            for rid in sum(o.uses.values(), []):
                objs[rid].agents.add(o.name)
                if objs[rid].layer == "skills" and o.name not in as_list(objs[rid].fm.get("used_by")) \
                        and "*" not in objs[rid].agents and objs[rid].fm:
                    find("asymmetric", "warning", objs[rid],
                         f"{o.name}'s persona lists this skill, but its used_by does not name {o.name}")
    for o in objs.values():
        if o.layer == "skills":
            for rid in sum(o.uses.values(), []):
                objs[rid].agents |= {a for a in o.agents}
                t = objs[rid]
                if t.layer == "tools" and t.fm and o.name not in as_list(t.fm.get("skills")):
                    find("asymmetric", "warning", t, f"skill {o.name} lists this tool, but its skills: does not name it")
    for o in objs.values():
        if o.layer == "tools":
            for ref in as_list(o.fm.get("skills")):
                src, lay, nm = resolve(ref, "skills", o.source, names)
                rid = f"{src}/{lay}/{nm}"
                if rid not in objs:
                    find("missing-reference", "error", o, f"skills: {ref} does not exist")
                elif o.id not in objs[rid].uses.get("tools", []):
                    find("asymmetric", "warning", o, f"its skills: names {nm}, but that skill's tools: does not list it")

    # files that point into WDS's agents folder
    for s in srcs:
        owner = {}
        for o in objs.values():
            if o.source == s.name:
                for f in o.files:
                    owner[f] = o
        for f in files_under(s):
            if f.suffix.lower() not in TEXT:
                continue
            text = read(f)
            if WDS_PATH in text:
                n = text.count(WDS_PATH)
                line = next(i for i, l in enumerate(text.splitlines(), 1) if WDS_PATH in l)
                find("mentions-wds-path", "error", owner.get(f), f"{n} mention(s), first on line {line}", f)

    sources = []
    for s in srcs:
        note = read(s / ".source").strip()
        m = re.search(r"source:\s*(\S+)", note)
        counts = {l: sum(1 for o in objs.values() if o.source == s.name and o.layer == l) for l in LAYERS}
        sources.append({"name": s.name, "path": s.relative_to(folder).as_posix() if s != folder else ".",
                        "copy_of": (m.group(1) if m else (note.splitlines()[0] if note else "")),
                        "counts": {k: v for k, v in counts.items() if v}})
    findings.sort(key=lambda f: ({"error": 0, "warning": 1, "info": 2}[f["severity"]], f["kind"], f["object"], f["path"]))
    return Catalog(folder=folder, sources=sources, objects=objs, findings=findings)


def to_json(c: Catalog) -> dict:
    objs = []
    for oid in sorted(c.objects):
        o = c.objects[oid]
        fm = o.fm
        objs.append({
            "id": o.id, "source": o.source, "layer": o.layer, "name": o.name,
            "path": (o.main or o.path).relative_to(c.folder).as_posix(),
            "version": str(fm.get("version") or ""), "owner": str(fm.get("owner") or ""),
            "description": str(fm.get("description") or ""), "status": str(fm.get("status") or ""),
            "used_by": sorted(as_list(fm.get("used_by"))), "agents": sorted(o.agents),
            "uses": {k: o.uses.get(k, []) for k in REF_FIELDS},
            "referenced_by": sorted(o.referenced_by),
            "has_evals": has_evals(o.text) if o.layer == "guardrails" else None,
            "lines": o.text.count("\n") + (1 if o.text and not o.text.endswith("\n") else 0),
            "files": len(o.files),
        })
    kinds: dict[str, int] = {}
    for f in c.findings:
        kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
    by_layer = {l: sum(1 for o in c.objects.values() if o.layer == l) for l in LAYERS}
    return {"schema": SCHEMA, "folder": c.folder.as_posix(), "sources": c.sources, "objects": objs,
            "findings": c.findings,
            "summary": {"objects": len(objs), "by_layer": {k: v for k, v in by_layer.items() if v},
                        "findings": dict(sorted(kinds.items()))}}


def default_folder(heim: str | None) -> Path:
    if floor is None:
        raise SystemExit("Error: give the agents folder (heim-floor is not beside this tool).")
    f = floor.load(heim=heim)
    if f.format == 2:
        return (f.root / str(f.config.get("agents") or ".heimai/agents/")).resolve()
    return (f.root / "agents").resolve()


def short(ids: list[str], src: str) -> str:
    return ", ".join(i.split("/", 2)[2] if i.startswith(src + "/") else i for i in ids)


def print_tables(c: Catalog, show_all: bool, only_source: str | None, only_layer: str | None) -> None:
    print(f"Agents folder: {c.folder}")
    flags: dict[str, list[str]] = {}
    for f in c.findings:
        flags.setdefault(f["object"], []).append(f["kind"])
    for s in c.sources:
        if only_source and s["name"] != only_source:
            continue
        copy = f"copy of {s['copy_of']}" if s["copy_of"] else "edited here"
        print(f"\n== {s['name']}  ({copy})  " + ", ".join(f"{v} {k}" for k, v in s["counts"].items()))
        for layer in LAYERS:
            if only_layer and layer != only_layer:
                continue
            rows = [o for o in sorted(c.objects.values(), key=lambda o: o.name) if o.source == s["name"] and o.layer == layer]
            if not rows:
                continue
            print(f"\n  {layer}")
            for o in rows:
                agents = ", ".join(sorted(o.agents)) or "-"
                uses = "; ".join(f"{k}: {short(v, s['name'])}" for k, v in o.uses.items())
                fl = sorted(set(flags.get(o.id, [])) - {"unknown-agent"})
                who = "" if layer == "agents" else f"used by {agents}   "
                print(f"    {o.name:<28} {who}" + (f"uses {uses}" if uses else "")
                      + (f"   [{', '.join(fl)}]" if fl else ""))
    print(f"\nFindings ({len(c.findings)})")
    kinds: dict[str, list[dict]] = {}
    for f in c.findings:
        kinds.setdefault(f["kind"], []).append(f)
    for kind, items in kinds.items():
        print(f"\n  {kind} ({len(items)}, {items[0]['severity']})")
        for f in items if show_all else items[:15]:
            print(f"    {f['path']}: {f['detail']}")
        if not show_all and len(items) > 15:
            print(f"    … {len(items) - 15} more (--all lists them)")
    if not c.findings:
        print("  none")


def main() -> int:
    utf8()
    ap = argparse.ArgumentParser(description="List the agents and capabilities in an agents folder (see tool.md).")
    ap.add_argument("folder", nargs="?", help="an agents folder, or one source in it (default: the Heim's)")
    ap.add_argument("--heim", help="the Heim whose agents folder to read")
    ap.add_argument("--source", help="show only this source")
    ap.add_argument("--layer", choices=LAYERS, help="show only this layer")
    ap.add_argument("--all", action="store_true", help="list every finding")
    ap.add_argument("--json", action="store_true", help="the stable JSON the glass reads")
    ap.add_argument("--strict", action="store_true", help="exit 1 when there is an error finding")
    a = ap.parse_args()
    try:
        folder = Path(a.folder).resolve() if a.folder else default_folder(a.heim)
    except Exception as e:  # floor.FloorError
        print(f"Error: {e}", file=sys.stderr)
        return 2
    if not folder.is_dir():
        print(f"Error: {folder} is not a folder.", file=sys.stderr)
        return 2
    c = scan(folder)
    if a.json:
        print(json.dumps(to_json(c), ensure_ascii=False, indent=2))
    else:
        print_tables(c, a.all, a.source, a.layer)
    if a.strict and any(f["severity"] == "error" for f in c.findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
