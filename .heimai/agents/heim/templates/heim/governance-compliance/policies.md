# Policies

The policies for this Heim, in the order they are read. Agents read this list at every session start and follow the files in this order: the principles every time, the other files when the task touches their area. A lower level may tighten a rule, never loosen it. When two levels say different things, the stricter one wins, unless the difference is recorded with a reason in {Org}'s [framework]({org}/framework.md#differences-from-the-heim-default).

This file is owned by this Heim. Idun creates it at setup (`governance-init`) and updates it when a policy folder is added or removed. The folders it lists are owned by their sources: a folder with a `.source` file is a synced copy and is never edited here.

## 1. Heim default (`heim/`, synced from HeimAI)

- [Principles](heim/principles.md)
- [Framework](heim/framework.md) · [Tools](heim/tools.md) · [Data](heim/data.md) · [Risk](heim/risk.md) · [Agents](heim/agents.md) · [Access](heim/access.md) · [Incidents](heim/incidents.md) · [Transparency](heim/transparency.md)

## 2. {Org} (`{org}/`, {source})

Status: {status}

- [Principles]({org}/principles.md)
- [Framework]({org}/framework.md) · [Tools]({org}/tools.md) · [Data]({org}/data.md) · [Risk]({org}/risk.md) · [Agents]({org}/agents.md) · [Access]({org}/access.md) · [Incidents]({org}/incidents.md) · [Transparency]({org}/transparency.md)

**Incident log:** [{org}/incidents.md]({org}/incidents.md), in the source Heim. The wrap writes incidents there. In a Heim with a copy, the incident is written in the source Heim, or handed over to its owner.

## 3. Project

No project tightenings yet.

<!--
Template notes (remove when filled):
- Use the organization's own file names when its policy is localized (for example `acme/ramverk.md`, `acme/incidenter.md`), and write this file in the organization's language.
- No organization policy yet: drop section 2. The Heim default then applies alone. `heim/` is a read-only copy, so there is no incident log to write to: the wrap puts findings in the handover until the organization has its own policy.
- A project tightening is a folder `governance-compliance/<project>/` with one file per area it tightens. Each file names the rule it tightens.
-->
