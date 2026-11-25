---
tool: session-start
used_by: [every agent]
skills: [handover]
needs: Python 3.10+
---

# session-start

Finds the handovers a session starts from, wherever the session runs: in a repo, in a worktree, or in a folder above them. Run it from the dev root (`dev_root:` in `~/.wds/me.md`) and every checked-out repo is in reach, so a resume command works without knowing where the handover was written. This is story 1.1 in the PRD.

## Commands

```bash
python agents/heim/tools/session-start/find.py [folder] --stamp YYYY-MM-DD_HH-MM [--repo <name>] [--summary "<words>"]
python agents/heim/tools/session-start/find.py [folder] --open [--agent <agent>] [--user <user>]
```

- **Resume** (`--stamp`): every handover whose filename starts with the timestamp. The repo and the summary from the resume command only rank the matches; the repo is a hint, not a path, so a handover written in a worktree (`acme-heim-quarters`) is found from a command that says `acme-heim`.
- **A normal start** (`--open`): the open handovers (`status: öppen` or `open`), to one agent if `--agent` is given, in the user's own folder and `all-users`.

## What it searches

- **Every sessions folder below the folder**: `sessions/` and the numbered `NN-sessions/` of a Heim (`heimdocs/06-sessions/`), up to seven levels down. It skips `.git`, `node_modules`, build output and links, and never descends into a sessions folder looking for another.
- **The other worktrees of the repo** the folder is in, so a session started inside one checkout still sees handovers on branches checked out beside it.
- **The private cabinet** (`private:` in `~/.wds/me.md`), for the personal parts.

## What it returns

For each handover: the timestamp, the status, the checkout it is in (folder name and branch), user and agent folder, the summary from the filename and the path. Two things are folded in so the list shows each handover once:

- **The same file in several worktrees** of one repo is listed once, from the checkout on `main`, else the main checkout, else the first; the others are in `also_in`.
- **A file in the private cabinet with the same name** as a handover elsewhere is that handover's personal part, given in `personal`. Alone it is a handover of its own, since the private cabinet is also the private agent's working repo, unless its front matter says `part: personal`: the personal part of a handover in a repo not searched is never listed alone.

The checkout in the result is where the session works and where the handover is taken (`git -C <repo_path>`). If its branch is not the repo's default, say so when the handover is shown: the work is there and nowhere else until the branch is merged.

On a computer with about 30 sessions folders, a search from the dev root takes 2–5 seconds.
