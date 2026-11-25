---
tool: watchdog
used_by: [idun]
skills: [onboarding]
tools: [heim-floor]
needs: Python 3.10+, Node.js 18+, git
version: 0.1.0
---

# watchdog

Installs or updates the Watchdog in a Heim: the runner, its `.source` note and the GitHub workflow. What the Watchdog does and how a Heim uses it is in [Set up the Watchdog](https://github.com/whiteport-collective/HeimAI/blob/main/docs/set-up/set-up-the-watchdog.md); the runner and the workflow are HeimAI's `watchdog/` folder. **A dry run unless `--yes`.** It never commits or pushes.

## Commands

```bash
python agents/heim/tools/watchdog/watchdog.py install [--heim <folder>] [--from <folder>] [--version <x.y.z>] [--yes]
```

| Option | What it does |
|---|---|
| `--heim` | The Heim, the root of its git repo. Default: the current folder |
| `--from` | The folder with `heim-run.mjs` and `watchdog.yml`. The HeimAI clone's `watchdog/`, with `--version` from the release's tag |
| `--version` | The version written in `.source` |
| `--yes` | Writes the files |

## What it does

1. Finds the Heim through its floor plan ([heim-floor](../heim-floor/tool.md)) and the runner's folder: `.heimai/machine/runner/` for `.heimai/heimai.yaml`, `.heim/runner/` for `heim.yaml`.
2. Shows each file as `new`, `same` or `changed`: the runner, `.source` and `.github/workflows/watchdog.yml`.
3. Runs the new runner on the Heim with `--dry`, and the installed one too, and says whether the timeline comes out the same. Where it differs, it shows the lines; read them before `--yes`. A new runner that fails on the Heim stops everything.
4. Warns when the floor plan names a `lighthouse:` that has not reported yet, since the Watchdog would then warn at its first run.
5. With `--yes`, writes the files and `.source` (`from`, `version`, `copied`), and prints the `git add` and `git commit` lines, by path.

Then, after the person's yes: push, run **Watchdog** once by hand in the repo's **Actions** tab, and check that it committed the timeline.

## Refuses

- A folder that is not the root of a git repo. A Heim inside another, such as a project, is run by the outer Heim's Watchdog.
- A `heimai.yaml` whose `machine:` moves the runner's folder, since the workflow looks in `.heimai/machine/runner/`. Change the workflow's path by hand, as the set-up page says.
- `--from` without `--version`.

Tried on 2026-11-21 on a private Heim (0.2.0, all the same), a copy of it at 0.1 (the timeline the same, then written and checked again), a `heimai: 2` copy with nested Heims (the difference shown), a project inside it and a folder outside git (both refused).

Exit codes: 0 shown or written, 1 the new runner failed on the Heim, 2 refused.
