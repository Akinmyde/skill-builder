#!/usr/bin/env python3
"""Create a new skill folder that passes check_skill.py, ready to fill in.

Usage:
    python3 scripts/new_skill.py my-skill --path ~/.claude/skills
    python3 scripts/new_skill.py my-skill --path . --references --scripts
    python3 scripts/new_skill.py deploying-app --path . --manual

Flags:
    --references   add references/details.md and link it from SKILL.md
    --scripts      add scripts/run.py and a line that says to run it
    --manual       only a person can start the skill (disable-model-invocation: true)

The new files hold [FILL: ...] markers. check_skill.py warns about each one until
it is replaced, so nothing half-written slips through.

Exit codes: 0 = created and checked, 1 = created but the check found errors,
2 = not created (bad name, or the folder already exists).

Python 3.8 or newer, standard library only.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Built from two parts so this file does not hold the marker in a comment line itself.
FILL_MARK = "[" + "FILL:"
NAME_RULE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
NAME_MAX = 64

SKILL_TEMPLATE = """---
name: {name}
description: "[FILL: what the skill does, in third person.] Use when [FILL: the situations and the words people type]."
{manual}---

# {title}

[FILL: one or two sentences on the job this skill does and the result it gives.]

## Rules for every run

1. [FILL: the rule that matters most, with its reason.]
2. [FILL: the next rule, with its reason.]

## Steps

Copy this checklist into the reply and tick it off:

```text
Progress:
- [ ] 1 [FILL: first step]
- [ ] 2 [FILL: second step]
- [ ] 3 Check the result
```

1. **[FILL: first step].** [FILL: what to do.] Done when [FILL: a line you can check].
2. **[FILL: second step].** [FILL: what to do.] Done when [FILL: a line you can check].
3. **Check the result.** [FILL: how to check it.] If the check fails, return to step 2.
{extras}"""

REFERENCE_TEMPLATE = """# [FILL: topic]

[FILL: the detail that only some runs need. Add a '## Contents' list at the top
if this file grows past 100 lines.]
"""

SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
# @MARK@ what this script does, and what it prints.]

import sys


def main():
    # @MARK@ replace this line with the real work.]
    print("not written yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def main(argv=None):
    parser = argparse.ArgumentParser(description="Create a new skill folder that passes check_skill.py.")
    parser.add_argument("name", help="lowercase letters, numbers and hyphens, for example processing-invoices")
    parser.add_argument("--path", default=".", help="the folder to create the skill in (default: here)")
    parser.add_argument("--references", action="store_true", help="add references/details.md")
    parser.add_argument("--scripts", action="store_true", help="add scripts/run.py")
    parser.add_argument("--manual", action="store_true", help="only a person can start the skill")
    args = parser.parse_args(argv)

    name = args.name
    if not NAME_RULE.fullmatch(name) or len(name) > NAME_MAX:
        print("'%s' is not a valid name. Fix: use lowercase letters, numbers and single hyphens, at most %d "
              "characters, for example 'processing-invoices'." % (name, NAME_MAX), file=sys.stderr)
        return 2
    if "anthropic" in name or "claude" in name:
        print("'%s' contains a reserved word (anthropic or claude). Fix: choose another name." % name, file=sys.stderr)
        return 2
    folder = Path(args.path).expanduser() / name
    if folder.exists():
        print("%s already exists. Fix: choose another name, or delete the folder first." % folder, file=sys.stderr)
        return 2

    extras = []
    if args.references:
        extras.append("- [references/details.md](references/details.md): [FILL: what it holds]. Read it when [FILL: the step that needs it].")
    if args.scripts:
        extras.append("- `scripts/run.py`: run it, do not read it. [FILL: what it prints.]")
    extras_text = ("\n## Files\n\n" + "\n".join(extras) + "\n") if extras else ""
    title = " ".join(part.capitalize() for part in name.split("-"))
    manual = "disable-model-invocation: true\n" if args.manual else ""

    try:
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(SKILL_TEMPLATE.format(name=name, title=title, manual=manual, extras=extras_text), encoding="utf-8")
        if args.references:
            (folder / "references").mkdir()
            (folder / "references" / "details.md").write_text(REFERENCE_TEMPLATE, encoding="utf-8")
        if args.scripts:
            (folder / "scripts").mkdir()
            (folder / "scripts" / "run.py").write_text(SCRIPT_TEMPLATE.replace("@MARK@", FILL_MARK), encoding="utf-8")
    except OSError as error:
        print("Could not create %s: %s. Fix: check that the parent folder exists and you can write to it." % (folder, error), file=sys.stderr)
        return 2

    print("Created %s" % folder, flush=True)
    checker = Path(__file__).resolve().parent / "check_skill.py"
    result = subprocess.run([sys.executable, str(checker), str(folder)])
    print("Next: replace every [FILL: ...] marker, then run check_skill.py again until it shows no warnings.")
    return 1 if result.returncode == 1 else 0


if __name__ == "__main__":
    sys.exit(main())
