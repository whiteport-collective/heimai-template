# A new or second computer

The person already has a Heim and is adding or moving to a computer ("ny dator", "I'm setting up my Mac"). Do the work on the computer that already works, so the new one only has to follow a handover.

On the working computer, write a handover to Idun in the person's own Heim, with everything the new computer needs under `## Next`, in order:

1. **The programs:** git, the GitHub CLI and Python 3.10 or newer (on a Mac, Homebrew first and ahead of Apple's Python in the path). `machine check` on the new computer shows what is missing.
2. **The login:** `gh auth login` in the browser, and the pending invitations the person expects.
3. **The repos:** every Heim this computer should have, as `<owner>/<repo>` and where it goes relative to the dev root, taken from the person's own Heim, so every agent and handover finds them in the same place as on this computer. Not every computer reaches every Heim: an employer's computer gets only the private Heim and the job's (ask once which).
4. **The per-computer file:** the lines for the new computer (`user`, `github`, `name`, `language`, `private`, `dev_root`), with its own paths.
5. **What differs per computer** and lives in the person's own Heim under this computer's name: the large-file folder, the screens and the microphone, named the first time they are used.

No passwords or keys in the handover: logins happen in the browser and keys stay in the password manager.

Commit and push the handover, and give the person one sentence to say on the new computer, in their language, in its own code block:

```
Set up Heim and take the handover <owner>/<name>-heim <timestamp>
```

On the new computer the person installs their AI tool and says that sentence; Idun takes the handover and walks the list, one step and one yes at a time.

**A person without GitHub on this computer** (their own Heim is a local folder): the handover cannot travel through git. Write it as a file the person carries over themselves, or set the new computer up from the beginning; say which in one line.
