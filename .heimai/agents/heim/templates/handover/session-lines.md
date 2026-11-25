Every session builds on the last: the soul files say who the person is, the handovers say where the work stands. The whole method is the handover skill, `{{agents}}/skills/handover/SKILL.md`; these lines are what every agent does without opening it.

The agents and their layers lie in `{{agents}}/`. A path in a skill or tool that starts with `agents/heim/`, `tools/`, `templates/` or `skills/` is in that folder.

**Start**, before the first answer, in this order, a resume command included. Don't print what you read.

0. **Who you are.** Your persona, `{{agents}}/agents/<you>/persona.md`, and this Heim's customization of you right after it when the list at the end of these lines names one. It comes before anything else, also when a resume command makes the handover look like the whole task.
1. **The handover.** A resume command (`/<agent> <repo> YYYY-MM-DD_HH-MM <summary>`): `python {{agents}}/tools/session-start/find.py --stamp YYYY-MM-DD_HH-MM --repo <repo> --summary "<summary>"`. Otherwise: `find.py --open --agent <you>`. Run it from where the session runs; the checkout it names is the session's repo, so read its `AGENTS.md` and run git there.
2. **The person.** `user:` and `private:` in `~/.wds/me.md`. Read the latest personal parts of the handovers first, then `soul.md` in `{{users}}<user>/` and in the private cabinet. Every start reads them before the box in step 4, a resume too: they decide how you show it and what you do next. Never read a `private/` folder unless you are the person's own agent. No such file (someone new, or a session in a browser): ask what to call them, use their folder in `{{users}}` (made from `_template/` on their yes when it is new), and pass `--user` to the handover tool.
3. **The policy.** The governance folder in `{{plan}}`, when it names one (a private Heim has none), its `policies.md`: the principles every session, the rest when the task touches it.
4. **Take it.** Show the handover in a short box in the person's language (about, from, the first line of `## Next`). On a yes: `python {{agents}}/tools/handover/handover.py take <file> --session <id>`, and start on `## Next` with no recap. The session id is the start time, `YYYY-MM-DD_HH-MM-<user>`.

**During**

- Once there is something to keep: `handover.py new --active --agent <you>`, the session file in `{{sessions}}<user>/<you>/`; commit it with each finished piece.
- **A thread as soon as a product takes shape.** Nobody knows at the start of a session what will be built. When you see a product of some kind taking shape, make its thread at once, even while Saga is still writing the brief: a process file in the processes folder that `tasks:` in `{{plan}}` names, in the folder of its field (`<field>/<product>.md`, with a `field.md` when the field is new), the plan as its points and who does each. Sharpen it as the work goes on: points added, split or marked done, and a line in its history for each step done, with why. The format is HeimAI's [process files](https://github.com/whiteport-collective/HeimAI/blob/main/docs/reference/process-files.md).
- Before a task, open everything it will reach (files, keys, services, programs) in one go.
- A correction is followed at once and, if it lasts, written where it belongs then: the person's soul file, the project's files, or, only when it changes how an agent or skill works in this repo alone, the customizations folder (the handover skill's soul review says which).
- Before working in another repo, read the session lines in its `AGENTS.md`: their last lines say what is customized there.
- Report each finished piece to the agent coordinating the work, when there is one.

**End**

- `/wrap`, or `/handoff` for one task: the handover skill. It ends with the resume command `handover.py receipt` prints, in its own code block.
- Done means delivered; what is only local is Left. Nothing about the person goes in this repo, nothing of the work in the private cabinet.
