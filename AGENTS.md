# My Heim: instructions for all AI agents

Applies to every agent working in this Heim: Claude, Copilot, Codex and others. The files for each tool (`CLAUDE.md`, `.claude/`, `.github/`, `.agents/`) only point here and into `agents/`; nothing else goes in them.

A Heim made from HeimAI's template; the glass names it when it is made

## Where things are

`heim.yaml` is the floor plan: it says where every folder lies, which agents are woken and what the Heim inherits. Find folders through it, never by a fixed path.

## Sessions

<!-- heim:session  The always-loaded session lines go here (start, during, end). heim-sync writes them; never by hand. -->
<!-- /heim:session -->

## Agents

The agents woken in this Heim. Their content lies in `agents/<source>/agents/<name>/`; Idun keeps this table.

| Agent | Source | Owns | Start |
|---|---|---|---|
| Idun | heim | Sets up Heims and the people in them, keeps the agents and their capabilities, and helps a business govern its work with AI | `/idun` |

## Rules

- A private Heim has no governance: the person's soul files are the rules, and Heim's defaults are offered as advice with the reason first.
- Everything in this repo is shared and professional. What is about one person goes in their private Heim.
- No secrets in any file. Name the password manager item, never the value.
- Folder and file names in lowercase.
