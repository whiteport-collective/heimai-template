---
tool: machine
used_by: [idun]
skills: [onboarding]
needs: Python 3.10+ (the check itself runs on any Python 3)
version: 0.1.0
copied_from: whiteport-design-studio, tools/machine.md (2026-11-19)
---

# machine

Checks which programs a Heim needs are on this computer, and says how to install the rest. `check` is built; installing is done by the agent with the printed command, after the person's yes, one program at a time, and checked again afterwards.

## Commands

```bash
python agents/heim/tools/machine/machine.py check [--json]
```

It checks git, the GitHub CLI, Python (3.10 or newer: every Heim tool needs it), PyYAML, and, as optional, Node.js 18 or newer and VS Code. For each one missing or too old it prints the install command for this system. Exit code 1 when a required program is missing, 0 otherwise. `--json` gives `{"schema": "heim-machine/1", "system", "programs": [{"program", "found", "ok", "required", "minimum", "install"}]}`.

## Installing

| Program | Windows (winget) | Mac (Homebrew) |
|---|---|---|
| Git | `winget install --id Git.Git -e` | `brew install git` |
| GitHub CLI | `winget install --id GitHub.cli -e` | `brew install gh` |
| Python | `winget install --id Python.Python.3.12 -e` | `brew install python` |
| PyYAML | `python -m pip install pyyaml` | `python3 -m pip install pyyaml` |
| Node.js | `winget install --id OpenJS.NodeJS.LTS -e` | `brew install node` |
| VS Code | `winget install --id Microsoft.VisualStudioCode -e` | `brew install --cask visual-studio-code` |

- After an install on Windows a new terminal may be needed before the program is found.
- **On a Mac,** `python3` is often Apple's own 3.9 even after `brew install python`. Homebrew's wins only when Homebrew comes first in the path: ask, check that the line is not already in `~/.zprofile`, then add `eval "$(/opt/homebrew/bin/brew shellenv)"` (`/usr/local/bin/brew` on an Intel Mac) and open a new terminal. `which python3` should then show Homebrew's.
- **A Mac without Homebrew:** ask before installing it, with the command from brew.sh.

## Git identity

```bash
git config --global user.name "<Name>"
git config --global user.email "<email>"
```

The dev root, where the repos live, is `C:/dev` on Windows and `~/dev` on a Mac or Linux unless the person has another; it is written in the per-computer file (`heim-setup write-computer-file`).
