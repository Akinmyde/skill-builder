# skill-builder

skill-builder is a Claude skill for people who write skills. It reads a skill the way Claude will meet it, measures it against 46 rules drawn from Anthropic's documentation, and tells you what to fix, line by line. It can also start a new skill for you, or rework an old one after it misbehaves.

It never edits a skill on the first pass. You see the findings, you choose, and only then does anything change.

## What goes wrong with skills

Most skill problems are invisible until a run goes badly:

- **It never starts.** Claude chooses a skill from its description alone. A vague description, or YAML that fails to parse, and the skill sits unused.
- **It forgets half way.** After compaction, Claude Code keeps only the first 5,000 tokens of a skill. Rules near the bottom disappear.
- **It reads part of a file.** A file reached only through another file may get a quick preview instead of a full read.
- **It over-steers a new model.** Anthropic's Fable 5 guide warns that skills written for earlier models are often too prescriptive and can lower quality. Requests to write out the model's reasoning can now be refused.

skill-builder looks for all of these, and more.

## Quick start

1. Copy the repository into your skills folder (see the next section).
2. In Claude Code, ask: *"Check my deploy skill."*
3. Read the report, then reply with the numbers of the fixes you want.

## Adding it to Claude

**Claude Code, all projects.** Clone it into your personal skills folder:

```bash
git clone https://github.com/Akinmyde/skill-builder ~/.claude/skills/skill-builder
```

**Claude Code, one project.** Run this from the project's root instead:

```bash
git clone https://github.com/Akinmyde/skill-builder .claude/skills/skill-builder
```

The folder must be named `skill-builder`, to match the skill's name. On Windows the personal folder is `.claude\skills` inside your user folder; downloading the ZIP and unpacking it there also works.

**claude.ai.** Make a ZIP of `SKILL.md`, `LICENSE`, `references/` and `scripts/` (the `examples/` folder is not needed), then upload it from the Skills page in your settings. Turn on code execution so the checker can run.

## How to use it

skill-builder does three jobs. Pick the one that matches your situation, and ask in plain words; you do not need a command.

### Check a skill, then fix it

**When:** before you share a skill, after you change one, when a skill behaves oddly, or when you move to a newer model.

**Ask:** *"Check my deploy skill."* For a whole folder: *"Go through ~/.claude/skills and tell me what to fix first."*

**What happens:**

1. Claude runs the checker on the skill, then reads every file in it.
2. Claude marks all 46 rules as fail, not applicable or pass, with the file and line for each.
3. Claude shows you the report in the chat, with a numbered list of fixes, biggest effect first. It stops there and changes nothing.
4. **You reply with the numbers of the fixes you want**, for example *"Apply 1, 2 and 4."* Reply *"all"* to take every fix, or *"none"* to stop.
5. Claude makes only those changes, then runs the checker again. If a new problem shows up, it fixes that before it reports back.

For a folder, Claude first shows one summary line per skill, then writes full reports for the skills you pick (by default, the five with the most errors).

### Build a new skill

**When:** you keep doing the same task with Claude and keep explaining the same things.

**Ask:** *"Turn this into a skill, we write release notes like this every Friday."*

**What happens:** Claude writes three test prompts and records how it does without a skill, then creates the skill folder, fills it in and checks it. **You review the test results** and say whether the skill does the job.

### Improve a skill after it went wrong

**When:** a skill missed something, or you corrected Claude while it was using one.

**Ask:** *"The report skill keeps forgetting the date filter. Fix it."*

**What happens:** Claude finds the idea behind the miss, rewrites the rule around it near the top of the skill, and runs the checker. The skill usually gets shorter. **You check the change** before you rely on it.

Asking it to *"improve my skill for Opus 5.5"* does a check first, then improves the skill with the fixes you choose.

### Where the report goes

The report appears in the chat; nothing is saved to a file unless you ask. To keep it, add that to your request, for example *"Check my deploy skill and save the report to reports/deploy.md."* The checker script prints to the terminal, or JSON with `--json`, which you can send to a file with `> report.json`.

For a full example, see [the sample report](examples/notes-helper-report.md) on a skill that is broken on purpose.

## Running the checker yourself

`scripts/check_skill.py` decides the rules a program can decide, in about a second. It runs on Python 3.8 or later with nothing to install, on macOS, Linux and Windows.

- Check one skill: `python3 scripts/check_skill.py path/to/skill`
- Check every skill in a folder, as one summary: `python3 scripts/check_skill.py --all path/to/skills`
- Get JSON for another tool: add `--json`
- Leave a rule out for this run: add `--skip valid-name`
- Also flag em dashes, as a house style: add `--no-em-dash`
- Start a new skill: `python3 scripts/new_skill.py my-skill --path path/to/skills` (add `--references`, `--scripts` or `--manual` as needed)

The checker exits with `0` when there are no errors, `1` when there are errors, and `2` when it could not run at all.

Each line of output gives the level, the rule, the file and line, and the fix. A few lines from the sample skill:

```text
Skill: examples/notes-helper (name: Notes_Helper)
  ERROR  frontmatter-loads        SKILL.md:3  the description value holds ': ', which YAML reads as a new key, so the frontmatter will not parse. Fix: wrap the value in double quotes.
  ERROR  one-hop                  reference/formats.md:5  reference/action-items.md is reached only through reference/formats.md, never from SKILL.md, so Claude may read only its start. Fix: link it from SKILL.md, or fold it into reference/formats.md.
  WARN   third-person             SKILL.md:3  the description is not in third person ("I can"). It goes into the system prompt. Fix: write "Fills PDF forms", not "I can" or "You can".
  WARN   no-reasoning-transcript  SKILL.md:19  this asks Claude to write out its reasoning ("Think step by step and write"). Newer models may refuse it as reasoning extraction. Fix: ask for the answer and a short reason for it.
  ...
Result: 7 error(s), 10 warning(s), 6 note(s) - fix the errors first.
```

The complete output is in [examples/notes-helper-check.txt](examples/notes-helper-check.txt).

### What it ignores on purpose

Some matches look like problems but are not, so the checker leaves them alone:

- words inside code, inline code or quotes, such as a line that tells Claude to search for "TODO";
- test folders, fixtures, build output and package manifests;
- placeholder links like `{path}` or `(link)`;
- comments inside a YAML list;
- a full Windows path such as `C:\Users\...` that a skill mentions on purpose (relative paths with backslashes are still flagged);
- a subfolder that is a skill of its own, which is reported once rather than checked as part of its parent.

### Team exceptions

When your team has a rule that overrides one of these, write it down in a `skill-builder.json` file, either in the skill's folder or in the folder that holds your skills. The checker reads both, whether you check one skill or use `--all`:

```json
{"skip": {"valid-name": "our skill names use a colon namespace, such as team:deploy"}}
```

The rule is then shown as skipped in every report, together with your reason, so nobody mistakes it for a pass.

## The 46 rules

The rules fall into ten groups. Each line below is a one-sentence summary, written from Anthropic's pages. The full text, with the reason and the check for each rule, is in [references/rules.md](references/rules.md).

Each rule ends with who checks it: *script* (the checker decides), *script + read* (the checker flags candidates and Claude confirms each one in context) or *read* (Claude judges it during a check and cites the evidence). *Practice* marks a rule that comes from experience rather than from Anthropic's docs.

### The header

- **frontmatter-loads**: the `---` block opens on the very first line and its YAML parses; otherwise the skill loads with every field empty. *Script.* [Claude Code: frontmatter][cc-fm]
- **valid-name**: at most 64 lowercase letters, numbers and hyphens, no XML tags, no "anthropic" or "claude", and the same as the folder, since the folder is the default name. *Script.* [Best practices: frontmatter][bp-yaml]
- **name-says-the-job**: the name tells a reader what the skill does (`processing-pdfs`), not `helper` or `data`, and one naming style runs through the whole set. *Script + read.* [Best practices: naming][bp-naming]
- **known-fields**: every field is spelled the way Claude Code expects, because it skips unknown ones in silence; only six fields survive a claude.ai upload or the Skills API. *Script.* [Claude Code: outside Claude Code][cc-portable]
- **who-starts-it**: you, Claude or both, chosen on purpose; a manual-only skill also drops its description from context and is not preloaded into subagents. *Read.* [Claude Code: who invokes a skill][cc-invoke]

### The trigger

- **description-in-limits**: a description exists, holds no XML tags and stays within 1,024 characters. *Script.* [Best practices: frontmatter][bp-yaml]
- **third-person**: it describes the skill ("Processes Excel files") because it is placed in the system prompt, never "I can" or "You can". *Script + read.* [Best practices: descriptions][bp-desc]
- **what-and-when**: it names what the skill does and the situations that should start it, in the terms people use, since Claude picks from many skills on this text alone. *Script + read.* [Best practices: descriptions][bp-desc]
- **key-use-first**: the main use case leads, because Claude Code cuts the listing at 1,536 characters and drops the least-used descriptions when the list runs over budget. *Script + read.* [Claude Code: descriptions cut short][cc-cut]

### The layout

- **short-body**: under 500 lines, because a loaded body stays in context and costs tokens on every later turn. *Script.* [Best practices: progressive disclosure][bp-pd]
- **key-rules-first**: what matters most is near the top, because compaction keeps only the first 5,000 tokens of a skill. *Script + read.* [Claude Code: stops following][cc-stops]
- **split-by-topic**: SKILL.md is the overview; detail lives in files by area or by case, so a task opens only what it needs. *Read.* [Best practices: progressive disclosure][bp-pd]
- **one-hop**: SKILL.md links every reference file itself, because Claude may only preview a file it reaches through another one. *Script.* [Best practices: nested references][bp-nested]
- **contents-list**: a reference file over 100 lines opens with a table of contents, so a partial read still shows its scope. *Script.* [Best practices: contents list][bp-toc]
- **reachable-files**: every file is linked or named, every link resolves, no backups sit in the folder, and file names say what they hold. *Script + read.* [Best practices: runtime environment][bp-runtime]
- **forward-slashes**: paths use `/`, which works everywhere; backslashes fail on Unix. *Script.* [Best practices: Windows paths][bp-paths]

### The writing

- **earns-its-tokens**: each paragraph gives Claude something it lacks; say what to do, not why or how at length. *Read.* [Best practices: concise][bp-concise]
- **control-matches-risk**: loose guidance where many ways work, a template where one is better, an exact script where a slip is costly. *Read.* [Best practices: degrees of freedom][bp-freedom] + practice
- **no-expiry-dates**: nothing that turns false with time; old methods go under "Old patterns". *Script + read.* [Best practices: time-sensitive text][bp-time]
- **one-word-per-idea**: one term per thing, every time ("field", never box or element). *Read.* [Best practices: terminology][bp-terms]
- **template-strictness**: each output template says whether its shape is fixed or a default. *Read.* [Best practices: templates][bp-template]
- **show-examples**: where style decides quality, show input and output pairs. *Read.* [Best practices: examples][bp-examples]
- **one-default**: name one approach and one exception, not a list of every tool that could work. *Read.* [Best practices: too many options][bp-options]
- **full-tool-names**: MCP tools carry their server (`GitHub:create_issue`), or Claude may not find them. *Read.* [Best practices: MCP tools][bp-mcp]
- **nothing-unfinished**: no TODO, FIXME or `[FILL: ...]` left in. *Script.* Practice
- **one-rule-one-place**: each rule is stated once, and new guidance replaces the old wording. *Read.* Practice

### The flow

- **checklist**: hard work comes as ordered steps Claude copies and ticks, each with a checkable result and a step to return to on failure. *Script + read.* [Best practices: workflows][bp-workflows]
- **check-and-fix-loop**: check, fix, check again, with a script or a style guide as the check. *Read.* [Best practices: feedback loops][bp-loops]
- **plan-check-run**: risky or batch work writes a plan file, a script checks it, then it runs. *Read.* [Best practices: verifiable outputs][bp-plan]
- **standing-instructions**: "after every edit", not "once", because Claude Code never re-reads the skill on later turns. *Read.* [Claude Code: skill lifecycle][cc-lifecycle]

### Code and scripts

- **scripts-handle-errors**: a script deals with the failures it can expect instead of passing them to Claude. *Read.* [Best practices: solve, don't defer][bp-solve]
- **explained-constants**: every setting says why it has its value; no "voodoo constants". *Read.* [Best practices: solve, don't defer][bp-solve]
- **run-or-read**: the skill says whether to run a script (the usual case, only its output costs tokens) or read it. *Read.* [Best practices: utility scripts][bp-scripts]
- **helpful-errors**: messages name the exact problem and the valid choices. *Read.* [Best practices: verifiable outputs][bp-plan]
- **install-lines**: packages are listed with their install line; claude.ai can install them, the Claude API cannot. *Script + read.* [Best practices: packages][bp-packages]

### Newer models

- **not-overprescribed**: no hand-holding a capable model does not need, removed only after a test proves it. *Read + test.* [Fable 5: scaffolding changes][f5-scaffold]
- **no-reasoning-transcript**: never ask Claude to echo or explain its internal reasoning in the reply; that can trigger a refusal. A short reason for the answer is fine. *Script + read.* [Fable 5: scaffolding changes][f5-scaffold], [Opus 5.5][o55-thinking]
- **reasons-given**: each request says what it is part of, who it is for and what the result enables. *Read.* [Fable 5: give the reason][f5-reason]
- **light-steering**: one short instruction instead of a list, capitals only for real hard lines. *Script + read.* [Fable 5: instruction following][f5-steer] + practice
- **independent-check**: long work says how it gets checked, against real tool results, by a fresh-context checker rather than self-review. *Read.* [Fable 5: scaffolding changes][f5-scaffold]

### Guards

- **hard-rules-in-hooks**: a rule that must hold every time is a hook in the skill's frontmatter, because hooks run whether or not Claude follows the text. *Script + read.* [Claude Code: stops following][cc-stops], [hooks in skills][hooks]

### Testing

- **tests-first**: three test cases from real gaps and a no-skill baseline, before the skill is written. *Read.* [Best practices: evaluations first][bp-evals]
- **fresh-session-test**: real prompts in a new session, skill on and off, watching which files Claude opens. *Read.* [Best practices: iterate with Claude][bp-ab], [Claude Code: evaluate][cc-evals]
- **model-coverage**: tried on each model meant to run it: Haiku for enough guidance, Sonnet for clarity, Opus for over-explaining. *Read.* [Best practices: test with all models][bp-models] + practice

### The skill set

- **unique-triggers**: no two skills claim the same requests. *Read.* Practice
- **unused-skills-off**: skills that never run are found with `/skill-doctor` and turned off, since every listed skill costs context on every turn. *Read.* [Claude Code: unused skills][cc-unused]

## Licence

MIT licence: see [LICENSE](LICENSE).

[bp-concise]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#concise-is-key
[bp-freedom]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#set-appropriate-degrees-of-freedom
[bp-models]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#test-with-all-models-you-plan-to-use
[bp-naming]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#naming-conventions
[bp-desc]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions
[bp-pd]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#progressive-disclosure-patterns
[bp-nested]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#avoid-deeply-nested-references
[bp-toc]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#structure-longer-reference-files-with-table-of-contents
[bp-workflows]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#use-workflows-for-complex-tasks
[bp-loops]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#implement-feedback-loops
[bp-time]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#avoid-time-sensitive-information
[bp-terms]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#use-consistent-terminology
[bp-template]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#template-pattern
[bp-examples]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#examples-pattern
[bp-evals]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#build-evaluations-first
[bp-ab]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#develop-skills-iteratively-with-claude
[bp-paths]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#avoid-windows-style-paths
[bp-options]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#avoid-offering-too-many-options
[bp-solve]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#solve-dont-defer
[bp-scripts]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#provide-utility-scripts
[bp-plan]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#create-verifiable-intermediate-outputs
[bp-packages]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#package-dependencies
[bp-runtime]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#runtime-environment
[bp-mcp]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#mcp-tool-references
[bp-yaml]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#yaml-frontmatter-requirements
[cc-fm]: https://code.claude.com/docs/en/skills#frontmatter-reference
[cc-portable]: https://code.claude.com/docs/en/skills#using-skill-frontmatter-outside-claude-code
[cc-invoke]: https://code.claude.com/docs/en/skills#control-who-invokes-a-skill
[cc-lifecycle]: https://code.claude.com/docs/en/skills#skill-content-lifecycle
[cc-stops]: https://code.claude.com/docs/en/skills#claude-stops-following-a-skill
[cc-cut]: https://code.claude.com/docs/en/skills#skill-descriptions-are-cut-short
[cc-evals]: https://code.claude.com/docs/en/skills#evaluate-and-iterate-on-a-skill
[cc-unused]: https://code.claude.com/docs/en/skills#find-unused-skills
[hooks]: https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents
[f5-scaffold]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5#recommended-scaffolding-changes
[f5-steer]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5#strong-instruction-following
[f5-reason]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5#give-the-reason-not-only-the-request
[o55-thinking]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5#prompts-written-for-thinking-disabled
