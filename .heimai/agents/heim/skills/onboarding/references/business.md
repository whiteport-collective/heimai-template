# A business's Heim

From a confirmed inventory to a Heim where the business's people can start working with their agents. For one person that is a few files and a handover; for an organization it is a sequence of phases, each ending with a gate the person can see. Understand before building: each phase informs the next, and skipping ahead produces wrong decisions.

Start from the confirmed summary and do not reopen what it answered. Scale to the business: a two-person studio never gets enterprise ceremony, a department never gets a flat folder.

## 1. Understand the business

What it does and for whom, who the people are (roles, how at ease they are with these tools), how the work runs today and where it hurts, what agents should take over, and how it relates to whoever runs the setup (client, partner, internal). Read the room on depth: a small studio needs five sentences, a department a page. It is written as the Heim's first documents once the Heim exists.

**Gate:** the person confirms that it is accurate.

## 2. The Heim

- **The repo:** the business's existing repo, or a new one under the business's own GitHub account or organization, private unless the person says otherwise. **Keep the repos few:** split a Heim into another repo only where access demands it (a team part everyone shares, an admin part for those invited); every repo has its own access to keep track of.
- **The glass:** the `HeimAI Glass` app installed on the business's account or organization for the Heim's repos, or the Heim is missing from everyone's glass ([setup step 8](../SKILL.md#the-setup-built-from-the-inventory)).
- **The floor plan and folders:** `heim-scaffold create --kind business`, dry first; it writes `heim.yaml`, `AGENTS.md`, the users folder and its template, the sessions folder and the inbox, and never overwrites. In an existing code project the Heim's folders go in `heimdocs/`, and the project's own files are never touched.
- **What it inherits and wakes:** the agents the business needs (`agents:` in the floor plan); the sync copies them and what they use, after a yes.

**Gate:** an agent starts in the Heim and finds it (`heim-status` shows it as expected).

## 3. Governance, when wanted

Only with a business signal for it, and only after a yes: the governance skill owns the whole of it, from `governance-init` to approval. It is not released yet: say so, and note the wish in the inbox. The business's policy has one source Heim, usually the one it already works in; its other Heims point to it.

**Gate:** the business's approver has read the framework at an agreed milestone, or the status says in progress and the handover says what is left.

## 4. How agents and capabilities are organized

Record the business's own decision, and why, in its policy's skill governance section, or in the Heim's decisions when it has no policy: flat for a small business, by department or team for a larger one (who owns which skills, who may change them). Three lines is enough. It is a decision about ownership, not a technical preference.

## 5. The business's own agents

Reuse Heim's agents first. An agent of the business's own only where a work area needs one, built with [manage-capabilities](../../manage-capabilities/SKILL.md) in the business's own source folder, never inside `agents/heim/`. For non-technical people, a short guide in the business's language: which agents exist and what each does in their terms, how to give them work, what they never do without asking, where things are, who to ask.

**Gate:** each agent starts and does its main task.

## 6. People

[add-person.md](add-person.md) for each person, owners and admins first. The access maps (`people-access-map.md`, `repo-access-map.md` from the Heim templates, filled from `github access-map`) once there is more than one person.

**Gate:** each person can start an agent and complete a real task.

## 7. Infrastructure last

Anything realtime or always on (the Lighthouse, scheduled automations) comes last and is optional: what it supports must exist first, and when the business has a policy, it is configured only from approved sections.

## Hand over

To the agent the first real work belongs to, usually Saga for the brief, with the confirmed summary under `## Done` and the first step under `## Next`.
