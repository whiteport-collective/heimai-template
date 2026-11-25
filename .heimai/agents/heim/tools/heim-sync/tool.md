---
tool: heim-sync
used_by: [idun]
skills: [manage-capabilities]
tools: [heim-floor]
needs: Python 3.10+, PyYAML
---

# heim-sync

Copies a Heim's woken agents and the capabilities they use into the Heim, in full, and writes the pointers its AI hosts read and the hooks its dependencies declare. A Heim then runs its agents from its own repo alone, which is what Claude on the phone and the web needs (decision 24, the bullets of 2026-11-19; decision 32: only what is woken). This is story 5.6 in the PRD.

## Commands

```bash
python agents/heim/tools/heim-sync/sync.py [dry-run] [--heim <folder>] [--from <sources>]
python agents/heim/tools/heim-sync/sync.py run --yes [--heim <folder>] [--from <sources>]
python agents/heim/tools/heim-sync/sync.py status [--heim <folder>] [--from <sources>]
```

- **`dry-run`** (the default) prints the plan and writes nothing.
- **`run --yes`** writes it and prints the receipt: what was added, replaced and removed, and every warning. Without `--yes` it prints the plan and stops.
- **`status`** shows what is installed, from which source, version and commit, what the Heim overrides, what was edited in a copy, and what a sync would change now.
- **`--heim`**: the Heim. Defaults to the nearest Heim at or above the current folder, found by [heim-floor](../heim-floor/tool.md).
- **`--from`**: the sources folder, one folder per source (`heim/`, `taste/`). That is the `agents/` folder of a clone of HeimAI. Without `--from`, `<dev_root>/Heim/HeimAI/agents/` is used if it exists (`dev_root:` in `~/.wds/me.md`). How a Heim gets and updates its agents, step by step: [Get and update your agents](https://github.com/whiteport-collective/HeimAI/blob/main/docs/set-up/get-and-update-your-agents.md).

## Policy

The rules are the Heim's governance framework, not this file: a sync into another repo asks first, and a dry run does not; a copy is a mirror of its source, `.source` shows its version, and a copy is never edited. In a business's Heim they are in the folder its floor plan names with `governance:`. The tool enforces them:

- `run` writes nothing without `--yes`, and the agent passes `--yes` only after the person has seen the dry run and said yes. Unknown options stop with the help text, and never sync.
- **The source must be reviewed content**: its checkout on the default branch, with nothing uncommitted under the sources folder. Otherwise `run` stops; `--allow-unreleased` is for trying a branch on a scratch Heim.
- **A reference that does not resolve stops `run`** and is listed in the dry run. `--allow-missing` copies what resolves and records the rest in `.source` under `missing:`.
- **A copy edited in place stops `run`,** and so does a file added to it. The change belongs in `customizations/`, at the same path, or upstream. `--discard-edits` overwrites it.

## What it copies

The floor plan says what is woken: in `heim.yaml` (`heim: 1`) `agents:` (a list of agents), in `.heimai/heimai.yaml` (`heimai: 2`) `agents_woken:`, since there `agents:` is the agents folder (heimai-yaml.md, Renamed keys); and `capabilities:` (skills woken without an agent). Both are read through [heim-floor](../heim-floor/tool.md). From each one the tool follows the front matter:

| Object | Follows |
|---|---|
| agent (`agents/<name>/persona.md`) | `skills`, `guardrails`, `apps`, `tools`, `templates` |
| skill (`skills/<name>/SKILL.md`) | `tools`, `templates`, `guardrails`, `references` (also another skill's: `bugreport-anything/business-impact`); `apps` only when a Heim app has the name, else it is a program (layer 7) |
| tool (`tools/<name>/`), app (`apps/<name>/`) | `tools`, `templates`, `guardrails` |
| dependencies (`dependencies/*.md`) | taken when `for:` names a taken object; without `for:`, when anything from its source is taken |

`used_by:` and a tool's `skills:` point backwards and are never followed. A reference with a source prefix (`taste/design-taste-frontend`) comes from that source; without one it means the referrer's own source when that is not heim, then heim, then the Heim's own source. A tool that loads another from beside it (`parent / "heim-floor"`) without listing it in `tools:` gets it anyway, with a note asking for the front matter to say so. Agents, skills, tools and apps are copied as whole folders, templates and guardrails as the file or folder named. `__pycache__` and `.pyc` are never copied.

## Where it writes

- **One folder per source** in the Heim's agents folder: `agents/heim/`, `agents/taste/`. The agents folder is `agents:` in a `heimai: 2` floor plan, default `.heimai/agents/` (decision 34); in `heim: 1`, `agents/` at the root, or the path in `agents_folder:`. Each folder is replaced whole by what is taken (files not taken are removed) and gets a `.source`: the source repo, path, commit, branch, version (the tag at the commit, else `unreleased`), the date, the objects, anything missing, and a hash of every file, which is how the next sync sees an edited copy or an upstream change. A source folder nothing woken uses any more is removed, if heim-sync wrote its `.source`.
- **Never touched:** a folder without `.source` that has files (a source or a hand-made folder: the sync stops), a folder whose `.source` it did not write and that is not one of its sources (the WDS folder a Heim had before the switch, which the switch removes, not the sync), the Heim's own source and `agents/heim/customizations/`. It deletes nothing outside its folders except pointer files carrying its marker.
- **Pointers**, only for woken agents, their skills and `capabilities:`:

  | Host | Agent | Skill |
  |---|---|---|
  | Claude Code | `.claude/commands/<agent>.md` | `.claude/skills/<skill>/SKILL.md` |
  | Codex | `.agents/skills/<agent>/SKILL.md` | `.agents/skills/<skill>/SKILL.md` |
  | Copilot | `.github/agents/<agent>.agent.md`, `.github/prompts/<agent>.prompt.md` | |

  An agent's pointer says to read its persona (and its customization after it, if there is one) and follow the session start in `AGENTS.md`. A skill's pointer carries the skill's real `name` and `description`, so the host knows when to use it, and one line saying where the skill lies. Each carries `Generated by heim-sync. Change the source, never this file.` A pointer is replaced when it carries that marker, the WDS `/sync-skills` marker, or `Adapter for Heim's`; a hand-written file is never replaced, only reported. A pointer for something no longer woken is removed when it carries the heim-sync marker or the older Heim marker, or is a WDS pointer to an agent; WDS pointers to skills (`wrap`, `handoff`, `sync-skills`) stay for the switch. A woken agent missing from the sources keeps its old pointer.
- **Commands a skill keeps:** a skill with `commands: [wrap, handoff]` in its front matter gets `.claude/commands/<command>.md`, `.github/prompts/<command>.prompt.md` and `.agents/skills/<command>/SKILL.md`, each saying to read the skill and follow that section. They replace the WDS pointers of the same name, so a Heim keeps `/wrap` and `/handoff` through the handover skill; `sync-skills` stays for the switch.
- **Hooks** in `.claude/settings.json`, from the dependencies that are taken. Hooks heim-sync did not write stay as they are.
- **The session lines in `AGENTS.md`** (story 5.5), when a woken agent uses the handover skill: `templates/handover/session-lines.md`, with the Heim's agents folder, sessions folder, repo cabinet (`users:`) and floor plan file filled in, written between `<!-- heim:session … -->` and `<!-- /heim:session -->`. Only that block is written; the rest of `AGENTS.md` is the Heim's. A lone start marker (Idun's template before 2026-11-20) gets the block in its place. An `AGENTS.md` without the marker is left alone and the dry run says so: the marker goes where the person wants the lines.

## Customizations

A Heim changes what the sources deliver in one place, beside the layers: `agents/heim/customizations/`, at the same paths as the synced files (story 5.10). The sync never writes into it, never removes from it and never hashes it, so nothing in it is lost at an update. Changes to the person's style go in their soul file and the project's ways in its files; a customization is the exception, for how one agent or skill works in this repo alone ([soul review](../../skills/handover/references/soul-review.md)).

- **`additions.md` adds.** `customizations/agents/saga/additions.md` or `customizations/skills/brief/additions.md` is read right after the synced persona or skill, and wins where they differ. The synced file keeps updating underneath. A file object adds with `<name>.additions.<ext>` beside it (`templates/meeting-report.additions.md`).
- **The same name replaces.** `customizations/templates/meeting-report.md` replaces the synced one; a replaced persona or `SKILL.md` gets the pointers. When the synced file changes upstream under a replacement, `dry-run`, `run` and `status` say so, with the diff size.
- **A guardrail is only added to.** A replacement in `customizations/guardrails/` stops the run.
- **The folder is the list.** The pointers name the customization, and the session lines in `AGENTS.md` end with what is customized, so every agent sees it at the start and when it moves to another repo. A customization may name tools, guardrails and other objects in its front matter; they are taken like the synced file's.
- **What stops a run:** a file in `customizations/` that matches nothing in the sources (a typo, or something only this Heim has), a replaced guardrail, a file edited in or added to the synced copy (move it into `customizations/`, or `--discard-edits`), and a file in the Heim's own source at a synced path, which would change nothing. A customization of something not woken here is only noted.
- **Movable.** A customization folder copied into another Heim works there with no other change.
- **An app is customized at the points it declares** (story 5.11), since code reads no addition: `customizations/apps/<app>/` may hold only the files of the points in its `app.md` `customizable:` (`settings.yaml`, `theme.css` and `assets/`, `texts/`, `plugins/`), else the run stops. A file at a synced path is a fork: allowed only under the app's `forkable:` paths, said at every run (with the upstream diff when the original changed), and a stop anywhere else, since the app would never read it.

What only this Heim has (an agent, skill or tool of its own) is a source of its own, `agents/<own>/`, named by `own_source:` in the floor plan (default `local`), with the same layers. It can be woken; it gets pointers and nothing is copied. A change meant for every Heim is proposed to HeimAI as an issue (its CONTRIBUTING.md), and comes back in a release.

## Hooks in a dependencies file

A dependencies file declares hooks in its front matter, in the shape of Claude Code's `hooks` setting (event, then matcher groups):

```yaml
---
name: taste-gate
for: [design-taste-frontend]
hooks:
  Stop:
    - hooks:
        - type: command
          command: node agents/taste/tools/taste-kit/scripts/gate.mjs --hook claude
          timeout: 600
---
```

A fenced `yaml` block with a top-level `hooks:` in the body is read as well, which is how Taste's `taste-gate-hook.md` writes it today. heim-sync appends `# heim-sync: <source>/dependencies/<file>` to each command it writes, and on every run removes the commands carrying that mark and adds the current ones, so a hook that is no longer needed goes away. The dry run prints each command in full with `--verbose`: a hook runs a shell command on its own, so the person's yes to the run is their yes to the hook.

## Later

- **The GitHub Action** (decision 19): the same script run in each Heim's repo by a workflow shipped with the template, fetching HeimAI at a release tag, opening a pull request with the receipt as its text instead of writing on a branch. Started by "the one who made the change" after a release, or by the person from the glass or on a schedule.
- `install-commands`: pointers in the person's own `~/.claude/commands/` that find the session's repo and read its copy (decision 24).
- Writing a Heim's permissions from `dependencies/` (Saga's lists what to allow).
