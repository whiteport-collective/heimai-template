---
tool: brief
used_by: [saga]
skills: [brief]
tools: [heim/heim-floor]
needs: Python 3.10+
---

# brief

Starts a brief from the suite templates and checks what is still open in one. `new` copies the chosen suite documents (decision 26: why 00-09, what 10-19, how 20-29) into a brief folder with the project, date, person, language and brand path filled in, and never overwrites a file. `check` lists, per document, what nobody has answered yet; it works on any brief, also one not made from the templates. The Heim and its brand folder are found through the floor plan ([heim-floor](../heim-floor/tool.md)); the templates in `templates/brief/` beside `tools/`. This is story 5.1 in the PRD.

## Commands

```bash
python agents/heim/tools/brief/brief.py new 01-brief --docs 01,10,11,20,21 --project "Sjöbod" --person "Åsa" --lang sv
python agents/heim/tools/brief/brief.py new 01-brief --brand
python agents/heim/tools/brief/brief.py new 01-brief --extra "Audiences and voices" --level what
python agents/heim/tools/brief/brief.py check 01-brief
```

**`new <brief-folder>`** writes the documents in `--docs` (default `01`) and always `presentation.md` and `highlights.yaml` when they are missing. It fills:

- `{{project}}`: `--project`, else `feature:` in the project's `feature.yaml`, else the Heim's name.
- `{{date}}`: today. `{{person}}`: `--person`, else `[needed: the person's name]`. `{{lang}}`: `--lang`, else `language:` in the floor plan, else `en`.
- `{{brand}}`: the brand folder relative to the brief folder: `--brand-folder`, else `03-brand/` or `brand/` under heimdocs, else `../03-brand/`.

`--brand` also writes the brand's `tone-of-voice.md` and `visual-identity/visual-direction.md` with `{{organization}}` as the Heim's `name:`; with no brand folder it makes `03-brand/` under heimdocs. `--extra "Title" --level why|what|how` adds `NN-title.md` with the next free number at that level, above the suite's own numbers (02, 12, 22 in an empty folder).

It prints the brief folder, the Heim, the brand path, and one line per file: `wrote` or `skipped (exists, left as it is)`.

**`check <brief-folder>`** reads every `.md` and `.yaml` in the folder (personal drafts `*.draft-<user>.md` are skipped and named) and prints per document:

- the sections whose body is empty or only `[needed: …]`, with their line;
- every `[needed: …]` marker and leftover `{{…}}` placeholder, with its line;
- the number of `*(draft)*` marks, which are counted but do not make the brief open.

Then where each `10-` and `11-` document points for the brand, and whether that folder exists, and a summary line ending `Open.` or `Nothing open.`

## Exit codes

- `new`: 0 done (also when everything was skipped), 2 on an error (unknown document number, no templates, `--brand` outside a Heim).
- `check`: 0 nothing open, 1 something open (an empty section, a marker, a placeholder or a missing brand folder), 2 on an error.
