# The rules

The 46 rules this skill checks, in ten groups. Each rule has a short name, a definition, why it matters, how it is checked and where it comes from. The definitions are written from Anthropic's own pages, listed under Sources. How to write each part is in writing.md; testing is in testing.md.

## Contents

- How to mark a rule
- The header
- The trigger
- The layout
- The writing
- The flow
- Code and scripts
- Newer models
- Guards
- Testing
- The skill set
- Patterns to name in a fix
- The report
- Sources

## How to mark a rule

Mark every rule **Pass**, **Fail** or **N/A**, and give the evidence.

- **Checked by the script.** `check_skill.py` decides. Pass means it reports no ERROR or WARN under that rule's name. A NOTE alone is a pass; mention it when it matters.
- **Flagged by the script, confirmed by a read.** The script lists candidates. Read each one where it sits and decide. A match inside a quoted example, a test file or a template is not a fail.
- **Judged by a read.** Cite the file and line that shows the pass or the fail. "Looks fine" is not evidence.
- **N/A** only when the rule cannot apply, for example the code rules in a skill with no code. Say why.

A team can skip a rule on purpose in `skill-builder.json`, for example `{"skip": {"valid-name": "our names use a colon namespace"}}`. The report then shows the rule as skipped, with the reason. Use it when a house rule wins, never to hide a fail.

## The header

**frontmatter-loads.** The frontmatter is the YAML block between two `---` lines, and Claude Code looks for it only when the first `---` is the very first line of SKILL.md. If the opening line is anything else, the whole file, markers included, is read as instructions. If the YAML inside fails to parse, the skill still loads, but with every field empty, so it has no description to be found by.
*Why:* a skill with empty fields cannot start on its own. *Checked by* the script. *Source:* Claude Code skills, frontmatter reference.

**valid-name.** The name is at most 64 characters of lowercase letters, numbers and hyphens, holds no XML tags, and does not use the reserved words "anthropic" or "claude". In Claude Code it is also the command shown in the `/` menu, and it defaults to the folder name, so keep the two the same.
*Why:* the Skills API refuses a name that breaks the format, and a name that differs from its folder is hard to find. *Checked by* the script. *Source:* Best practices, frontmatter requirements; Claude Code skills, frontmatter reference.

**name-says-the-job.** A reader can tell what the skill does from its name alone. Anthropic suggests the verb-plus-ing form (`processing-pdfs`, `testing-code`) and accepts noun phrases (`pdf-processing`) or plain actions (`process-pdfs`). Vague names (`helper`, `utils`) and overly general ones (`data`, `files`) fail, and so does a mix of naming styles across one set of skills.
*Why:* consistent, descriptive names make skills easy to mention, search and organise. *Flagged by* the script, *confirmed by* a read. *Source:* Best practices, naming conventions.

**known-fields.** Every frontmatter field is one Claude Code knows, spelled exactly as listed, hyphens included. Claude Code skips an unknown field without a word. A claude.ai upload, the Skills API and Anthropic's packaging script accept only six fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`) and stop with an error on anything else.
*Why:* a misspelt field does nothing and no one is told; an extra field blocks an upload. *Checked by* the script. *Source:* Claude Code skills, frontmatter reference and frontmatter outside Claude Code.

**who-starts-it.** The skill's start mode is chosen on purpose. By default both you and Claude can start it, and its description sits in context all the time. `disable-model-invocation: true` means only a person starts it with `/name`; its description leaves Claude's context, and it is not preloaded into subagents or run by scheduled tasks. `user-invocable: false` hides it from the `/` menu so that only Claude starts it.
*Why:* a skill with side effects (deploy, send, pay) should wait for a person, and background knowledge should not clutter the menu. *Judged by* a read; the script catches only a skill that nobody can start. *Source:* Claude Code skills, control who invokes a skill.

## The trigger

**description-in-limits.** The description exists, is no longer than 1,024 characters and holds no XML tags.
*Why:* Claude reads the description, and only the description, when it decides which skill fits a request. *Checked by* the script. *Source:* Best practices, frontmatter requirements.

**third-person.** The description speaks about the skill, not as it: "Processes Excel files and generates reports", never "I can help you" or "You can use this to".
*Why:* the text is placed into the system prompt, and a shifting point of view makes skills harder to pick. *Flagged by* the script, *confirmed by* a read. *Source:* Best practices, writing effective descriptions.

**what-and-when.** The description says what the skill does and the situations that should start it, with the key terms people use. A vague line such as "Helps with documents" fails.
*Why:* Claude may choose among a hundred or more skills, and the description is all it has to go on. *Flagged by* the script, *confirmed by* a read. N/A for the "when" part of a manual-only skill, because Claude never sees that description. *Source:* Best practices, writing effective descriptions.

**key-use-first.** The most important use case opens the description, and the description plus `when_to_use` fits in 1,536 characters.
*Why:* Claude Code cuts the combined text at 1,536 characters in its skill list. When the list outgrows its budget (about 1% of the context window), it drops whole descriptions, starting with the skills used least. *Flagged by* the script, *confirmed by* a read. *Source:* Claude Code skills, frontmatter reference and descriptions cut short.

## The layout

**short-body.** The SKILL.md body stays under 500 lines. Near that size, split detail into separate files.
*Why:* once a skill loads, its body stays in context for the rest of the conversation, so every line costs tokens on every later turn. *Checked by* the script. *Source:* Best practices, progressive disclosure; Claude Code skills, skill content lifecycle.

**key-rules-first.** The instructions that matter most sit near the top of SKILL.md.
*Why:* when Claude Code compacts a conversation, it re-attaches each skill's most recent copy but keeps only its first 5,000 tokens, within a shared budget of 25,000 tokens filled from the most recently used skill. An older skill can be dropped altogether. *Flagged by* the script (it shows where the 5,000-token cut falls), *confirmed by* a read. *Source:* Claude Code skills, skill content lifecycle and Claude stops following a skill.

**split-by-topic.** SKILL.md works as an overview that points to detail, like the contents page of a guide. Detail sits in separate files by area (finance in one, sales in another) or by case (the common path inline, the rare path behind a link), so a task reads only what it needs.
*Why:* bundled files cost nothing until Claude opens one. *Judged by* a read. *Source:* Best practices, progressive disclosure.

**one-hop.** Every reference file is linked straight from SKILL.md, not only from another reference file.
*Why:* when Claude meets a link inside a linked file, it may preview it with a command such as `head -100` instead of reading it, and so work from part of the file. *Checked by* the script. *Source:* Best practices, avoid deeply nested references.

**contents-list.** A reference file longer than 100 lines opens with a table of contents.
*Why:* a partial read still shows everything the file covers. *Checked by* the script. *Source:* Best practices, table of contents.

**reachable-files.** Every bundled file is linked or named somewhere Claude will look, every link resolves, no backup copies sit in the folder, and file names say what they hold (`form_validation_rules.md`, not `doc2.md`). Folders are arranged by area or feature, not as `docs/file1.md`.
*Why:* Claude moves through a skill like a file system and opens files by their names and links. A file nobody names is never read. *Flagged by* the script, *confirmed by* a read. *Source:* Best practices, runtime environment; observe how Claude navigates skills.

**forward-slashes.** File paths use forward slashes (`scripts/helper.py`), even on Windows.
*Why:* forward slashes work on every system; backslash paths fail on Unix. *Checked by* the script. *Source:* Best practices, avoid Windows-style paths.

## The writing

**earns-its-tokens.** Each piece of text gives Claude something it does not already have. Ask of every paragraph: does Claude need this explanation, can I assume it knows this, is it worth its tokens? State what to do rather than narrate how or why.
*Why:* the context window is shared with the system prompt, the conversation and every other skill, and Claude is already capable. *Judged by* a read. *Source:* Best practices, concise is key; Claude Code skills, skill content lifecycle.

**control-matches-risk.** How tightly a step is specified follows how fragile it is. Plain guidance where several approaches work and context decides. A template or a script with options where one pattern is preferred. An exact script with few or no options where a slip is costly or the order must not change. One skill can mix levels, and asking "what if Claude does this differently?" shows which a step needs.
*Why:* a narrow path with drops on both sides needs rails; an open field needs only a direction. *Judged by* a read. *Source:* Best practices, set appropriate degrees of freedom; the mix and the question come from practice.

**no-expiry-dates.** The skill holds nothing that becomes wrong with time, such as "before August 2025, use the old API". The current method is stated plainly; older methods move to an "Old patterns" section.
*Why:* a dated rule turns false without anyone noticing. *Flagged by* the script, *confirmed by* a read. *Source:* Best practices, avoid time-sensitive information.

**one-word-per-idea.** One term names one thing throughout: always "field", never field, box, element and control in turn; always "extract", never pull, get and retrieve.
*Why:* consistent terms help Claude parse and follow instructions. *Judged by* a read. *Source:* Best practices, use consistent terminology.

**template-strictness.** A template for output says how closely to follow it. Strict for API responses and data formats ("use this exact structure"); a flexible default elsewhere ("adjust the sections as needed").
*Why:* without the cue, Claude has to guess whether the shape is fixed. *Judged by* a read. *Source:* Best practices, template pattern.

**show-examples.** Where the quality of the output depends on style, the skill shows pairs of input and output, as in ordinary prompting.
*Why:* a few real pairs pin down style faster than a description of it. *Judged by* a read. *Source:* Best practices, examples pattern.

**one-default.** The skill names one approach and, where needed, one exception: "Use pdfplumber for text; for scanned PDFs that need OCR, use pdf2image with pytesseract." It does not list every tool that could work.
*Why:* a list of equal options leaves Claude to choose with less context than the author had. *Judged by* a read. *Source:* Best practices, avoid offering too many options.

**full-tool-names.** MCP tools are named with their server: `BigQuery:bigquery_schema`, `GitHub:create_issue`.
*Why:* without the server prefix, Claude may not find the tool, above all when several MCP servers are connected. *Judged by* a read. *Source:* Best practices, MCP tool references.

**nothing-unfinished.** No TODO or FIXME markers and no `[FILL: ...]` placeholders from the scaffold remain. A sentence that only mentions the word TODO is fine.
*Why:* an unfinished line reads to Claude as an instruction it cannot carry out. *Checked by* the script. *Source:* practice.

**one-rule-one-place.** Each rule is stated once. New guidance is folded into the rule it changes, and the old wording goes.
*Why:* copies drift apart, and every repeat costs tokens on every turn. *Judged by* a read. *Source:* practice.

## The flow

**checklist.** Complex work is broken into clear steps in order. For the hardest workflows, the skill gives a checklist that Claude copies into its reply and ticks as it goes. Each step ends with a result someone can check, and the list says which step to return to when a check fails.
*Why:* a visible list keeps Claude from skipping steps or stopping early. *Flagged by* the script (it looks for the line that sends Claude back), *confirmed by* a read. *Source:* Best practices, use workflows for complex tasks.

**check-and-fix-loop.** Output where quality matters runs through a loop: check, fix the errors, check again. The check can be a validator script or a style guide Claude compares the draft against.
*Why:* Anthropic says this loop greatly improves output quality. *Judged by* a read. *Source:* Best practices, implement feedback loops.

**plan-check-run.** For batch work, destructive changes, complex validation or high-stakes jobs, Claude first writes the plan in a structured file (for example `changes.json`), a script checks the plan, and only then do the changes run. The full sequence is: analyse, plan, check the plan, run, verify.
*Why:* errors show up before anything changes, a script gives an objective check, and the plan can be revised without touching the originals. *Judged by* a read. *Source:* Best practices, create verifiable intermediate outputs.

**standing-instructions.** Guidance meant for the whole task is written to hold for the whole task: "Run the tests after every edit", not "Run the tests".
*Why:* Claude Code adds the skill's text to the conversation once and does not read the file again on later turns. *Judged by* a read. *Source:* Claude Code skills, skill content lifecycle and Claude stops following a skill.

## Code and scripts

All five are N/A when the skill has no code.

**scripts-handle-errors.** A script deals with the failures it can expect (a missing file, a denied permission) and reports what it did, instead of failing and leaving the problem to Claude.
*Why:* Claude has less context about the failure than the script's author. *Judged by* a read. *Source:* Best practices, solve, don't defer.

**explained-constants.** Every setting in a script says why it has its value: `REQUEST_TIMEOUT = 30  # most HTTP requests finish within 30 seconds`.
*Why:* if the author does not know the right value, Claude cannot work it out either. Anthropic calls unexplained values "voodoo constants". *Judged by* a read. *Source:* Best practices, solve, don't defer.

**run-or-read.** The skill says whether Claude should run each script ("Run `analyze_form.py` to extract the fields") or read it as reference ("See `analyze_form.py` for the extraction method"). Running is the usual choice.
*Why:* a script that runs costs only its output in tokens, and it is more reliable than code Claude writes on the spot. *Judged by* a read. *Source:* Best practices, provide utility scripts and runtime environment.

**helpful-errors.** Script messages name the exact problem and what is available: "Field 'signature_date' not found. Available fields: customer_name, order_total, signature_date_signed".
*Why:* a specific message lets Claude fix the problem in one try. *Judged by* a read. *Source:* Best practices, create verifiable intermediate outputs.

**install-lines.** The packages the skill needs are listed in SKILL.md, with the line that installs them.
*Why:* where a skill runs decides what it can install. claude.ai can install from npm and PyPI and pull from GitHub; the Claude API has no network access and cannot install anything at run time. *Flagged by* the script, *confirmed by* a read. *Source:* Best practices, package dependencies.

## Newer models

Anthropic's prompting guides for Claude Fable 5 and Opus 5.5 ask for changes to skills written for earlier models. Fable 5 in particular follows instructions closely enough that heavy steering now does harm.

**not-overprescribed.** The skill does not over-direct a capable model: no walkthroughs of things the model knows, no long lists of behaviours, no common sense spelled out. Candidates are removed only after a test shows the model does as well without them.
*Why:* Anthropic says skills written for earlier models are often too prescriptive for Fable 5 and can lower output quality. *Judged by* a read, then a test. *Source:* Fable 5 guide, recommended scaffolding changes.

**no-reasoning-transcript.** The skill never tells Claude to echo, transcribe or explain its internal reasoning in the reply, and does not ask it to write reasoning out in place of thinking. A short explanation of the answer, or a summary of the actions taken, is still fine.
*Why:* such instructions can trigger the `reasoning_extraction` refusal on Fable 5 and Opus 5.5, and the server-side fallback does not retry that refusal. *Flagged by* the script, *confirmed by* a read. *Source:* Fable 5 guide, recommended scaffolding changes; Opus 5.5 guide, prompts written for thinking disabled.

**reasons-given.** Requests carry their purpose: what the larger task is, who it is for and what the result makes possible.
*Why:* with the intent stated, the model links the task to the right information instead of guessing what is wanted. *Judged by* a read. *Source:* Fable 5 guide, give the reason, not only the request.

**light-steering.** One short instruction does the work of a list. "Keep the answer brief" works as well as naming every way an answer can sprawl. Capitals are kept for real hard lines, and the skill says plainly what Claude should not do on its own.
*Why:* Fable 5 follows a brief instruction well, and when everything is in capitals nothing stands out. *Flagged by* the script (it counts capitalised MUST, NEVER and the like), *confirmed by* a read. *Source:* Fable 5 guide, strong instruction following; the capitals point comes from practice.

**independent-check.** Long or high-stakes work says how it gets checked and when, and checks progress against real tool results. A separate checker with fresh context (a subagent that did not do the work, comparing against the spec) is preferred over self-review.
*Why:* Anthropic reports that fresh-context checkers tend to outperform self-critique, and that checking against tool results nearly ended made-up status reports in its tests. *Judged by* a read. *Source:* Fable 5 guide, recommended scaffolding changes and strong instruction following.

## Guards

**hard-rules-in-hooks.** A rule that must hold every single time (block a command, check before each edit) is enforced by a hook, ideally declared in the skill's own `hooks` frontmatter. Judgment calls stay in prose.
*Why:* Claude Code runs a hook every time its event fires, whether or not Claude is following the skill. A skill's hooks register when it is invoked and keep running for the rest of the session; `once: true` removes a hook after its first successful run. *Flagged by* the script (it looks for "must always" wording in a skill with no hooks), *confirmed by* a read. *Source:* Claude Code skills, Claude stops following a skill; Claude Code hooks, hooks in skills and agents.

## Testing

**tests-first.** Before writing much of the skill, the author runs Claude on real tasks without it, writes down where it fails, builds three test cases from those gaps, and records the result without the skill as a baseline. Then the smallest skill that passes is written and refined against the baseline.
*Why:* the skill then solves real problems rather than imagined ones. Anthropic offers no built-in way to run these tests. *Judged by* a read (are the tests in the folder or the repo?). *Source:* Best practices, build evaluations first.

**fresh-session-test.** The skill is tried on real prompts in a new session, once with it on and once with it off, and someone watches how Claude moves through it: files read in an odd order, links missed, one file read every time, a file never opened. A second Claude can do the testing while the first helps write.
*Why:* a skill starting shows only that Claude found it, not that it worked; and leftover context from writing the skill hides gaps in what it says. *Judged by* a read (ask the owner). *Source:* Claude Code skills, evaluate and iterate; Best practices, develop skills with Claude and observe how Claude navigates.

**model-coverage.** The skill is tried on every model meant to run it, with one question per model: Haiku, is there enough guidance? Sonnet, is it clear and efficient? Opus, does it avoid over-explaining? The full sweep is kept for skills that matter most or carry risk.
*Why:* a skill adds to a model, so what works for Opus may need more detail for Haiku. *Judged by* a read (ask the owner). *Source:* Best practices, test with all models; when to sweep comes from practice.

## The skill set

Run these when you check a folder of skills.

**unique-triggers.** No two skills claim the same requests. Merge them, or narrow each description to its own job.
*Why:* when two descriptions match the same request, Claude has nothing to choose between them by. *Judged by* a read (put the descriptions side by side). *Source:* practice.

**unused-skills-off.** Skills that never run are found and turned off. In Claude Code, `/skill-doctor` shows what each skill costs in context and how often it is used, and flags skills never invoked.
*Why:* every listed skill adds to context on every turn, used or not. *Judged by* a read (ask the owner to run it). *Source:* Claude Code skills, find unused skills.

## Patterns to name in a fix

Name the pattern in each proposed fix, so the owner sees the cause and not only the line. The names come from Matt Pocock's "writing-great-skills".

- **No-op:** a line the model already follows without being told (earns-its-tokens, not-overprescribed). Delete the sentence.
- **Duplication:** one meaning in two places (one-rule-one-place). Keep one.
- **Sediment:** old layers kept because removing them felt risky (no-expiry-dates, one-rule-one-place). Fold them into the rule above them.
- **Sprawl:** long, though every line is live (short-body, split-by-topic). Move detail behind links; split by branch.
- **Rushed finish:** steps end vaguely, so the agent hurries (checklist). Write a result that can be checked.

## The report

Use this shape: fails first, then N/A, then passes. For a folder of skills, start with the `--all` summary from the script.

```markdown
# Skill check: {skill-name}

Script: {E} errors, {W} warnings, {N} notes. Rules: {F} fail, {X} N/A, {P} pass, {S} skipped on purpose.

## Fails
- **third-person.** SKILL.md:3 says "I can help you with notes". Fix: "Turns meeting notes into ...".

## Not applicable
- **scripts-handle-errors.** The skill has no scripts.

## Passes
- **one-hop.** The script found nothing.

## Fixes, biggest effect first
1. {fix}. Closes {rule names}. {why it matters, one line}

## For you to decide
- {anything that changes behaviour, or a cut that needs a test first}

Nothing has changed yet. Reply with the numbers of the fixes to apply.
```

## Sources

- **Best practices:** Anthropic, Skill authoring best practices. https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **Claude Code skills:** https://code.claude.com/docs/en/skills
- **Claude Code hooks:** https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents
- **Fable 5 guide:** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- **Opus 5.5 guide:** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5

The definitions were written from these pages as read on 2026-11-12.
