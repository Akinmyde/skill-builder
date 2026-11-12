# Testing a skill

A skill that starts proves only that Claude found it. Test two things apart: does it start on the prompts it should, and is the result right when it does.

## Contents

- Write the tests first
- Run with and without the skill
- One Claude writes, another tests
- Watch which files Claude opens
- Test on the models it runs on
- Test before you cut
- Check with fresh context
- Test prompts for this skill

## Write the tests first

Write the tests before the skill, so the skill closes real gaps and not imagined ones.

1. Run Claude on three or more real tasks with no skill. Note where it fails, or where you keep giving the same context.
2. Turn each gap into a test prompt with the result you expect.
3. Record how Claude does without the skill. That is the baseline.
4. Write the smallest skill that closes the gaps.
5. Run the tests again, compare with the baseline, and improve. If a test still fails, return to step 4.

One simple shape per test, kept in the skill's repo or an `evals/` folder:

```text
### {short name}
Prompt: {exactly what a person would type}
Should start the skill: yes
First file Claude should open: {file}
Done looks like: {one line you can check}
```

Add at least one prompt that should not start the skill. It catches a description that claims too much.

Anthropic's page also shows a JSON shape (`skills`, `query`, `files`, `expected_behavior`) for machine-readable tests. It has no built-in runner. Anthropic's skill-creator plugin uses its own `evals/evals.json`.

## Run with and without the skill

Run each prompt in a new session with the skill on, then again with it off, and compare. Use a new session, because context left over from writing the skill hides gaps.

- **A personal or project skill in Claude Code:** turn it off for the second run with `"skillOverrides": { "{skill-name}": "off" }` in settings, or from the `/skills` menu.
- **A skill in a plugin:** use `claude plugin eval`, which runs each prompt again with no plugin loaded.
- **To automate it:** Anthropic's skill-creator plugin (`/plugin install skill-creator@claude-plugins-official`) runs with and without the skill, grades both, and compares tokens and time.

## One Claude writes, another tests

Work with one Claude (A) to write and improve the skill. Give the skill to a new Claude (B) with real tasks, not made-up cases. Watch B. Take each miss back to A with the facts: "B wrote the report but skipped the date filter, though the skill names it. Is the rule too far down?" Repeat until B handles new tasks with no help.

## Watch which files Claude opens

While B works, note:

- **An odd order:** files read in an order you did not plan. The layout is less clear than you think.
- **A missed file:** an important file never opened. Make the link clearer, or move the content into SKILL.md.
- **The same file every run:** that content probably belongs in SKILL.md.
- **A file never opened:** it is not needed, or nothing says when to read it. Delete it, or add the "read it when" line.

## Test on the models it runs on

A skill adds to a model, so results change with the model. Ask one question per model:

- **Haiku:** is there enough guidance?
- **Sonnet:** is it clear and lean?
- **Opus:** does it over-explain?

Test with care for cost. Run every model only for skills you depend on, or that can spend money, delete data or publish. For the rest, test on the model you use most, and widen the test only when something looks wrong.

## Test before you cut

Newer models often do better with fewer instructions, but a line that looks unneeded may hold up one edge case. Before you cut lines for being too prescriptive:

1. List the lines to cut and why each one may not be needed.
2. Copy the skill, cut the lines in the copy, and run the tests on both versions in new sessions, on the model the skill runs on.
3. Keep a cut only where the short version does as well or better. Put back any line whose cut changed the result.
4. Write the evidence in the change list: which test, which model, what changed.

## Check with fresh context

When the result matters, check it with a separate Claude that did not do the work. Give it the spec and the result. A checker with fresh context finds more than self-review. Use the same idea inside long work: "after each stage, have a subagent check the output against the spec".

## Test prompts for this skill

### Check one skill
Prompt: `check my deploy skill against the skill rules`
Should start the skill: yes
First file Claude should open: references/rules.md, after it runs the script
Done looks like: a report with one row per rule, fails first, and no file changed

### Check a set
Prompt: `go through every skill in ~/.claude/skills and tell me what to fix first`
Should start the skill: yes
First file Claude should open: the `--all` table from the script, then references/rules.md
Done looks like: the summary table, full reports for the skills the owner picks, no file changed

### Build a skill from a repeated task
Prompt: `turn this into a skill, we write release notes like this every Friday`
Should start the skill: yes
First file Claude should open: references/testing.md, to write the tests first
Done looks like: a new folder that passes the script and its three test prompts

### Fix a skill after a miss
Prompt: `the report skill keeps forgetting the date filter, fix it`
Should start the skill: yes
First file Claude should open: the report skill's SKILL.md, then references/rules.md
Done looks like: the rule rewritten with its reason near the top, the file no longer than before, the script clean

### Should not start
Prompt: `write a Python script that renames my photos by date`
Should start the skill: no
