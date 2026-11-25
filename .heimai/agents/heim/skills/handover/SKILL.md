---
name: handover
source: heim
owner: all
description: How a session starts from where the last one stopped, keeps itself resumable, and ends by handing over, to the same agent or another one. One skill for the start, the session file, the wrap and the handoff. Use at every session start and resume command (/<agent> <repo> YYYY-MM-DD_HH-MM <summary>), when the person says wrap, hand over, handoff, "we stop here" ("vi slutar här"), or when a task belongs to another agent.
used_by: [idun, saga, freya, mimir, viska]
version: 0.1.0
tools: [heim/session-start, heim/handover, heim/project-log]
templates: [heim/handover]
guardrails: [heim/memory, heim/inventory-before-work]
references: [soul-review, gc-findings]
replaces: [wrap, handoff, session]
commands: [wrap, handoff]
---

# Handover

The memory lives in files, not in the model. The soul files say who the person is and how they want to work ([soul-files](../soul-files/SKILL.md)); the handovers say where the work stands. A session starts from what earlier sessions left, keeps what it does resumable while it works, and ends by leaving more behind. That is why the person never has to repeat themselves, and why any agent in any tool can pick up where another stopped.

The agent owns the delivery. What is left undone should itch: a draft half finished, a question nobody answered, a step waiting for someone. What only the person can do (approve, pay, sign, log in) is one line ("Approve the mail"), never a reason for the work to wait.

The mechanics (filenames, keys, taking, logging, the resume command) are [the handover tool](../../tools/handover/tool.md)'s; this skill is the judgment around them. The words written into the files are English (`status: open`, `## Next`); the text is written in the person's language unless the repo says otherwise.

## Start

Before the first answer, know four things in this order, because each changes how you answer the next: which repo, who you work with, which policy applies, and what is waiting. Your persona comes before all four, from the command that woke you. A resume command changes none of this: it names the handover, and the person and the policy are still read before the box (story 5.7 found resume starts that skipped the persona and the soul files). Don't print what you read.

1. **The repo.** A resume command names it; a session may start in the repo, a worktree or any folder above. Run `session-start` from where the session runs ([find.py](../../tools/session-start/tool.md)): it finds the handover in any checkout and the personal part in the private cabinet. The checkout it is in is the session's repo; read that repo's `AGENTS.md` when it is not the current folder, and run git there. A repo that is not cloned on this computer: say so in one line and stop.
2. **The person.** The user is `user:` in `~/.wds/me.md`. Read the latest personal parts first (decision 27): they already hold the people, the goals, the state and the next step. Then `soul.md` in both cabinets, and the rest as the work needs. When a person comes up, open their file in `people/` before answering. A new user gets a folder from the template and the soul files grow from the sessions; no interview.
3. **The policy.** The reading list is the governance folder's `policies.md` (the floor plan says where). Read the principles every session and the other files when the task touches their area. A synced copy (a `.source` beside it) is never edited. If a task would break a principle, say so before doing it.
4. **What is waiting.**
   - **Resume** (a timestamp): show the handover as a short box in the person's language (repo when it is not here, what it is about, from whom, the first line of `## Next`), and on a yes run `take` and start on `## Next` at once, with no recap. Say when its checkout is on a branch that is not merged: the work is there and nowhere else.
   - **A normal start:** list the open handovers to this agent (`--open --agent`), the user's own and `all-users`, and propose the newest. Read every open one to you, not only the one you take.
   - **A session file still `active`** that is not this session's: another window may still run it. Show it with the time of its last commit, and take it over only on the person's yes.

Note the start time: it is the session id, `YYYY-MM-DD_HH-MM-<user>`.

## During the session

- **Keep it resumable.** Any session can end without warning. As soon as there is something to keep (a checklist, a decision, a finished piece), write the session file with `new --active`. `## In progress` holds what only this session needs; `## Done`, `## Left` and `## Next` grow as they become clear. Commit it with the work each time a piece is finished. It is in the work repo, so only the work goes in it.
- **Drive to delivery.** Start with what is closest to finished or has stood still longest. Ask why it stopped and remove exactly that. Do everything up to the last click. Someone blocked by this work comes before your own next step. Promises and requests found in notes, mails and messages become tasks with a link to the source.
- **Inventory first** ([inventory-before-work](../../guardrails/inventory-before-work.md)): every file, key, service and program the work will reach is opened before the first step.
- **Learn as you go** ([soul-files](../soul-files/SKILL.md)): a correction is followed at once and, if it holds beyond today, written where it belongs then, not saved for the wrap.
- **Report** to the agent coordinating the work, when there is one, as each piece lands: what, where, the commit, what is open.
- **Propose a wrap** when the session grows long or a step is done. A wrap is a handover the person can read; a compacted context is not.

## Handoff: one task to another agent

The session goes on. Run `new --handoff --from <you> --to <agent> --summary "<the task>"`, and write the task alone: what is already done of it and the decisions it rests on, what is left, the steps in order so the recipient can start at once, and links to every file needed. Commit only that file (`handoff: <session-id> → <to>: <one line>`), show the resume command, and go on where you were. An idea that belongs to another agent's work is handed off the same way and removed from yours.

## Wrap: end the session

The wrap does not ask what happened: the agent was there, and takes it from the conversation, the session file and git. It asks only where something should live when that is missing.

1. **Who and to whom.** From: the agent that was active. To: whoever takes the next step; usually yourself. When the next step is another agent's, write to them, and a short wrap to yourself if you have threads of your own left.
2. **Sort the session file.** Each item in `## In progress`: finished goes to one line under `## Done`; to continue goes under `## Left` or `## Next` (the checklist itself when the next session works from it); working notes are struck, since git keeps them. Then run `new --from <you> [--to <agent>] --summary "<3 to 6 words>" --continues <the handover you took>`. Without a session file it writes both parts from the templates.
3. **Write the work part** for whoever continues, complete enough to work from alone:
   - **Done means delivered.** Under `## Done` goes only what the recipient actually has: live and checked, sent, approved, merged. What exists only locally, on an unmerged branch or in a draft goes under `## Left`, marked *only local* with what stops it.
   - Point to the process points in `tasks/` instead of repeating them; carry what is not there: the context, why the work stopped, what the next session starts with.
   - It reads in a minute. It never mentions the personal part.
4. **Write the personal part**, by one test: if the person left the organization tomorrow, what would they take with them? What they achieved, the feedback and what they can do better, the people they worked with and where things stand with each, the goals, the next steps, and how the session went. Not the work itself and nothing of the organization's: no figures, client data, strategy, code or copies from the work part ([memory](../../guardrails/memory.md)). Nothing new for the person: still write the part with its links, so the session is in their history.
5. **Soul review:** go through the whole conversation and write in what the files do not hold yet, each thing in its file ([soul-review.md](references/soul-review.md)). A correction of the method goes to Idun as a proposal, not into a soul file.
6. **G&C:** an incident, a deviation or a gap the session showed is reported or proposed ([gc-findings.md](references/gc-findings.md)). Nothing found: skip it.
7. **Capabilities:** a skill, tool or script made or changed in the session lives in its source, one commit per object. Nothing that works is left in a scratchpad or temp folder.
8. **Log and close:** `log <work part> --text "<one to three points>"` writes each project's design log and the private log. If this session took a handover and its work is delivered, `take <it> --done`. Commit the work part, the logs and the repo's user files in the work repo (`wrap: <session-id>: <one line>`), and the personal part and private files in the private cabinet. Push only where the repo says so or the person asks.
9. **Receipt:** run `receipt` and show the person the session id, the recipient, both parts in full (so they see nothing of the organization's went into the personal one), what changed in the soul files per file, G&C, the commits, and every `!` line from the receipt as what is still to do. End with the resume command in its own code block.

## Done

- The person could close the window now and lose nothing: the next session, any agent in any tool, starts from the handover without asking what happened.
- `receipt` shows no gap it did not say aloud.

## Commands

`/wrap` and `/handoff` stay as commands; both open this skill in that mode.
