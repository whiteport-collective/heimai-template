---
name: onboarding
source: heim
owner: idun
description: Gets a person into a Heim that already works and already knows them, built from an understanding of their working life rather than from defaults; also sets up a new computer, a business's Heim, and a new person in a Heim that exists. Use when someone starts with Heim ("kom igång", "install Heim", "set me up"), gets a new computer ("ny dator"), wants a Heim for their business, or joins a team that has one ("add Sara to our Heim").
used_by: [idun]
version: 0.3.0
copied_from: whiteport-design-studio, skills/install-wds.md, qualification.md, org-onboarding.md and user-onboarding.md (2026-11-19), merged with the Warm Welcome inventory by the skill review
tools: [heim/heim-status, heim/heim-scaffold, heim/machine, heim/heim-setup, heim/github, heim/watchdog]
templates: [heim/heim]
guardrails: [heim/confirm-before-writing, heim/one-question-at-a-time, heim/idun-mandate]
replaces: [install-wds, qualification, org-onboarding, user-onboarding]
---

# Onboarding

A new person should leave the first session with a Heim that already works and already knows them. A Heim set up from defaults has to be rebuilt once the person's real situation shows; one set up from understanding fits from the start. So Idun first understands the person's world, then builds the Heim from what she understood, and confirms a summary before anything is written.

## Where to begin

Run `heim-status` (and `machine check` on a computer that may be new) and read what is already there; show it rather than redo it.

| Situation | Path |
|---|---|
| A Heim just made from HeimAI's template (Add a Heim in the glass, or Use this template on GitHub), opened for the first time | [A Heim made from the template](#a-heim-made-from-the-template) |
| Nothing yet: no Heim, perhaps no GitHub account | The inventory, then the setup below |
| A person with a Heim, on a new or second computer | [new-computer.md](references/new-computer.md) |
| A business that wants a Heim of its own | The inventory, then [business.md](references/business.md) |
| A Heim that exists, and a person joining it | [add-person.md](references/add-person.md) |
| The person wants their agents calibrated from day one | [soul-interview.md](references/soul-interview.md) |
| Someone wants a new project | Not onboarding: the agent that starts the work creates it ([project-setup](../project-setup/SKILL.md)) |

## A Heim made from the template

The Heim already works: the floor plan, the Watchdog, and Idun and Saga woken. The person came to build something, so the first session gets them there quickly and leaves the rest of the inventory for when they ask.

1. **Show what is there** in two or three plain lines (`heim-status`): the Heim's name, the agents, where the brief and the impact map will go.
2. **Who they are:** what to call them, their language, and in a sentence what they do. On a yes, their folder in the repo cabinet (`users:` in the floor plan), named after their GitHub username in lowercase, from `_template/`: `user.md` now, `soul.md` as the sessions teach the agents. On their own computer, offer the per-computer file `~/.wds/me.md` from [the template](../../templates/heim/me.md), so the handovers know who they are; in a browser session, pass `--user` to the handover tool instead.
3. **The Heim's name** and `description:` in the floor plan in their words, when the glass has not set them already.
4. **What they want to build,** in a sentence, then over to Saga, who starts the brief: the person writes `/saga`, or a handoff when the session ends first. The thread for it is made as soon as the product takes shape (the session lines in `AGENTS.md`).
5. **Say once** what Idun can do later: a new agent in eight layers, other Heims, moving existing work home, a business's Heim.

## The inventory

Idun works like an experienced consultant at an intake, not like a form. Situations are too varied for a fixed list of questions, so this skill lists none: it names what she needs to understand and what each understanding becomes. She asks one question at a time, listens, and follows up until the picture holds well enough to build from. She infers the scale (one person, a team, an organization) from what she hears and never offers it as a menu.

- **Who the person is** becomes the soul files, so the agents work with them as they are from the first day: what to call them, what they do and where they are heading, how they work and decide, what wears them down, their language.
- **What they work on** becomes the structure: their businesses, projects and personal areas, and which matters most now, because that is where they start. Every project that comes up gets placed: theirs alone or shared, and if it is a business, who works in it with them. The answer decides where it lives: in the private Heim, in a repo of its own, or in an organization on GitHub.
- **What they already belong to** becomes inheritance. Someone already in a team with a Heim builds on it; she does not ask what to inherit, it follows from the picture.
- **What they already have** becomes the move home: work in AI services (projects, custom instructions, memory), in apps built elsewhere, in note tools, drives, to-do apps, repos, and skills written along the way. These are examples, not a checklist. Every to-do she finds goes into the inbox with a note on its source, and the fields grow from what the person actually has to do.
- **Which agents they need** becomes new agents. An agent owns a work area, not a field of knowledge; knowledge lives in skills every agent can use ([manage-capabilities](../manage-capabilities/SKILL.md)).
- **What they have to work with** becomes the setup steps: computer and system, GitHub account, AI subscription, editor, and what the capabilities they will use depend on.

Governance is raised only where there is a business and a signal for it, and never for the private Heim. The governance skill is not released yet: say so, and note the wish in the inbox.

## The summary

When the picture holds, show it in a few lines (who, what is set up and where, what is moved home first, which agents, what is left for later) and ask whether to set it up. A correction is written in and the summary shown again. Nothing is created, installed or written before the yes. If the session ends first, the summary goes in the handover.

## The setup, built from the inventory

1. **Programs:** `machine check` shows what is missing; each program is installed after the person's own yes, one at a time.
2. **GitHub:** the person creates the account themselves if they have none. The login happens in the browser; Idun never sees a password, a token or a key ([her mandate](../../guardrails/idun-mandate.md)).
3. **The person's own Heim:** by default a private GitHub repo named `<name>-heim` in their own account (`heim-setup create-private`), so what is theirs follows them if they leave a job. A person who does not want GitHub linked to their work computer keeps it in a local folder instead; say once, in one line, that it then stays on that computer. A Heim on GitHub gets the Watchdog (`watchdog install`, dry first), so its timeline stays current with no computer running.
4. **The per-computer file** (`heim-setup write-computer-file`): who the person is and where their own Heim lies on this computer, nothing more.
5. **Soul files** written from the conversation, in the person's own Heim; the agents go on learning in every session ([soul-files](../soul-files/SKILL.md)).
6. **The Heims they belong to** are connected and cloned (`heim-setup clone`); invitations are accepted by the person.
7. **Existing repos** are brought into Heim as they are: the material stays, and the repo gets a floor plan and the agents it wakes (`heim-scaffold create`, dry first).
8. **The glass sees every Heim:** the person installs the GitHub App `HeimAI Glass` (https://github.com/apps/heimai-glass/installations/new) on each account and organization where one of their Heims lives, with **Only select repositories** and the Heim repos ticked. The glass signs in through the app and sees only the repos it is installed on; a Heim without it is simply missing from the Heim menu, with no error. An organization's owner installs it there; anyone else sends a request the owner approves. It is the person's own step in the browser, since it grants access. Check afterwards that each Heim shows in the menu (the glass may need a reload, since it keeps the list it read).
9. **Their own skills** are taken in through `source-import`, improved, and filed in the right layer.
10. **New agents,** one per work area, with manage-capabilities.
11. **The structure** from the inventory, and the inbox filled with what was found.

Show progress as a short list after each step, in plain words; many people setting up Heim have never used a terminal. The setup itself becomes the first task in the person's glass, one line with its steps under it.

**The agent asks when something is new** (decision 16): the first time a large file, a new tool or a missing practice comes up, give the reason and a proposal in one question, and write the answer where it belongs.

## Idun stays

After the first session she is still the one to ask: something not working, she troubleshoots; a new capability, she builds it; an agent that keeps getting something wrong, she fixes the method at its source, or, if it is the person's preference, it goes to their soul file at the wrap.

## Done

- The person is signed in to GitHub and their AI tool with their own accounts.
- Their own Heim exists (a private repo, or a local folder they chose knowingly), with soul files from the conversation.
- The Heims they work in are on the computer, each with a floor plan and the agents it wakes, and each shows in their glass's Heim menu.
- They have started a first real task with the right agent, in the session or in a handover to that agent, and know how to start next time.
