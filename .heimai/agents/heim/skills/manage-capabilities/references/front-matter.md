# Front matter, layer by layer

Every object says which agents use it and what it uses, so the catalog can draw an agent with its layers under it and the glass can show it. This is the one place the keys are written. Values are YAML: quote a value that holds `: ` (a colon and a space), or the glass cannot read it.

References between objects are written `heim/<name>` (another layer is told by the key) or `<source>/<name>` for another source; within the same source a bare name is enough in a persona's `skills:` and `guardrails:`.

## Persona: `agents/<name>/persona.md`

```yaml
name: saga
source: heim
description: <who, in one or two sentences>
version: 0.1.0
copied_from: <repo>, <path> (<date>), <how it was changed>    # only for something taken from elsewhere
skills: [brief, impact-map, project-setup]
guardrails: [one-question-at-a-time, confirm-before-writing]
apps: []
```

Subagents and references lie beside the persona, in `agents/<name>/`. A subagent has `name`, `source`, `used_by`, `skills`, `version`.

## Skill: `skills/<name>/SKILL.md`

```yaml
name: brief                      # the folder's name
source: heim
owner: saga                      # the agent that keeps it; "all" when nobody owns it alone
description: <what it does>. Use when <the situations, and the words people say>.
used_by: [saga]                  # every agent that uses it
version: 0.1.0
copied_from: <repo>, <path> (<date>), <how it was changed>
tools: [heim/brief, heim/project-log]
templates: [heim/brief]
guardrails: [heim/one-question-at-a-time]
replaces: [product-brief]        # older names it answers to
```

`references/` beside `SKILL.md`, one level deep. A reference with dated facts has `checked:` and `review_by:` (YYYY-MM-DD) in its own front matter; `capability-lint` warns when `review_by:` has passed.

## Tool: `tools/<name>/tool.md`

```yaml
tool: brief
used_by: [saga]                  # agents
skills: [brief]                  # the skills that use it; each of them lists the tool in tools:
needs: Python 3.10+
version: 0.1.0
status: specified                # only while the tool is a specification, not yet built
```

The script lies beside `tool.md`. A tool finds a Heim's folders through `heim-floor`, never by a fixed path.

## Template: `templates/<name>` or `templates/<name>/`

No front matter of its own: a template is content that is copied, and its own front matter, if any, belongs to the copy. Who uses it is read from the skills that list it in `templates:`.

## App: `apps/<name>/app.md`

`name`, `source`, `used_by`, `version`, and how it is started (`start:`, `url:`). An app is something the person opens and works in; a program a tool calls is a dependency.

**Customizable** (story 5.11): an app a Heim may make its own lists its points, `customizable: [settings, theme, texts, plugins]` (any of the four), and, only when it reads a copy of its own files from the customization, `forkable: [static/]`. The app reads `agents/heim/customizations/apps/<name>/` at start and runs unchanged without it; heim-sync stops on a file there that is none of the declared points. The points' files are `settings.yaml`, `theme.css` with `assets/`, `texts/<lang>.json` and `plugins/<plugin>/`. The app's `app.md` has a section *Customizing it* with the keys, the slots and *Changes to the contract*: a key or slot is removed only with a line there. Viska Studio, an app in HeimAI's development, is the first example; it is not released yet.

## Automation: `automations/<name>/`

`name`, `source`, `used_by`, `skills`, `tools`, and when it runs (`schedule:`). It never does what needs a person's yes.

## Dependencies: `dependencies/<agent-or-capability>.md`

```yaml
name: saga
source: heim
for: [saga, brief, impact-map]
```

The body is a table: what is needed, for what, and how to check it; then the permissions the host should allow.

## Guardrail: `guardrails/<name>.md`

```yaml
name: confirm-before-writing
source: heim
applies_to: <who and when>
used_by: [saga, freya, mimir, idun]
decided: <who, date, where>
```

The body states the rule and its reason, calmly, once, and ends with `## Evals`: a table with at least one case (a prompt or a fixture) and what is expected, concrete enough for a grader to check.
