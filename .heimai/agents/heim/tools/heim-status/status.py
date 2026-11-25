#!/usr/bin/env python3
"""Print a Heim's floor plan, woken agents and capabilities, what is installed under its
agents folder, its policy, and the handovers still open. Reads only. See tool.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "heim-floor"))
sys.path.insert(0, str(HERE.parent / "handover-audit"))
import floor  # type: ignore  # noqa: E402

try:
    import audit as handovers  # type: ignore
except ImportError:
    handovers = None

LAYERS = ("agents", "skills", "tools", "templates", "apps", "automations", "dependencies", "guardrails")


def as_list(v) -> list:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    if isinstance(v, str):
        return [x.strip() for x in v.strip("[]").split(",") if x.strip()]
    return []


def woken(f) -> list[str]:
    cfg = f.config
    if f.format == 2:
        return as_list(cfg.get("agents_woken"))
    return as_list(cfg.get("agents"))     # in heim: 1, agents: is the list of woken agents


def agents_folder(f, override: str | None) -> Path:
    if override:
        return Path(override).resolve()
    if f.format == 2:
        return (f.root / str(f.config.get("agents") or ".heimai/agents/")).resolve()
    return (f.root / "agents").resolve()


def people_folder(f) -> Path:
    if f.format == 2:
        return (f.root / str(f.config.get("users") or ".heimai/users/")).resolve()
    return (f.heimdocs / str(f.config.get("people") or "users/")).resolve()


def read_source_note(folder: Path) -> str:
    p = folder / ".source"
    if not p.is_file():
        return ""
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"source:\s*(\S+)", text)
    v = re.search(r"version:\s*(\S+)", text)
    return (m.group(1) if m else text.strip().splitlines()[0]) + (f" v{v.group(1)}" if v else "")


def installed(folder: Path) -> list[dict]:
    out = []
    if not folder.is_dir():
        return out
    for src in sorted(p for p in folder.iterdir() if p.is_dir() and not p.name.startswith(".")):
        layers = {}
        for layer in LAYERS:
            d = src / layer
            if d.is_dir():
                names = sorted({p.stem if p.is_file() else p.name for p in d.iterdir()
                                if not p.name.startswith((".", "_")) and p.name != "__pycache__"})
                layers[layer] = names
        out.append({"source": src.name, "copy_of": read_source_note(src), "layers": layers})
    return out


def governance(f) -> dict:
    gov = f.governance or (f.heimdocs / "governance-compliance")
    out = {"folder": f.rel(gov), "exists": gov.is_dir(), "policies": (gov / "policies.md").is_file(),
           "parts": []}
    if not gov.is_dir():
        return out
    for d in sorted(p for p in gov.iterdir() if p.is_dir()):
        status = ""
        for name in ("framework.md", *sorted(x.name for x in d.glob("*.md"))):
            p = d / name
            if p.is_file():
                m = re.search(r"^Status:\s*(.+)$", p.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
                if m:
                    status = m.group(1).strip()
                    break
        out["parts"].append({"name": d.name, "copy_of": read_source_note(d), "status": status})
    return out


def main() -> int:
    floor.utf8_stdout()
    ap = argparse.ArgumentParser(description="Print a Heim's status (see tool.md).")
    ap.add_argument("--heim", help="the Heim's folder (default: the nearest at or above here)")
    ap.add_argument("--agents-folder", help="where its agents lie, when not at the default place")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        f = floor.load(heim=a.heim)
    except floor.FloorError as e:
        print(f"No Heim here: {e}", file=sys.stderr)
        return 2
    cfg = f.config
    agf = agents_folder(f, a.agents_folder)
    inst = installed(agf)
    heim_src = next((s for s in inst if s["source"] == "heim"), None)
    have = set(heim_src["layers"].get("agents", [])) if heim_src else set()
    for s in inst:
        have |= set(s["layers"].get("agents", []))
    wk = woken(f)
    ppl = people_folder(f)
    people = sorted(p.name for p in ppl.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))) if ppl.is_dir() else []
    hv = []
    if handovers and f.sessions:
        hv = [h for h in handovers.collect([f.sessions]) if h["status"] in ("open", "taken", "active")]
    inherits = cfg.get("inherits") if isinstance(cfg.get("inherits"), list) else []
    data = {
        "schema": "heim-status/1", "name": f.name, "kind": cfg.get("kind") or "", "root": str(f.root),
        "floor_plan": f.rel(f.plan), "format": f.format, "heimdocs": f.rel(f.heimdocs),
        "folders": {"projects": [f.rel(p) for p in f.projects], "sessions": f.rel(f.sessions) if f.sessions else "",
                    "people": f.rel(ppl), "agents": f.rel(agf)},
        "agents_woken": wk, "capabilities": cfg.get("capabilities") or {},
        "inherits": [{"from": str(i.get("from", "")), "take": as_list(i.get("take"))} for i in inherits if isinstance(i, dict)],
        "installed": inst, "woken_not_installed": [x for x in wk if x not in have],
        "installed_not_woken": sorted(x for x in have if wk and x not in wk),
        "people": people, "governance": governance(f),
        "handovers": [{k: h[k] for k in ("stamp", "status", "user", "agent", "summary")} for h in hv],
    }
    if a.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    def mark(p: Path) -> str:
        return "" if p.exists() else "  (missing)"
    print(f"Heim          {f.name}" + (f"  ({data['kind']})" if data["kind"] else ""))
    print(f"Root          {f.root}")
    print(f"Floor plan    {data['floor_plan']}  (format {f.format})")
    print(f"heimdocs      {data['heimdocs']}")
    for p in f.projects:
        print(f"projects      {f.rel(p)}{mark(p)}")
    if f.sessions:
        print(f"sessions      {f.rel(f.sessions)}{mark(f.sessions)}")
    print(f"people        {f.rel(ppl)}{mark(ppl)}" + (f"  {len(people)}: {', '.join(people)}" if people else ""))
    print(f"\nWoken         {', '.join(wk) if wk else '(none named in the floor plan)'}")
    caps = data["capabilities"]
    if isinstance(caps, dict) and caps:
        for src, names in caps.items():
            print(f"Capabilities  {src}: {', '.join(as_list(names))}")
    for i in data["inherits"]:
        print(f"Inherits      {i['from']}  take {', '.join(i['take'])}")
    print(f"\nAgents folder {f.rel(agf)}{mark(agf)}")
    for s in inst:
        copy = f"  (copy of {s['copy_of']})" if s["copy_of"] else "  (this Heim's own)"
        print(f"  {s['source']}{copy}")
        for layer, names in s["layers"].items():
            shown = ", ".join(names[:8]) + (f", … {len(names) - 8} more" if len(names) > 8 else "")
            print(f"    {layer:<13} {len(names):>3}  {shown}")
    if data["woken_not_installed"]:
        print(f"  woken, not installed: {', '.join(data['woken_not_installed'])}")
    if data["installed_not_woken"]:
        print(f"  installed, not woken: {', '.join(data['installed_not_woken'])}")
    g = data["governance"]
    print(f"\nGovernance    {g['folder']}" + ("" if g["exists"] else "  (none: not set up, which is fine)"))
    if g["exists"]:
        print(f"  policies.md   {'present' if g['policies'] else 'missing'}")
        for part in g["parts"]:
            kind = f"copy of {part['copy_of']}" if part["copy_of"] else "source here"
            print(f"  {part['name']:<13} {kind}" + (f"; Status: {part['status']}" if part["status"] else ""))
    print(f"\nHandovers     {len(hv)} not done" + ("" if hv else "  (none)"))
    for h in sorted(hv, key=lambda h: h["stamp"], reverse=True)[:12]:
        print(f"  {h['stamp']}  {h['status']:<6} {h['user'] or '-'}/{h['agent'] or '-'}  {h['summary'][:56]}")
    if len(hv) > 12:
        print(f"  … {len(hv) - 12} more (handover-audit lists them all)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
