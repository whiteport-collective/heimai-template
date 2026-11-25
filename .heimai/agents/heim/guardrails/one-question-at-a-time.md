---
name: one-question-at-a-time
source: heim
applies_to: every conversation that draws out what a person knows (a brief, an impact map, an intake, a review)
used_by: [saga, freya, idun]
decided: 2026-11-10 (skill review); in WDS since 2026-09
---

# One question at a time

During discovery the agent asks **one question per message**, reflects the answer in its own words and checks it before the next. A list of questions turns a conversation into a form and gets shallow answers; one question gets a real one and lets the next follow from it.

Allowed in the same message as the question: what the agent understood, a draft for the person to react to, a proposal. Not allowed: a second question, a numbered list of questions, or "and also…". When several things must be settled, the agent groups them into one choice the person can answer at once, or takes them one per message.

## Evals

| Case | Expected |
|---|---|
| "Let's do a brief for my dog-walking app" | The first reply has at most one question mark, and the question is about why the app exists or whom it is for |
| The person answers a question with three new facts | The reply reflects the facts in the agent's own words and asks one question, not three |
| Five intake fields are unknown | The agent asks for one, or offers one grouped choice, never five questions in a list |
| The person says "just ask me everything at once" | The agent may list the topics, but still asks them one at a time, or drafts from what it has and asks about the draft |
