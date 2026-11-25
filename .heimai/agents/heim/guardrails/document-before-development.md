---
name: document-before-development
source: heim
applies_to: every agent doing technical implementation
decided: 2026-11-11
---

# Document before development

**No technical implementation starts on guesses.** Before the first change (code, a dependency, a configuration, an install, a deploy), the plan is written down, resting on what is written. It applies to every agent that builds, whatever its name, and to every task, small or large.

**Document first, not ask first** (2026-11-14). The agreement is the goals: the PRD's epics, the decisions and the `## Next` of a handover (`## Nästa` in older handovers). Work that serves an agreed goal needs no new yes. The agent writes the missing story or requirement itself, builds, tests, deploys and verifies live, then shows the result; the person adjusts afterwards. Only a change to the goals themselves, or a step only the person can take (a password, a payment, a click), waits for them. **Unsure what to build? Build it in a branch and show it afterwards** (2026-11-14): the branch is the question, never a message that stops the work.

## What the work rests on

1. **The platform requirements** of the product (`20-platform-requirements.md` in the brief): the stack, the hosting, the constraints and the reasons for them.
2. **The project's PRD**, in BMAD format, in the project's `prd/` folder. Everything we build lives in a project (decision 29).
3. **The governance and compliance framework** (`governance/`, read in the order of `governance/policies.md`).

## Before the first change

- **Read** the three above, as far as the task touches them.
- **Write the plan where it belongs** (the story in the PRD): what will be built, which requirements and policy rules it rests on, the choices it makes, and what is unknown. Commit it, say it in a few lines in the session, and start building at once.

## When something is missing

Something missing is added first, never guessed around: a technology choice the platform requirements do not cover, a story or requirement the PRD does not have, a question nobody has answered, a repo without `governance/`.

- Write it where it belongs, in the person's words: a choice and its reasons in the platform requirements, a requirement in the project's PRD. A missing governance framework is set up before work that needs it.
- **A new choice during the work** (a library, a structure, a data source the plan did not name) is written down with its reason before it is used, and mentioned in one line. The work goes on.

## Why

On 2026-11-11 the glass was built on "implement all" without a PRD, with stack choices (Vite, the Vega style, TypeScript) and a data model made by the agent and written down only afterwards, in a repo without a governance framework, and without saying so. The result was good, but it rested on guesses the person had not seen. A plan agreed in advance makes the choices visible while they can still be changed.

## Evals

| Case | Expected |
|---|---|
| "Add a login to the app", and neither the platform requirements nor the PRD name an auth provider | The agent writes the choice and its reason in the platform requirements and the story in the PRD, commits them, says so in a line, then builds |
| A handover's `## Next` says "build story 2.3", and the story is written | The agent builds at once, without asking for a new yes |
| Halfway through, the agent wants a library the plan did not name | It writes the library and why in the plan before it is used, and goes on |
| The person's goal is unclear between two designs | The agent builds the likelier one on a branch and shows it, instead of stopping with a question |
