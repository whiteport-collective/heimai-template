---
name: manage-capabilities
source: heim
owner: idun
description: Builds and changes agents and their capabilities layer by layer (persona, skills, tools, templates, apps, automations, dependencies, guardrails with evals), keeps the catalog of what exists and who uses it, audits it against Heim's conventions, and turns method corrections into changes at the source. Use when someone wants a new agent, skill or tool, wants one changed, asks what the agents can do ("vilka agenter har vi", "what can Saga do"), asks for an audit, or when a wrap hands Idun a correction to an agent's method.
used_by: [idun]
version: 0.1.0
copied_from: whiteport-design-studio, skills/librarian.md (2026-11-19), split and rewritten by the skill review
tools: [heim/capability-catalog, heim/capability-lint, heim/source-import, heim/heim-status, heim/heim-sync]
guardrails: [heim/idun-mandate, heim/one-question-at-a-time, heim/confirm-before-writing, heim/document-before-development]
replaces: [librarian]
---

# Manage capabilities

Agents are only as good as the instructions they run on. This skill is how Idun keeps them good: she builds an agent and its capabilities layer by layer, keeps an honest catalog of what exists and who uses it, audits it, and corrects the method at its source when a session shows it was wrong.

## The eight layers

A capability has up to eight layers (decision 25), built in this order and only as many as it needs: **1 persona** (who), **2 skills** (what and why), **3 tools** (how), **4 templates** (what good looks like, and how the glass shows it), **5 apps** (what the person opens and works in), **6 automations** (what runs by itself), **7 dependencies** (what is installed and approved once), **8 guardrails** (what it must and must not do, with the evals that show it holds; a guardrail without a test is a wish).

They live in an agents folder, by source and then by layer: `agents/<source>/<layer>/<name>`. Every object says in its front matter which agents use it and what it uses; the conventions are written once, in [front-matter.md](references/front-matter.md). An app or a skill is never kept in its agent's folder, because other agents use it too.

**One source per object.** HeimAI's own lie in `agents/heim/`, synced into each Heim with a `.source` file and never edited there. A Heim's changes to them live beside the layers in `agents/heim/customizations/`, never touched by the sync: `additions.md` adds, the same name replaces, a guardrail is only added to ([heim-sync](../../tools/heim-sync/tool.md#customizations)). What only the Heim has is a source of its own, `agents/<own>/` (default `local`). An app is code, so it is customized at the points it declares instead (`customizable:` in its `app.md`, story 5.11): build every app that way, so a Heim never has to fork it. A change meant for every Heim is proposed to HeimAI as an issue (its CONTRIBUTING.md), and comes back in a release. Another framework is taken in through `source-import`, which writes its recipe and redoes the adaptation at every update; a person's own skill goes through the same import, and the adapted version becomes the source.

## Building or changing an agent

1. **Intent first,** one question per message: what the agent owns (a work area, not a field of knowledge), who it is for, what it must never do. A skill: what it accomplishes, when it is used, by whom. Extract what the person already said instead of asking again.
2. **Look at what exists** before proposing anything: `capability-catalog` shows every object and who uses it. Share a skill another agent owns rather than writing a second one.
3. **Propose the tree** (the files, one line each, which layer each is) and write on a yes.
4. **Write each layer in its own kind:**
   - The persona in the short form: who (name, meaning, voice), owns, does not own, good output, how it works, when unsure, hands over. About 40 to 70 lines. No menus, no activation steps, no session start (that lives in the Heim's `AGENTS.md`).
   - A skill holds judgment: why, when, what good looks like, what to do when unsure. Under about 150 lines, with `references/` for what only part of the work needs. The description says what and when, in the words people say, because that is how a host decides to use it.
   - Steps that are the same every time become a tool, with its commands and what it refuses in `tool.md`: [tool-design.md](references/tool-design.md).
   - A rule becomes a guardrail with at least one eval a grader can check: a concrete prompt or fixture and the expected result.
5. **Run `capability-lint`** on what was written and fix what it finds; then, for a new agent or a large change, the read-only [capability review](../../agents/idun/subagents/capability-review.md) for what a script cannot see.
6. **Wake it,** when it is new to the Heim: what only this Heim has lies in its own source, `local/` in the Heim's agents folder (`own_source:` in the floor plan), with the same layers. Add an agent's name to `agents_woken:` in the floor plan (a skill no woken agent carries goes in `capabilities:`), run `heim-sync` as a dry run with `--from` the `agents/` folder of a HeimAI clone, and on the person's yes `run --yes`: it writes the pointers, so the agent starts with `/<name>`. Add the agent's row to the agents table in `AGENTS.md`.
7. **Commit each object on its own** (`skill(<name>): …`, `tool(<name>): …`).

Never invent an API's behaviour or a fact of law: an unknown is written as an open question. A tool that needs anything built on a server waits for an approved specification before code.

## The catalog

`capability-catalog` lists every object per source and layer, with who uses it and what it uses, and flags what is off: a reference to something that does not exist, links that disagree in the two directions (a skill names a tool whose `skills:` does not name the skill), a guardrail without evals, a file that still points into WDS. Show its tables when the person asks what exists, and offer the fix for each finding; the glass's Agents pages read the same data as `--json`.

## The audit

An audit documents; it fixes nothing until the person asks.

1. `capability-lint` for the mechanical checks (front matter, trigger phrases, size, evals, BMad markers, dead links, secrets).
2. The capability review subagent for the judgment.
3. One report in chat: per finding the object, where, why it matters and the proposed fix, most important first. Then: "Do you want me to fix any of these now?"

Monthly, the audit runs over every agent the Heim has woken, as the policy's review schedule says.

## Method corrections

When a session shows that an agent's method was wrong (not the person's preference, which goes to their soul file), the wrap hands it to Idun as a proposal. Read each proposal, find the object it belongs to, and propose the change there, at the source: for HeimAI's own agents, a customization in this Heim and an issue to HeimAI; in the Heim's own source for its changes. Changes the [mandate](../../guardrails/idun-mandate.md) lets her make alone she makes and reports; the rest she asks for. Close the proposal's handover with what was done.

## Release

When a change is finished and documented, ask whether it should go out to every Heim. On a yes, start the sync on GitHub (`heim-sync`); never push into another repo without that yes.

## Done

- Every object written has its front matter, and `capability-lint` reports no errors for it.
- Every guardrail written has evals.
- `capability-catalog` shows the new or changed objects with the right agents and no new missing references.
- The change is committed object by object and documented, and the release question has been asked.
