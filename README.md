# HeimAI template

The empty base for a new Heim: a home for agents, where people and agents work together, in git and owned by you. The Open Glass makes a Heim from it when you choose Add a Heim, or you choose **Use this template** on GitHub.

What it holds:

- `.heimai/heimai.yaml`, the floor plan: where every folder of the Heim lies, and which agents are woken.
- Idun and Saga, the first agents, in `.heimai/agents/heim/`, copied from HeimAI's `agents/` with a `.source` that says the version. Open the repo in Claude Code and say hello: Idun starts, and Saga takes over with the brief and the impact map. `AGENTS.md` tells the assistant how.
- `.heimai/01-brief/` and `.heimai/02-impact-map/`, placeholders that the first agent session replaces with your brief and impact map.
- `.heimai/tasks/inbox.md`, where anything small goes, and `.heimai/users/_template/` for the people who work here.
- The Watchdog: `.github/workflows/watchdog.yml` runs `.heimai/machine/runner/heim-run.mjs` twice a day, keeps the timeline current and tells you by a GitHub issue when the agents have stopped.

The guides are at [heimai.org](https://heimai.org) and in [HeimAI](https://github.com/whiteport-collective/HeimAI). How the agents are updated: [Get and update your agents](https://github.com/whiteport-collective/HeimAI/blob/main/docs/set-up/get-and-update-your-agents.md).
