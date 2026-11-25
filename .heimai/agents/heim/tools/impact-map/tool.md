---
tool: impact-map
used_by: [saga]
skills: [impact-map]
tools: [heim/heim-floor]
needs: Python 3.10+, PyYAML
---

# impact-map

Checks an impact map's content in `impact-map.yaml` and ranks each persona's driving forces, so the map can be trusted before the glass draws it (open-glass FR34). It replaces the checks and the one threshold definition of WDS's trigger-map render; there is no render tool, since the glass draws the map from the file. Without a path it checks `*impact-map/impact-map.yaml` under the Heim's heimdocs, found through the floor plan ([heim-floor](../heim-floor/tool.md)). This is story 5.1 in the PRD.

## Commands

```bash
python agents/heim/tools/impact-map/validate.py 02-impact-map
python agents/heim/tools/impact-map/validate.py 02-impact-map/impact-map.yaml
python agents/heim/tools/impact-map/validate.py --heim <folder>
```

## What it checks

Errors make the map invalid:

- the YAML does not parse;
- `goals` missing or empty; a goal without `id`, `name` or `objectives`; an id used twice; an objective without `target`;
- `personas` missing or empty; a persona without `name`, `priority`, `goals` or `forces`, or naming a goal id that does not exist;
- a force whose `dir` is not `+` or `-`, without `what`, `why` or `when`, or whose `f`, `i` or `fit` is not a whole number 1-5.

Warnings do not:

- more than three goals, or more than three objectives in a goal: above the default of three, not an error;
- a target that is still `[needed: …]`;
- fewer than three or more than five forces in a direction;
- a `{{placeholder}}` left from the template.

## What it prints

The project, its status and how many goals and personas; the errors; the warnings; every `[needed: …]` marker with where it is (`goals[G1].objectives[0].target`); then per persona its forces ranked by `f + i + fit`, labelled with the one threshold definition at the top of the script: 13-15 high, 10-12 medium, below 10 low. The last line is `Result: valid` or `Result: INVALID` with the counts.

## Exit codes

0 valid (warnings allowed), 1 invalid, 2 the file cannot be read or PyYAML is missing.
