# Writing a skill

How to write each part of a skill so Claude follows the same process on every run. The rules, with their IDs, are in rules.md. This file is the how.

## Contents

- Frontmatter fields
- The description
- The name
- Shape and layout
- How much control to give
- Steps, checks and loops
- Templates, examples, defaults and words
- Scripts and packages
- Hooks for rules that cannot bend
- Writing for newer models
- Tools for judging a line

## Frontmatter fields

Line 1 is `---`. Put a value in double quotes when it holds `: `, starts with `[`, `{`, `@` or a backtick, or holds a backslash. If you do not, the YAML fails and the skill loads with no fields.

| Field | What it does | Works outside Claude Code |
|---|---|---|
| `name` | Lowercase letters, numbers, hyphens; at most 64. It becomes the slash command | Yes |
| `description` | What the skill does and when to use it; at most 1,024 characters | Yes |
| `license`, `compatibility`, `metadata` | The licence; what the skill needs to run (at most 500 characters); your own data | Yes |
| `allowed-tools` | Tools Claude may use without asking, during the turn that starts the skill | Yes |
| `when_to_use` | More trigger words, added after the description | No |
| `disable-model-invocation` | `true`: only a person can start it, and Claude never sees the description | No |
| `user-invocable` | `false`: only Claude can start it; it is hidden from the `/` menu | No |
| `argument-hint`, `arguments` | A hint for autocomplete; named arguments for `$name` | No |
| `paths` | Globs. Claude starts the skill alone only for matching files | No |
| `context`, `agent`, `background` | `context: fork` runs the skill in a subagent with no chat history | No |
| `model`, `effort` | The model or the effort while the skill runs | No |
| `hooks` | Hooks that register when the skill runs and stay for the session | No |
| `shell`, `disallowed-tools` | The shell for injected commands; tools taken away while it runs | No |

For a skill you upload to claude.ai or the Skills API, use only the six fields marked Yes. Any other field makes the upload fail.

Choose who starts the skill by what it does. A job with side effects you want to control (deploy, send, pay) gets `disable-model-invocation: true`. Background knowledge that is not an action gets `user-invocable: false`. Anything else stays model-invoked, and its description costs context on every turn.

## The description

Claude reads only the description before it picks a skill. Write it as a trigger.

1. **What, then when.** One sentence on what the skill does. Then "Use when ..." with the situations and the words people type.
2. **The key use case first.** Claude Code cuts `description` plus `when_to_use` at 1,536 characters in the skill list. When the list is over budget, it drops whole descriptions of skills that rarely run.
3. **Third person.** It goes into the system prompt: "Turns meeting notes into action lists", not "I can help you" or "You can use this".
4. **One trigger per job.** Synonyms for the same job add length, not reach. Keep the distinct jobs.
5. **Say the cases plainly.** Claude tends to use skills too little, not too much. Name the cases where the skill applies; do not hint.

Good:

```yaml
description: Extracts text and tables from PDF files, fills forms and merges documents. Use when the user works with PDFs or mentions forms or document extraction.
```

Too vague to pick out of a hundred skills: "Helps with documents", "Processes data".

A manual-only skill (`disable-model-invocation: true`) is never matched by Claude, so its description can be a one-line summary for people.

## The name

Name the activity. The gerund form is best (`processing-pdfs`, `analysing-spreadsheets`). A noun phrase (`pdf-processing`) or an action (`process-pdfs`) also works. Do not use vague names (`helper`, `utils`, `tools`), general ones (`documents`, `data`), the reserved words "anthropic" and "claude", or a mix of patterns in one set. Keep the `name` field and the folder name the same.

## Shape and layout

SKILL.md is a contents page, not a manual. Claude reads it when the skill starts and opens other files only when a step points to them.

| Shape | Use it when |
|---|---|
| One file | One job, short enough to read in full |
| Bundle | One job, with reference files or scripts that only some runs need |
| Router | Several jobs in one area; a table in SKILL.md sends each job to its own file |

Order SKILL.md by importance. After compaction Claude Code keeps only the first 5,000 tokens of a skill, so the rules that matter most go at the top. Write standing instructions ("check the output after each change"), not one-time steps, because Claude does not read the file again on later turns.

Three ways to keep detail out of the way:

1. **A quick start plus references.** The common path in SKILL.md; each advanced topic in its own linked file.
2. **By area.** One file per area (`reference/finance.md`, `reference/sales.md`), so a sales question never loads finance. Give search hints for big files.
3. **The rare path behind a link.** The common case stays inline.

SKILL.md links every reference file directly, never only through another reference file. A file over 100 lines starts with a `## Contents` list. Name each file for what it holds. Keep backups and drafts outside the skill folder.

## How much control to give

Match how tightly you write a step to how much damage a mistake does.

| Control | Form | Use it when | Example |
|---|---|---|---|
| Light | Plain guidance | Many ways work; context decides | Code review: "check structure, edge cases and readability" |
| Medium | A template, or a script with options | One way is better, some change is fine | `make_report(data, format="markdown")` |
| Tight | An exact script with few or no options | A mistake costs a lot, or the order must not change | `python scripts/migrate.py --verify --backup`, "add no other flags" |

Think of a narrow bridge with drops on both sides: it needs exact rails. An open field needs only a direction.

Two habits from practice:

- **Mix levels in one skill.** A content skill can leave the writing loose and lock the publishing step to one exact command.
- **Ask "what if Claude does this step differently?"** If the answer is "nothing bad", loosen the step. If it is "money spent, data deleted, something published", lock it to a script and put a check before it.

## Steps, checks and loops

For multi-step work, give Claude a checklist to copy into its reply and tick. Each step ends with a "done when" line you can check, and the list says where to go back when a check fails.

```text
Progress:
- [ ] 1 Read the form (run scripts/read_form.py)
- [ ] 2 Write the field map (fields.json)
- [ ] 3 Check the field map (run scripts/check_fields.py)
- [ ] 4 Fill the form
- [ ] 5 Check the result. If it fails, return to step 2.
```

**The loop.** Run the check, fix what failed, check again. Move on only when the check passes. The check does not have to be code: "compare the draft with STYLE.md and list each miss" works the same way.

**Branches.** Name the decision first ("A new document, or a change to one?"), then give each branch its own steps. When a branch grows long, move it into its own file.

**Plan, check, then run.** For batch, destructive or high-stakes jobs, Claude writes the plan to a file (for example `changes.json`), a script checks it, and only then does anything run. Errors show before anything changes, and the plan can change without touching the originals.

## Templates, examples, defaults and words

- **Templates.** Say how strict. "Use this exact shape" for data formats and API responses. "A default; change the sections to fit the material" for reports.
- **Examples.** When style matters, show two or three pairs of input and output. They fix the style faster than any description.
- **One default.** "Use pdfplumber for text. For scanned PDFs that need OCR, use pdf2image with pytesseract." One default and one way out, never a list of five libraries.
- **One word per idea.** Choose "field" and keep it. Different words read as different things.
- **Nothing that goes stale.** State today's method. Put old methods under an `## Old patterns` heading, in a `<details>` block if they are long.

## Scripts and packages

Add a script when the same code would be written again on each run, when the result must be the same every time, or when the logic needs tests.

- **Say run or read.** "Run `scripts/read_form.py` to list the fields" (the default: only the output costs tokens), or "Read `scripts/read_form.py` for the method".
- **Handle errors in the script.** A missing file or a denied permission is handled there, and the script prints what happened.
- **Give each constant a reason.** `TIMEOUT = 30  # most calls finish well inside 30 seconds`, never a bare `47`.
- **Errors say what and how.** "Field 'signature_date' not found. Fields: customer_name, order_total."
- **Put an install line next to the step that needs a package**, for example `pip install pypdf`. Claude Code and claude.ai can install packages. The Claude API has no network and cannot, so a skill for the API can use only what its environment already has.
- **MCP tools by full name.** `BigQuery:bigquery_schema`, not `bigquery_schema`.
- **Claude Code only.** `${CLAUDE_SKILL_DIR}` is the skill's folder, so `python ${CLAUDE_SKILL_DIR}/scripts/x.py` works from any folder. The same variable in `allowed-tools` (for example `Bash(${CLAUDE_SKILL_DIR}/scripts/x.py *)`) lets the script run without a permission prompt.

## Hooks for rules that cannot bend

Claude follows prose with judgment. It can skip a line, and after compaction only the start of a skill stays in context. Claude Code runs a hook on its event whether or not Claude follows the skill. So a rule that must hold on every run (block a dangerous command, run a check before each edit) belongs in a hook.

A skill can carry its own hooks in its frontmatter. They register when the skill starts and stay for the rest of the session. Add `once: true` to a hook that should run only once.

```yaml
---
name: deploying-to-staging
description: Deploys the app to staging, with a safety check on each shell command. Use when the user asks to deploy or ship to staging.
disable-model-invocation: true
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/check-command.sh"
---
```

Keep judgment in prose and hard lines in hooks. Hooks work only in Claude Code; for claude.ai, keep the rule in prose near the top. Full format: https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents

## Writing for newer models

Claude Fable 5, Opus 5.5 and Sonnet 5.5 follow instructions closely and do more on their own. Change five things:

1. **Cut the support they no longer need.** Skills written for older models are often too prescriptive and can make output worse. Find the hand-holding (walkthroughs of things the model knows, long lists of behaviours, common sense restated) and test what happens without it. Delete only what the test shows is not needed (testing.md, "Test before you cut").
2. **Do not ask for the reasoning in the reply.** A request to write out or transcribe the model's reasoning can be refused as reasoning extraction. Ask for the answer, a short reason for it, or a summary of the actions taken.
3. **Give the reason.** "Keep it under 1,536 characters, because Claude Code cuts the list there" lets Claude handle cases the rule did not name, and tells a later editor when the rule has stopped mattering.
4. **Steer lightly.** One short instruction ("give the outcome first, then the detail") works as well as a list of each unwanted behaviour. Keep capitals for real hard lines.
5. **Spell out the check.** Say how and when the work gets checked. For long or high-stakes runs, a checker with fresh context (a subagent that did not do the work, comparing against the spec) usually beats self-review.

## Tools for judging a line

These ideas come from Matt Pocock's "writing-great-skills".

- **The goal is the same process.** A skill works when Claude follows the same process each run, not when it gives identical output.
- **The no-op test.** For each sentence, ask: would Claude act differently without it? If not, delete the whole sentence; do not trim words.
- **Loaded words.** A short idea the model already knows (a "tight" loop, a "red" test) can replace a sentence of explanation. Use the same word in the description and the body, so both point at the same behaviour.
- **Finish lines.** "Make a change list" invites a rushed finish. "Every changed file has a line in the list" does not. Make each "done when" checkable and, where it matters, complete.
- **When to split.** Split off a new model-invoked skill only when it has its own trigger words or another skill must reach it, because each description costs context on every turn. Move a long run of steps into separate files when the later steps tempt Claude to rush the current one.
- **One rule, one place.** When new evidence arrives, find the idea behind it and rewrite the rule around that idea. Do not add a new block under the old one. A good change usually makes the file shorter.
