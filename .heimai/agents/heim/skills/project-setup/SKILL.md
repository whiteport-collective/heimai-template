---
name: project-setup
source: heim
owner: saga
description: "Starts a new project in a Heim: a short intake, one question at a time, the summary confirmed, then the project's folder with its card and intake. Use when work starts on something that has no project yet; the agent that starts the work creates it."
used_by: [saga, freya, mimir, viska]
version: 0.1.0
copied_from: whiteport-design-studio, skills/project-setup.md (2026-11-19), rewritten by the skill review
tools: [heim/project-scaffold, heim/project-log]
templates: [heim/project]
guardrails: [heim/confirm-before-writing, heim/one-question-at-a-time]
---

# Project setup

Takes "we want to make X" to a project the work can start in. **The agent that starts the work creates the project:** Saga for a brief, Viska for a film, Freya or Mimir when that is where it begins. Idun sets up the Heim itself; she does not create projects.

| Situation | Path |
|---|---|
| No Heim yet (no floor plan: `.heimai/heimai.yaml` or `heim.yaml`) | Idun sets up the Heim first; then this skill |
| A Heim, a new project | This skill, run by the agent that starts the work |
| The project already exists | Show it and where it stands (`scaffold.py scan`); nothing is created |

## Read first

`tools/project-scaffold/scaffold.py scan` shows the Heim, its projects and any open handover that names a project. Whatever the handover, the conversation or the person's material already answers is not asked again.

## The intake

One question per message, only what is still unknown.

1. **Client:** the organization, and who commissions the work.
2. **Name and slug:** the slug is short, lowercase, with hyphens (`summer-campaign`); it becomes the folder name.
3. **What is made:** a website, an app, a film, a campaign, a service, a report.
4. **Why:** the problem or the goal, in a sentence or two.
5. **Known constraints:** an existing brand, a platform already decided, legal or accessibility requirements, a budget.
6. **Languages.**

When it matters: a milestone, references the client likes, integrations already known, and **where the code lives** (a folder in this repo such as `app/`, its own repo, or not decided yet), so Mimir knows where to build.

Then the summary, from [the intake template](../../templates/project/00-intake.md), and the question whether to set it up. A correction is written in and the summary shown again.

## Create

Only on the person's yes: `scaffold.py create <slug> … --yes` writes `<projects>/<slug>/feature.yaml` and `01-brief/00-intake.md`. The project gets more folders later, when its work needs them (decision 26); until then it inherits that part from the Heim (the brand, the people, the impact map). The tool never overwrites, and without `--yes` it only shows what it would write.

The intake is read by the client too: commercial terms and private notes are kept out of it, and no credential is ever written in a file (name the password manager item instead).

`log.py append <slug> --agent <agent> --text "Project set up from the intake. Next: …"`, commit, and **go straight on** with the work the project was created for, from the intake, so the person does not answer the same questions again. When that work is another agent's (usually the brief, Saga's), hand over to that agent with the confirmed intake under `## Done` and the first step under `## Next`.
