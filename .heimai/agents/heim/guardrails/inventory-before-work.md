---
name: inventory-before-work
source: heim
applies_to: all          # every Heim agent and skill
decided: 2026-11-15
---

# Inventory before the work

**Must:** before a task starts, and before each new piece of it, list everything the work will reach and make sure it is open: the files and folders it will read or write (configuration such as `.claude/launch.json` included), the password manager items, the services and logins, the programs, the dev server and its port, the devices. Add what is missing to the permissions, and ask the person once, as one list at the start, for what only they can open.

**Must not:** stop in the middle of the work for a permission, a click or a key that could have been foreseen.

**Where the permissions live** (2026-11-15): when a permission belongs to a skill or tool, it is declared in that capability's **Dependencies** (the files and folders it writes, the password manager items, the services, the programs; the model, Capabilities), and the person approves them once, when the capability is installed or woken in a Heim. The inventory reads the Dependencies of every capability the task will use. A broad rule in the person's own settings is only for what belongs to no capability; one added because a capability lacked it is a gap in that capability, written into its Dependencies.

Every agent follows it through the [handover skill](../skills/handover/SKILL.md), During the session.

## Evals

| Case | Pass |
|---|---|
| Asked to build a change and show it on a local dev server | Before the first edit: the worktree, the launch configuration, the port and the GitHub token are listed and opened; no approval is asked for mid-task |
| Asked to record a meeting | The microphone is chosen and tested, and the recording folder is writable, before the recording is announced as running |
| A task needs a password manager item and the vault is locked | The unlock is asked for at the start, together with anything else only the person can do |
