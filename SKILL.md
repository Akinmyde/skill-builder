---
name: skill-builder
description: Checks, builds and improves Agent Skills (folders with a SKILL.md) against Anthropic's skill rules and the prompting guides for newer Claude models. A check reports every rule as pass, fail or N/A, with file and line evidence and a proposed fix, and changes nothing until the owner picks the fixes. Use when someone asks to check, audit, review or score a skill or a folder of skills; to build a new skill or turn a repeated task into one; to improve, shorten or update an old skill for newer models; or to run the skill checker.
license: MIT
---

# Skill Builder

Checks, builds and improves skills so that Claude follows the same process on every run. A skill is a contents page, not a manual: the description gets it picked, SKILL.md says what to do, and detail waits in reference files until a step needs it.

## Rules for every mode

1. **Report before you change anything.** Start from evidence: the script output and a full read of the skill. In CHECK, edit nothing until the owner picks the fixes, because each change alters every future run and that call is theirs. A direct request to fix a named problem already counts as that choice.
2. **Fold in; do not stack.** Put new guidance into the rule it changes and delete what it replaces. A good edit usually leaves the skill shorter. Write the reason, not the date, so a later editor can tell whether the rule still holds.
3. **Test before you cut.** Newer models often do better with fewer instructions, but only a run with and without the line proves it is not needed. Method: references/testing.md, "Test before you cut".
4. **The script is the floor, not the ceiling.** `scripts/check_skill.py` checks what a script can check. The rules marked "read" in references/rules.md need a careful read.

## Choose the mode

| Mode | Use it when | You give back |
|---|---|---|
| CHECK | A skill or a folder of skills needs a check, a score or a fix list | A report, then only the fixes the owner picks |
| BUILD | No skill does the job yet | A new skill folder that passes the script and its test prompts |
| IMPROVE | A skill exists and new evidence arrived: a correction, a miss, a shipped result | The same skill, rewritten around the idea behind the evidence, usually shorter |

"Improve this skill" means CHECK, then IMPROVE with the fixes the owner picks.

## CHECK

Copy this checklist into the reply and tick it off:

```text
Check progress:
- [ ] 1 Script run on every skill in scope
- [ ] 2 Each skill read in full: SKILL.md, references, scripts
- [ ] 3 Every rule marked pass, fail or N/A, with evidence
- [ ] 4 Report written
- [ ] 5 Owner picked the fixes
- [ ] 6 Picked fixes applied
- [ ] 7 Script run again with no new errors or warnings
```

**Step 1. Run the script.** `python3 scripts/check_skill.py {skill-folder}` for one skill, or `--all {folder}` for a set. Then check in full the skills the owner picks; by default, the five with the most errors. Add `--json` to parse the output. Done when you have output for every skill in scope.

**Step 2. Read the skill.** All of it: SKILL.md, each reference file, each script. Done when you can name the skill's job, its branches and what each file is for.

**Step 3. Mark every rule.** Open references/rules.md. Script rules take the script's result. Read rules need evidence you can cite as a file and a line. A rule skipped in `skill-builder.json` is marked "skipped", with its reason. Done when no rule is unmarked.

**Step 4. Write the report** in the shape at the end of references/rules.md: the table with fails first, the fixes ranked by effect, then what needs the owner's decision. examples/notes-helper-report.md shows the standard.

**Step 5. Stop and ask.** End the turn with the numbered fixes. Edit nothing until the owner picks.

**Step 6. Apply the picked fixes** as IMPROVE describes. Before you cut a line as too prescriptive (the not-overprescribed rule), run the test in references/testing.md.

**Step 7. Run the script again.** If it shows a new error or warning, return to step 6.

## BUILD

```text
Build progress:
- [ ] 1 Evidence: the task done once with no skill, gaps noted
- [ ] 2 Three test prompts and a no-skill baseline
- [ ] 3 Shape, who starts it, and how much control
- [ ] 4 Folder created
- [ ] 5 Frontmatter and body written
- [ ] 6 Script clean
- [ ] 7 Tests run again in a new session
- [ ] 8 Read rules pass
```

1. **Evidence.** Do the task once with Claude and no skill, or read real past examples. Note what you had to explain. Done when you can list the gaps the skill must close.
2. **Tests first.** Write three prompts people would type, and record the result with no skill (references/testing.md). Done when the baseline is written down.
3. **Shape.** Choose one file, a bundle or a router; who can start the skill; and how much control each step gets (references/writing.md). Done when each choice has a one-line reason.
4. **Create the folder.** Run `python3 scripts/new_skill.py {name} --path {skills-folder}`, with `--references`, `--scripts` or `--manual` as needed. It creates the folder and checks it. Done when the folder exists.
5. **Write.** The description first, then the body: the key rules at the top, a checklist with a way-back line for multi-step work, detail in linked files. Replace every `[FILL: ...]` marker. Done when nothing is left to fill.
6. **Check.** Run the script on the folder. Fix every error; fix every warning or write down why it stays. If an error remains, return to step 5.
7. **Test again.** Run the test prompts in a new session with the skill on. If one fails, return to step 5.
8. **Read rules.** Mark the rules that need a read. Done when none fails.

## IMPROVE

1. **Name the evidence** in one line: what happened, what the owner said, what shipped.
2. **Find the idea** that explains it. If you cannot name it, you are not ready to edit.
3. **Rewrite** every line the idea touches, and delete the lines it makes unneeded. If a shipped result contradicts an older rule, the shipped result wins; tell the owner.
4. **Check.** Run the script. The file should not have grown; if it did, find what the new rule made unneeded. If the script shows a new error, return to step 3.

## Files

- [references/rules.md](references/rules.md): all 46 rules, each with its name, definition, why it matters, how to check it and its source, plus the report shape and the patterns to name. Read it in CHECK step 3, and before you call any skill done.
- [references/writing.md](references/writing.md): how to write each part: frontmatter, description, layout, control, steps, scripts, hooks, newer models. Read it in BUILD steps 3 to 5 and in IMPROVE.
- [references/testing.md](references/testing.md): tests, baselines, two-Claude testing, model coverage, test before you cut. Read it in BUILD steps 2 and 7, and before you cut lines.
- [examples/notes-helper-report.md](examples/notes-helper-report.md): a finished report for the flawed sample skill in `examples/notes-helper/`, built from the script output in `examples/notes-helper-check.txt`. Read it to see the standard for a report.
- `scripts/check_skill.py`: run it, do not read it. `--help` lists the flags.
- `scripts/new_skill.py`: run it to create a new skill folder.

Script paths are relative to this skill's folder (in Claude Code, `${CLAUDE_SKILL_DIR}`). Use `python3`, or `python` on Windows. Python 3.8 or newer, standard library only, nothing to install.
