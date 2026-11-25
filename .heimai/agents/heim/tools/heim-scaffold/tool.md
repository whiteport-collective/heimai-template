---
tool: heim-scaffold
used_by: [idun]
skills: [onboarding]
tools: [heim-floor]
needs: Python 3.10+
version: 0.1.1
copied_from: whiteport-design-studio, skills/org-onboarding.md and idun/references/workspace-templates.md (2026-11-19), the workspace step as a script
---

# heim-scaffold

Creates a new Heim's floor plan and folders from [`templates/heim/`](../../templates/heim/), and adds a person's folder to a Heim that exists. It shows what it would write and writes nothing without `--yes`; it never overwrites, and a folder that is already a Heim is refused. What it writes is the least a Heim needs; the brief, the projects and the policy are made later by the skills that own them.

## Commands

```bash
# a business's Heim in the current folder, with Idun and Saga woken
python agents/heim/tools/heim-scaffold/scaffold.py create --name "Northwind Bakery" --kind business \
  --agents idun,saga --person "Åsa Berg" --user asaberg            # shows the tree
python agents/heim/tools/heim-scaffold/scaffold.py create ... --yes                 # writes

# a person's own Heim, in a folder of its own
python agents/heim/tools/heim-scaffold/scaffold.py create --name "Åsa's Heim" --kind private --into ../asa-heim --yes

# a person joins a Heim
python agents/heim/tools/heim-scaffold/scaffold.py add-person saraek --name "Sara Ek" [--heim <folder>] --yes
```

`create` takes `--kind private|business|project`, and optionally `--into`, `--description`, `--organization`, `--heimdocs`, `--agents` (default `idun`), `--inherits <source>` (repeatable), `--lang` (default `en`), `--person`, `--user`, `--github`, `--date`.

## What `create` writes

| File | From |
|---|---|
| `heim.yaml` | `heim.yaml`: name, kind, language, the folder keys, the woken agents, a commented `inherits:` and, for a business, a commented `governance:` key |
| `AGENTS.md`, `CLAUDE.md` | `agents-md.md` (with the agents table, each agent's line from its persona) and `claude-md.md` |
| `.gitignore` | `gitignore.txt`: the note for the owner and large files stay out, the machine folder is in git, since the Watchdog commits the timeline there and the glass reads it (0.1.1; 0.1.0 left the whole machine folder out); when one exists, the lines it lacks are named, not added |
| `<heimdocs>/00-decisions.md` | `decisions.md` |
| `<heimdocs>/06-sessions/README.md` | `sessions-readme.md` |
| `<heimdocs>/users/README.md`, `users/_template/` | `users/` |
| `<heimdocs>/tasks/inbox.md` | `inbox.md` |
| `<heimdocs>/users/<user>/` | `users/_template/`, with `--user` |

**heimdocs** is `.` (the Heim's folders at its root), or `heimdocs/` when the folder already holds code (`package.json`, `src/`, `pyproject.toml` and the like), so a Heim dropped into an existing project leaves the project's own files alone. `--heimdocs` overrides it.

The floor plan written is `heim: 1`. When the Heims move into `.heimai/` (decision 34), the move script converts it and this tool writes `heimai: 2`.

## Refuses

- a folder that already has `heim.yaml` or `.heimai/heimai.yaml` (exit 3): show it with `heim-status` instead;
- governance for a private Heim (decision 15);
- a person whose folder exists (`add-person`, exit 3): it lists what is there.

It does not commit, create a repo or install anything; `heim-setup` creates the repo and the git tool commits. Tried on 2026-11-19 on a scratch business Heim and a private one.
