---
name: brief
source: heim
owner: saga
description: "Writes the brief, the foundation every later decision is checked against (why it exists, for whom, what success is), together with the person in conversation, plus content and language, visual direction, platform requirements and keyword analysis when they are in scope. Use when a Heim or a project needs its brief, when a brief needs updating, or when someone says \"let's do the brief\" (\"vi gör briefen\")."
used_by: [saga]
version: 0.1.0
copied_from: whiteport-design-studio, skills/product-brief/ (2026-11-19), rewritten by the skill review
tools: [heim/brief, heim/project-log]
templates: [heim/brief]
guardrails: [heim/one-question-at-a-time, heim/material-before-questions, heim/proposals-are-marked, heim/visual-authority]
replaces: [product-brief]
---

# Brief

The brief is what every later decision is checked against. A good one lets Freya design and Mimir build without guessing why, and lets the person recognise their own business in it. It is written together with the person, one question at a time, because its value is the understanding behind it, not the document.

## The suite

The brief is a folder, `01-brief/`, in the Heim or in the project it serves (the Heim's floor plan, `.heimai/heimai.yaml`, says where its folders lie). Its documents are numbered by level (decision 26): 00–09 why, 10–19 what, 20–29 how. A document that is not written leaves its number free; nothing is renumbered, and a new document takes the next free number at its level.

| Document | When |
|---|---|
| `00-intake.md` | Written by [project-setup](../project-setup/SKILL.md) when the project starts |
| `01-brief.md` | Always |
| `10-content-language.md` | Voice, language, audiences or content structure came up |
| `11-visual-direction.md` | Style, references, colour, typography or imagery came up |
| `20-platform-requirements.md` | Something is to be built: platforms, integrations, limits, risks, open questions with an owner each. Strategic boundaries the client can read, not a technical spec |
| `21-keyword-analysis.md` | Search matters: what the target users search for, per language, and which page answers it |
| `presentation.md`, `highlights.yaml` | When the brief is agreed: what the glass shows on top and in each document's tab |

`tools/brief/brief.py new <brief folder>` writes the chosen documents from the templates and `check <brief folder>` lists what is still open. The folder is given from where the session runs: the Heim's is `brief:` in the floor plan (`.heimai/01-brief/` in a new Heim), a project's is `01-brief/` in the project's folder. **The voice and the visual direction are the organization's,** not the project's: the first time they are written, they go in the brand folder (`tone-of-voice.md`, `visual-identity/visual-direction.md`), and `10` and `11` point there and add only what is the project's own. If the brand already has them, read them and discuss only what differs.

## What the brief must cover

Before `01-brief.md` is agreed, Saga and the person share an understanding of each of these. The order is a default, not a script: follow the conversation and come back for what is missing.

| Topic | Understood when Saga can say |
|---|---|
| Vision | Why it exists and what change it creates |
| Positioning | Who it is really for, and why they would choose it over what they do today |
| Business model | How it makes money or is paid for: B2B, B2C or both, and the pricing approach |
| Business customers | Only when others decide and buy: who they are and how they differ from the daily users |
| Target users | Two or three behavioural profiles, with names: what they try to get done and what stops them |
| Concept | What kind of thing it is, in one sentence, and its core structural idea |
| Success | What numbers change twelve months on, and the timeline |
| Alternatives | What people do instead, doing nothing included, and what is genuinely different |
| Constraints | The hard walls: technical, budget, time, regulation |

For the other documents the same holds for what their sections name. For `20`, build on the constraints already known and ask only for what is new.

## How the conversation goes

- **One question per message.** Reflect what you heard in your own words, check it, then go deeper: [discovery.md](references/discovery.md).
- **Material first.** Read everything the person has before the first question, show what it already answers, and ask only about the gaps: [existing-material.md](references/existing-material.md).
- **Opening questions** that tend to work: "Why does this exist, and what does it change?", "Who is it really for, and why would they choose it over what they do today?", "What does success look like a year from now?", "What are the hard walls?"
- **For the other documents:** [content-and-seo.md](references/content-and-seo.md) for `10` and `21`, [visual-direction.md](references/visual-direction.md) for `11`.
- **Draft live.** Write the documents as the understanding grows, so the person sees them take shape; mark what is not agreed with *(draft)* and what nobody has answered with `[needed: …]`.
- **In doubt, say so.** An answer the person was unsure of, or a claim nobody has checked, is written as open, never as fact.

## Drafting from material

When the person asks Saga to propose rather than discover ("write a first draft from this"), she drafts from the material that exists and nothing else: the person's documents, recordings, the Heim's earlier work. Every proposal is marked as hers until the person confirms it. Research on the web may support a proposal, labelled as research, never as the person's view. She shows the draft in pieces the person can react to, and goes back to conversation where a part stays weak.

## Done

The brief is done when the person has read it and agreed that it says what they mean.

- Every topic above is in `01-brief.md`, and each document that came up is written.
- `brief.py check` lists nothing open that the person has not chosen to leave open.
- Nothing in the suite is Saga's idea presented as the person's.
- `presentation.md` and `highlights.yaml` say the main points, so the glass shows the brief at a glance.
- `tools/project-log/log.py` records the brief as agreed, the work is committed, and the impact map is offered next.
