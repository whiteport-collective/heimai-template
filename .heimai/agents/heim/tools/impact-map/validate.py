#!/usr/bin/env python3
"""Check an impact map (impact-map.yaml) and rank each persona's driving forces.

    python validate.py [<folder or impact-map.yaml>] [--heim DIR]

Errors make the map invalid; warnings do not. Without a path it checks
heimdocs/*impact-map/impact-map.yaml of the Heim found through the floor plan
(../heim-floor/floor.py). See tool.md.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "heim-floor"))
import floor  # noqa: E402

try:
    import yaml
except ImportError:
    yaml = None

# The one threshold definition: a force's total f + i + fit (3-15) at or above the bound gets the label.
THRESHOLDS = [(13, "high"), (10, "medium"), (0, "low")]
DEFAULT_MAX = 3            # goals, and objectives per goal: above this is a warning, not an error
FORCES_PER_DIRECTION = (3, 5)
SCORES = ("f", "i", "fit")

NEEDED = re.compile(r"\[needed(?::[^\]]*)?\]")
PLACEHOLDER = re.compile(r"\{\{[^{}]+\}\}")


def level(total: int) -> str:
    return next(label for bound, label in THRESHOLDS if total >= bound)


def threshold_text() -> str:
    parts, upper = [], 15
    for bound, label in THRESHOLDS:
        parts.append(f"{label} {bound}-{upper}" if bound else f"{label} below {upper + 1}")
        upper = bound - 1
    return ", ".join(parts)


def label_of(item, index: int) -> str:
    if isinstance(item, dict):
        for k in ("id", "name"):
            v = item.get(k)
            if isinstance(v, str) and v and not NEEDED.search(v) and not PLACEHOLDER.search(v):
                return v
    return str(index)


def walk(node, path: str, found: list):
    """Every string with a [needed] marker or a {{placeholder}}, with where it is."""
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, f"{path}.{k}" if path else str(k), found)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f"{path}[{label_of(v, i)}]", found)
    elif isinstance(node, str):
        for m in NEEDED.finditer(node):
            found.append(("needed", path, m.group(0)))
        for m in PLACEHOLDER.finditer(node):
            found.append(("placeholder", path, m.group(0)))


def blank(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip()) or v == [] or v == {}


def validate(data) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if not isinstance(data, dict):
        return ["the file is not a map of keys"], warnings

    goals = data.get("goals")
    ids = set()
    if not isinstance(goals, list) or not goals:
        errors.append("goals: missing or empty")
        goals = []
    elif len(goals) > DEFAULT_MAX:
        warnings.append(f"goals: {len(goals)} goals, above the default of {DEFAULT_MAX}, not an error")
    for gi, g in enumerate(goals):
        where = f"goals[{label_of(g, gi)}]"
        if not isinstance(g, dict):
            errors.append(f"{where}: not a map")
            continue
        for k in ("id", "name"):
            if blank(g.get(k)):
                errors.append(f"{where}: no {k}")
        gid = g.get("id")
        if gid is not None:
            if str(gid) in ids:
                errors.append(f"{where}: the id {gid} is used twice")
            ids.add(str(gid))
        objectives = g.get("objectives")
        if not isinstance(objectives, list) or not objectives:
            errors.append(f"{where}: no objectives")
            continue
        if len(objectives) > DEFAULT_MAX:
            warnings.append(f"{where}: {len(objectives)} objectives, above the default of {DEFAULT_MAX}, not an error")
        for oi, o in enumerate(objectives):
            ow = f"{where}.objectives[{oi}]"
            if not isinstance(o, dict):
                errors.append(f"{ow}: not a map")
            elif blank(o.get("target")):
                errors.append(f"{ow}: no target (a number and a date, or [needed: …] saying what is missing)")
            elif NEEDED.search(str(o.get("target"))):
                warnings.append(f"{ow}: the target is still [needed]")

    personas = data.get("personas")
    if not isinstance(personas, list) or not personas:
        errors.append("personas: missing or empty")
        personas = []
    for pi, p in enumerate(personas):
        where = f"personas[{label_of(p, pi)}]"
        if not isinstance(p, dict):
            errors.append(f"{where}: not a map")
            continue
        for k in ("name", "priority"):
            if blank(p.get(k)):
                errors.append(f"{where}: no {k}")
        pg = p.get("goals")
        if not isinstance(pg, list) or not pg:
            errors.append(f"{where}: no goals (the business goals it serves)")
        else:
            for ref in pg:
                if str(ref) not in ids:
                    errors.append(f"{where}: goal {ref} is not a goal id ({', '.join(sorted(ids)) or 'none'})")
        forces = p.get("forces")
        if not isinstance(forces, list) or not forces:
            errors.append(f"{where}: no forces")
            continue
        count = {"+": 0, "-": 0}
        for fi, fo in enumerate(forces):
            fw = f"{where}.forces[{label_of(fo, fi)}]"
            if not isinstance(fo, dict):
                errors.append(f"{fw}: not a map")
                continue
            d = str(fo.get("dir", ""))
            if d not in count:
                errors.append(f"{fw}: dir is {fo.get('dir')!r}, must be \"+\" or \"-\"")
            else:
                count[d] += 1
            for k in ("what", "why", "when"):
                if blank(fo.get(k)):
                    errors.append(f"{fw}: no {k}")
            for k in SCORES:
                v = fo.get(k)
                if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 5:
                    errors.append(f"{fw}: {k} is {v!r}, must be a whole number 1-5")
        lo, hi = FORCES_PER_DIRECTION
        for d, n in count.items():
            if not lo <= n <= hi:
                warnings.append(f"{where}: {n} forces in direction {d}, the norm is {lo}-{hi}")
    return errors, warnings


def ranking(data) -> list[str]:
    out = []
    personas = data.get("personas") if isinstance(data, dict) else None
    for pi, p in enumerate(personas if isinstance(personas, list) else []):
        if not isinstance(p, dict):
            continue
        goals = ", ".join(str(g) for g in p.get("goals") or []) if isinstance(p.get("goals"), list) else ""
        name = label_of(p, pi)
        name = f"persona {pi + 1} (no name yet)" if name == str(pi) else name
        out.append(f"{name} ({p.get('priority', '?')}{'; goals ' + goals if goals else ''})")
        scored = []
        for fo in p.get("forces") or []:
            if not isinstance(fo, dict):
                continue
            vals = [fo.get(k) for k in SCORES]
            if all(isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= 5 for v in vals):
                scored.append((sum(vals), fo, vals))
        scored.sort(key=lambda t: t[0], reverse=True)
        for total, fo, vals in scored:
            out.append(f"  {total:>2} {level(total):<6} {fo.get('dir', '?')} {fo.get('name', '')}"
                       f"  (f{vals[0]} i{vals[1]} fit{vals[2]})")
        if not scored:
            out.append("  (no scored forces)")
    return out


def find_map(arg: str | None, heim: str | None) -> Path:
    if arg:
        p = Path(arg)
        return p / "impact-map.yaml" if p.is_dir() else p
    f = floor.load(heim=heim)
    hits = sorted(f.heimdocs.glob("*impact-map/impact-map.yaml"))
    if not hits:
        raise floor.FloorError(f"no */impact-map.yaml under {f.heimdocs}; give the path")
    return hits[0]


def main() -> int:
    floor.utf8_stdout()
    ap = argparse.ArgumentParser(description="Check an impact map and rank its forces (see tool.md).")
    ap.add_argument("path", nargs="?", help="impact-map.yaml or the folder it lies in (default: the Heim's)")
    ap.add_argument("--heim", help="the Heim, when no path is given")
    a = ap.parse_args()
    if yaml is None:
        print("Error: impact-map validate needs PyYAML: python -m pip install pyyaml", file=sys.stderr)
        return 2
    try:
        path = find_map(a.path, a.heim)
        text = path.read_text(encoding="utf-8")
    except (OSError, floor.FloorError) as e:
        print(f"Error: cannot read the impact map: {e}", file=sys.stderr)
        return 2

    print(f"Impact map: {path.resolve()}")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        print(f"\nErrors (1):\n  - the YAML does not parse: {e}")
        print("\nResult: INVALID.")
        return 1

    errors, warnings = validate(data)
    found: list = []
    walk(data, "", found)
    if isinstance(data, dict):
        goals, personas = data.get("goals"), data.get("personas")
        print(f"Project: {data.get('project', '?')} · status {data.get('status', '?')} · "
              f"{len(goals) if isinstance(goals, list) else 0} goals, "
              f"{len(personas) if isinstance(personas, list) else 0} personas")
    placeholders = [f for f in found if f[0] == "placeholder"]
    warnings += [f"{path_}: placeholder {t} not filled" for _, path_, t in placeholders]

    print(f"\nErrors ({len(errors)}):" if errors else "\nErrors: none")
    for e in errors:
        print(f"  - {e}")
    print(f"\nWarnings ({len(warnings)}):" if warnings else "\nWarnings: none")
    for w in warnings:
        print(f"  - {w}")
    needed = [f for f in found if f[0] == "needed"]
    print(f"\n[needed] markers ({len(needed)}):" if needed else "\n[needed] markers: none")
    for _, path_, t in needed:
        print(f"  - {path_}: {t}")
    rank = ranking(data)
    if rank:
        print(f"\nForces per persona, by f + i + fit ({threshold_text()}):")
        for line in rank:
            print(line)
    print(f"\nResult: {'INVALID' if errors else 'valid'}"
          + (f", {len(errors)} errors" if errors else "")
          + (f", {len(warnings)} warnings" if warnings else "") + ".")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
