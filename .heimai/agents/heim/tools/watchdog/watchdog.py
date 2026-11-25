#!/usr/bin/env python3
"""Install or update the Watchdog in a Heim: the runner, its .source note and the GitHub workflow.

A dry run unless --yes. It never commits or pushes; it prints the commit line, and the push waits
for the person's yes. See tool.md beside this file.
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "heim-floor"))
import floor  # noqa: E402

# In the development repo, the Watchdog's own folder, six folders up from here.
DEV_FEATURE = Path(__file__).resolve().parents[6] / "watchdog"


class Refused(Exception):
    pass


def find_part(folder: Path, name: str, sub: str) -> Path:
    for p in (folder / name, folder / sub / name):
        if p.is_file():
            return p
    raise Refused(f"no {name} in {folder} (or its {sub}/ folder)")


def source_of(args) -> tuple[Path, Path, str, str]:
    """(runner, workflow, version, label) to copy from."""
    if args.source:
        src = Path(args.source).resolve()
    elif DEV_FEATURE.is_dir():
        src = DEV_FEATURE
    else:
        raise Refused("--from is needed: the HeimAI clone's watchdog/ folder")
    runner = find_part(src, "heim-run.mjs", "runner")
    workflow = find_part(src, "watchdog.yml", "workflow")
    version = args.version
    if not version and (src / "feature.yaml").is_file():
        version = str(floor.read_yaml(src / "feature.yaml").get("version") or "")
    if not version:
        raise Refused("--version is needed: the release's version, as in its tag watchdog-v<version>")
    label = "the development repo, unreleased" if src == DEV_FEATURE else "HeimAI/watchdog"
    return runner, workflow, version, label


def git_root(folder: Path) -> Path | None:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=folder, capture_output=True, text=True, encoding="utf-8")
    return Path(r.stdout.strip()).resolve() if r.returncode == 0 else None


def runner_folder(f: floor.Floor) -> Path:
    if f.format == 1:
        return f.root / ".heim" / "runner"
    if f.plan != f.root / ".heimai" / "heimai.yaml":
        raise Refused(f"the floor plan is {f.rel(f.plan)}; the workflow reads .heimai/heimai.yaml or heim.yaml")
    machine = str(f.config.get("machine") or ".heimai/machine/").strip().rstrip("/")
    if machine != ".heimai/machine":
        raise Refused(f"machine: moves the runner's folder to {machine}/; the workflow looks in "
                      ".heimai/machine/runner/, so change its path by hand (Set up the Watchdog, HeimAI docs)")
    return f.root / ".heimai" / "machine" / "runner"


def text(p: Path) -> str | None:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n") if p.is_file() else None


def dry(runner: Path, root: Path) -> tuple[int, str]:
    r = subprocess.run(["node", str(runner), "--root", str(root), "--dry"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120)
    return r.returncode, (r.stdout + r.stderr).replace("\r\n", "\n")


def main() -> int:
    floor.utf8_stdout()
    ap = argparse.ArgumentParser(description="Install or update the Watchdog in a Heim.")
    ap.add_argument("command", choices=["install"])
    ap.add_argument("--heim", default=".", help="the Heim's folder (default: the current folder)")
    ap.add_argument("--from", dest="source", help="the folder with heim-run.mjs and watchdog.yml")
    ap.add_argument("--version", help="the version being copied (default: feature.yaml in --from)")
    ap.add_argument("--yes", action="store_true", help="write the files; without it nothing changes")
    args = ap.parse_args()

    try:
        runner_src, workflow_src, version, label = source_of(args)
        f = floor.load(heim=args.heim)
        top = git_root(f.root)
        if top is None:
            raise Refused(f"{f.root} is not in a git repo; the Watchdog runs on GitHub, in the Heim's repo")
        if not top.samefile(f.root):
            raise Refused(f"{f.root} is a Heim inside the repo {top}; the outer Heim's Watchdog runs it")
        folder = runner_folder(f)
    except (Refused, floor.FloorError) as e:
        print(f"Refused: {e}")
        return 2

    runner = folder / "heim-run.mjs"
    source = folder / ".source"
    workflow = f.root / ".github" / "workflows" / "watchdog.yml"
    released = "" if label.startswith("the development repo") else f" (tag watchdog-v{version})"
    note = (f"from: {label}\nversion: {version}\ncopied: {dt.date.today().isoformat()}{released}\n"
            "change it there, never here\n")

    installed = "none"
    for line in (text(source) or "").splitlines():
        if line.startswith("version:"):
            installed = line.split(":", 1)[1].strip()

    print(f"Heim:      {f.name} ({f.root})")
    print(f"Floor plan: {f.rel(f.plan)}")
    print(f"Installed: {installed}    Copying: {version} from {label}")
    print()
    changes = []
    for dst, new in ((runner, text(runner_src)), (workflow, text(workflow_src))):
        old = text(dst)
        state = "new" if old is None else "same" if old == new else "changed"
        print(f"  {state:8} {f.rel(dst)}")
        if state != "same":
            changes.append((dst, new))
    old_version = installed if installed != "none" else None
    print(f"  {'same' if old_version == version else 'changed' if source.is_file() else 'new':8} {f.rel(source)}")

    print()
    code_new, out_new = dry(runner_src, f.root)
    if code_new != 0:
        print(f"The new runner failed on this Heim (exit {code_new}); nothing is copied:")
        print("\n".join(out_new.splitlines()[-15:]))
        return 1
    if runner.is_file():
        _, out_old = dry(runner, f.root)
        if out_old == out_new:
            print(f"Timeline: the old and the new runner give the same result ({len(out_new.splitlines())} lines).")
        else:
            a = [x for x in out_old.splitlines() if x.strip()]
            b = [x for x in out_new.splitlines() if x.strip()]
            diff = [f"    - {x}" for x in a if x not in b][:8] + [f"    + {x}" for x in b if x not in a][:8]
            print("Timeline: the new runner gives another result. Read the change before --yes:")
            print("\n".join(diff))
    else:
        print(f"Timeline: the new runner reads the Heim ({len(out_new.splitlines())} lines).")

    lighthouse = f.config.get("lighthouse")
    if lighthouse and not (folder.parent / "lighthouse.json").is_file():
        print(f"Note: the floor plan names the Lighthouse {lighthouse}, but it has not reported here yet;"
              " the Watchdog will warn at its first run.")

    paths = [f.rel(runner), f.rel(source), f.rel(workflow)]
    if not args.yes:
        print("\nA dry run: nothing written. With --yes the files above are written.")
        return 0

    for dst, new in changes:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(new, encoding="utf-8", newline="\n")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(note, encoding="utf-8", newline="\n")
    print("\nWritten. Commit by path, and push only on the person's yes:")
    print(f'  git -C "{f.root}" add -- ' + " ".join(paths))
    print(f'  git -C "{f.root}" commit -m "The Watchdog {version}" -- ' + " ".join(paths))
    print("Then run Watchdog once by hand on GitHub (Actions) and check that it committed the timeline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
