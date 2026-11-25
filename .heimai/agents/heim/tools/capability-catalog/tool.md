---
tool: capability-catalog
used_by: [idun]
skills: [manage-capabilities]
tools: [heim-floor]
needs: Python 3.10+, PyYAML (recommended; without it front matter is read line by line)
version: 0.1.0
copied_from: whiteport-design-studio, skills/librarian.md (2026-11-19), the catalog mode as a script
---

# capability-catalog

Walks an agents folder and lists every object per source and layer, with which agents use it and what it uses, read from the objects' own front matter ([the conventions](../../skills/manage-capabilities/references/front-matter.md)). It flags what is off. The glass's Agents pages (open-glass epic 6) read its `--json`, so that form is kept stable and documented below. Reads only.

## Commands

```bash
python agents/heim/tools/capability-catalog/catalog.py                    # the Heim's agents folder, as tables
python agents/heim/tools/capability-catalog/catalog.py agents/ --json     # the stable JSON
python agents/heim/tools/capability-catalog/catalog.py agents/heim --layer skills
python agents/heim/tools/capability-catalog/catalog.py --source heim --all
```

The folder is an agents folder (each subfolder a source) or one source (it has layer folders). Without one, the Heim's agents folder is found through the floor plan: `agents/` at the root in `heim: 1`, the `agents:` key or `.heimai/agents/` in `heimai: 2`. `--strict` exits 1 when there is an error finding.

## What it reads

| Layer | Object | Front matter from |
|---|---|---|
| agents | `agents/<name>/` | `persona.md` (or an older `instructions.md`) |
| skills | `skills/<name>/` | `SKILL.md` |
| tools | `tools/<name>/` | `tool.md` |
| templates | `templates/<name>` (a file or a folder) | none; who uses it is read from the skills |
| apps | `apps/<name>/` | `app.md` |
| automations | `automations/<name>/` | `automation.md` |
| dependencies | `dependencies/<name>.md` | the file |
| guardrails | `guardrails/<name>.md` | the file |

The keys `skills`, `tools`, `templates`, `guardrails` and `apps` are references; `heim/brief`, `heim/tools/brief/tool.md`, `brief` and `taste/<name>` all resolve. `used_by` names agents. A tool's `skills:` names the skills that use it.

**Who uses an object** (`agents`) is worked out three ways and joined: its own `used_by`; an agent whose persona lists it; and, for a tool, template or guardrail, the agents of every skill that lists it.

## Findings

| Kind | Severity | When |
|---|---|---|
| `missing-reference` | error | a reference names an object that does not exist (also in another source that is not in the folder) |
| `guardrail-without-evals` | error | a guardrail has no `## Evals` table with at least one case |
| `mentions-wds-path` | error | any text file in a source points into WDS's agents folder |
| `asymmetric` | warning | a persona lists a skill whose `used_by` does not name the agent; a skill lists a tool whose `skills:` does not name it, or the other way round |
| `front-matter-not-yaml` | warning | front matter a YAML reader rejects (usually an unquoted `: `); it is still read line by line |
| `used-by-names-a-skill` | warning | `used_by` names a skill; a tool names its skills in `skills:` |
| `no-front-matter` | warning | an object that should have front matter has none |
| `unknown-agent` | info | `used_by` names an agent that is not in the folder (it may live in another repo) |

## The JSON (schema `heim-capability-catalog/1`)

Keys and their order are stable; lists are sorted; nothing in it changes between two runs on the same files (no timestamp). A new key may be added within version 1; a key is never renamed or removed without a new schema version.

```json
{
  "schema": "heim-capability-catalog/1",
  "folder": "C:/dev/acme-heim/agents",
  "sources": [
    {"name": "heim", "path": "heim", "copy_of": "acme/HeimAI@1a2b3c4", "counts": {"agents": 1, "skills": 3}}
  ],
  "objects": [
    {
      "id": "heim/skills/brief", "source": "heim", "layer": "skills", "name": "brief",
      "path": "heim/skills/brief/SKILL.md",
      "version": "0.1.0", "owner": "saga", "description": "…", "status": "",
      "used_by": ["saga"], "agents": ["saga"],
      "uses": {"skills": [], "tools": ["heim/tools/brief"], "templates": ["heim/templates/brief"],
               "guardrails": ["heim/guardrails/one-question-at-a-time"], "apps": []},
      "referenced_by": ["heim/agents/saga"],
      "has_evals": null, "lines": 74, "files": 5
    }
  ],
  "findings": [
    {"kind": "missing-reference", "severity": "error", "object": "heim/skills/x",
     "path": "heim/skills/x/SKILL.md", "detail": "tools: heim/y does not exist"}
  ],
  "summary": {"objects": 42, "by_layer": {"agents": 1, "skills": 3}, "findings": {"missing-reference": 1}}
}
```

- `id` is `<source>/<layer>/<name>` and is how objects refer to each other in `uses` and `referenced_by`.
- `copy_of` is the `source:` line of the source folder's `.source` file, empty for a Heim's own source.
- `used_by` is what the object declares; `agents` is everyone who reaches it (`"*"` for `used_by: [all]`).
- `has_evals` is true or false for guardrails and null for every other layer. `lines` counts the main file; `files` every file of the object.
- `findings` are sorted by severity (error, warning, info), then kind, object and path.

Exit codes: 0 listed, 1 an error finding with `--strict`, 2 no folder or no Heim.
