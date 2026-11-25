---
name: impact-map
source: heim
owner: saga
description: "Builds the impact map with the person in workshops: the business goals with measurable objectives, the people the goals depend on, and the forces that drive those people toward and away. Use when the brief exists and the work needs to know whom it serves and what drives them, when the map needs updating, or when someone says \"let's do the impact map\" (\"vi gör effektkartan\")."
used_by: [saga]
version: 0.1.0
copied_from: whiteport-design-studio, skills/trigger-map/ (2026-11-19), rewritten as the impact map by the skill review
tools: [heim/impact-map, heim/project-log]
templates: [heim/impact-map]
guardrails: [heim/one-question-at-a-time, heim/proposals-are-marked, heim/content-not-form, heim/needs-not-solutions]
replaces: [trigger-map]
---

# Impact map

The impact map connects what the organization wants to what drives the people it depends on: the goals, the people who reach them, and the forces that pull those people forward or push them away. Freya designs from it, and every later choice can be checked against it: which person does this serve, and which force does it answer? It is built in workshops with the person, because the forces have to be recognised, not invented.

It needs the brief (`01-brief/01-brief.md`). Without one, start there.

## Content and form are kept apart

The content lives in one file, `02-impact-map/impact-map.yaml`, in the format of [the template](../../templates/impact-map.yaml). The glass draws the map from it (zoomable, a card per goal, persona and force), so every Heim's map looks the same and nobody draws one by hand. Saga changes the map only in the yaml, and a person who sharpens a word in the glass changes the same field. `tools/impact-map/validate.py` checks the file after every change: the goals, the objectives' targets, the personas' fields, the forces and their scores, every `[needed: …]`, and the forces ranked.

## The workshops

One workshop at a time, one question at a time. Write each result into the yaml when the person confirms it, validate, and commit, so they watch the map grow in the glass.

| Workshop | Done when the yaml holds |
|---|---|
| 1. Goals | The vision in a sentence or two, and the goals, the main outcome first, then what makes it possible. Each goal has measurable objectives with a target. Three goals with three objectives is the default, not a rule. |
| 2 to 4. One persona each | A name that sticks (a first name and a role), priority, who they are, what drives them, how it feels when the problem hits, how they find and decide, three to five forces toward and three to five away, each as *what*, *why* and *when* and scored, and which goals the persona serves. The persona with the most strategic weight first. |

The features are not on the map. When there are screens, Freya tags each one with the usage goal it serves, so the map stays about people and the design is checked against it.

**Openings that tend to work:** "What does winning look like for you, as a picture rather than a number?", "What has to be true for that to happen?", "How will you know you got there?", "Tell me about [Name]'s day", "What would make [Name] feel they have won?", "What is [Name] most afraid of here?" Follow the person rather than the list. The method, with examples: [method.md](references/method.md).

## What makes it good

- **Only what came out of the conversation.** Where Saga proposes from the material before a workshop, the persona's `status_note` and the map's `scores_note` say so, and the person confirms or changes it.
- **Forces are needs, not solutions.** A feature named as a force ("they want a template library") is turned back into the need behind it.
- **Forces are specific.** "Figures he can't check, when he reads the deck, because one he can't check makes him doubt them all" says something "wants trust" never does.
- **Scores are honest.** A 15 is rare; the ranking decides what Freya designs for first.
- **No trigger points or success states.** They belong in Freya's scenarios.

## Drafting from material

Asked to propose a map rather than build it in workshops, Saga drafts from the brief and the material that exists, with `status: draft` and every persona's `status_note` saying the forces and scores are her hypotheses. She walks the person through it one persona at a time and goes back to a workshop where a part stays weak.

## Done

- `impact-map.yaml` holds every workshop and `validate` passes; any warning left is one the person chose.
- The person has gone through the map in the glass and agreed; `status: agreed`.
- `tools/project-log/log.py` records the map as agreed, the work is committed, and Saga offers the handover to Freya.
