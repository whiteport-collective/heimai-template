---
tool: handover-audit
used_by: [idun]
skills: []
tools: [heim-floor]
needs: Python 3.10+
version: 0.1.0
---

# handover-audit

Lists a Heim's handovers by status and age and flags the threads that stopped, as the list the storage audit (not released yet) reasons over. The sessions folder is found through the floor plan ([heim-floor](../heim-floor/tool.md)). It reads the English and the older Swedish keys alike (`open`/`öppen`, `taken`/`tagen`, `done`/`klar`, `taken_by`/`tagen_av`, `from`/`från`, `to`/`till`) and the session files marked `active`. Reads only; it moves nothing.

## Commands

```bash
python agents/heim/tools/handover-audit/audit.py                      # the Heim's sessions folder
python agents/heim/tools/handover-audit/audit.py --heim <folder> --all
python agents/heim/tools/handover-audit/audit.py --sessions <folder> --sessions <folder> --json
```

`--open-weeks` (default 3) and `--active-hours` (default 24) set when an open handover and an active session count as left. `--all` also lists the done handovers.

## Findings

| Kind | When |
|---|---|
| `taken-without-wrap` | `status: taken`, and no later handover continues it: none names it in `continues:`, and none has the session id in its `taken_by:` |
| `active-stale` | a session file still `status: active` after `--active-hours`: the session ended without a wrap |
| `open-old` | `status: open` for longer than `--open-weeks` |
| `links-personal-part` | a work part links into a private cabinet or the person's own Heim, or holds a heading for a personal section |
| `front-matter-incomplete` | no `status:` or no `session:` |

The personal-part check is deliberately light: mentioning the idea of a personal part is fine, and the skill reads the rest. The age is counted from the time in the file name.

## Output

Per status, newest first: the time, the age in days, user and agent folder, and the summary from the file name; then the findings. `--json` gives `{"schema": "heim-handover-audit/1", "heim", "sessions", "handovers": [{"path", "stamp", "user", "agent", "summary", "status", "session", "from", "to", "taken_by", "continues", "age_hours"}], "findings": [{"kind", "path", "stamp", "detail"}]}`. `heim-status` uses the same reading for its list of handovers not done.

Not done yet: checking, per session, that the work part exists in every repo the session touched and the personal part in the person's own Heim; that needs the list of the person's Heims, and the skill does it by reading. Tried on 2026-11-19 on a Heim with 67 handovers (6 findings) and on a scratch Heim.

Exit codes: 0 listed, 2 no Heim or no sessions folder.
