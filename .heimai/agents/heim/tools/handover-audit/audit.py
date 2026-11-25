#!/usr/bin/env python3
"""List a Heim's handovers by status and age, and flag the threads that stopped.

Reads only. Flags: a handover `taken` with no later wrap, an `active` session file
older than a day, an `open` handover older than some weeks, front matter without a
status or a session, and a work part that links into a private cabinet.
The storage-audit skill reasons over the list; this tool moves nothing. See tool.md.
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
sys.path.insert(0, str(HERE.parent / "heim-floor"))
try:
    import floor  # type: ignore
except ImportError:
    floor = None

STAMP = re.compile(r"^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2})")
STATUS = {"open": "open", "öppen": "open", "oppen": "open", "taken": "taken", "tagen": "taken",
          "done": "done", "klar": "done", "active": "active"}
# A link into a private cabinet, or a section of the personal part kept in the work part. Mentioning the
# idea of a personal part (decision 27) is fine; the skill judges the rest.
PERSONAL = re.compile(r"\]\([^)]*(?:/private/|-private/|-heim/sessions/|private-heim)|^#{1,3}\s*(?:personal|personligt|personliga)\b",
                      re.IGNORECASE | re.MULTILINE)


def utf8() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def front_matter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line and not line.startswith((" ", "\t")):
            k, v = line.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def collect(folders: list[Path]) -> list[dict]:
    """Every handover file under the sessions folders, with its status, age and parts of its name."""
    now = dt.datetime.now()
    out = []
    for root in folders:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.md")):
            m = STAMP.match(p.name)
            if not m:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            fm = front_matter(text)
            stamp = m.group(1)
            when = dt.datetime.strptime(stamp, "%Y-%m-%d_%H-%M")
            rel = p.relative_to(root).parts
            user = rel[0] if len(rel) > 2 else ""
            agent = rel[1] if len(rel) > 2 else (rel[0] if len(rel) > 1 else "")
            rest = p.stem[len(stamp):].lstrip("-")
            if user and rest.startswith(user + "-"):
                rest = rest[len(user) + 1:]
            raw = fm.get("status", "").lower()
            out.append({
                "path": str(p), "sessions": str(root), "stamp": stamp, "user": user, "agent": agent,
                "summary": rest.replace("-", " "), "status": STATUS.get(raw, raw or "?"),
                "session": fm.get("session", ""), "from": fm.get("from", fm.get("från", "")),
                "to": fm.get("to", fm.get("till", "")),
                "taken_by": fm.get("taken_by", fm.get("tagen_av", "")),
                "continues": Path(fm.get("continues", "")).stem if fm.get("continues") else "",
                "age_hours": round((now - when).total_seconds() / 3600, 1),
                "_text": text,
            })
    return out


def audit(items: list[dict], open_weeks: float, active_hours: float) -> list[dict]:
    continued = {h["continues"] for h in items if h["continues"]}
    by_session: dict[str, list[dict]] = {}
    for h in items:
        if h["session"]:
            by_session.setdefault(h["session"], []).append(h)
    findings = []

    def add(h, kind, detail):
        findings.append({"kind": kind, "path": h["path"], "stamp": h["stamp"], "detail": detail})

    for h in items:
        stem = Path(h["path"]).stem
        if h["status"] == "taken":
            later = stem in continued or any(
                o["path"] != h["path"] for o in by_session.get(h["taken_by"], []))
            if not later:
                who = f"taken by {h['taken_by']}" if h["taken_by"] else "no taken_by"
                add(h, "taken-without-wrap", f"{who}; no later handover continues it")
        if h["status"] == "active" and h["age_hours"] > active_hours:
            add(h, "active-stale", f"active for {h['age_hours'] / 24:.1f} days; the session ended without a wrap")
        if h["status"] == "open" and h["age_hours"] > open_weeks * 7 * 24:
            add(h, "open-old", f"open for {h['age_hours'] / 24 / 7:.1f} weeks")
        missing = [k for k in ("status", "session") if not (h["status"] != "?" if k == "status" else h[k])]
        if missing:
            add(h, "front-matter-incomplete", "missing " + ", ".join(missing))
        if PERSONAL.search(h["_text"]):
            add(h, "links-personal-part", "the work part links into a private cabinet or holds a personal section")
    order = {"taken-without-wrap": 0, "active-stale": 1, "open-old": 2, "links-personal-part": 3,
             "front-matter-incomplete": 4}
    return sorted(findings, key=lambda f: (order.get(f["kind"], 9), f["stamp"]))


def sessions_folders(heim: str | None) -> tuple[str, list[Path]]:
    if floor is None:
        raise SystemExit("Error: heim-floor is not beside this tool; pass --sessions.")
    f = floor.load(heim=heim)
    return f.name, [f.sessions] if f.sessions else []


def main() -> int:
    utf8()
    ap = argparse.ArgumentParser(description="List handovers by status and age, and flag stopped threads (see tool.md).")
    ap.add_argument("--heim", help="the Heim (default: the nearest at or above here)")
    ap.add_argument("--sessions", action="append", help="a sessions folder to read instead (repeatable)")
    ap.add_argument("--open-weeks", type=float, default=3)
    ap.add_argument("--active-hours", type=float, default=24)
    ap.add_argument("--all", action="store_true", help="also list the done handovers")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        if a.sessions:
            name, folders = "", [Path(s).resolve() for s in a.sessions]
        else:
            name, folders = sessions_folders(a.heim)
    except Exception as e:  # floor.FloorError and a missing sessions key
        print(f"Error: {e}", file=sys.stderr)
        return 2
    items = collect(folders)
    findings = audit(items, a.open_weeks, a.active_hours)
    if a.json:
        clean = [{k: v for k, v in h.items() if not k.startswith("_")} for h in items]
        print(json.dumps({"schema": "heim-handover-audit/1", "heim": name,
                          "sessions": [str(f) for f in folders], "handovers": clean,
                          "findings": findings}, ensure_ascii=False, indent=2))
        return 0
    print(f"Handovers{' in ' + name if name else ''}: {len(items)} in {', '.join(str(f) for f in folders)}")
    for status in ("active", "open", "taken", "done", "?"):
        group = [h for h in items if h["status"] == status]
        if not group:
            continue
        print(f"\n{status} ({len(group)})")
        if status == "done" and not a.all:
            print("  (use --all to list them)")
            continue
        for h in sorted(group, key=lambda h: h["stamp"], reverse=True):
            age = h["age_hours"] / 24
            print(f"  {h['stamp']}  {age:5.1f} d  {h['user'] or '-'}/{h['agent'] or '-'}  {h['summary'][:60]}")
    others = sorted({h["status"] for h in items} - {"active", "open", "taken", "done", "?"})
    for status in others:
        print(f"\n{status} ({sum(1 for h in items if h['status'] == status)})")
    print(f"\nFindings ({len(findings)})")
    for f in findings:
        rel = Path(f["path"]).name
        print(f"  {f['kind']:<24} {rel}: {f['detail']}")
    if not findings:
        print("  none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
