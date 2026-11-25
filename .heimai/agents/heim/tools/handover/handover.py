#!/usr/bin/env python3
"""The mechanics of a handover, the same every time: names, keys, logs and the resume command.

    new --active --agent saga                     the session file, while the session runs
    new --from saga [--to freya] --summary "..."  the handover: the work part and the personal part
    take <handover> --session <id> [--done]       taken (or done), committed in its own checkout
    log <work part> --text "..."                  the project logs and the private log
    receipt <work part>                           where both parts lie, what is not pushed or merged, the resume command

The judgment (what was delivered, what belongs to the work and what to the person,
where each learning goes) is the handover skill's. Folders come from the floor plan
(../heim-floor/floor.py), the private cabinet and the checkouts from session-start
(../session-start/find.py). See tool.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "heim-floor"))
sys.path.insert(0, str(HERE.parent / "session-start"))
import floor  # noqa: E402
import find as ss  # noqa: E402

STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$")
SESSION = re.compile(r"^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2})(?:-([a-z0-9][a-z0-9-]*))?$")
NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# The words in the files are English; older handovers use the Swedish ones (i18n, decision of 2026-11-11).
STATUS_WORD = {"open": ("open", "öppen"), "taken": ("taken", "tagen"), "done": ("done", "klar"), "active": ("active", "pågår")}
NEXT_OF = {"taken": {"open": "taken", "öppen": "tagen", "oppen": "tagen"},
           "done": {"open": "done", "taken": "done", "öppen": "klar", "oppen": "klar", "tagen": "klar"}}
SECTIONS = {"in_progress": ("In progress", "Pågår"), "done": ("Done", "Gjort"), "left": ("Left", "Kvar"),
            "next": ("Next", "Nästa"), "files": ("Files", "Filer"), "project_parts": ("Project parts", "Projektdelar"),
            "for_you": ("For you", "För dig")}


class Refused(Exception):
    pass


# ---------- small helpers ----------

def now() -> dt.datetime:
    return dt.datetime.now().astimezone()


def iso(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M") + t.strftime("%z")[:3] + ":" + t.strftime("%z")[3:]


def slug(words: str) -> str:
    s = words.lower().replace("å", "a").replace("ä", "a").replace("ö", "o").replace("é", "e").replace("ü", "u")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def git(args: list[str], cwd: Path | str) -> tuple[int, str]:
    p = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr).strip()


def me_value(key: str) -> str:
    """A line from the per-computer file `~/.wds/me.md` (`user:`, `private:`)."""
    try:
        for line in (Path.home() / ".wds" / "me.md").read_text(encoding="utf-8").splitlines():
            m = re.match(rf"^\s*{key}\s*:\s*([^#\s]+)", line)
            if m:
                return m.group(1).strip("`\"'")
    except OSError:
        pass
    return ""


def user_of(arg: str | None) -> str:
    u = (arg or me_value("user")).lower()
    if not u or not NAME.match(u):
        raise Refused("no user: give --user, or set `user:` in ~/.wds/me.md")
    return u


def session_id(arg: str | None, user: str, default_now: bool = True) -> str:
    if not arg:
        if not default_now:
            raise Refused("--session is needed: the session id of the session that takes it (YYYY-MM-DD_HH-MM-<user>)")
        return f"{now():%Y-%m-%d_%H-%M}-{user}"
    m = SESSION.match(arg)
    if not m:
        raise Refused(f"the session {arg!r} is not YYYY-MM-DD_HH-MM or YYYY-MM-DD_HH-MM-<user>")
    return f"{m.group(1)}-{m.group(2) or user}"


def start_of(session: str) -> str:
    t = dt.datetime.strptime(session[:16], "%Y-%m-%d_%H-%M").astimezone()
    return iso(t)


def front_matter(text: str) -> tuple[list[str], list[str]]:
    """(front matter lines, body lines); no front matter gives ([], all lines)."""
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                return lines[1:i], lines[i + 1:]
    return [], lines


def fm_get(fm: list[str], *keys: str) -> str:
    for line in fm:
        k, _, v = line.partition(":")
        if k.strip().lower() in keys:
            return v.strip()
    return ""


def fm_set(fm: list[str], key: str, value: str, aliases: tuple[str, ...] = (), after: str | None = None) -> list[str]:
    """Set a top-level key in place (an alias spelling keeps its own key); a missing key goes after `after`, else last."""
    out, done = [], False
    for line in fm:
        k = line.partition(":")[0].strip().lower()
        if not done and k in (key, *aliases) and not line.startswith((" ", "\t")):
            out.append(f"{line.partition(':')[0]}: {value}".rstrip())
            done = True
        else:
            out.append(line)
    if not done:
        idx = next((i + 1 for i, l in enumerate(out) if l.partition(":")[0].strip().lower() == after), len(out)) \
            if after else len(out)
        out.insert(idx, f"{key}: {value}".rstrip())
    return out


def as_list(v: str) -> list[str]:
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        v = v[1:-1]
    return [x.strip().strip("\"'") for x in v.split(",") if x.strip()]


def section(body: list[str], key: str) -> list[str] | None:
    """The lines under a `## <heading>` (either language), or None when the heading is missing."""
    names = {n.lower() for n in SECTIONS[key]}
    for i, line in enumerate(body):
        if line.startswith("## ") and line[3:].strip().lower() in names:
            out = []
            for l in body[i + 1:]:
                if l.startswith("## "):
                    break
                out.append(l)
            return out
    return None


def has_content(lines: list[str] | None) -> bool:
    return bool(lines) and any(re.sub(r"^\s*([-*]|\d+\.|- \[[ x]\])\s*", "", l).strip() for l in lines)


def fill(template: str, values: dict[str, str]) -> str:
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), ""), template)


def template(name: str) -> str:
    return (floor.templates_dir(__file__) / "handover" / name).read_text(encoding="utf-8")


def write_new(path: Path, text: str):
    if path.exists():
        raise Refused(f"{path} exists; a handover is never overwritten")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


# ---------- where things are ----------

def checkout_of(path: Path) -> tuple[Path, str, str]:
    """(checkout root, folder name, branch) of the checkout holding path."""
    path = path.resolve()
    if not any((p / ".git").exists() for p in [path, *path.parents]):
        folder = path if path.is_dir() else path.parent
        return folder, folder.name, ""          # a local folder, not a repo
    repo_path, name, branch, _common, _main = ss.repo_of(path)
    return Path(repo_path), name, branch


def repo_name(checkout: Path) -> str:
    """The repo's name, not the worktree's folder: the main checkout's folder name, else the remote's."""
    code, url = git(["remote", "get-url", "origin"], checkout)
    if code == 0 and url:
        return re.sub(r"\.git$", "", url.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1])
    code, common = git(["rev-parse", "--path-format=absolute", "--git-common-dir"], checkout)
    if code == 0 and common.endswith(".git"):
        return Path(common).parent.name
    return checkout.name


def sessions_folder(where: Path, heim: str | None) -> Path:
    """The floor plan's sessions folder in a Heim; `sessions/` at the checkout root elsewhere."""
    try:
        f = floor.load(heim=heim or str(where))
        if f.sessions:
            return f.sessions
    except floor.FloorError:
        pass
    root = checkout_of(where)[0]
    readme = root / "sessions" / "README.md"
    if readme.exists() and re.search(r"^\s*sessions:\s*private", readme.read_text(encoding="utf-8"), re.M):
        raise Refused(f"{readme} says `sessions: private`: the work part goes where `sessions:` in the private "
                      f"cabinet's projects/<repo>.md points; give that folder with --sessions")
    return root / "sessions"


def cabinet() -> tuple[Path | None, Path | None]:
    """(the private cabinet folder, the checkout or folder whose `sessions/` holds the personal parts)."""
    raw = me_value("private")
    if not raw:
        return None, None
    folder = Path(os.path.expanduser(raw))
    if not folder.exists():
        return None, None
    return folder.resolve(), ss.private_cabinet()


def personal_twin(work: Path) -> Path | None:
    _, root = cabinet()
    if not root:
        return None
    if not (root / "sessions").is_dir():
        return None
    hits = list((root / "sessions").rglob(work.name))
    if not hits:   # a session that touched several repos has one personal part, named after the first
        sid = work.name[:16]
        hits = [p for p in (root / "sessions").rglob(f"{sid}-*.md") if work.name in p.read_text(encoding="utf-8")]
    return hits[0] if hits else None


# ---------- new ----------

def cmd_new(a) -> int:
    user = user_of(a.user)
    where = Path(a.where or ".").resolve()
    sessions = Path(a.sessions).resolve() if a.sessions else sessions_folder(where, a.heim)
    checkout, folder_name, branch = checkout_of(where)
    repo = repo_name(checkout)

    if a.active:
        agent = a.agent or a.from_
        if not agent or not NAME.match(agent):
            raise Refused("--agent: the agent this session runs as, lowercase (saga)")
        sid = session_id(a.session, user)
        path = sessions / user / agent / f"{sid}-{agent}-active.md"
        values = {"session": sid, "start": start_of(sid), "user": user, "agent": agent, "model": a.model or "",
                  "tool": a.tool or "", "projects": ", ".join(as_list(a.projects or "")), "repos": repo}
        write_new(path, fill(template("session.md"), values))
        print(f"session file  {path}")
        return 0

    frm = a.from_
    if not frm or not NAME.match(frm):
        raise Refused("--from: the agent that writes the handover, lowercase (saga)")
    to = a.to or frm
    if not NAME.match(to):
        raise Refused(f"--to {to!r} must be a lowercase agent name")
    words = slug(a.summary or "")
    n = len([w for w in words.split("-") if w])
    if n == 0:
        raise Refused("--summary: what the session did (or, for a handoff, the task), 3 to 6 words")
    person = (a.for_ or user).lower()
    if not NAME.match(person):
        raise Refused(f"--for {person!r} must be a user folder name or all-users")

    # the session id: given, else the session file's, else now
    own = sessions / user / frm
    active = None
    if a.session:
        sid = session_id(a.session, user)
        cand = own / f"{sid}-{frm}-active.md"
        active = cand if cand.exists() else None
    else:
        files = sorted(own.glob(f"*-{user}-{frm}-active.md")) if own.is_dir() else []
        files = [f for f in files if fm_get(front_matter(f.read_text(encoding="utf-8"))[0], "status") in STATUS_WORD["active"]]
        if files and not a.handoff:
            active = files[-1]
            sid = active.name[: -len(f"-{frm}-active.md")]
        else:
            sid = session_id(None, user)
            if not a.handoff:
                print(f"note: no session file and no --session; the id is now ({sid}), not the session's start")
    if a.handoff:
        active = None   # a handoff hands one task; the session file stays with the session

    name = f"{sid}-{frm}-{words}.md"
    work = sessions / person / to / name
    end = iso(now())
    projects = as_list(a.projects or "")
    continues = a.continues or ""

    if active:
        text = active.read_text(encoding="utf-8")
        fm, body = front_matter(text)
        left = section(body, "in_progress")
        if has_content(left):
            raise Refused(f"{active.name} still has `## In progress`: move each item to Done, Left or Next, or strike it, "
                          f"then run new again")
        body = drop_section(body, "in_progress")
        fm = fm_set(fm, "status", "open")
        fm = fm_set(fm, "end", end, ("slut",), after="start")
        fm = fm_set(fm, "from", frm, ("från",), after="user")
        fm = fm_set(fm, "to", to, ("till",), after="from")
        fm = fm_set(fm, "taken_by", "", ("tagen_av",), after="status")
        if projects:
            fm = fm_set(fm, "projects", f"[{', '.join(projects)}]")
        if continues:
            fm = fm_set(fm, "continues", continues)
        if work.exists():
            raise Refused(f"{work} exists; a handover is never overwritten")
        work.parent.mkdir(parents=True, exist_ok=True)
        code, out = git(["mv", str(active), str(work)], checkout_of(active)[0])
        if code != 0:   # not tracked yet: a plain move
            active.rename(work)
        work.write_text("---\n" + "\n".join(fm) + "\n---\n" + "\n".join(body), encoding="utf-8", newline="\n")
        print(f"work part     {work}  (from the session file {active.name})")
    else:
        values = {"session": sid, "start": start_of(sid), "end": end, "user": user, "from": frm, "to": to,
                  "model": a.model or "", "tool": a.tool or "", "projects": ", ".join(projects), "repos": repo,
                  "continues": continues}
        write_new(work, fill(template("work.md"), values))
        print(f"work part     {work}")

    if a.handoff or a.no_personal:
        print("personal part none" + (" (a handoff writes none)" if a.handoff else ""))
    else:
        write_personal(work, sid, user, frm, to, repo, checkout)
    if not 3 <= n <= 6:
        print(f"note: the summary has {n} words; 3 to 6 read best in the resume command")
    if branch and branch not in default_branches(checkout):
        print(f"note: the checkout {folder_name} is on {branch}; the receipt will say until it is merged")
    return 0


def drop_section(body: list[str], key: str) -> list[str]:
    names = {n.lower() for n in SECTIONS[key]}
    out, skip = [], False
    for line in body:
        if line.startswith("## "):
            skip = line[3:].strip().lower() in names
        if not skip:
            out.append(line)
    return out


def write_personal(work: Path, sid: str, user: str, frm: str, to: str, repo: str, checkout: Path):
    folder, root = cabinet()
    if not root:
        print("personal part none: `private:` in ~/.wds/me.md is missing or not on this computer (the skill asks where)")
        return
    if work.resolve().is_relative_to(root):
        print("personal part none: the work part is already in the private cabinet")
        return
    work_rel = work.resolve().relative_to(checkout).as_posix()
    line = f"- {repo}: `{work_rel}`"
    # one personal part per session, however many repos it touched
    existing = [p for p in (root / "sessions").rglob(f"{sid}-*.md")] if (root / "sessions").is_dir() else []
    if existing:
        p = existing[0]
        text = p.read_text(encoding="utf-8")
        if line in text:
            print(f"personal part {p}  (already links {repo})")
            return
        fm, body = front_matter(text)
        fm = fm_set(fm, "repos", "[" + ", ".join(dict.fromkeys(as_list(fm_get(fm, "repos")) + [repo])) + "]")
        for i, l in enumerate(body):
            if l.startswith("## ") and l[3:].strip().lower() in {n.lower() for n in SECTIONS["project_parts"]}:
                j = i + 1
                while j < len(body) and body[j].startswith("- "):
                    j += 1
                body.insert(j, line)
                break
        p.write_text("---\n" + "\n".join(fm) + "\n---\n" + "\n".join(body), encoding="utf-8", newline="\n")
        print(f"personal part {p}  (added the link to {repo})")
        return
    p = root / "sessions" / repo.lower() / to / work.name
    values = {"session": sid, "user": user, "from": frm, "to": to, "repos": repo, "project_line": line}
    write_new(p, fill(template("personal.md"), values))
    print(f"personal part {p}")


# ---------- take ----------

def cmd_take(a) -> int:
    path = Path(a.handover).resolve()
    if not path.is_file():
        raise Refused(f"no handover at {path}")
    target = "done" if a.done else "taken"
    sid = ""
    if not a.done:
        sid = session_id(a.session, user_of(a.user), default_now=False)
    parts = [path]
    twin = personal_twin(path)
    if twin and twin.resolve() != path:
        parts.append(twin)
    for p in parts:
        take_one(p, target, sid, a)
    return 0


def take_one(path: Path, target: str, sid: str, a):
    text = path.read_text(encoding="utf-8")
    fm, body = front_matter(text)
    if not fm:
        raise Refused(f"{path.name} has no front matter")
    status = fm_get(fm, "status").lower()
    new = NEXT_OF[target].get(status)
    if status in STATUS_WORD[target]:
        who = fm_get(fm, "taken_by", "tagen_av")
        if target == "taken" and who and who != sid and not a.force:
            raise Refused(f"{path.name} is already taken by {who}: another window may still be running it; "
                          f"--force takes it over on the person's yes")
        if not (target == "taken" and who != sid):
            print(f"{target:<6} already  {path}")
            return
        new = status
    if new is None:
        if not a.force:
            who = fm_get(fm, "taken_by", "tagen_av")
            raise Refused(f"{path.name} is `{status}`" + (f" (taken by {who})" if who else "") +
                          f"; --force to set it {target} anyway")
        new = STATUS_WORD[target][0]
    fm = fm_set(fm, "status", new)
    if sid:
        key = "tagen_av" if fm_get(fm, "tagen_av") or any(l.startswith("tagen_av:") for l in fm) else "taken_by"
        fm = fm_set(fm, key, sid, ("taken_by", "tagen_av"), after="status")
    path.write_text("---\n" + "\n".join(fm) + "\n---\n" + "\n".join(body), encoding="utf-8", newline="\n")
    checkout = checkout_of(path)[0]
    stamp = path.name[:16]
    msg = (f"take: {stamp} handover, by {sid}" if target == "taken" else f"close: {stamp} handover, done") + \
          "\n\n" + (a.trailer or "")
    if a.no_commit or not (checkout / ".git").exists():
        print(f"{new:<6} {path}  (not committed)")
        return
    rel = path.relative_to(checkout).as_posix()
    code, out = git(["add", "--", rel], checkout)
    if code == 0:
        code, out = git(["commit", "-q", "-m", msg.strip(), "--", rel], checkout)
    if code != 0:
        raise Refused(f"set {new} in {path}, but the commit failed: {out}")
    _, h = git(["rev-parse", "--short", "HEAD"], checkout)
    print(f"{new:<6} {path}  committed {h} in {checkout.name}")


# ---------- log ----------

def load_project_log():
    spec = importlib.util.spec_from_file_location("project_log", HERE.parent / "project-log" / "log.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_log(a) -> int:
    work = Path(a.handover).resolve()
    if not work.is_file():
        raise Refused(f"no handover at {work}")
    text = " ".join((a.text or "").split())
    if not text:
        raise Refused("--text: one to three points on what happened, in one line")
    fm, _ = front_matter(work.read_text(encoding="utf-8"))
    sid, frm, to = fm_get(fm, "session"), fm_get(fm, "from", "från"), fm_get(fm, "to", "till")
    projects = a.project or as_list(fm_get(fm, "projects"))
    checkout = checkout_of(work)[0]

    if projects:
        pl = load_project_log()
        try:
            f = floor.load(heim=a.heim or str(work.parent))
        except floor.FloorError as e:
            raise Refused(f"the project logs need a Heim: {e}")
        for p in projects:
            folder, _name, _ = pl.resolve(f, p)
            logfile = folder / "05-progress" / "00-design-log.md"
            link = Path(os.path.relpath(work, logfile.parent)).as_posix()
            ns = argparse.Namespace(project=p, agent=frm, to=to, session=sid, text=f"{text} [Handover]({link})")
            pl.cmd_append(f, ns)
    else:
        print("project log  none: the handover names no project (projects: [])")

    folder, root = cabinet()
    if folder:
        log = folder / "log.md"
        twin = personal_twin(work)
        where = f" · {twin.relative_to(root).as_posix()}" if twin else ""
        repos = ", ".join(as_list(fm_get(fm, "repos"))) or repo_name(checkout)
        line = f"- {sid} {repos} ({frm} → {to}): {text}{where}"
        old = log.read_text(encoding="utf-8") if log.exists() else "# Session log\n\nOne line per session, newest first.\n"
        if line in old:
            print(f"private log  already has the line ({log})")
        else:
            lines = old.split("\n")
            at = next((i for i, l in enumerate(lines) if l.startswith("- ")), len(lines))
            if at == len(lines):
                lines += ["", line] if lines[-1].strip() else [line]
            else:
                lines.insert(at, line)
            log.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8", newline="\n")
            print(f"private log  {log}")
    else:
        print("private log  none: no private cabinet on this computer")
    return 0


# ---------- receipt ----------

def default_branches(checkout: Path) -> list[str]:
    code, out = git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], checkout)
    if code == 0 and out:
        return [out.split("/", 1)[-1]]
    return [b for b in ("main", "master") if git(["rev-parse", "--verify", "-q", f"refs/heads/{b}"], checkout)[0] == 0]


def state_of(path: Path) -> list[str]:
    """What is not yet where everyone can see it: uncommitted, unpushed, unmerged."""
    checkout, folder_name, branch = checkout_of(path)
    if not (checkout / ".git").exists():
        return ["a local folder, not a repo: saved, nothing to push"]
    out = []
    rel = path.relative_to(checkout).as_posix()
    _, st = git(["status", "--porcelain", "--", rel], checkout)
    if st:
        out.append(f"! not committed: {rel}")
    code, ahead = git(["rev-list", "--count", "@{u}..HEAD"], checkout)
    if code != 0:
        out.append(f"! not pushed: {branch or 'HEAD'} has no upstream")
    elif ahead.strip() != "0":
        out.append(f"! not pushed: {ahead.strip()} commit(s) on {branch} not on the remote")
    defaults = default_branches(checkout)
    if branch and defaults and branch not in defaults:
        base = defaults[0]
        merged = git(["merge-base", "--is-ancestor", "HEAD", base], checkout)[0] == 0
        if not merged:
            out.append(f"! not merged: {branch} is not in {base}; the work is only on that branch")
    return out or ["committed and pushed"]


def cmd_receipt(a) -> int:
    work = Path(a.handover).resolve()
    if not work.is_file():
        raise Refused(f"no handover at {work}")
    fm, body = front_matter(work.read_text(encoding="utf-8"))
    sid, frm, to = fm_get(fm, "session"), fm_get(fm, "from", "från"), fm_get(fm, "to", "till")
    status = fm_get(fm, "status")
    checkout, folder_name, branch = checkout_of(work)
    twin = personal_twin(work)

    print(f"Session    {sid}   {frm} → {to}   status: {status}")
    if (checkout / ".git").exists():
        print(f"Work part  {work.relative_to(checkout).as_posix()}   in {folder_name}" + (f" [{branch}]" if branch else ""))
    else:
        print(f"Work part  {work}")
    for s in state_of(work):
        print(f"           {s}")
    if twin:
        print(f"Personal   {twin}")
        for s in state_of(twin):
            print(f"           {s}")
    else:
        print("Personal   none")
    gaps = [SECTIONS[k][0] for k in ("done", "next") if not has_content(section(body, k))]
    if section(body, "in_progress") is not None:
        gaps.append("In progress is still there")
    if status.lower() in STATUS_WORD["active"]:
        gaps.append("status is still active")
    if gaps:
        print(f"Check      ! {'; '.join(gaps)}")
    words = work.stem[len(sid) + 1:] if work.stem.startswith(sid) else work.stem[17:]
    if words.startswith(frm + "-"):
        words = words[len(frm) + 1:]
    print()
    print(f"/{to} {folder_name} {sid[:16]} {words.replace('-', ' ')}")
    return 0


# ---------- main ----------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="The mechanics of a handover (see tool.md).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="the session file (--active), or the handover's work and personal parts")
    n.add_argument("--active", action="store_true", help="write the session file <session>-<agent>-active.md")
    n.add_argument("--agent", help="with --active: the agent the session runs as")
    n.add_argument("--from", dest="from_", help="the agent that writes the handover")
    n.add_argument("--to", help="the agent that takes the next step (default: --from)")
    n.add_argument("--for", dest="for_", help="the person who runs it (default: you), or all-users")
    n.add_argument("--summary", help="3 to 6 words: what the session did, or the task for a handoff")
    n.add_argument("--session", help="YYYY-MM-DD_HH-MM[-user], the session's start (default: the session file's)")
    n.add_argument("--projects", help="comma-separated project folder names")
    n.add_argument("--continues", help="the filename of the handover this session took")
    n.add_argument("--model", help="the model id")
    n.add_argument("--tool", help="claude, copilot, codex, …")
    n.add_argument("--handoff", action="store_true", help="hand one task over; the session goes on (no personal part)")
    n.add_argument("--no-personal", action="store_true", help="write only the work part")
    n.add_argument("--sessions", help="the sessions folder, when the floor plan cannot say")
    n.add_argument("--where", help="a folder in the repo the work was done in (default: here)")

    t = sub.add_parser("take", help="set a handover taken (or --done) and commit it in its checkout")
    t.add_argument("handover")
    t.add_argument("--session", help="the session that takes it")
    t.add_argument("--done", action="store_true", help="set it done: the work it handed over is delivered")
    t.add_argument("--force", action="store_true", help="take it although it is not open")
    t.add_argument("--no-commit", action="store_true")
    t.add_argument("--trailer", help="lines to end the commit message with (Co-Authored-By: …)")

    lg = sub.add_parser("log", help="a line in each project's design log, and in the private log")
    lg.add_argument("handover", help="the work part")
    lg.add_argument("--text", required=True)
    lg.add_argument("--project", action="append", help="a project (default: the handover's projects:)")

    r = sub.add_parser("receipt", help="where both parts lie, what is not yet shared, and the resume command")
    r.add_argument("handover", help="the work part")

    for p in (n, t, lg, r):
        p.add_argument("--user", help="the user folder name (default: user: in ~/.wds/me.md)")
        p.add_argument("--heim", help="the Heim, when the command runs outside it")

    a = ap.parse_args(argv)
    floor.utf8_stdout()
    try:
        return {"new": cmd_new, "take": cmd_take, "log": cmd_log, "receipt": cmd_receipt}[a.cmd](a)
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    except (floor.FloorError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
