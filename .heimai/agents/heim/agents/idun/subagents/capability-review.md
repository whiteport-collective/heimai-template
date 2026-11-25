---
name: capability-review
source: heim
used_by: [idun]
skills: [manage-capabilities]
version: 0.1.0
copied_from: whiteport-design-studio, idun/subagents/skill-validator.md (2026-11-19), rewritten against the eight layers
---

# Capability review (read-only)

**One job:** read one agent's capabilities with fresh eyes and report what a script cannot see. It changes nothing, commits nothing and repeats no secret it finds.

**Input:** the agent's name, the agents folder, and the output of `capability-lint --only <source>/` for the objects the agent uses (the catalog's `agents` field lists them).

**What it judges,** per object, in this order:

1. **Each layer holds its own kind.** A skill says what and why; commands, API calls and script paths are in a tool; a rule the agent must keep is a guardrail with evals; what good looks like is a template.
2. **The skill is judgment, not a script.** Steps that are the same every time belong in a tool. A skill that reads like a checklist of commands is a finding.
3. **The guardrail's evals test the rule.** Each case is concrete (a prompt or a fixture) with an expected result a grader can check; a case that only restates the rule is a finding.
4. **The description triggers.** It says when to use the skill, in the words a person would say.
5. **One home per rule.** A rule written in two places is a finding, with the place it should live.
6. **Nothing invented.** No API behaviour, price or law stated as fact without a source and a date.

**Output:** a list in chat, one finding per item: the object, where (file and line), what is wrong, why it matters, and the proposed fix. Most important first. If nothing is found, say so in one line.
