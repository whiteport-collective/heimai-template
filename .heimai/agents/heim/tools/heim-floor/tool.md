---
tool: heim-floor
used_by: [saga, freya, mimir, idun]
skills: [brief, impact-map, project-setup]
needs: Python 3.10+
---

# heim-floor

Finds a Heim and its folders through its floor plan, so no tool carries a fixed path. The root is the nearest folder at or above the current folder (or `--heim`) holding `.heimai/heimai.yaml` (decision 34) or `heim.yaml` (today); when both are there, `.heimai/heimai.yaml` wins. In `heim.yaml` (`heim: 1`) `heimdocs:` is relative to the root (default `.`) and `projects:` (default `projects/`, may be a list), `sessions:` and `governance:` are relative to `heimdocs:`. In `heimai.yaml` (`heimai: 2`) every path is relative to the root and a missing key means `.heimai/<key>/` (heimai-yaml.md). The tools `brief`, `impact-map`, `project-scaffold` and `project-log` import it; it also reads small YAML (PyYAML when installed, else the flat keys of a floor plan and `feature.yaml`).

## Commands

```bash
python agents/heim/tools/heim-floor/floor.py [--heim <folder>]
```

It prints the Heim's name and root, the floor plan it read and its format, the heimdocs, projects, sessions, governance, brand and agents folders relative to the root, with `(missing)` after a folder that does not exist, and the woken agents. The brand folder is `03-brand/` or `brand/` under heimdocs.

**The agents.** In `heimai: 2` the agents folder is `agents:` (default `.heimai/agents/`) and the woken agents are `agents_woken:`; in `heim: 1` the woken agents are `agents:` (decision 32) and the folder is `agents/` at the root or `agents_folder:`. A list under `agents:` in a `heimai: 2` file not yet renamed is still read as the woken agents.

In a tool, from the tool's own folder:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "heim-floor"))
import floor
f = floor.load(heim=args.heim)          # raises floor.FloorError
f.root, f.name, f.heimdocs, f.projects, f.sessions, f.governance, f.agents, f.woken
floor.agents_of(config, fmt)            # (the agents folder or None, the woken agents)
floor.brand_folder(f); floor.templates_dir(__file__); floor.read_yaml(path)
```

Exit codes: 0 found, 2 no Heim or a floor plan that cannot be read.
