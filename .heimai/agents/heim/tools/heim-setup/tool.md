---
tool: heim-setup
used_by: [idun]
skills: [onboarding]
needs: Python 3.10+, git, the GitHub CLI
version: 0.1.0
status: specified
copied_from: whiteport-design-studio, skills/install-wds.md (2026-11-19), its mechanical steps
---

# heim-setup

**A specification, not built yet.** Until it is, the agent runs the commands below by hand, one at a time, each after the person's yes. The person's own Heim and the per-computer file are what make every other Heim on the computer findable.

## Commands (to build)

```bash
python agents/heim/tools/heim-setup/setup.py create-private --name <name> [--local <folder>] [--yes]
python agents/heim/tools/heim-setup/setup.py write-computer-file --user <id> --private <path> --dev-root <path> [--yes]
python agents/heim/tools/heim-setup/setup.py clone [--from <the person's own Heim>] [--yes]
```

### create-private

Creates the person's own Heim. **By default a private GitHub repo `<name>-heim`** in the person's own account, so what is theirs follows them if they leave a job:

```bash
gh repo create <github-user>/<name>-heim --private --clone      # into <dev_root>/<github-user>/<name>-heim
```

then `heim-scaffold create --kind private --into <that folder> --yes`, commit and push. **With `--local <folder>`**, for a person who does not want GitHub linked to their work computer: the same skeleton in a local folder, no repo; the tool prints the one line Idun says once, that it then stays on that computer. It refuses a repo or folder that exists, and shows it instead.

### write-computer-file

Writes the per-computer file (today `~/.wds/me.md`, outside every repo) from [`templates/heim/me.md`](../../templates/heim/me.md): `user`, `github`, `name`, `language`, `private`, `dev_root`. Nothing else goes there; what differs per computer (the large-file folder, the screens, the microphone) is kept in the person's own Heim under the computer's name (decision 33). An existing file is shown with the lines that would change, and changed only with `--yes`.

### clone

Clones the Heims this computer should have, as the person's own Heim lists them, each into the same place relative to the dev root as on the person's other computers, so every agent and handover finds them. A Heim already cloned is skipped; one the person has no access to is reported with the invitation to accept. Not every computer gets every Heim: the list can say which computers each Heim belongs on.

## Refuses and never does

- Never asks for or handles a password, token or key; `gh auth login` runs in the browser.
- Never accepts an invitation; it lists them (`github invitations`) for the person to accept.
- Never overwrites a repo, a folder or the per-computer file without showing it first.

## Open

- The per-computer file's name and folder once Heim moves to `.heimai/` (decision 34): `~/.wds/me.md` today.
- How the person's own Heim lists the Heims and the computers each belongs on (`heims:` in its `heimai.yaml`, per the floor-plan draft).
