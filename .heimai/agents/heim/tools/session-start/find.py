#!/usr/bin/env python3
"""Find handovers in every sessions folder below a folder.

A session can be started in a repo, a worktree, or any folder above them
(the dev root). This walks down from that folder, finds every `sessions/`
and numbered `NN-sessions/` folder (`heimdocs/06-sessions/`), and lists the
handovers in them: across repos, worktrees on unmerged branches and the
private cabinet. See tool.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SKIP = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", "dist", "build",
    ".next", ".nuxt", ".cache", ".turbo", "vendor", "target", ".idea", ".vscode",
    "site-packages", ".wrangler", "coverage",
}
SESSIONS_DIR = re.compile(r"^(\d\d-)?sessions$", re.IGNORECASE)
STAMP = re.compile(r"^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2})")
OPEN = {"öppen", "oppen", "open"}
TAKEN = {"tagen", "taken"}
DONE = {"klar", "done"}


def walk_sessions(root: Path, max_depth: int):
    """Yield every sessions folder below root, without descending into one."""
    stack = [(root, 0)]
    while stack:
        folder, depth = stack.pop()
        try:
            entries = list(os.scandir(folder))
        except (PermissionError, FileNotFoundError, NotADirectoryError, OSError):
            continue
        for e in entries:
            try:
                if not e.is_dir(follow_symlinks=False) or e.is_symlink():
                    continue
                if getattr(e, "is_junction", lambda: False)():
                    continue
            except OSError:
                continue
            name = e.name
            if SESSIONS_DIR.match(name):
                yield Path(e.path)
            elif name not in SKIP and not name.startswith("$") and depth < max_depth:
                stack.append((Path(e.path), depth + 1))


def front_matter(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            if f.readline().strip() != "---":
                return {}
            data = {}
            for line in f:
                if line.strip() == "---":
                    break
                if ":" in line:
                    k, v = line.split(":", 1)
                    data[k.strip().lower()] = v.strip()
            return data
    except OSError:
        return {}


_repo_cache: dict[Path, tuple[str, str, str, str, bool]] = {}


def repo_of(path: Path) -> tuple[str, str, str, str, bool]:
    """(checkout path, folder name, branch, shared git dir, is main checkout) of the checkout holding path.

    Worktrees of one repo share the git dir, so the same handover on several
    branches can be listed once.
    """
    for parent in [path, *path.parents]:
        if parent in _repo_cache:
            return _repo_cache[parent]
        git = parent / ".git"
        if git.exists():
            branch, common, main = "", str(git.resolve()).lower(), git.is_dir()
            try:
                gitdir = git
                if git.is_file():  # a worktree: ".git" points at its gitdir
                    text = git.read_text(encoding="utf-8").strip()
                    gitdir = Path(text.split(":", 1)[1].strip())
                    if not gitdir.is_absolute():
                        gitdir = (parent / gitdir).resolve()
                    cd = gitdir / "commondir"
                    if cd.exists():
                        common = str((gitdir / cd.read_text(encoding="utf-8").strip()).resolve()).lower()
                head = (gitdir / "HEAD").read_text(encoding="utf-8").strip()
                branch = head.split("refs/heads/", 1)[1] if "refs/heads/" in head else head[:7]
            except (OSError, IndexError):
                pass
            result = (str(parent), parent.name, branch, common, main)
            _repo_cache[parent] = result
            return result
    return (str(path.parent), path.parent.name, "", str(path.parent).lower(), True)


def private_cabinet() -> Path | None:
    """The repo or local folder holding the private cabinet; personal parts are in its `sessions/`."""
    me = Path.home() / ".wds" / "me.md"
    try:
        for line in me.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*-?\s*\**private\**\s*[:=]\s*`?([^`\s#]+)`?", line, re.IGNORECASE)
            if m and (":" in m.group(1) or m.group(1).startswith(("/", "~"))):
                cabinet = Path(os.path.expanduser(m.group(1))).resolve()
                checkout = repo_of(cabinet)[0]
                return Path(checkout) if (Path(checkout) / ".git").exists() else cabinet
    except OSError:
        pass
    return None


def status_of(fm: dict) -> str:
    s = fm.get("status", "").lower()
    if s in OPEN:
        return "open"
    if s in TAKEN:
        return "taken"
    if s in DONE:
        return "done"
    return s or "?"


def worktrees_of(root: Path) -> list[Path]:
    """The other checkouts of the repo root is in, so a session started inside
    one repo still sees handovers on branches checked out beside it."""
    git = root / ".git"
    for parent in [root, *root.parents]:
        git = parent / ".git"
        if git.exists():
            break
    else:
        return []
    try:
        common = git
        if git.is_file():
            gitdir = Path(git.read_text(encoding="utf-8").split(":", 1)[1].strip())
            common = (gitdir / (gitdir / "commondir").read_text(encoding="utf-8").strip()).resolve()
        found = [common.parent] if common.name == ".git" else []
        for wt in (common / "worktrees").glob("*/gitdir"):
            found.append(Path(wt.read_text(encoding="utf-8").strip()).parent)
        return [p.resolve() for p in found if p.exists() and p.resolve() != parent.resolve()]
    except (OSError, IndexError):
        return []


def find(root: Path, max_depth: int):
    private = private_cabinet()
    roots = [root, *worktrees_of(root)]
    if private and not any(private.is_relative_to(r) for r in roots):
        roots.append(private)  # the personal parts, wherever the session runs
    seen = set()
    for sessions in (s for r in roots for s in walk_sessions(r, max_depth)):
        if sessions in seen:
            continue
        seen.add(sessions)
        for dirpath, _dirs, files in os.walk(sessions):
            for name in files:
                m = STAMP.match(name)
                if not m or not name.lower().endswith(".md"):
                    continue
                path = Path(dirpath) / name
                rel = path.relative_to(sessions).parts
                user = rel[0] if len(rel) >= 3 else ""
                agent = rel[1] if len(rel) >= 3 else (rel[0] if len(rel) == 2 else "")
                fm = front_matter(path)
                repo_path, repo, branch, common, main = repo_of(path)
                is_private = bool(private) and str(path.resolve()).lower().startswith(str(private).lower())
                summary = name[:-3]
                # <stamp>-<user>-<från>-<summary>: strip what the folders already say
                rest = summary[len(m.group(1)):].lstrip("-")
                for part in (user, fm.get("från", fm.get("from", ""))):
                    if part and rest.lower().startswith(part.lower() + "-"):
                        rest = rest[len(part) + 1:]
                yield {
                    "stamp": m.group(1),
                    "part": "personal" if is_private else "work",
                    "status": status_of(fm),
                    "repo": repo,
                    "repo_path": repo_path,
                    "branch": branch,
                    "user": user,
                    "agent": agent,
                    "from": fm.get("från", fm.get("from", "")),
                    "to": fm.get("till", fm.get("to", agent)),
                    "summary": rest.replace("-", " "),
                    "path": str(path),
                    "_key": (common, str(path.relative_to(repo_path)).lower()),
                    "_main": main,
                    "_personal": fm.get("part", fm.get("del", "")).lower() in ("personal", "personlig"),
                }


def collapse(hits: list[dict]) -> list[dict]:
    """One entry per handover: the same file in several worktrees of a repo is listed once.

    The checkout kept is the one on main/master, else the main checkout, else
    the first; the others go in `also_in`. The file is the same on every branch
    that has it, so where it is taken matters only for the commit.
    """
    groups: dict[tuple, list[dict]] = {}
    for h in hits:
        groups.setdefault(h["_key"], []).append(h)
    out = []
    for group in groups.values():
        group.sort(key=lambda h: (h["branch"] in ("main", "master"), h["_main"]), reverse=True)
        first = dict(group[0])
        first["also_in"] = [f"{h['repo']} [{h['branch']}]" for h in group[1:]]
        out.append(first)
    # A file in the private cabinet with the same name as a work part is that
    # handover's personal part: attach it. Alone, it is a handover of its own
    # (the private cabinet is also a working repo, for the private agent).
    work_names = {Path(h["path"]).name.lower(): h for h in out if h["part"] == "work"}
    kept = []
    for h in out:
        h["personal"] = ""
        if h["part"] == "personal":
            twin = work_names.get(Path(h["path"]).name.lower())
            if twin:
                twin["personal"] = h["path"]
                continue
            if h.get("_personal"):   # the personal part of a handover in a repo not searched: never one of its own
                continue
            h["part"] = "work"
        kept.append(h)
    for h in kept:
        h.pop("_key", None)
        h.pop("_main", None)
        h.pop("_personal", None)
    return kept


def main() -> int:
    ap = argparse.ArgumentParser(description="Find handovers below a folder (see tool.md).")
    ap.add_argument("root", nargs="?", default=".", help="where the session runs (default: here)")
    ap.add_argument("--stamp", help="YYYY-MM-DD_HH-MM from a resume command")
    ap.add_argument("--summary", help="the summary words from the resume command, to rank several matches")
    ap.add_argument("--repo", help="the repo named in the resume command, to rank several matches")
    ap.add_argument("--open", action="store_true", help="only open handovers")
    ap.add_argument("--agent", help="only handovers to this agent")
    ap.add_argument("--user", help="only this user's folder (all-users is always included)")
    ap.add_argument("--depth", type=int, default=7, help="how deep to look for sessions folders (default 7)")
    ap.add_argument("--json", action="store_true", help="JSON for agents")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    hits = collapse(list(find(root, a.depth)))
    if a.stamp:
        hits = [h for h in hits if h["stamp"].lower() == a.stamp.lower()]
    if a.open:
        hits = [h for h in hits if h["status"] == "open"]
    if a.agent:
        ag = a.agent.lower()
        hits = [h for h in hits if ag in (h["agent"].lower(), h["to"].lower())]
    if a.user:
        hits = [h for h in hits if h["user"].lower() in (a.user.lower(), "all-users")]

    words = set((a.summary or "").lower().split())
    repo = (a.repo or "").lower()

    def rank(h):
        overlap = len(words & set(h["summary"].lower().split()))
        repo_hit = 0 if not repo else (2 if h["repo"].lower() == repo else 1 if h["repo"].lower().startswith(repo) else 0)
        return (overlap, repo_hit, h["stamp"])

    hits.sort(key=rank, reverse=True)

    if a.json:
        json.dump({"root": str(root), "handovers": hits}, sys.stdout, ensure_ascii=False, indent=1)
        print()
        return 0
    if not hits:
        print(f"No handovers found below {root}")
        return 1
    for h in hits:
        branch = f" [{h['branch']}]" if h["branch"] else ""
        print(f"{h['stamp']}  {h['status']:<6} {h['repo']}{branch}  {h['user']}/{h['agent']}  {h['summary']}")
        print(f"    {h['path']}")
        if h["personal"]:
            print(f"    personal part: {h['personal']}")
        if h["also_in"]:
            print(f"    also in: {', '.join(h['also_in'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
