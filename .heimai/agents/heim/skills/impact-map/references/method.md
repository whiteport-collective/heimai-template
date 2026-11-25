# The impact map: method

Read it before a workshop and when a goal, a persona or a force will not come out right. The format is [the template](../../../templates/impact-map.yaml); the examples here are fictional.

## Goals and objectives

A **goal** is a direction that lasts and is worth wanting; an **objective** is how progress toward it is measured, with a number and a date.

- **Order:** the main outcome first ("become profitable"), then the goals that make it possible ("happier customers", "work smarter").
- **A metric is not a goal.** "40 % fewer phone calls" is an objective under "work smarter"; "first page on Google" is an objective under "a steady flow of customers".
- **Each objective belongs to its goal.** Work–life balance goes under working smarter, not under profit.
- **Test:** would the goals still hold if the tactics changed? Is reaching them exciting?
- A target nobody has set yet is written `[needed: number and date]`, not guessed.

```yaml
- id: G2
  name: Happier customers
  why: Customers who come back cost nothing to find
  objectives:
  - {objective: Rating on the map services, target: "4.8 or more by June", short: rating 4.8}
  - {objective: Customers who come back within a year, target: "70 %", short: 70 % return}
```

## Personas

Deep, not demographic. "Johan, 32, consultant" informs nothing; what he is trying to do, what he fears, and when, does.

- **Two or three, deeply understood,** beat ten sketched. More than four dilutes the focus.
- **Usage goals, not life goals.** In life Hanna wants to be a respected dog trainer; *when she books a walker* she wants to know her dog is safe. Design for the goal active in this use, informed by the life goal.
- **The context decides.** The same person has different active goals when comparing prices and when showing off their work; don't mix them.
- **How they find and decide** (`usage:` in the yaml): where they first hear of it, what makes them arrive, how they behave, who decides.

## Driving forces

Forces toward (wishes) and away (fears and frustrations); both, because fear often moves people faster than hope. Each force is **what** they want or fear, **why** it matters, and **when** it is active:

- Too vague: "wants peace of mind".
- Specific: "Knows the walker shows up (*what*), because a missed walk means a dog alone for ten hours (*why*), when she leaves for an early shift (*when*)."

Three questions test a force: could a designer answer it with something specific? Does it reveal a motive beyond "wants it to work"? Is it clear when it is active? A no to any of them means more *what*, *why* or *when*.

**Needs, never solutions.** "Wants a template library" is a solution; ask what it would give them ("not starting from a blank page before a client meeting") and write that.

## Scores

Each force is scored 1–5 three ways; the sum ranks it. `validate.py` prints the ranking with the bands below, which are defined in the script and nowhere else.

| | 5 | 3 | 1 |
|---|---|---|---|
| **f** (how often) | every time | regularly | a rare case |
| **i** (how strongly) | blocks action if not met | important, manageable | nice to have |
| **fit** (how well this can answer it) | a direct answer | a partial answer | hard to answer here |

**13–15 high:** design for it first. **10–12 medium:** group into shared answers. **Below 10 low:** later. High intensity with low fit is a limit of the product; high frequency with low intensity is table stakes; low frequency with high intensity is an edge case for another channel.

## Common mistakes

- **Too many personas.** Two or three, deeply understood.
- **Only forces toward.** The fears are often what moves people.
- **Solutions as forces.** They lock the design early and age the map.
- **Generic goals.** "A better experience" cannot be designed for.
- **Invented psychology.** What the person did not say is a hypothesis, marked as one.
