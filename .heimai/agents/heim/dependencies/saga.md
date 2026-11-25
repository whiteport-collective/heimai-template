---
name: saga
source: heim
for: [saga, brief, impact-map, project-setup]
---

# Saga's dependencies

What must be on the computer, and approved once when Saga is woken in a Heim, so her tools run without asking.

| Needs | For | Check |
|---|---|---|
| Python 3.10 or later | every Saga tool | `python --version` |
| PyYAML | `tools/impact-map/validate.py`, and the scaffold and log tools when present | `python -c "import yaml"`; install with `python -m pip install pyyaml` |
| A browser the agent can drive | looking at the person's reference sites (brief, visual direction) | the Heim's browser tool |

**Permissions** the host should allow in the Heim, so the work does not stop for a click: reading and writing the Heim's brief, impact map, brand and projects folders; running `python agents/heim/tools/{brief,impact-map,project-scaffold,project-log,heim-floor}/*.py`; `git add` and `git commit` in the Heim. `heim-sync` writes these into the host's settings when Saga is woken (story 5.6).
