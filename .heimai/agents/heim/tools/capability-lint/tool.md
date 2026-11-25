---
tool: capability-lint
used_by: [idun]
skills: [manage-capabilities]
tools: [capability-catalog]
needs: Python 3.10+, PyYAML (recommended), capability-catalog beside it
version: 0.1.0
copied_from: whiteport-design-studio, idun/references/quality-criteria.md (2026-11-19), its mechanical checks as a script; the BMad-shaped criteria dropped
---

# capability-lint

Checks every agent and capability in an agents folder against Heim's conventions, the mechanical half of an audit. It replaces the WDS audit checklist, which required an XML workflow in every skill and allowed 500 lines: nothing here asks for a step format, and size is guidance, not a gate. It uses `capability-catalog`'s scan, so it sees the same objects and links. Reads only; it fixes nothing. The judgment half is the [capability review](../../agents/idun/subagents/capability-review.md).

## Commands

```bash
python agents/heim/tools/capability-lint/lint.py                                  # the Heim's agents folder
python agents/heim/tools/capability-lint/lint.py agents/ --only heim/skills/governance
python agents/heim/tools/capability-lint/lint.py agents/ --errors
python agents/heim/tools/capability-lint/lint.py agents/ --json
```

## Rules

| Rule | Level | Checks |
|---|---|---|
| `front-matter` | error | a persona, skill, tool, app, dependency or guardrail has front matter |
| `required-keys` | error (warning for tools) | skill: `name`, `description`, `used_by` (or `owner`), `version`; persona: `name`, `description`, `skills`, `guardrails`; guardrail: `name`, `applies_to`; dependency: `name`, `for`; app: `name`; tool: `tool`, `used_by`, `skills` |
| `guardrail-evals` | error | every guardrail ends with an `## Evals` table with at least one case |
| `wds-path` | error | no file points into WDS's agents folder |
| `secret` | error | nothing that looks like a GitHub token, an API key, a Slack token, an AWS key or a private key |
| `missing-reference` | error | from the catalog: a reference to an object that does not exist |
| `trigger-phrases` | warning | a skill's description says when to use it ("Use when …") or quotes the words people say |
| `size` | warning | a skill above about 150 lines, a persona above about 80, a reference above 250 |
| `name-matches-folder` | warning | `name:` (or `tool:`) is the folder's name |
| `bmad-markers` | warning | no BMad workflow tags or `{output_folder}` placeholders in prose (code spans and blocks are skipped) |
| `calm-rules` | warning | three or more shouted words (`MUST`, `NEVER`, `ALWAYS` …) in a file: write the rule and its reason instead |
| `dead-link` | warning | a relative link in a markdown file leads to a file that exists |
| `review-by-passed` | warning | a `review_by:` date in any front matter of the object has passed |
| `asymmetric`, `front-matter-not-yaml`, `used-by-names-a-skill` | warning | from the catalog |

## Output

Per object, each finding with its level, rule, message and `path:line`, then `N objects checked: E errors, W warnings.` `--json` gives `{"schema": "heim-capability-lint/1", "folder", "errors", "warnings", "results": [{"object", "level", "rule", "message", "line", "path"}]}`.

Exit codes: 0 no errors, 1 errors found, 2 no folder or no Heim.
