---
name: content-not-form
source: heim
applies_to: everything the glass draws from a data file (the impact map, a presentation, highlights)
used_by: [saga, freya]
decided: 2026-11-10 (skill review, the impact map editable in the glass); decision 36
---

# Content, not form

A map, a presentation or a view the glass draws is **changed only through its content**: `impact-map.yaml`, `presentation.md`, `highlights.yaml`. Neither an agent nor a person edits a drawn copy, and no agent draws the map by hand as markdown, HTML or SVG. So every Heim's map looks the same, and a word sharpened in the glass lands in the same field an agent would change.

## Evals

| Case | Expected |
|---|---|
| A fixture map; "Change Lars's top fear to X" | `impact-map.yaml` is edited, `validate.py` runs, and no `.md`, `.html` or `.svg` in `02-impact-map/` is written |
| "Make me an impact map as a picture I can send" | The agent writes the yaml and points to the glass's map; it does not draw an SVG by hand |
| A presentation slide has a typo | `presentation.md` is fixed; a `presentation.html` beside it is never hand-edited |
