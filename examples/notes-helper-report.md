# Skill check: notes-helper

Script: 7 errors, 10 warnings, 6 notes (full output in notes-helper-check.txt). Rules: 23 fail, 12 N/A, 11 pass, 0 skipped.

The sample is broken on purpose. It shows what a finished report looks like.

## Contents

- Fails
- Not applicable
- Passes
- Fixes, biggest effect first
- For you to decide

## Fails

- **frontmatter-loads.** SKILL.md:3 the description holds ": " with no quotes, so the YAML fails and the skill loads with no fields. Fix: wrap the description in double quotes.
- **valid-name.** SKILL.md:2 `Notes_Helper`: capitals, an underscore, and not the folder name. Fix: rename to `taking-meeting-notes` and rename the folder to match.
- **name-says-the-job.** SKILL.md:2 "Helper" names nothing. Fix: same fix as valid-name.
- **third-person.** SKILL.md:3 "I can help you". Fix: "Turns meeting transcripts into summaries, action items and Word files."
- **what-and-when.** SKILL.md:3 no "Use when" part. Fix: add "Use when the user shares a meeting transcript or asks for minutes, a recap or action items."
- **split-by-topic.** SKILL.md:21 links two references, but export detail sits inline at SKILL.md:23-27. Fix: move export detail into reference/exporting.md.
- **one-hop.** reference/formats.md:5 is the only link to reference/action-items.md. Fix: link action-items.md from SKILL.md.
- **contents-list.** reference/meeting-types.md is 182 lines with no contents list. Fix: add a `## Contents` list at the top.
- **reachable-files.** SKILL.md:29 links style.md, which does not exist; reference/misc.md is linked by nothing; SKILL.md.old is a backup. Fix: delete the dead link, misc.md and SKILL.md.old.
- **forward-slashes.** SKILL.md:25 `scripts\export_notes.py`. Fix: write `scripts/export_notes.py`.
- **earns-its-tokens.** SKILL.md:9-10 "read the whole transcript" and "never guess a name" restate what Claude does anyway. Fix: cut them, after the test in testing.md (pattern: no-op).
- **no-expiry-dates.** SKILL.md:23 "Before March 2025, export with the old Word template". Fix: state the current template; delete the old one.
- **nothing-unfinished.** SKILL.md:27 "TODO: add the Slack export". Fix: delete the line, or build the export.
- **checklist.** SKILL.md:14-17 has boxes but no "done when" and no way-back line. Fix: add a finish line per step and "If the export fails, return to step 2".
- **check-and-fix-loop.** Nothing checks the summary before export. Fix: add: "compare the summary with reference/formats.md and list each miss".
- **run-or-read.** SKILL.md:25 says to run the script, but not what it prints or where the file goes. Fix: add "It writes {name}.docx next to the notes file".
- **install-lines.** scripts/export_notes.py:5 imports `docx`, with no install line. Fix: add `pip install python-docx` next to the export step.
- **no-reasoning-transcript.** SKILL.md:19 "write out your reasoning before the summary". Fix: "Give the summary, then one line on what it leaves out".
- **reasons-given.** SKILL.md:9-10 rules with no reason. Fix: give the reason for each rule that stays.
- **light-steering.** SKILL.md:9-10 six capitalised MUST, ALWAYS, NEVER, CRITICAL. Fix: write the rules plainly; keep capitals for none or one.
- **tests-first.** No test prompts in the folder. Fix: write three prompts and a baseline (testing.md).
- **scripts-handle-errors.** scripts/export_notes.py fails with a raw traceback when the notes file is missing. Fix: catch the missing file and print "Notes file {path} not found. Pass the path to the .txt notes."
- **helpful-errors.** Same line as scripts-handle-errors. Fix: same fix as scripts-handle-errors.

## Not applicable

- **control-matches-risk.** No step can spend money, delete data or publish.
- **template-strictness.** No templates.
- **show-examples.** The summary style is set in reference/formats.md.
- **full-tool-names.** No MCP tools.
- **one-rule-one-place.** One rules block only.
- **plan-check-run.** No batch or destructive work.
- **not-overprescribed.** Covered by earns-its-tokens; test before you cut.
- **independent-check.** Short, low-stakes job; check-and-fix-loop covers the check.
- **fresh-session-test.** Ask the owner; nothing in the folder.
- **model-coverage.** Ask the owner; nothing in the folder.
- **unique-triggers.** One skill checked, not a set.
- **unused-skills-off.** One skill checked, not a set.

## Passes

- **who-starts-it.** No side effects need a person to start it, so model-invoked is right.
- **description-in-limits.** Script: no description-in-limits findings.
- **key-use-first.** Script: no key-use-first findings.
- **short-body.** 29 lines.
- **key-rules-first.** Rules at SKILL.md:9-10.
- **one-word-per-idea.** "summary" and "action item" are used the same way throughout.
- **one-default.** One export path.
- **standing-instructions.** No one-time steps that should hold for the whole task.
- **explained-constants.** No constants.
- **hard-rules-in-hooks.** The "must always" rules are judgment calls; cutting them (earns-its-tokens) settles the note.
- **known-fields** (pass, with a note). SKILL.md:4 `version` is ignored by Claude Code. Fix: move it under `metadata:`.

## Fixes, biggest effect first

1. Quote the description, and rewrite it in third person with a "Use when" part. Closes frontmatter-loads, third-person, what-and-when. Without this the skill never starts on its own.
2. Rename the skill and its folder to `taking-meeting-notes`. Closes valid-name, name-says-the-job.
3. Delete style.md's dead link, reference/misc.md and SKILL.md.old; link action-items.md from SKILL.md; add a contents list to meeting-types.md. Closes one-hop, contents-list, reachable-files.
4. Replace the reasoning request with "give the summary, then one line on what it leaves out". Closes no-reasoning-transcript.
5. Rewrite the rules block plainly, with reasons, and cut the no-op lines after a test. Closes earns-its-tokens, reasons-given, light-steering.
6. Give the checklist finish lines, a way back and a check of the summary. Closes checklist, check-and-fix-loop.
7. Fix the export: forward slashes, an install line, what the script prints, and an error message for a missing file. Closes forward-slashes, scripts-handle-errors, run-or-read, helpful-errors, install-lines.
8. Move export detail into reference/exporting.md; delete the dated template rule and the TODO. Closes split-by-topic, no-expiry-dates, nothing-unfinished.
9. Write three test prompts and a baseline. Closes tests-first.

## For you to decide

- Fix 5 cuts lines. Run the test in testing.md first, on the model the skill runs on.
- Fix 2 changes the slash command from `/Notes_Helper` to `/taking-meeting-notes`.

Nothing has changed yet. Reply with the numbers of the fixes to apply.
