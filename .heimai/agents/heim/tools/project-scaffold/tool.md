---
tool: project-scaffold
used_by: [saga]
skills: [project-setup]
tools: [heim/heim-floor]
needs: Python 3.10+
---

# project-scaffold

Shows what a Heim already has, and starts a new project from the templates once the person has confirmed the intake. A project is `<projects>/<slug>/` with `feature.yaml` and `01-brief/00-intake.md`, and gets more folders when the work needs them (decision 26); the A to E folders of WDS are read in older projects but never created. `create` writes nothing without `--yes` and never overwrites. The projects and sessions folders come from the floor plan ([heim-floor](../heim-floor/tool.md)), the templates from `templates/project/` beside `tools/`. This is story 5.1 in the PRD.

## Commands

```bash
python agents/heim/tools/project-scaffold/scaffold.py scan [--heim <folder>]
python agents/heim/tools/project-scaffold/scaffold.py create sjobod --name "Sjöbod" --what "A site for boat hire" --client "Åsa" --code app/
python agents/heim/tools/project-scaffold/scaffold.py create sjobod --name "Sjöbod" --what "A site for boat hire" --client "Åsa" --code app/ --yes
```

**`scan`** prints the Heim's name and root, each projects folder, and per project its folder name and `feature:` · `status` · `version` from `feature.yaml`. A `feature.yaml` that is not valid YAML is still read, line by line, and says so. A project with WDS's `A-Product-Brief/` and the like is listed as `WDS layout`. Under each project come the open handovers (`status: open` or `öppen`) in the sessions folder whose `projects:` names it, with who they go to; open handovers naming a project that is not a folder are listed last.

**`create <slug> --name "Name"`** takes `--what`, `--client`, `--builds`, `--goal`, `--constraints`, `--language`, `--milestone`, `--code app/|repo|undecided` and `--sources`; a field not given becomes `[needed: …]`. `--projects-folder` chooses one when the floor plan names several (default: the first). The slug is lowercase letters, digits and hyphens.

- Without `--yes` it prints the tree it would write, the filled `feature.yaml` and intake, and `Nothing written: add --yes after the person has confirmed the summary.`
- With `--yes` it writes the two files, prints `wrote` per file and the fields still `[needed]`.
- If `<projects>/<slug>/` exists, it refuses in both modes and names what is there.

## Exit codes

0 printed or written, 1 refused because the project folder exists, 2 on an error (bad slug, a projects folder not in the floor plan, no Heim, no templates).
