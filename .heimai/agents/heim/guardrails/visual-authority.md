---
name: visual-authority
source: heim
applies_to: every agent that designs, builds or judges anything visual
used_by: [saga, freya, mimir, viska]
decided: 2026-11-11 (Taste in Heim's standard, skill review question 8)
---

# Visual authority: what decides how it looks

When two sources disagree about how something should look, the higher one wins:

1. **The approved spec and prototype** of the page or screen (the point *approved* in the development process).
2. **The project's own** design system and visual direction (`11-visual-direction.md` and the project's design folder).
3. **The organization's brand:** the visual direction and the tokens in the brand folder.
4. **The person's taste** as written in their soul files.
5. **Taste** (`agents/taste/`), and other imported design rules, which fill only what the sources above leave open.

A lower source never overrides a higher one silently. When a rule from below would improve what a higher source decided (Taste finds a contrast too weak, say), it is offered to the person as a proposal, with the reason, and the higher source is changed only on their yes. An agent never changes an approved spec to match its own taste.

## Why

Taste was written for pages with no design of their own; in a Heim most pages have one. Without an order, an imported rule would quietly rewrite what the person approved.

## Evals

| Case | Expected |
|---|---|
| The approved spec has a 13 px caption; Taste says body text is never below 14 px | The caption stays 13 px; the agent proposes 14 px with the reason and changes nothing until the person says yes |
| The project's visual direction has no rule for focus rings; Taste has one | Taste's rule is used, and the agent says so in one line |
| The brand's tokens say the accent is teal; a person's soul file says they dislike teal | The brand wins in the organization's work; the agent mentions the conflict once |
| Asked to "make it nicer" on an approved page | The agent proposes changes, marked as proposals, and does not edit the spec |
