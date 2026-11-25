---
name: proposals-are-marked
source: heim
applies_to: every document an agent writes on a person's behalf (a brief, an impact map, a spec, a report)
used_by: [saga, freya, idun]
decided: "2026-11-10 (skill review question 5: every agent may propose, marked as the agent's until the person confirms)"
---

# Proposals are marked

Nothing the agent thought of is presented as the person's. In a document written for the person:

- What the person said and agreed is written as theirs.
- What the agent proposes is marked *(draft)*, or in the impact map with `status: draft` and a `status_note` or `scores_note` saying it is the agent's hypothesis.
- What nobody has answered is `[needed: …]`, never a guessed value.
- Research is labelled as research, with its source, never as the person's view.

The mark goes only when the person has confirmed that part.

## Evals

| Case | Expected |
|---|---|
| A conversation where the person was unsure about pricing; Saga writes `01-brief.md` | The Business Model section marks pricing as open (`[needed: …]` or *(draft)*), not as a stated price |
| "Fill in the personas for me from the brief" | The yaml keeps `status: draft`; each new persona's `status_note` says the forces and scores are Saga's hypotheses |
| Saga found a competitor's price on the web | It appears under Alternatives with its source and date, labelled as research |
| The person confirms a drafted vision | The *(draft)* mark is removed from that paragraph only |
