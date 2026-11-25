# Soul review: where each learning goes

The wrap's safety net. The agent wrote in what should last during the session ([soul-files](../../soul-files/SKILL.md), Learn as you go); at the wrap it goes through the whole conversation, compares it with what the files say now, and writes in what is not there yet.

## What to look for

- **Facts about the person:** where they work, role, manager and colleagues, clients, what has happened, addresses, companies.
- **People in their life:** who someone is, the relationship, what you did together.
- **Corrections** of the agent, and what the person appreciated or rejected.
- **Insights** into how they think, decide and what they value.
- **Goals** added, changed or reached.
- Things **delivered**.

## Where it goes

This table is the one place the routing is written; the soul-files skill says what each file is.

| New | File | Cabinet |
|---|---|---|
| Their current situation: workplace, role, manager, colleagues, clients, what has happened | `heartbeat.md` | private |
| Their own style: how agents should work with them everywhere (tone, pace, format, what irritates), also when learned in this repo | `soul.md` | private |
| How we work together in this repo: roles, agreements, ways of working in the team and with the agents | `soul.md` | work, `users/<user>/` |
| Who they are: values, drives, ways of thinking | `identity.md` | private |
| Professional profile: skills, experience, way of working | `user.md` | private |
| Lasting facts: addresses, companies with registration numbers, contact channels | `user.md`, the Facts section | private |
| People: who, the relationship, history with dates and sources; contact details stay in their address book, and the file refers there | `people/<name>.md`, and a line in `people/README.md` | private |
| Their role in this project | `user.md` | work |
| Personal goals | `objectives.md` | private |
| The project's goals and theirs in it | `objectives.md` | work |
| Delivered, at CV level: what, for whom, when ("built the open glass for a client"), never how it was done inside the client | `achievements.md`, at the top, with a link to the work part | private |
| Finance, health, sensitive details about relationships | a handover to the person's own agent, in their private Heim | private, never a soul file, never a work repo |
| How the project works, for every agent and person in it: its language, the client's conventions, where things are | the project's files: the Heim's `AGENTS.md`, its policy, the project brief | work |
| How one agent or skill works in this repo only, when the soul and the project files do not fit: "Saga asks more here", "the brief here starts from the call notes", a tool only used here | the customizations folder, `agents/heim/customizations/<layer>/<name>/additions.md` ([heim-sync](../../../tools/heim-sync/tool.md#customizations)) | work, the repo the change concerns |

## Rules

- **Update and optimise; don't just add lines.** Write it where it belongs, merge duplicates, replace what no longer holds, strike what is out of date. Corrections and events get dates. Keep each file short enough to read at every start.
- **The agent's method is not the person's soul.** A correction of how a skill, template or conversation guide works is a gap in the capability: hand it to Idun as a proposal (a handover to `idun`), and follow the correction for the rest of the session. Only when it holds for this repo alone does it become a customization, written at once with one line said ("Noted in <repo>, agents/heim/customizations/agents/saga/additions.md: …") and committed in that repo, that file alone.
- **Soul and project files first; a customization is the exception** (story 5.10). Before writing one, ask whether it is really the person's style or the project's way; most corrections are.
- **The repo is the one the learning concerns,** not the one the session started in. A session working in three repos writes each repo's customization in that repo.
- **A customization adds; it replaces only when it contradicts the synced file.** An addition still gets every upstream improvement; a replacement does not, and heim-sync says so each time the source changes under it. A guardrail is only ever added to.
- **The work cabinet is shared with the team:** nothing private there, and nothing changed in someone else's folder.
- **The private cabinet never holds the organization's information.** A lesson is written as the person's own ("wants the figure before the reasoning"), not as the client's business.
- **Private files are written directly** and committed in their own repo. Touch only the files where something new happened; `heartbeat.md` is created the first time there is something to write.
- **No private cabinet on this computer:** ask once where it should live (a repo the person owns, or a local folder, never the work repo), write it in `private:` in `~/.wds/me.md`, and create what is needed. If they decline, show in the receipt what would have been saved.
