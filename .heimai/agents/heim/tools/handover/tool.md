---
tool: handover
used_by: [every agent]
skills: [handover]
tools: [heim/heim-floor, heim/session-start, heim/project-log]
templates: [heim/handover]
needs: Python 3.10+, git
version: 0.1.0
---

# handover

The mechanics of a handover, so the filename, the keys, the logs and the resume command come out the same every time, whichever agent and model writes them. What goes in a handover is the [handover skill](../../skills/handover/SKILL.md)'s judgment; this tool only does the steps that never vary. This is story 1.2 in the PRD.

## Commands

```bash
python agents/heim/tools/handover/handover.py new --active --agent saga [--session YYYY-MM-DD_HH-MM] [--projects a,b] [--model <id>] [--tool claude]
python agents/heim/tools/handover/handover.py new --from saga [--to freya] [--for <user>|all-users] --summary "<3 to 6 words>" [--continues <file>] [--handoff]
python agents/heim/tools/handover/handover.py take <handover> --session YYYY-MM-DD_HH-MM [--trailer "Co-Authored-By: …"]
python agents/heim/tools/handover/handover.py take <handover> --done
python agents/heim/tools/handover/handover.py log <work part> --text "<one to three points in one line>"
python agents/heim/tools/handover/handover.py receipt <work part>
```

- **`new --active`** writes the session file `<session-id>-<agent>-active.md` in `<sessions>/<user>/<agent>/`, with `status: active` and empty `## In progress`, `## Done`, `## Left` and `## Next`. The session id is `YYYY-MM-DD_HH-MM-<user>`, the session's start in local time; without `--session` it is now.
- **`new --from`** writes the handover in two parts with the same filename, `<session-id>-<from>-<summary>.md`:
  - **The work part** in the recipient's folder, `<sessions>/<for>/<to>/`. When this agent's session file is there, it becomes the work part: the tool refuses while `## In progress` still holds anything (sorting it is the skill's step), then removes the heading, sets `status: open`, `end`, `from`, `to` and an empty `taken_by`, and moves the file with `git mv`. The session id is then the session file's. Without one, the work part is written from `templates/handover/work.md`.
  - **The personal part** in the private cabinet, `sessions/<repo>/<to>/` at the root of the repo or folder that holds it (decision 27), from `templates/handover/personal.md`, linking the work part. A session that touched several repos has one personal part: a second `new` with the same session id adds its link and repo to the first one. `--no-personal` writes none; so does `--handoff`, which hands one task over while the session goes on, and leaves the session file alone.
  - It never overwrites a file. The summary is lowercased, å and ä become a and ö becomes o, and it notes when the summary is not 3 to 6 words or the checkout is not on the default branch.
- **`take`** sets `status: taken` and `taken_by: <session id>` in the handover and in its personal part, and commits each in its own checkout, the one file alone (`take: <stamp> handover, by <session id>`). It refuses a handover that is not open, or that another session has taken (another window may still run it); `--force` takes it over on the person's yes. `--done` sets `status: done` when the work it handed over is delivered (`close: <stamp> handover, done`). A handover written with the Swedish keys keeps them (`status: tagen`, `tagen_av:`).
- **`log`** adds the line, with a link to the handover, at the top of each project's design log through [project-log](../project-log/tool.md) (the projects in the handover's `projects:`, or `--project`), and the line `- <session id> <repos> (<from> → <to>): <text> · <personal part>` at the top of `log.md` in the private cabinet.
- **`receipt`** prints the session, both parts and, for each, what is not yet where others can see it: not committed, not pushed (or no upstream), and a branch not merged into the default branch, where the work is only on that branch (FR5). It flags a handover with no Done or Next, a `## In progress` left, or `status: active`. The last line is the resume command, with the folder name of the checkout the work part is in:

  ```
  /saga acme-heim 2026-11-20_00-25 brief agreed, map next
  ```

## Where it writes

- **The sessions folder** is the floor plan's `sessions:` ([heim-floor](../heim-floor/tool.md)), else `sessions/` at the checkout root. A repo whose `sessions/README.md` says `sessions: private` needs `--sessions <folder>`, the place in the private cabinet the skill names.
- **The private cabinet** is `private:` in `~/.wds/me.md`; the personal parts lie in `sessions/` at the root of the repo or folder holding it, found the same way as [session-start](../session-start/tool.md) finds them.
- Nothing is pushed. Pushing waits for the person (each repo's `AGENTS.md`).

## Exit codes

0 done, 1 refused (a missing or wrong argument, a file that exists, `## In progress` left, a handover not open or taken by another session), 2 on an error (a Heim or file that cannot be read).
