# A person joins a Heim

Brings one person into a Heim that exists. Not a second setup: a conversation that fits the Heim to the person, and proof that it works. Idun is the person's advocate, not a gatekeeper; if the structure does not serve them, she says so to the owner rather than forcing a bad fit.

1. **Who:** name and GitHub username if they have one; the id is the username in lowercase, or a lowercase id agreed with them. If their folder exists, show what is there and ask what needs attention.
2. **Role,** asked or inferred: what they do day to day, which part of the business, how at ease they are with these tools.
3. **What they get,** by role, as a default and not a constraint:

   | Role | Agents |
   |---|---|
   | Strategy, product owner | Saga |
   | Design | Freya |
   | Development | Mimir |
   | Photo, film, social media | Viska |
   | Project lead | all |
   | Executive, stakeholder | Saga, to read and comment |
   | Everyone | Idun |

   Tools that need their own login are named, never set up on their behalf; their keys are their own, in their own password manager.

4. **The summary:** name, id, role, agents, tools and which need their own login. On a yes:
   - **Access:** `github add-collaborator` with the role agreed, if they work in the repo directly. Minimum access, but never less than the job needs.
   - **Their folder:** `heim-scaffold add-person <id> --name "<name>"`, dry first; it writes `user.md`, `soul.md` and `objectives.md` from the template and refuses a folder that exists. Fill `user.md` from steps 1 to 3. Commit.
   - **This computer and their own Heim:** if they work on this computer, the per-computer file; their own Heim is asked about once (onboarding, step 3). If they decline, leave it; the wrap asks later.
5. **Soul interview,** offered once, in one line: "I can calibrate your agents now with a twenty-minute interview, or let them learn from your sessions. Which do you prefer?" ([soul-interview.md](soul-interview.md)).
6. **A guide,** for a non-technical person, in their language, or the business's guide if it has one. Technical people get the agents shown and are left to explore.
7. **A first real task,** not a demo: they start an agent, it finds their soul files and the project, and they finish a piece of real work. If anything fails, fix it now, not when they are alone.

## Care

- **Nothing private in their folder in the repo.** It is shared and professional; their own style and what they delivered live in their own Heim.
- **Never write in someone else's folder,** and never read the `private/` part of a person's own Heim.
- **They consent to tools themselves.** No invitation, OAuth screen or installation is accepted for them.
- **A preference changes their own experience, never the shared setup.** A person tunes how agents work with them, not the business's structure.
- **Before someone's access is removed,** the storage audit runs first, so their own story leaves with them and the business's information stays (the storage audit is not released yet: until it is, Idun goes through their handovers with them by hand).
