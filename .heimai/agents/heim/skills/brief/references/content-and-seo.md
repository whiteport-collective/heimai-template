# Content and search: `10-content-language.md` and `21-keyword-analysis.md`

Read it when voice, languages, content or search come up. Both documents are strategy: what the person envisions and what their users look for. Layouts, page specs and the technical side of search (speed, headers, schema, image sizes) belong to Freya and Mimir.

## Content structure: what the person envisions it holding

Without it, Freya designs flows through pages that do not exist in the person's head. Capture principles, not specifications: "the services are reachable from everywhere" is a principle; "a three-column grid of service cards" is a design decision for later.

**Understood when Saga can say:**

1. What kind of thing it is: one page, several pages, an app, a platform.
2. What content the person envisions, at whatever detail they have.
3. What must be seen first, without scrolling, and what is secondary.
4. How people should find things, as principles (not a menu design).
5. What is explicitly left out, and what waits for later.
6. How clear the person's picture is.

**Match the person's readiness.** Specific ("one page: what we fix, where we are, our number") is written as strong direction. Exploring ("four or five pages, maybe") is written with its open questions. Blank ("you tell me") is written as open, with whatever preferences came up. All three are good outcomes; never force a decision the person is not ready to make.

**An example**, for a fictional bicycle workshop in Exempelby:

```markdown
## Content Structure
One page, phone first. "People with a flat tyre want three things fast: can you fix it, where are you, what's your number."
- First, without scrolling: the phone number, what we repair, the address and opening hours.
- Then: the story, the reviews.
- Always reachable: the phone number.
- Not included: online booking (they want calls), a blog.
- Clarity: very specific, from what customers ask on the phone.
```

## Keyword analysis: what the target users search for

1. **Start from the target users** in `01-brief.md`: what each of them searches for when the problem appears, when they compare, and when they are ready to act.
2. **Gather** what exists: words the person wants to be found for, what competitors are found for, what customers actually say.
3. **Per language, natively.** Keywords are not translated; ask what a native speaker would type, the local words, the common misspellings, the long phrases.
4. **Measure** volumes with a tool or a search console when one is at hand, and say where each figure comes from and when it was read; an estimate is marked *(estimate)*.
5. **One main keyword per page,** in a page and keyword table. Freya reads it when she specifies each page.
6. **The URL pattern** is decided here with its reason: one folder per language (`/en/`) as the default, translated slugs where the person wants them; lowercase, hyphens, no special characters.

| Intent | Example (the fictional workshop) |
|---|---|
| A service | "cykelreparation Exempelby" (bicycle repair Exempelby) |
| Near me | "cykelverkstad nära mig" (bicycle workshop near me) |
| A problem | "byta innerslang" (change an inner tube) |
| The name | "Cykelverkstaden Exempelby" |
| Knowledge | "hur ofta serva cykeln" (how often to service a bike) |

Local search, structured data and the technical checklist are decided with the platform requirements and carried out in the build; Saga notes in `20-platform-requirements.md` that the site needs them, and leaves how to Freya and Mimir.
