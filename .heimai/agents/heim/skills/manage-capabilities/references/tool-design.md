# Designing a tool

A tool holds how: the commands, the calls and the script, so the skill can hold only what and why. Settle the design one topic at a time, proposing a default for each.

1. **Read what exists first:** the catalog, any tool with a similar name, commands already written inside skills (they belong here), and the service's own documentation.
2. **Type:** an HTTP API first, then a CLI, then a script in the tool's own folder. No MCP server in a session; a service that only offers one is called once by a script that starts it for that call and stops it.
3. **Actions:** which only read (safe to run on its own), and which write. A writing action shows what it would do and acts only with `--yes`, never overwrites what exists, and refuses with a clear message and its own exit code.
4. **Credentials:** which password manager item holds the key, and whether each person logs in with their own account or one shared account is used. The value is never written anywhere.
5. **Folders:** found through the floor plan with `heim-floor`, never by a fixed path, so the move to `.heimai/` costs nothing.
6. **Server-side work** (a webhook, OAuth on a server, a cache): write a specification first (what it does, what data it touches and where it runs, how it is authenticated, how it is stopped, what it costs) and get it approved. No code before that. Approved work goes to Mimir as a build.
7. **Unknowns:** a behaviour the documentation does not settle is written as an open question in `tool.md`, never guessed.

## `tool.md`

The front matter from [front-matter.md](front-matter.md); then what the tool is for in a paragraph, the commands in a code block, what it does and refuses, what it prints (and its `--json` form, if a page or another tool reads it), its exit codes, and what it does not do yet. Python 3.10+ with the standard library and PyYAML, or Node with no dependencies, unless the tool says why.

Test it on a scratch Heim and, read-only, on a real one before it is called done; write in `tool.md` what it was tried on.
