#!/usr/bin/env python3
"""Check which programs a Heim needs are on this computer, and print how to install the rest.

Reads only: it never installs. The agent runs the printed command after the person's yes,
one program at a time. See tool.md.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys

PROGRAMS = [
    # name, command, minimum version, required, Windows install, Mac install
    ("git", ["git", "--version"], None, True, "winget install --id Git.Git -e", "brew install git"),
    ("GitHub CLI", ["gh", "--version"], None, True, "winget install --id GitHub.cli -e", "brew install gh"),
    ("Python", [sys.executable, "--version"], (3, 10), True,
     "winget install --id Python.Python.3.12 -e", "brew install python"),
    ("Node.js", ["node", "--version"], (18, 0), False, "winget install --id OpenJS.NodeJS.LTS -e", "brew install node"),
    ("VS Code", ["code", "--version"], None, False,
     "winget install --id Microsoft.VisualStudioCode -e", "brew install --cask visual-studio-code"),
]


def version_of(cmd: list[str]) -> str | None:
    exe = cmd[0] if cmd[0] == sys.executable else shutil.which(cmd[0])
    if not exe:
        return None
    try:
        out = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (out.stdout or out.stderr).strip().splitlines()
    return text[0] if text else ""


def parse(v: str) -> tuple[int, ...]:
    m = re.search(r"(\d+)\.(\d+)", v or "")
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Check the programs a Heim needs (see tool.md).")
    ap.add_argument("command", choices=["check"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    system = platform.system()
    mac = system == "Darwin"
    rows = []
    for name, cmd, minimum, required, win, brew in PROGRAMS:
        v = version_of(cmd)
        ok = v is not None and (minimum is None or parse(v) >= minimum)
        rows.append({"program": name, "found": v or "", "ok": ok, "required": required,
                     "minimum": ".".join(map(str, minimum)) if minimum else "",
                     "install": "" if ok else (brew if mac else win if system == "Windows" else "")})
    try:
        import yaml  # type: ignore  # noqa: F401
        rows.append({"program": "PyYAML", "found": "installed", "ok": True, "required": True, "minimum": "", "install": ""})
    except ImportError:
        rows.append({"program": "PyYAML", "found": "", "ok": False, "required": True, "minimum": "",
                     "install": f"{sys.executable} -m pip install pyyaml"})
    if a.json:
        print(json.dumps({"schema": "heim-machine/1", "system": system, "programs": rows}, indent=2))
    else:
        print(f"System: {system} {platform.release()}")
        for r in rows:
            state = "ok" if r["ok"] else ("missing" if not r["found"] else f"too old (needs {r['minimum']})")
            need = "" if r["required"] else "  (optional)"
            print(f"  {r['program']:<11} {state:<20} {r['found'][:40]}{need}")
            if r["install"]:
                print(f"      install, after a yes: {r['install']}")
        if mac and any(r["install"].startswith("brew") for r in rows) and not shutil.which("brew"):
            print("  Homebrew is not installed: ask before installing it first (see tool.md).")
    missing = [r for r in rows if r["required"] and not r["ok"]]
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
