---
tool: heim-status
used_by: [idun]
skills: [onboarding, manage-capabilities]
tools: [heim-floor, handover-audit]
needs: Python 3.10+
version: 0.1.0
copied_from: whiteport-design-studio, idun/instructions.md (2026-11-19), the context scan and status print as a script
---

# heim-status

Shows what a Heim already has, so Idun shows it instead of redoing it: the floor plan and its folders, the agents it wakes and the capabilities it installs, what it inherits, what is installed under its agents folder (per source and layer, and whether each source is a synced copy), the people with a folder, its policy (the reading list and each part's `Status:`), and the handovers not yet done. Everything is found through the floor plan ([heim-floor](../heim-floor/tool.md)); the handovers are read the way [handover-audit](../handover-audit/tool.md) reads them. Reads only.

## Commands

```bash
python agents/heim/tools/heim-status/status.py [--heim <folder>] [--agents-folder <folder>] [--json]
```

The agents folder is `agents/` at the root in `heim: 1`, and the `agents:` key or `.heimai/agents/` in `heimai: 2`; `--agents-folder` points elsewhere. The woken agents are `agents:` in `heim: 1` and `agents_woken:` in `heimai: 2`.

## Output

Lines for the Heim, its root, floor plan and folders (with `(missing)` after a folder that does not exist), the woken agents, the capabilities and the inheritance; then each source under the agents folder with its layers, and which woken agents are not installed and which installed agents are not woken; the policy; and up to twelve handovers not done, newest first.

`--json` gives `{"schema": "heim-status/1", "name", "kind", "root", "floor_plan", "format", "heimdocs", "folders": {"projects", "sessions", "people", "agents"}, "agents_woken", "capabilities", "inherits", "installed": [{"source", "copy_of", "layers": {"<layer>": [names]}}], "woken_not_installed", "installed_not_woken", "people", "governance": {"folder", "exists", "policies", "parts": [{"name", "copy_of", "status"}]}, "handovers": [{"stamp", "status", "user", "agent", "summary"}]}`.

Tried on 2026-11-19 on a scratch Heim and on two working Heims, one with both the Heim and the WDS agents installed.

Exit codes: 0 shown, 2 no Heim here.
