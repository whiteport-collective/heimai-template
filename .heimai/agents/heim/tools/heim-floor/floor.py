#!/usr/bin/env python3
"""Find a Heim and its folders through its floor plan, never through a fixed path.

The Heim root is the nearest folder at or above a start folder that holds
`.heimai/heimai.yaml` (decision 34) or `heim.yaml` (today); when both lie in
the same folder, `.heimai/heimai.yaml` wins. A `heimai.yaml` directly in a
folder that is not named `.heimai` is a nested Heim with that folder as root.

Folder keys:
- `heim: 1` (heim.yaml): `heimdocs:` is relative to the root (default `.`);
  `projects:` (default `projects/`, may be a list), `sessions:` (default
  `sessions/`) and `governance:` are relative to `heimdocs:`.
- `heimai: 2` (heimai.yaml): every path is relative to the root, and a missing
  key means `.heimai/<key>/` (`heimdocs:` defaults to `.heimai/`).

Imported by the tools beside it; run on its own it prints the floor plan. See tool.md.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # the fallback below reads the flat keys a floor plan and feature.yaml use
    yaml = None


class FloorError(Exception):
    """No Heim found, or its floor plan cannot be read."""


# ---------- small YAML: PyYAML when installed, else flat keys ----------

def strip_comment(text: str) -> str:
    """The value part of a YAML line without a trailing ` # comment`, respecting quotes."""
    quote = ""
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or text[i - 1] in " \t"):
            return text[:i].rstrip()
    return text.rstrip()


def _scalar(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        inner = v[1:-1]
        return inner.replace('\\"', '"').replace("\\\\", "\\") if v[0] == '"' else inner.replace("''", "'")
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_scalar(p) for p in inner.split(",")] if inner else []
    if v in ("", "~", "null"):
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def parse_flat_yaml(text: str) -> dict:
    """Top-level `key: value` lines, inline lists `[a, b]` and block lists `- item`. Enough for
    heim.yaml's folder keys and feature.yaml; nested maps are kept as None."""
    out: dict = {}
    current = None
    for raw in text.splitlines():
        line = strip_comment(raw)
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            m = re.match(r"^([A-Za-z0-9_.-]+)\s*:(.*)$", line)
            if not m:
                current = None
                continue
            key, value = m.group(1), m.group(2).strip()
            out[key] = _scalar(value) if value else None
            current = key if not value else None
        elif current is not None:
            m = re.match(r"^\s+-\s+(.*)$", line)
            if m:
                if not isinstance(out[current], list):
                    out[current] = []
                out[current].append(_scalar(m.group(1)))
    return out


def read_yaml(path: Path) -> dict:
    """A YAML file as a dict: PyYAML if installed, else parse_flat_yaml. Raises FloorError."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise FloorError(f"cannot read {path}: {e}") from e
    if yaml is not None:
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as e:
            raise FloorError(f"{path} is not valid YAML: {e}") from e
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise FloorError(f"{path} is not a map of keys")
        return data
    return parse_flat_yaml(text)


def read_card(path: Path) -> tuple[dict, str]:
    """A project's feature.yaml, even when it is not valid YAML (an unquoted `next:` holding `: `):
    (its keys, a note saying it is not valid YAML, else ""). Raises FloorError when it cannot be read."""
    try:
        return read_yaml(path), ""
    except FloorError:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            raise FloorError(f"cannot read {path}: {e}") from e
        return parse_flat_yaml(text), "not valid YAML, read line by line"


# ---------- the Heim ----------

@dataclass
class Floor:
    root: Path
    plan: Path                 # the floor plan file that was read
    format: int                # 1 for heim.yaml, 2 for heimai.yaml
    name: str
    config: dict
    heimdocs: Path
    projects: list[Path] = field(default_factory=list)
    sessions: Path | None = None
    governance: Path | None = None
    agents: Path | None = None             # the agents' folder (decision 24)
    woken: list[str] = field(default_factory=list)   # the agents woken here (decision 32)

    def rel(self, p: Path) -> str:
        """p relative to the Heim root, with forward slashes, for printing."""
        try:
            return Path(p).resolve().relative_to(self.root).as_posix() or "."
        except ValueError:
            return str(p)


def find_root(start: Path) -> tuple[Path, Path] | None:
    """(root, floor plan file) of the nearest Heim at or above start."""
    start = start.resolve()
    if start.is_file():
        start = start.parent
    for d in [start, *start.parents]:
        if (d / ".heimai" / "heimai.yaml").is_file():
            return d, d / ".heimai" / "heimai.yaml"
        if d.name != ".heimai" and (d / "heimai.yaml").is_file():
            return d, d / "heimai.yaml"
        if (d / "heim.yaml").is_file():
            return d, d / "heim.yaml"
    return None


def _paths(value, default: str) -> list[str]:
    if value is None or value == "":
        return [default]
    if isinstance(value, list):
        return [str(v) for v in value if v] or [default]
    return [str(value)]


def _names(value) -> list[str]:
    """A list of names from `[a, b]`, a block list, or one name."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if v is not None and str(v).strip()]
    return [str(value).strip()] if isinstance(value, str) and value.strip() else []


def agents_of(config: dict, fmt: int) -> tuple[str | None, list[str]]:
    """(the agents' folder from the root or None for the default, the woken agents).

    `heimai: 2`: `agents:` is the folder and `agents_woken:` the list (heimai-yaml.md, Renamed keys).
    `heim: 1`: `agents:` is the list (decision 32), and the folder is `agents_folder:` when given.
    A list under `agents:` in a format 2 file not yet renamed is still read as the woken list."""
    value = config.get("agents")
    if fmt == 2:
        if isinstance(value, list):
            return config.get("agents_folder") or None, _names(value)
        return (str(value) if isinstance(value, str) and value.strip() else None), _names(config.get("agents_woken"))
    folder = config.get("agents_folder") or (value if isinstance(value, str) and value.strip() else None)
    return folder, _names(value) if isinstance(value, list) else []


def load(start: str | Path | None = None, heim: str | Path | None = None) -> Floor:
    """The Heim at --heim, or the nearest one at or above start (default: the current folder)."""
    where = Path(heim or start or ".")
    if not where.exists():
        raise FloorError(f"{where} does not exist")
    found = find_root(where)
    if not found:
        raise FloorError(f"no .heimai/heimai.yaml or heim.yaml at or above {where.resolve()}")
    root, plan = found
    config = read_yaml(plan)
    fmt = 2 if plan.name == "heimai.yaml" else 1
    if fmt == 2:
        heimdocs = (root / str(config.get("heimdocs") or ".heimai/")).resolve()
        base, dflt = root, lambda k: f".heimai/{k}/"
    else:
        heimdocs = (root / str(config.get("heimdocs") or ".")).resolve()
        base, dflt = heimdocs, lambda k: f"{k}/"
    projects = [(base / p).resolve() for p in _paths(config.get("projects"), dflt("projects"))]
    sessions = (base / _paths(config.get("sessions"), dflt("sessions"))[0]).resolve()
    gov = config.get("governance")
    governance = (base / str(gov)).resolve() if gov else None
    folder, woken = agents_of(config, fmt)
    agents = (root / (folder or (".heimai/agents/" if fmt == 2 else "agents/"))).resolve()
    return Floor(root=root, plan=plan, format=fmt, name=str(config.get("name") or root.name),
                 config=config, heimdocs=heimdocs, projects=projects,
                 sessions=sessions, governance=governance, agents=agents, woken=woken)


def brand_folder(floor: Floor) -> Path | None:
    """The Heim's brand folder: 03-brand/ or brand/ under the heimdocs base, if one exists."""
    for name in ("03-brand", "brand"):
        if (floor.heimdocs / name).is_dir():
            return floor.heimdocs / name
    return None


def templates_dir(tool_file: str | Path) -> Path:
    """<tool dir>/../../templates/, the same in the source's delivery folder and in a Heim's agents/heim/."""
    return (Path(tool_file).resolve().parent / ".." / ".." / "templates").resolve()


def utf8_stdout() -> None:
    """Print å ä ö on a Windows console too."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Print a Heim's floor plan (see tool.md).")
    ap.add_argument("--heim", help="the Heim's folder (default: the nearest at or above here)")
    a = ap.parse_args()
    try:
        f = load(heim=a.heim)
    except FloorError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    print(f"Heim:       {f.name}  ({f.root})")
    print(f"Floor plan: {f.rel(f.plan)}  (format {f.format})")
    print(f"heimdocs:   {f.rel(f.heimdocs)}")
    for p in f.projects:
        print(f"projects:   {f.rel(p)}{'' if p.is_dir() else '  (missing)'}")
    if f.sessions:
        print(f"sessions:   {f.rel(f.sessions)}{'' if f.sessions.is_dir() else '  (missing)'}")
    if f.governance:
        print(f"governance: {f.rel(f.governance)}{'' if f.governance.is_dir() else '  (missing)'}")
    b = brand_folder(f)
    print(f"brand:      {f.rel(b) if b else '(none)'}")
    if f.agents:
        print(f"agents:     {f.rel(f.agents)}{'' if f.agents.is_dir() else '  (missing)'}")
    print(f"woken:      {', '.join(f.woken) if f.woken else '(none)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
