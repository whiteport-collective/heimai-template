---
tool: source-import
used_by: [idun]
skills: [manage-capabilities]
needs: git, Python 3.9+ with PyYAML
---

# source-import

Takes any framework or repo with agents or skills into the Heim (decision 24). The judgment (what to take, where it lands, what to correct, what to ask) is written once in the source's recipe, `agents/<source>/import.yaml`; this tool carries it out the same way every time, so the adaptation survives when the source is updated.

## Commands

```bash
python agents/heim/tools/source-import/source_import.py scan <git-url-or-path> [--ref <sha>]
python agents/heim/tools/source-import/source_import.py run agents/<source>/import.yaml [--update] [--dry-run]
```

- **scan** prints an inventory: skills with their front matter and hooks, the scripts that call out to the network or start processes, the size of each folder, the licence. It is what a recipe is written from.
- **run** clones the source at the commit in `import.lock` (the newest with `--update`), applies the recipe and writes into the recipe's folder: the layers, `source.md`, `import-report.md` and the lock. Files the source no longer produces are removed (tracked in `.import-manifest.json`). `--dry-run` prints the report and writes nothing.

Sources are cached in `~/.heim/cache/sources/` (`HEIM_CACHE` overrides). A source is never executed, only read and copied.

## The recipe

| Key | Does |
|---|---|
| `take` | `from` (in the source) → `to` (in the layers), with `exclude` globs. Text is normalised to LF. |
| `front_matter` | per file: `move` a key into its own file (a hook into `dependencies/`), `drop` keys, `set` keys such as `metadata.used_by` |
| `split` | cut a section by its exact heading into another layer (`to`), with a `title`, an `intro` and the line left behind (`replace_with`) |
| `corrections` | `find`/`replace` or `insert_after`/`insert`, each with its `reason`. The anchor must occur exactly once; otherwise nothing is guessed and it goes to the person |
| `questions` | what only the person can answer; listed in the report, never applied |
| `skipped`, `flags` | what was left out and why; what governance should look at (network, processes, hooks) |

Every generated Markdown file gets a line saying where it came from and that the recipe, not the file, is what to change.

## A person's own skills

The same flow, once (decision 24): run the import, then delete `import.yaml` and `import.lock`. The adapted files are the source from then on.

## After a run

Read `import-report.md`. Corrections whose anchor is gone and the open questions are the person's before the update is committed. The first recipe, for Taste, is not released yet.
