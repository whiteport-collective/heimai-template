#!/usr/bin/env python3
"""source-import: take any framework or repo with agents or skills into a Heim.

Decision 24. The recipe (agents/<source>/import.yaml) says what to take, where each part
lands in the eight layers, how skills are split and what is corrected. This script does it,
the same way every time, so the adaptation survives when the source is updated.

    python source_import.py scan <git-url-or-path> [--ref <sha|branch>]
    python source_import.py run <path/to/import.yaml> [--update] [--dry-run]

scan  prints an inventory of a source: skills, references, scripts, the hosts they call,
      hooks in front matter, sizes per folder and the licence. The input to writing a recipe.
run   clones the source at the commit in import.lock (or the newest with --update), applies
      the recipe into the recipe's folder, and writes source.md, import-report.md and the lock.
      A correction whose anchor is gone is not guessed at: it is listed for the person.

Needs git and Python 3.9+ with PyYAML.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("source-import needs PyYAML: pip install pyyaml")

CACHE = Path(os.environ.get("HEIM_CACHE", Path.home() / ".heim" / "cache" / "sources"))
TEXT_EXT = {".md", ".txt", ".json", ".yaml", ".yml", ".html", ".css", ".js", ".mjs", ".ts", ".py", ".sh", ".toml"}
SCRIPT_EXT = {".js", ".mjs", ".cjs", ".ts", ".py", ".sh", ".ps1"}
HOST_RE = re.compile(r"https?://([a-z0-9.-]+\.[a-z]{2,})", re.I)
LOCAL_HOSTS = {"www.w3.org", "example.com", "127.0.0.1", "localhost"}
SPAWN_RE = re.compile(r"child_process|spawn\(|execSync|execFile|subprocess|os\.system")
MANIFEST = ".import-manifest.json"


# ---------------------------------------------------------------- git

def git(*args: str, cwd: Path | None = None) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def fetch(source: str, ref: str | None) -> tuple[Path, str]:
    """Return a checkout of the source at ref (default: newest on the default branch) and its sha."""
    if Path(source).exists():
        path = Path(source).resolve()
    else:
        name = re.sub(r"[^a-z0-9]+", "-", source.lower().split("://")[-1]).strip("-")
        path = CACHE / name
        if (path / ".git").exists():
            git("fetch", "--quiet", "origin", cwd=path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            git("clone", "--quiet", source, str(path))
    if (path / ".git").exists():
        target = ref or git("rev-parse", "origin/HEAD", cwd=path) if not Path(source).exists() else (ref or "HEAD")
        git("checkout", "--quiet", "--detach", target, cwd=path)
        return path, git("rev-parse", "HEAD", cwd=path)
    return path, "local"


# ---------------------------------------------------------------- markdown helpers

def split_front_matter(text: str) -> tuple[dict, str]:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = yaml.safe_load(text[3:end]) or {}
            return fm, text[end + 4:].lstrip("\r\n")
    return {}, text


def join_front_matter(fm: dict, body: str) -> str:
    if not fm:
        return body
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=100).strip()
    return f"---\n{dumped}\n---\n\n{body}"


def heading_level(line: str) -> int:
    m = re.match(r"^(#{1,6})\s", line)
    return len(m.group(1)) if m else 0


def cut_section(body: str, heading: str) -> tuple[str, str] | None:
    """Remove the section that starts with the exact heading line; return (rest, section)."""
    lines = body.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == heading.strip():
            level = heading_level(line)
            j = i + 1
            while j < len(lines) and not (0 < heading_level(lines[j]) <= level):
                j += 1
            section = "\n".join(lines[i:j]).rstrip() + "\n"
            rest = "\n".join(lines[:i] + ["{{SPLIT}}"] + lines[j:])
            return rest, section
    return None


# ---------------------------------------------------------------- scan

def scan(source: str, ref: str | None) -> str:
    path, sha = fetch(source, ref)
    out = [f"# Scan of {source}", "", f"Commit `{sha}`, {dt.date.today()}.", ""]
    lic = next((p for p in path.glob("LICEN[CS]E*")), None)
    out.append(f"**Licence:** {lic.read_text(encoding='utf-8', errors='replace').splitlines()[0] if lic else 'none found'}")
    out += ["", "## Skills", "", "| Skill | Name | Lines | Hooks | Folders beside it |", "|---|---|---|---|---|"]
    for sk in sorted(path.rglob("SKILL.md")):
        if ".git" in sk.parts:
            continue
        fm, body = split_front_matter(sk.read_text(encoding="utf-8", errors="replace"))
        sub = ", ".join(sorted(p.name for p in sk.parent.iterdir() if p.is_dir()))
        out.append(f"| `{sk.relative_to(path).as_posix()}` | {fm.get('name', '')} | {body.count(chr(10))} | "
                   f"{', '.join(fm.get('hooks', {}).keys()) if isinstance(fm.get('hooks'), dict) else ''} | {sub} |")
    out += ["", "## Scripts", "", "| Script | Calls out to | Starts processes |", "|---|---|---|"]
    for sc in sorted(p for p in path.rglob("*") if p.suffix in SCRIPT_EXT and ".git" not in p.parts and p.is_file()):
        if "node_modules" in sc.parts or sc.stat().st_size > 2_000_000:
            continue
        txt = sc.read_text(encoding="utf-8", errors="replace")
        hosts = sorted({h.lower() for h in HOST_RE.findall(txt)} - LOCAL_HOSTS)
        if hosts or SPAWN_RE.search(txt):
            out.append(f"| `{sc.relative_to(path).as_posix()}` | {', '.join(hosts) or '-'} | {'yes' if SPAWN_RE.search(txt) else '-'} |")
    out += ["", "## Size per folder", "", "| Folder | Files | KB |", "|---|---|---|"]
    for d in sorted(p for p in path.iterdir() if p.is_dir() and p.name != ".git"):
        files = [f for f in d.rglob("*") if f.is_file()]
        out.append(f"| `{d.name}/` | {len(files)} | {sum(f.stat().st_size for f in files) // 1024:,} |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- run

class Import:
    def __init__(self, recipe_path: Path, update: bool, dry: bool):
        self.recipe_path = recipe_path.resolve()
        self.root = self.recipe_path.parent
        self.recipe = yaml.safe_load(self.recipe_path.read_text(encoding="utf-8"))
        self.lock_path = self.root / "import.lock"
        self.lock = json.loads(self.lock_path.read_text(encoding="utf-8")) if self.lock_path.exists() else {}
        self.update, self.dry = update, dry
        self.files: dict[Path, bytes | str] = {}  # target path -> content
        self.applied: list[str] = []
        self.missing: list[str] = []
        self.taken: list[tuple[str, str, int, int]] = []

    # ---- reading

    def src(self, rel: str) -> Path:
        return self.checkout / rel

    def read_target(self, rel: str) -> str:
        p = self.root / rel
        if p not in self.files:
            raise SystemExit(f"{rel} is not produced by any take step")
        c = self.files[p]
        return c if isinstance(c, str) else c.decode("utf-8")

    def write_target(self, rel: str, content: str) -> None:
        self.files[self.root / rel] = content

    # ---- steps

    def take(self) -> None:
        for t in self.recipe.get("take", []):
            base = self.src(t["from"])
            excl = t.get("exclude", [])
            dest = self.root / t["to"]
            items = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
            n = size = 0
            for p in items:
                rel = p.name if base.is_file() else p.relative_to(base).as_posix()
                if any(fnmatch.fnmatch(rel, e) for e in excl):
                    continue
                target = dest if base.is_file() and dest.suffix else dest / rel
                data = p.read_bytes()
                try:
                    self.files[target] = data.decode("utf-8").replace("\r\n", "\n") if p.suffix in TEXT_EXT else data
                except UnicodeDecodeError:
                    self.files[target] = data
                n += 1
                size += len(data)
            self.taken.append((t["from"], t["to"], n, size))

    def front_matter(self) -> None:
        for f in self.recipe.get("front_matter", []):
            fm, body = split_front_matter(self.read_target(f["file"]))
            for key, to in (f.get("move") or {}).items():
                if key in fm:
                    value = yaml.safe_dump({key: fm.pop(key)}, sort_keys=False, allow_unicode=True, width=1000)
                    note = f.get("move_note", "")
                    self.write_target(to, f"# {key} from {f['file']}\n\n{note}\n\n```yaml\n{value}```\n")
                    self.applied.append(f"front matter `{key}` of `{f['file']}` moved to `{to}`")
            for key in f.get("drop", []):
                if fm.pop(key, None) is not None:
                    self.applied.append(f"front matter `{key}` dropped from `{f['file']}`")
            for key, value in (f.get("set") or {}).items():
                fm[key] = value
                self.applied.append(f"front matter `{key}` set in `{f['file']}`")
            self.write_target(f["file"], join_front_matter(fm, body))

    def splits(self) -> None:
        for s in self.recipe.get("split", []):
            fm, body = split_front_matter(self.read_target(s["file"]))
            cut = cut_section(body, s["heading"])
            if not cut:
                self.missing.append(f"split: heading `{s['heading']}` not found in `{s['file']}`")
                continue
            rest, section = cut
            first, _, after = section.partition("\n")
            title = f"# {s['title']}" if s.get("title") else first
            intro = s.get("intro", "").strip()
            self.write_target(s["to"], f"{title}\n\n" + (f"{intro}\n\n" if intro else "") + after.lstrip("\n"))
            self.write_target(s["file"], join_front_matter(fm, rest.replace("{{SPLIT}}", s.get("replace_with", "").rstrip() + "\n")))
            self.applied.append(f"split `{s['heading']}` out of `{s['file']}` into `{s['to']}`")

    def corrections(self) -> None:
        for c in self.recipe.get("corrections", []):
            text = self.read_target(c["file"])
            anchor = c.get("find") or c.get("insert_after")
            count = text.count(anchor)
            label = f"`{c['file']}`: {c['reason']}"
            if count != 1:
                self.missing.append(f"correction not applied ({'anchor gone' if count == 0 else f'anchor found {count} times'}) in {label}")
                continue
            if "find" in c:
                text = text.replace(anchor, c["replace"])
            else:
                text = text.replace(anchor, anchor + c["insert"])
            self.write_target(c["file"], text)
            self.applied.append(f"corrected {label}")

    def stamp(self) -> None:
        line = (f"<!-- Generated by source-import from {self.recipe['source']['repo']}@{self.sha[:7]}. "
                f"Change import.yaml in agents/{self.recipe['name']}/, not this file. -->")
        for p, c in list(self.files.items()):
            if p.suffix == ".md" and isinstance(c, str):
                fm, body = split_front_matter(c)
                self.files[p] = join_front_matter(fm, f"{line}\n\n{body}")

    # ---- reports

    def source_md(self) -> str:
        r, s = self.recipe, self.recipe["source"]
        lines = [f"# {r['title']}", "", r.get("why", "").strip(), "",
                 f"- **Source:** {s['repo']} at `{self.sha}` ({self.date})",
                 f"- **Licence:** {s.get('licence', 'see LICENSE')}",
                 f"- **Used by:** {', '.join(r.get('used_by', []))}",
                 f"- **Recipe:** [import.yaml](import.yaml) · **Last run:** [import-report.md](import-report.md)", "",
                 "## Update", "",
                 "```bash", f"python agents/heim/tools/source-import/source_import.py run agents/{r['name']}/import.yaml --update", "```", "",
                 "Read the report: every correction whose anchor is gone, and every question, is the person's to answer before the update is committed.", ""]
        return "\n".join(lines)

    def report(self) -> str:
        r = self.recipe
        prev = self.lock.get("commit")
        out = [f"# Import report: {r['title']}", "",
               f"{self.date}, {r['source']['repo']} at `{self.sha[:7]}`" + (f" (previous `{prev[:7]}`)" if prev and prev != self.sha else ""), "",
               "## Taken", "", "| From | To | Files | KB |", "|---|---|---|---|"]
        out += [f"| `{a}` | `{b}` | {n} | {s // 1024:,} |" for a, b, n, s in self.taken]
        skipped = r.get("skipped", [])
        if skipped:
            out += ["", "## Not taken", ""] + [f"- `{x['path']}`: {x['why']}" for x in skipped]
        out += ["", "## Applied", ""] + [f"- {a}" for a in self.applied]
        out += ["", "## For the person", ""]
        if self.missing:
            out += [f"- **{m}**" for m in self.missing]
        out += [f"- **Question:** {q['question']} ({q['why']})" for q in r.get("questions", [])]
        if not self.missing and not r.get("questions"):
            out.append("Nothing.")
        flags = r.get("flags", [])
        if flags:
            out += ["", "## Flags for governance", ""] + [f"- {f}" for f in flags]
        return "\n".join(out) + "\n"

    # ---- run

    def run(self) -> None:
        s = self.recipe["source"]
        ref = None if self.update else self.lock.get("commit") or s.get("ref")
        self.checkout, self.sha = fetch(s["repo"], ref)
        self.date = dt.date.today().isoformat()
        self.take()
        self.front_matter()
        self.splits()
        self.corrections()
        self.stamp()
        self.files[self.root / "source.md"] = self.source_md()
        self.files[self.root / "import-report.md"] = self.report()
        if self.dry:
            print(self.files[self.root / "import-report.md"])
            return
        old = set(json.loads((self.root / MANIFEST).read_text(encoding="utf-8"))) if (self.root / MANIFEST).exists() else set()
        new = {p.relative_to(self.root).as_posix() for p in self.files}
        for rel in sorted(old - new):  # files the source no longer produces
            (self.root / rel).unlink(missing_ok=True)
        for p, c in self.files.items():
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(c, str):
                p.write_text(c, encoding="utf-8", newline="\n")
            else:
                p.write_bytes(c)
        (self.root / MANIFEST).write_text(json.dumps(sorted(new), indent=1), encoding="utf-8")
        self.lock_path.write_text(json.dumps({"repo": s["repo"], "commit": self.sha, "date": self.date}, indent=1) + "\n", encoding="utf-8")
        print(self.files[self.root / "import-report.md"])
        print(f"{len(new)} files written to {self.root}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("scan"); a.add_argument("source"); a.add_argument("--ref")
    b = sub.add_parser("run"); b.add_argument("recipe"); b.add_argument("--update", action="store_true"); b.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "scan":
        print(scan(args.source, args.ref))
    else:
        Import(Path(args.recipe), args.update, args.dry_run).run()


if __name__ == "__main__":
    main()
