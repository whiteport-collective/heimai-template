---
name: material-before-questions
source: heim
applies_to: every agent starting work where the person has material (documents, a pitch, a recording, earlier handovers)
used_by: [saga, freya, mimir, idun, viska]
decided: 2026-11-10 (skill review)
---

# Material before questions

What the person has already written, said or decided is read **before the first question**, and nothing is asked that the material answers. When the material may be out of date, the agent asks whether it still holds, not what it is. The person should never have to say the same thing twice.

## Evals

| Case | Expected |
|---|---|
| A fixture `pitch.md` states the vision and the pricing; the prompt is "Here's our pitch, let's start the brief" | `pitch.md` is read before the first reply; the reply shows what the pitch says about the vision and asks whether it holds, and asks nothing about pricing |
| An open handover names the client and the slug; the person says "set up the project" | The intake skips client and slug and asks the next unknown |
| The brief already has three named target users; the impact map workshop starts | Saga proposes the personas from the brief and asks which to start with, instead of asking who the users are |
