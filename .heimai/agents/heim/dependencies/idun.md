---
name: idun
source: heim
for: [idun, onboarding, manage-capabilities]
---

# Idun's dependencies

What must be on the computer, and approved once when Idun is woken in a Heim, so her tools run without asking. `machine check` shows what is missing.

| Needs | For | Check |
|---|---|---|
| Python 3.10 or later | every Idun tool | `python --version` |
| PyYAML | reading floor plans and front matter (`capability-catalog`, `capability-lint`, `heim-status`, `heim-sync`) | `python -c "import yaml"`; install with `python -m pip install pyyaml` |
| git | committing, cloning Heims | `git --version` |
| The GitHub CLI, signed in through the browser | creating the person's own Heim, invitations, adding a person, the access maps | `gh auth status` |

**Permissions** the host should allow in the Heim, so the work does not stop for a click: reading the whole Heim; running `python agents/heim/tools/{heim-status,capability-catalog,capability-lint,handover-audit,machine,heim-floor}/*.py`, which only read; running `heim-scaffold` and `heim-sync` without `--yes` (they only show). Ask every time: the same two with `--yes`, `gh repo create`, `gh api -X PUT` or `-X PATCH`, any install command, and any sync or push into another repo. `heim-sync` writes these into the host's settings when Idun is woken.
