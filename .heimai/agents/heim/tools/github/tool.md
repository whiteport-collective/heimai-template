---
tool: github
used_by: [idun]
skills: [onboarding]
needs: the GitHub CLI (gh), signed in through the browser
version: 0.1.0
status: specified
copied_from: whiteport-design-studio, tools/github.md (2026-11-19)
---

# github

What setting up a Heim needs from GitHub, beyond committing and pushing: the login, creating a repo, invitations, adding a person, and the facts for the access maps. **The commands are ready to use; a wrapper script (`gh.py add-collaborator`, `access-map`) is specified, not built.** Every writing command waits for the person's yes in the session.

## Login

```bash
gh auth status                     # signed in, and as whom
gh auth login                      # the browser flow; walk the person through it
gh auth refresh -s admin:org       # only if the organization needs it (SSO, admin)
```

The agent never sees a password or a token: the login happens in the browser.

## Create a repo

```bash
gh repo create <owner>/<repo> --private --clone
```

Private unless the person says otherwise. A repo that exists is cloned or used, never created again. When a repo has several remotes, name the repo explicitly (`-R <owner>/<repo>`), since `gh` may pick the wrong one.

## Invitations

```bash
gh api user/repository_invitations --jq '.[] | "\(.id) \(.repository.full_name) \(.inviter.login)"'
gh api -X PATCH user/repository_invitations/<id>          # accept: only after the person's own yes
```

## add-collaborator

Adds a person to a repo with the role agreed in onboarding (`pull`, `triage`, `push`, `maintain` or `admin`; the least the job needs, never less):

```bash
gh api -X PUT repos/<owner>/<repo>/collaborators/<login> -f permission=push
gh api repos/<owner>/<repo>/invitations --jq '.[] | "\(.invitee.login) \(.permissions)"'     # pending
```

The person accepts the invitation themselves. To be built as `gh.py add-collaborator --repo <owner>/<repo> --user <login> --role <role> [--yes]`: shows the change, refuses a role above `push` without saying why, and prints the invitation link.

## access-map

The facts for `people-access-map.md` and `repo-access-map.md` (templates in `templates/heim/`):

```bash
gh api orgs/<org>/members --paginate --jq '.[].login'
gh api orgs/<org>/memberships/<login> --jq '{user: .user.login, role: .role, state: .state}'
gh repo list <org> --limit 200 --json name,visibility --jq '.[] | "\(.name) \(.visibility)"'
gh api repos/<org>/<repo>/collaborators --paginate --jq '.[] | "\(.login) \(.role_name)"'
```

To be built as `gh.py access-map --org <org>`: prints both tables, ready to paste; reads only.

## Which repos are Heims

```bash
gh api repos/<owner>/<repo>/contents/heim.yaml --silent && echo heim
gh api repos/<owner>/<repo>/contents/.heimai/heimai.yaml --silent && echo heim
```
