# Sources: why soul files, and what came from where

Heim's memory for people is plain markdown in two git cabinets. Several others work on the same problem, how an agent comes to know a person and keep it, and we have read them. This page says what we took from each, what we left and why, and what we built ourselves. Checked on 2026-11-11.

## The decision

**Soul files in git, not a memory database** (2026-11-11). The reasons, in order of weight:

1. **Anyone can read it.** The person opens the file and sees exactly what the agents believe about them, and corrects it. A database of embeddings cannot be read that way.
2. **Every agent and tool can use it.** Claude, Copilot, Codex and OpenClaw all read markdown from a repo. No MCP server, no middleware, nothing to keep running.
3. **It follows the person.** The private cabinet is the person's own repo; if they leave the job, it goes with them (decision 27). Nothing is locked into a vendor or a service, which is Heim's vision: free from lock-in to any AI company.
4. **IT can say yes.** It is git, which IT already controls and audits (Ivar's driving force in the impact map).
5. **It is small enough to read whole.** A person's soul files are a few hundred lines. At that size an agent reads them directly at the start; retrieval and vector search solve a problem we do not have. This is also Karpathy's argument against re-deriving knowledge at every query.

What we give up: semantic search across years of notes. If that is ever needed, it can be an index built from the files, never the other way round.

## Nate B. Jones

Substack: [natesnewsletter.substack.com](https://natesnewsletter.substack.com/) · Open Brain: [github.com/NateBJones-Projects/OB1](https://github.com/NateBJones-Projects/OB1)

| What | Taken? |
|---|---|
| **The two filing cabinets:** one for what the person works on, which stays with the work, and one for who the person is, which travels with them | **Taken.** It is the core of the soul files: the work cabinet and the private cabinet |
| **Agent Space** (a shared database the agents read and write through MCP) came from his thinking too | **Built and dropped.** HeimAI built it, then scrapped it: a database and an MCP server to run, and memory nobody could read. Heim went to git |
| **Open Brain (OB1):** one database (Supabase, Postgres with pgvector), an AI gateway and an MCP server, so every AI tool shares one memory of the person, stored as "thoughts" in a table | **Not taken.** It is the architecture we left with Agent Space. Its licence, FSL-1.1-MIT, is not open source: it forbids competing use, and each release becomes MIT only two years later, so none of its code can go into MIT-licensed HeimAI |
| Ideas in OB1 worth following: auto-capture at session end, panning for gold in transcripts, a five-layer interview on how a person works, provenance and use-policy on memories, memory for OpenClaw agents | **Taken as ideas when built,** rewritten in Heim's way and credited. Not watched monthly: OB1 is read again when one of these is built (decision 39) |

He has also shown that an AI voice on Substack with YouTube works, which is why HeimAI's voice with a membership will be on Substack, once there is something to say there (decision 39).

## Andrej Karpathy: LLM Wiki

Gist: [gist.github.com/karpathy/442a6bf555914893e9891c11519de94f](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) (April 2026)

An idea file, not code: paste it into your agent and it builds its own version. An LLM keeps a personal wiki of interlinked markdown pages, updating them as new material arrives instead of re-deriving everything at each question, and health-checks the wiki now and then for contradictions and gaps. Karpathy uses Claude Code as the agent and Obsidian to read.

| What | Taken? |
|---|---|
| **The agent does the bookkeeping:** the person thinks, the agent keeps the files current | **Taken.** "Learn as you go": the agent writes the correction into the right file at once, merged, not appended |
| **Files, not retrieval,** at personal scale | **Taken,** reason 5 above |
| **The health check** for contradictions, stale lines and gaps | **To be taken.** Listed under Not yet in the skill; a candidate for the Watchdog |
| **The idea file as a way to share** a method: instructions an agent adapts, instead of code | Already Heim's way: a skill is an idea file with a frame. Much like a BMad brief |
| **A free-form wiki** where any page can link to any other | **Not taken.** Heim's knowledge is ordered in threads (processes, projects, people, decisions), which is easier to follow and to show in the glass. What the ordered threads lack is a place for loose ideas, which is why the idea bank was added |

## OpenClaw

OpenClaw's agent workspace has its own `SOUL.md` and `MEMORY.md`. An agent run in OpenClaw with Claude does not use them; its `SOUL.md` says that everything that matters is written in git, and every round pulls first and ends with a report.

| What | Taken? |
|---|---|
| The names `SOUL.md` and the idea of a soul file per agent | **Shared,** not taken: the same word, arrived at in parallel. Heim's soul files are per person, not per agent |
| `MEMORY.md` and its nightly "dreaming" | **Not taken.** Turned off; the memory is in git |

## soul.py

[themenonlab.blog](https://themenonlab.blog/blog/markdown-vs-graph-database-agent-memory-soul-py-openlobster) (Prahlad Menon)

Two plain files, `SOUL.md` for identity and `MEMORY.md` for memory, in a private git repo; version 2 adds a vector store with keyword search as the fallback.

| What | Taken? |
|---|---|
| Identity and memory as markdown in a private git repo | **Confirms our choice,** arrived at separately. Nothing taken |
| The vector store | **Not taken,** reason 5 |

## BMad Method

[github.com/bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)

| What | Taken? |
|---|---|
| Knowledge gathered in ordered documents (the brief, then what follows) rather than loose notes | **Shared ground.** Heim's numbered documents (decision 26) go further in the same direction |
| A path from an idea to a project | **Built our own:** an idea waits in the idea bank until the person picks it up; then it becomes a project's intake with Saga |

## What we built ourselves

| Part | What |
|---|---|
| **Two cabinets in git** | The work cabinet in each repo (`users/<user>/`) and the private cabinet as the person's own private repo, `<name>-heim`, or a local folder when GitHub is not wanted on a work computer |
| **The file set** | `user`, `soul`, `identity`, `objectives`, `heartbeat`, `achievements`, `people/`, and what goes where |
| **`soul.md` as a behavioural contract** | Built only from the person's own corrections, each with its date, so agents follow what the person actually said |
| **The work cabinet wins** | When the two disagree, the more specific one decides |
| **`private/`** | A subfolder read only by the person's own agent |
| **What never goes in** | Finance, health, family and relationships stay with the person's own agent |
| **The personal part of every handover** | "If you left tomorrow, what would you take with you?" (decision 27), read first at the start |
| **The idea bank** | `ideas.md` in the private cabinet and in each Heim, never emptied, an idea becomes a project only by the person's choice |
