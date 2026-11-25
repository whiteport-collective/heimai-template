---
tool: project-log
used_by: [saga, freya, mimir, idun]
skills: [brief, impact-map, project-setup, handover]
tools: [heim/heim-floor]
needs: Python 3.10+
---

# project-log

Keeps a project's design log and its card, the same way for every agent that works in the project. `append` adds one dated line to the project's `05-progress/00-design-log.md`; `status` shows the project's `feature.yaml`, the only place its version and status are written (decisions 21 and 26), and changes `status`, `next` and `version` in it without touching the rest of the file or its comments. The project is found under the projects folder(s) of the floor plan ([heim-floor](../heim-floor/tool.md)). This is story 5.1 in the PRD.

## Commands

```bash
python agents/heim/tools/project-log/log.py append sjobod --agent saga --text "Intake confirmed with Åsa; the brief started."
python agents/heim/tools/project-log/log.py append heim --agent idun --text "Test Heim set up."
python agents/heim/tools/project-log/log.py status sjobod
python agents/heim/tools/project-log/log.py status sjobod --status "in progress" --version 0.1.0 --next "Brief: the vision in 01-brief.md"
```

`<project>` is a folder name under the projects folder(s), a path to a project folder, or `heim` for the Heim's own log, `05-progress/00-design-log.md` under heimdocs.

**`append`** keeps the log newest first, in this form: it puts `### YYYY-MM-DD (agent)` and `- text` at the top under `## Log`. If the top entry already has that heading (the same day and agent), the line joins it. With `--session <id> [--to <agent>]` the heading is `### <session id> (agent → to)`, the form a session log uses; the [handover tool](../handover/tool.md) passes them at every wrap. A new log gets `# Design log: <feature>`, one line saying the latest is at the top, and `## Log`. In a plain log without `## Log`, the old lines stay where they are and `## Log` is added after them. It prints `created` for a new log and what it added.

**`status`** without options prints `feature.yaml`, with a note if it is not valid YAML. With `--status`, `--next` or `--version X.Y.Z` it edits those top-level lines in place (the comment at the end of a line stays; `next` is always quoted, so a `: ` in it cannot break the file; a missing key is added at the end) and prints each line before and after, then `updated.` If the file is still not valid YAML because of another key, it says so.

## Exit codes

0 done, 1 refused (an unknown project, an agent name that is not lowercase, empty text, a version that is not X.Y.Z, no `feature.yaml`), 2 on an error (no Heim, a file that cannot be read or written).
