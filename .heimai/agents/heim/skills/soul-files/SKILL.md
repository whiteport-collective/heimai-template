---
name: soul-files
source: heim
owner: all
description: How every agent knows the person it works with and picks up where the last session ended. Two cabinets of plain markdown in git, one that stays with the work and one that follows the person, read at every start and written as the agent learns, plus an idea bank for loose ideas that might become something one day. Use at every session start and wrap, when the person corrects the agent or states a preference, and when the person tosses out an idea ("idea:" ("idé:"), "what if we …" ("tänk om vi …"), "save this" ("spara det här")).
used_by: [idun, saga, freya, mimir, viska]
version: 0.1.0
templates: [heim/ideas]
references: [sources]
status: draft
---

# Soul files

An agent that has to be told who you are every morning is a tool, not a colleague. The soul files are how every agent in a Heim knows the person: who they are, how they want to work, what they are aiming for and what they are in the middle of. The memory lives in files, not in the model, so any agent in any tool (Claude, Copilot, Codex, OpenClaw) can read it, the person can read and correct it, and it is versioned in git.

Why it is built this way, and what was taken from whom: [sources.md](references/sources.md).

## Two cabinets

| Cabinet | Where | Holds | Follows |
|---|---|---|---|
| **The work cabinet** | `users/<user>/` in the repo | How agents work with the person here, what they work on, what they have delivered | The work: it stays with the repo when the person leaves |
| **The private cabinet** | The private Heim, a private GitHub repo `<name>-heim` (or a local folder when GitHub is not wanted on a work computer); the per-computer file says where | Who the person is, their goals, their state, the people they work with, the personal part of every handover | The person: if they left the company tomorrow, this is what they would take with them (decision 27) |

When the two disagree, the work cabinet wins here, because it is more specific. The private cabinet's `private/` folder is read only by the person's own agent.

## The files

| File | Holds | Written when |
|---|---|---|
| `user.md` | Who the person is: role, background, how to reach them | Onboarding, and when it changes |
| `soul.md` | How agents should work with them: the behavioural contract, built from their own corrections | The person corrects the agent, states a preference, or reacts clearly |
| `identity.md` | Values, voice, what they stand for | Rarely, with the person |
| `objectives.md` | What they are aiming for | When goals are set or change |
| `heartbeat.md` | Their current situation: what is going on right now | As the situation changes |
| `achievements.md` | What they have delivered | When something is delivered |
| `people/` | One file per person they work with, and where things stand | When someone new appears or something changes |
| `sessions/<repo>/<agent>/` | The personal part of every handover (decision 27) | Every wrap |
| `ideas.md` | The idea bank: loose ideas that might become something one day | Whenever an idea is tossed out |

Finance, health, family and relationships never go into soul files or a work repo; they belong to the person's own agent.

## At the start

Read the latest personal parts of the handovers first (decision 27): they already hold the people, the goals, the state and the next step. Then `soul.md`, and the rest as the work needs. Let them shape the first answer: the person's language and register, how they decide, what frustrates them. Don't print what you read.

## Learn as you go

- **A correction, a preference or a clear reaction** is followed from that moment, without being told twice.
- **If it will hold beyond today,** write it at once in the file it belongs to, merged into what is there, and say so in one line: "Noted in soul.md: …".
- **A correction of the method** (how a skill works) is not a fact about the person: it goes to Idun as a proposal, and the agent follows it for the rest of the session.

## The idea bank

Heim's knowledge is ordered: processes, projects, people, decisions. That is a strength, but loose ideas and thoughts have nowhere to go, and they get lost or are pressed into a project too early (2026-11-11). `ideas.md` is the place for them.

- **Two banks:** the person's own in the private cabinet, and the business's in the Heim's `ideas.md`, at the top of its documents folder (`.heimai/` in a `heimai: 2` Heim, `heimdocs/` in an older one). An idea about the work goes to the Heim's, anything else to the person's.
- **Capture without asking.** When the person tosses out an idea, it goes in as one line, in their words, with the date and where it came from, from the template ([ideas.md](../../templates/ideas.md)). Say it in one line: "Saved in the idea bank." No questions, no project, no clarifying.
- **It is never emptied.** Unlike an inbox, nothing has to be processed. An idea stays until someone picks it up, and it can sit for a year.
- **An idea becomes a project only by the person's choice.** Then it is moved to the project's intake, and the line in the bank points there.
- **Surface, don't push.** When the work touches an idea in the bank, an agent may mention it in one line. Saga reads the bank when a new project or a brief starts.

## Guardrails

- **Must not:** write anything about the person they would not want to read; put finance, health, family or relationships in a soul file; read `private/` unless you are the person's own agent; turn an idea into a project or a task without the person.
- **Must:** say in one line what was written and where; merge rather than append, so the files stay short enough to read at every start.

## Not yet

- A health check of the soul files, after Karpathy's LLM Wiki: an agent that reads them now and then for contradictions, stale lines and gaps, and proposes fixes. A candidate for the Watchdog.
- How this skill and the soul interview in onboarding divide the work is settled when the interview is next revised.

## How the work is divided

This skill says what the files are and how an agent learns during a session. The [handover skill](../handover/SKILL.md) reads them at the start and goes through them at the wrap; which learning goes in which file, in which cabinet, is written once, in its [soul-review.md](../handover/references/soul-review.md). The rules on what may be written where are the [memory](../../guardrails/memory.md) guardrail.
