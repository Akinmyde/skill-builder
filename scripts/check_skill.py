#!/usr/bin/env python3
"""Check an Agent Skill folder against the rules a script can decide.

Usage:
    python3 scripts/check_skill.py path/to/skill            # one skill
    python3 scripts/check_skill.py --all path/to/skills      # every skill in a folder
    python3 scripts/check_skill.py path/to/skill --json      # machine-readable output
    python3 scripts/check_skill.py path/to/skill --skip valid-name # leave one rule out
    python3 scripts/check_skill.py path/to/skill --no-em-dash

Exit codes: 0 = no errors (warnings and notes allowed), 1 = errors found,
2 = the check could not run (bad path, unreadable folder).

Each finding names its rule, as listed in references/rules.md. Levels:
    ERROR  breaks a hard limit or stops the skill from loading or working
    WARN   breaks a rule; fix it or write down why it stays
    NOTE   worth a look; a person decides

A file named skill-builder.json in the skill folder or its parent folder can
skip rules on purpose, with a reason that is printed in every report:
    {"skip": {"valid-name": "our names use a colon namespace"}}

Python 3.8 or newer, standard library only.
"""

import argparse
import keyword
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

# ---------------------------------------------------------------------------
# Limits. Each one comes from Anthropic's skill docs unless marked otherwise.
# ---------------------------------------------------------------------------
NAME_MAX = 64                # name field limit (best practices: frontmatter requirements)
DESCRIPTION_MAX = 1024       # description field limit (same page)
LISTING_MAX = 1536           # Claude Code cuts description + when_to_use here in the skill list
DESCRIPTION_MIN = 50         # below this a description rarely says both what and when (practice)
BODY_MAX_LINES = 500         # SKILL.md body limit (best practices: progressive disclosure)
CONTENTS_MIN_LINES = 100     # files longer than this need a contents list (best practices)
CONTENTS_LOOK_LINES = 50     # the contents list must sit in the first 50 lines (practice)
COMPACTION_KEEP_TOKENS = 5000  # Claude Code keeps this much of a skill after compaction
CHARS_PER_TOKEN = 4          # rough English average, good enough for a size warning
EMPHASIS_MAX = 5             # more capitalised MUST/NEVER than this per file stops standing out (practice)
COMPATIBILITY_MAX = 500      # compatibility field limit (Claude Code frontmatter reference)
MAX_FILE_BYTES = 2_000_000   # larger files are data, not instructions; skip reading them
SHOW_LINES = 6               # line numbers shown per finding
SHOW_FILES = 8               # file names shown per finding

PORTABLE_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
CLAUDE_CODE_FIELDS = PORTABLE_FIELDS | {
    "when_to_use", "disable-model-invocation", "user-invocable", "argument-hint", "arguments",
    "paths", "context", "agent", "background", "model", "effort", "hooks", "shell",
    "disallowed-tools",
}
BOOLEAN_FIELDS = {"disable-model-invocation", "user-invocable", "background"}
BOOLEAN_WORDS = {"true", "false", "yes", "no", "on", "off", "1", "0"}
EFFORT_VALUES = {"low", "medium", "high", "xhigh", "max"}
SHELL_VALUES = {"bash", "powershell"}
RESERVED_WORDS = ("anthropic", "claude")
VAGUE_NAMES = {"helper", "helpers", "utils", "utilities", "tools", "tool", "documents", "docs",
               "data", "files", "misc", "stuff", "general", "assistant", "skill"}
VAGUE_NAME_PARTS = {"helper", "helpers", "utils", "util", "misc", "stuff", "thing", "things"}
VAGUE_FILE_STEM = re.compile(r"^(doc|docs|file|files|misc|stuff|temp|tmp|untitled|new|notes?|other|test)\d*$", re.I)
# "copy" counts only in the forms an editor or file manager leaves ("notes copy.md", "notes copy 2.md",
# "Copy of notes.md", "notes (copy).md", "notes.copy.md"), never as a word in a name such as check-copy.mjs.
BACKUP_NAME = re.compile(r"\.(bak|orig|old|backup)$|~$|\.(bak|orig|old)\.|[._-]backup\b|[\s.]copy(\s\d+)?(\.[^.]+)?$|^copy of\s|\(copy\)", re.I)

# Folders that are not for Claude to read: tests, fixtures, build output, environments.
NOT_FOR_CLAUDE = {"node_modules", "__pycache__", ".git", "venv", ".venv", "evals", "tests", "test",
                  "__tests__", "__test_fixtures__", "fixtures", "dist", "build", ".pytest_cache"}
# Files that belong to the repo, not to the skill's instructions.
REPO_FILES = {"readme.md", "license", "license.md", "license.txt", "notice", "notice.md",
              "changelog.md", "contributing.md", ".gitignore", ".gitattributes", "skill-builder.json"}
MANIFESTS = {"requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py", "setup.cfg",
             "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "pipfile",
             "tsconfig.json", "vitest.config.ts", "jest.config.js", "osv-scanner.toml"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".jsx", ".tsx",
                 ".sh", ".bash", ".zsh", ".ps1", ".json", ".yaml", ".yml", ".toml", ".html", ".css",
                 ".csv", ".xml", ".sql", ".rb", ".go", ".rs", ""}

RULE_ORDER = [
    "frontmatter-loads", "valid-name", "name-says-the-job", "known-fields", "who-starts-it",
    "description-in-limits", "third-person", "what-and-when", "key-use-first", "short-body",
    "key-rules-first", "one-hop", "contents-list", "reachable-files", "forward-slashes",
    "no-expiry-dates", "nothing-unfinished", "checklist", "install-lines",
    "no-reasoning-transcript", "light-steering", "hard-rules-in-hooks", "STYLE"
]
# Every rule in references/rules.md, including the ones only a reader can judge. A skip in
# skill-builder.json may name any of them; the report then shows the rule as skipped.
ALL_RULES = RULE_ORDER[:-1] + [
    "split-by-topic", "earns-its-tokens", "control-matches-risk", "one-word-per-idea", "template-strictness",
    "show-examples", "one-default", "full-tool-names", "one-rule-one-place", "check-and-fix-loop",
    "plan-check-run", "standing-instructions", "scripts-handle-errors", "explained-constants", "run-or-read",
    "helpful-errors", "not-overprescribed", "reasons-given", "independent-check", "tests-first",
    "fresh-session-test", "model-coverage", "unique-triggers", "unused-skills-off",
]
assert len(ALL_RULES) == 46
LEVELS = {"ERROR": 0, "WARN": 1, "NOTE": 2}

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------
FIRST_PERSON = re.compile(r"\b(I can|I will|I'll|I help|I'm|I am|I do|let me|my job)\b", re.I)
SECOND_PERSON = re.compile(r"\byou\s+(can|could|will|should|may|might)\b|\byou'll\b", re.I)
WHEN_CUE = re.compile(r"\b(use (it |this )?(when|for|if|whenever|to)|when (the )?(user|someone|you|a person|asked)|"
                      r"triggers? (on|when)|for (requests|questions|tasks) (about|like|involving)|"
                      r"if (the )?user|whenever)\b", re.I)
XML_TAG = re.compile(r"<\s*/?\s*[A-Za-z][\w:-]*(\s[^<>]*)?/?>")
MONTH = (r"(jan(uary)?|feb(ruary)?|mar(ch)?|apr(il)?|may|june?|july?|aug(ust)?|sep(t(ember)?)?|"
         r"oct(ober)?|nov(ember)?|dec(ember)?)")
TIME_PHRASE = re.compile(r"\b(before|after|until|since|as of|starting|from)\s+(" + MONTH + r"\s+)?(19|20)\d{2}\b", re.I)
ISO_DATE = re.compile(r"\b(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b")
REASONING_TRANSCRIPT = re.compile(
    r"\b(show|write out|print|output|include|spell out|lay out|transcribe|echo)\s+(your|the|its|all)\s+"
    r"(full\s+|complete\s+)?(reasoning|thinking|thought process|chain[- ]of[- ]thought|internal monologue)\b"
    r"|\bthink step[- ]by[- ]step,?\s+(and|then)\s+(write|show|explain|output|include|list|print)\b"
    r"|\bexplain your (full )?reasoning step[- ]by[- ]step\b", re.I)
EMPHASIS = re.compile(r"\b(CRITICAL|MUST|ALWAYS|NEVER|IMPORTANT)\b")
HARD_RULE = re.compile(r"\b(must always|must never|without exception|no exceptions|"
                       r"under no circumstances|always, without|never, ever)\b", re.I)
GO_BACK = re.compile(r"\b(return to|go back to|back to step|repeat (from )?step|loop back|start again from|re-?run step)\b", re.I)
CHECKBOX = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s")
# A TODO counts only as a marker: at the start of a line, in a code comment, or as "TODO:" / "TODO(".
TODO_COMMENT = re.compile(r"(#|//|/\*|<!--)\s*(TODO|FIXME|XXX)\b")
TODO_LABEL = re.compile(r"\b(TODO|FIXME|XXX)[:(]")
FILL_PLACEHOLDER = re.compile(r"\[FILL:")
# Relative paths written with backslashes, such as scripts\run.py. Absolute Windows paths
# (C:\Users\...) are left alone: a skill may name one on purpose, for example to convert it.
BACKSLASH_PATH = re.compile(r"(?<![A-Za-z]:)(?<![\\\w])((?:\.{1,2}|[\w-]+)(?:\\[\w.-]+)+\.[A-Za-z0-9]{1,6})\b")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+)(.+?)\1")
QUOTED = re.compile(r"\"[^\"\n]*\"|\u201c[^\u201d\n]*\u201d")
MD_LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^)]*[\"'])?\s*\)")
REF_LINK = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(\s|$)")
HEADING = re.compile(r"^(#{1,6})\s+(.*)")
CONTENTS_HEADING = re.compile(r"^\s{0,3}(#{1,6}\s*)?(\*\*)?(table of )?contents(\*\*)?\s*:?\s*$", re.I)
OLD_SECTION = re.compile(r"^(old patterns?|legacy|history|changelog|deprecated|previous versions?)\b", re.I)
FRONT_KEY = re.compile(r"^([A-Za-z0-9_][\w.-]*)[ \t]*:(?:[ \t]+(.*?))?[ \t]*$")

PY_IMPORT = re.compile(r"^\s*(?:from\s+([A-Za-z_][\w]*)[\w.]*\s+import\b|import\s+([A-Za-z_][\w]*(?:\s*,\s*[A-Za-z_][\w]*)*))")
JS_IMPORT = re.compile(r"(?:^\s*import\s+(?:[^'\"\n]*?\s+from\s+)?|\brequire\(\s*)['\"]([^'\"./\n][^'\"\n]*)['\"]", re.M)
PY_PACKAGE_FOR = {"yaml": "pyyaml", "cv2": "opencv-python", "PIL": "pillow", "bs4": "beautifulsoup4",
                  "sklearn": "scikit-learn", "fitz": "pymupdf", "docx": "python-docx", "pptx": "python-pptx",
                  "dateutil": "python-dateutil", "dotenv": "python-dotenv", "magic": "python-magic"}
NODE_BUILTINS = {"fs", "path", "os", "url", "util", "child_process", "crypto", "http", "https", "stream",
                 "events", "assert", "zlib", "readline", "process", "buffer", "net", "tls", "dns",
                 "querystring", "string_decoder", "timers", "worker_threads", "perf_hooks", "module", "vm"}
def standard_library():
    """Module names that ship with Python. Python 3.10+ lists them; older versions are read from disk."""
    names = set(getattr(sys, "stdlib_module_names", ()))
    if names:
        return names
    import sysconfig
    names = set(sys.builtin_module_names)
    for folder in {sysconfig.get_paths().get("stdlib"), sysconfig.get_paths().get("platstdlib")}:
        if not folder or not os.path.isdir(folder):
            continue
        for entry in os.listdir(folder):
            if entry == "site-packages":
                continue
            names.add(entry.split(".")[0])
        dynload = os.path.join(folder, "lib-dynload")
        if os.path.isdir(dynload):
            names.update(e.split(".")[0] for e in os.listdir(dynload))
    return names | FALLBACK_STDLIB


FALLBACK_STDLIB = {
    "abc", "argparse", "array", "ast", "asyncio", "base64", "bisect", "calendar", "collections", "contextlib",
    "copy", "csv", "dataclasses", "datetime", "decimal", "difflib", "email", "enum", "errno", "fnmatch",
    "fractions", "functools", "getpass", "glob", "gzip", "hashlib", "heapq", "hmac", "html", "http", "importlib",
    "inspect", "io", "itertools", "json", "logging", "math", "mimetypes", "multiprocessing", "operator", "os",
    "pathlib", "pickle", "platform", "pprint", "queue", "random", "re", "secrets", "select", "shlex", "shutil",
    "signal", "socket", "sqlite3", "ssl", "stat", "statistics", "string", "struct", "subprocess", "sys",
    "tempfile", "textwrap", "threading", "time", "timeit", "traceback", "types", "typing", "unicodedata",
    "unittest", "urllib", "uuid", "warnings", "weakref", "webbrowser", "xml", "zipfile", "zlib", "__future__"}
STDLIB = standard_library()


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
class Report:
    def __init__(self, path, skipped):
        self.path = path
        self.name = None
        self.findings = []
        self.skipped = skipped  # {rule: reason}

    def add(self, level, rule, file, lines, message):
        if rule in self.skipped:
            return
        rows = sorted({n for n in lines if n})
        self.findings.append({"level": level, "rule": rule, "file": file, "lines": rows, "message": message})

    def count(self, level):
        return sum(1 for f in self.findings if f["level"] == level)

    def sorted_findings(self):
        def key(f):
            rule = RULE_ORDER.index(f["rule"]) if f["rule"] in RULE_ORDER else 99
            return (LEVELS[f["level"]], rule, f["file"], f["lines"][:1])
        return sorted(self.findings, key=key)

    def passed(self):
        hit = {f["rule"] for f in self.findings if f["level"] in ("ERROR", "WARN")}
        return [r for r in RULE_ORDER if r != "STYLE" and r not in hit and r not in self.skipped]


def short(text, limit=60):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def where(file, lines):
    if not lines:
        return file
    shown = ",".join(str(n) for n in lines[:SHOW_LINES])
    return "%s:%s%s" % (file, shown, "..." if len(lines) > SHOW_LINES else "")


def list_names(names):
    names = sorted(names)
    text = ", ".join(names[:SHOW_FILES])
    return text + (" and %d more" % (len(names) - SHOW_FILES) if len(names) > SHOW_FILES else "")


# ---------------------------------------------------------------------------
# Frontmatter: a small YAML reader for the shapes skill frontmatter uses
# (plain, quoted and block scalars, flow and block lists, nested maps).
# ---------------------------------------------------------------------------
def parse_frontmatter(lines):
    """Return (fields, end_line, problems). fields maps key -> {value, line, quoted}.

    end_line is the 1-based line of the closing '---', or None when it is missing.
    problems is a list of (line, message) for YAML that will not parse.
    """
    problems = []
    if not lines or lines[0].strip() != "---":
        return None, None, problems
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        problems.append((1, "the frontmatter opens with '---' but never closes. Fix: add a '---' line after the last field."))
        return {}, None, problems
    fields = {}
    i = 1
    while i < end:
        raw = lines[i]
        number = i + 1
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if raw.startswith((" ", "\t")):
            i += 1  # belongs to the previous key
            continue
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            problems.append((number, "a tab indents this line. Fix: indent YAML with spaces."))
        match = FRONT_KEY.match(raw)
        if not match:
            problems.append((number, "this line is not 'key: value'. Fix: write it as 'key: value', or quote the value."))
            i += 1
            continue
        key, value = match.group(1), (match.group(2) or "")
        if key in fields:
            problems.append((number, "'%s' appears twice. Fix: keep one; YAML keeps only the last." % key))
        # Gather the indented lines that belong to this key.
        block = []
        j = i + 1
        while j < end and (not lines[j].strip() or lines[j].startswith((" ", "\t"))):
            block.append(lines[j])
            j += 1
        parsed, quoted, problem = read_value(key, value, block)
        if problem:
            problems.append((number, problem))
        fields[key] = {"value": parsed, "line": number, "quoted": quoted}
        i = j
    return fields, end + 1, problems


def strip_comment(value):
    """Drop a trailing ' # comment' from a plain scalar."""
    pos = value.find(" #")
    return value[:pos].rstrip() if pos >= 0 else value


def closing_quote(text, quote):
    """Index of the quote that closes text[0], or None. Handles '' and \\" escapes."""
    i = 1
    while i < len(text):
        ch = text[i]
        if quote == '"' and ch == "\\":
            i += 2
            continue
        if ch == quote:
            if quote == "'" and i + 1 < len(text) and text[i + 1] == "'":
                i += 2
                continue
            return i
        i += 1
    return None


def read_value(key, value, block):
    """Return (value, was_quoted, problem_or_None)."""
    text = value.strip()
    content = [b for b in block if b.strip() and not b.strip().startswith("#")]
    if text in ("|", ">", "|-", ">-", "|+", ">+"):
        joiner = "\n" if text.startswith("|") else " "
        return joiner.join(b.strip() for b in block).strip(), True, None
    if text == "" or text.startswith("#"):
        if not content:
            return "", False, None
        if all(c.strip().startswith("- ") or c.strip() == "-" for c in content if not c.startswith("    ")) and \
                content[0].strip().startswith("-"):
            items = [strip_comment(c.strip()[1:].strip()).strip("\"'") for c in content if c.strip().startswith("-")]
            return items, False, None
        return {"_map": [c.strip() for c in content]}, False, None
    if text[0] in "\"'":
        quote = text[0]
        joined = " ".join([text] + [b.strip() for b in block]).strip()
        close = closing_quote(joined, quote)
        if close is None:
            return text, True, "the %s value opens a %s quote and never closes it. Fix: close the quote." % (key, quote)
        rest = joined[close + 1:].strip()
        if rest and not rest.startswith("#"):
            return text, True, ("the %s value has text after its closing quote (%s). Fix: move it inside the quotes."
                                % (key, short(rest, 30)))
        inner = joined[1:close]
        return (inner.replace("''", "'") if quote == "'" else inner.replace('\\"', '"')), True, None
    if text[0] in "[{":
        close = "]" if text[0] == "[" else "}"
        joined = " ".join([text] + [b.strip() for b in block])
        if close not in joined:
            return text, False, "the %s value opens '%s' and never closes it. Fix: close it, or quote the value." % (key, text[0])
        inner = joined[1:joined.rfind(close)]
        if text[0] == "[":
            return [p.strip().strip("\"'") for p in inner.split(",") if p.strip()], False, None
        return {"_map": [p.strip() for p in inner.split(",") if p.strip()]}, False, None
    if text[0] in "@`":
        return text, False, ("the %s value starts with '%s', which YAML refuses. Fix: wrap the value in double quotes." % (key, text[0]))
    plain = strip_comment(text)
    if ": " in plain or plain.endswith(":"):
        return plain, False, ("the %s value holds ': ', which YAML reads as a new key, so the frontmatter "
                              "will not parse. Fix: wrap the value in double quotes." % key)
    more = [b.strip() for b in block if b.strip()]
    if more:
        plain = " ".join([plain] + more)
    return plain, False, None


# ---------------------------------------------------------------------------
# Files and text
# ---------------------------------------------------------------------------
def read_text(path):
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:4096]:
        return None
    return data.decode("utf-8", "replace").lstrip("\ufeff")


def collect_files(root):
    """Files that belong to the skill. Returns (files, nested_skill_folders).

    A subfolder that holds its own SKILL.md is a separate skill (a sample, a copy),
    so its files are left out and it is reported once.
    """
    files = []
    nested = []
    for folder, dirs, names in os.walk(root):
        keep = []
        for d in dirs:
            path = os.path.join(folder, d)
            if d in NOT_FOR_CLAUDE or d.startswith("."):
                continue
            if os.path.isfile(os.path.join(path, "SKILL.md")):
                nested.append(Path(path).relative_to(root).as_posix())
                continue
            keep.append(d)
        dirs[:] = sorted(keep)
        for name in sorted(names):
            if name == ".DS_Store" or name.endswith(".pyc"):
                continue
            files.append(Path(folder) / name)
    return files, nested


def prose_views(lines, start=0):
    """Return (with_code, prose, no_code) line lists.

    with_code keeps fenced code but blanks inline code; no_code blanks both; prose blanks
    both and quoted text too, so a pattern inside an example or a quotation is not taken as an instruction.
    Lines before `start` (the frontmatter) are blanked in both.
    """
    with_code, prose, no_code = [], [], []
    in_fence = None
    for i, line in enumerate(lines):
        if i < start:
            with_code.append("")
            prose.append("")
            no_code.append("")
            continue
        fence = FENCE.match(line)
        if fence:
            mark = fence.group(1)[0]
            in_fence = None if in_fence == mark else (mark if in_fence is None else in_fence)
            with_code.append("")
            prose.append("")
            no_code.append("")
            continue
        no_inline = INLINE_CODE.sub(" ", line)
        with_code.append(line if in_fence else no_inline)
        no_code.append("" if in_fence else no_inline)
        prose.append("" if in_fence else QUOTED.sub(" ", no_inline))
    return with_code, prose, no_code


def old_sections(lines):
    """Line indexes inside an 'Old patterns' style section, where dates are allowed."""
    inside, level, out = False, 0, set()
    for i, line in enumerate(lines):
        h = HEADING.match(line)
        if h:
            depth = len(h.group(1))
            if OLD_SECTION.match(h.group(2).strip()):
                inside, level = True, depth
            elif inside and depth <= level:
                inside = False
        if inside:
            out.add(i)
    return out


def links_in(lines):
    """(line_number, target) for every Markdown link outside code."""
    found = []
    for i, line in enumerate(lines):
        for m in MD_LINK.finditer(line):
            found.append((i + 1, m.group(1)))
        m = REF_LINK.match(line)
        if m:
            found.append((i + 1, m.group(1)))
    return found


def local_target(raw):
    """A link target as a relative path, or None for URLs, anchors and placeholders."""
    target = unquote(raw.split("#")[0].split("?")[0]).strip()
    if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith(("/", "~", "$")):
        return None
    if re.search(r"[{}<>*|\\\[\]^+()]|\$\{|\.\.\.", target):
        return None  # a placeholder or a pattern, not a file
    if "/" not in target and "." not in target:
        return None  # a bare word such as (URL) or (link) is a placeholder, not a path
    return target


def inside(root, path):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def mentions(text, rel):
    """True when text names rel by path or by a distinctive file name."""
    if rel in text:
        return True
    base = rel.rsplit("/", 1)[-1]
    return len(base) > 4 and re.search(r"(?<![\w./-])" + re.escape(base) + r"(?![\w])", text) is not None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def check_header(rep, folder_name, fields):
    def line(key):
        return [fields[key]["line"]] if key in fields else []

    name = fields.get("name", {}).get("value")
    if not name:
        rep.add("ERROR", "valid-name", "SKILL.md", [], "the frontmatter has no name. Fix: add 'name: %s' "
                "(lowercase, hyphens, same as the folder)." % folder_name)
    elif not isinstance(name, str):
        rep.add("ERROR", "valid-name", "SKILL.md", line("name"), "the name is a list or a map. Fix: make it one plain word such as '%s'." % folder_name)
    else:
        rep.name = name
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
            rep.add("ERROR", "valid-name", "SKILL.md", line("name"), "the name '%s' may hold only lowercase letters, numbers and single "
                    "hyphens. Fix: rename it to '%s'." % (name, re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")))
        if len(name) > NAME_MAX:
            rep.add("ERROR", "valid-name", "SKILL.md", line("name"), "the name is %d characters; the limit is %d. Fix: shorten it." % (len(name), NAME_MAX))
        for word in RESERVED_WORDS:
            if word in name.lower():
                rep.add("ERROR", "valid-name", "SKILL.md", line("name"), "the name contains the reserved word '%s'. Fix: remove it." % word)
        if folder_name and name != folder_name:
            rep.add("WARN", "valid-name", "SKILL.md", line("name"), "the name '%s' differs from the folder '%s'. Fix: make them the same, "
                    "so the folder, the slash command and the name match." % (name, folder_name))
        parts = [p for p in re.split(r"[-_]+", name.lower()) if p]
        if name.lower() in VAGUE_NAMES or any(p in VAGUE_NAME_PARTS for p in parts) or all(p in VAGUE_NAMES for p in parts):
            rep.add("WARN", "name-says-the-job", "SKILL.md", line("name"), "the name '%s' does not say what the skill does. Fix: name the "
                    "activity, for example 'processing-pdfs'." % name)

    unknown = sorted(k for k in fields if k not in CLAUDE_CODE_FIELDS)
    if unknown:
        rep.add("NOTE", "known-fields", "SKILL.md", [fields[k]["line"] for k in unknown], "Claude Code ignores these fields: %s. Fix: move "
                "them under 'metadata:' to keep them, or delete them." % ", ".join(unknown))
    not_portable = sorted(k for k in fields if k not in PORTABLE_FIELDS)
    if not_portable:
        rep.add("NOTE", "known-fields", "SKILL.md", [], "a claude.ai upload or the Skills API refuses fields other than %s; this skill "
                "also uses %s. This matters only if you upload it there." % (", ".join(sorted(PORTABLE_FIELDS)), ", ".join(not_portable)))
    for key in sorted(BOOLEAN_FIELDS & set(fields)):
        value = fields[key]["value"]
        # Claude Code also reads yes/no, on/off and 1/0 as booleans (skills docs, frontmatter reference).
        if fields[key]["quoted"] or str(value).lower() not in BOOLEAN_WORDS:
            rep.add("WARN", "known-fields", "SKILL.md", line(key), "%s is '%s'. Fix: write true or false, without quotes." % (key, value))
    if "effort" in fields and str(fields["effort"]["value"]).lower() not in EFFORT_VALUES:
        rep.add("WARN", "known-fields", "SKILL.md", line("effort"), "effort '%s' is not one of %s. Fix: pick one." % (fields["effort"]["value"], ", ".join(sorted(EFFORT_VALUES))))
    if "context" in fields and fields["context"]["value"] != "fork":
        rep.add("WARN", "known-fields", "SKILL.md", line("context"), "context accepts only 'fork'. Fix: write 'fork' or delete the field.")
    if "shell" in fields and str(fields["shell"]["value"]).lower() not in SHELL_VALUES:
        rep.add("WARN", "known-fields", "SKILL.md", line("shell"), "shell accepts only bash or powershell. Fix: pick one.")
    compat = fields.get("compatibility", {}).get("value")
    if isinstance(compat, str) and len(compat) > COMPATIBILITY_MAX:
        rep.add("WARN", "known-fields", "SKILL.md", line("compatibility"), "compatibility is %d characters; the limit is %d. Fix: shorten it." % (len(compat), COMPATIBILITY_MAX))

    manual_only = str(fields.get("disable-model-invocation", {}).get("value", "")).lower() in ("true", "yes", "on", "1")
    hidden = str(fields.get("user-invocable", {}).get("value", "")).lower() in ("false", "no", "off", "0")
    if manual_only and hidden:
        rep.add("WARN", "who-starts-it", "SKILL.md", line("user-invocable"), "disable-model-invocation: true and user-invocable: false "
                "together mean nobody can start this skill. Fix: remove one of them.")
    return manual_only


def check_trigger(rep, fields, manual_only):
    def line(key):
        return [fields[key]["line"]] if key in fields else []

    desc = fields.get("description", {}).get("value")
    if not desc:
        rep.add("ERROR", "description-in-limits", "SKILL.md", [], "the frontmatter has no description. Claude picks a skill by its description "
                "alone. Fix: add one that says what the skill does and when to use it.")
        return
    if not isinstance(desc, str):
        rep.add("ERROR", "description-in-limits", "SKILL.md", line("description"), "the description is a list or a map. Fix: make it one sentence or two of plain text.")
        return
    at = line("description")
    if len(desc) > DESCRIPTION_MAX:
        rep.add("ERROR", "description-in-limits", "SKILL.md", at, "the description is %d characters; the limit is %d. Fix: cut it to the "
                "job and its trigger words." % (len(desc), DESCRIPTION_MAX))
    tag = XML_TAG.search(desc)
    if tag:
        rep.add("ERROR", "description-in-limits", "SKILL.md", at, "the description holds an XML tag (%s). Fix: remove the tag." % short(tag.group(0), 30))
    person = FIRST_PERSON.search(desc) or SECOND_PERSON.search(desc)
    if person:
        rep.add("WARN", "third-person", "SKILL.md", at, "the description is not in third person (\"%s\"). It goes into the system "
                "prompt. Fix: write \"Fills PDF forms\", not \"I can\" or \"You can\"." % person.group(0))
    if not manual_only:
        if len(desc) < DESCRIPTION_MIN:
            rep.add("WARN", "what-and-when", "SKILL.md", at, "the description is %d characters, too short to pick this skill out of many. "
                    "Fix: say what it does and when to use it, with the words people type." % len(desc))
        if not WHEN_CUE.search(desc + " " + str(fields.get("when_to_use", {}).get("value", ""))):
            rep.add("WARN", "what-and-when", "SKILL.md", at, "the description says what the skill does but not when to use it. "
                    "Fix: add a 'Use when ...' clause with the words people type.")
    extra = fields.get("when_to_use", {}).get("value", "")
    total = len(desc) + (len(extra) if isinstance(extra, str) else 0)
    if total > LISTING_MAX:
        rep.add("WARN", "key-use-first", "SKILL.md", at, "description plus when_to_use is %d characters. Claude Code cuts the skill list "
                "at %d, so the end is lost. Fix: put the key use case first and cut the rest." % (total, LISTING_MAX))
    if FILL_PLACEHOLDER.search(desc):
        rep.add("WARN", "nothing-unfinished", "SKILL.md", at, "the description still holds a [FILL: ...] placeholder. Fix: write the real description.")


def check_layout(rep, lines, body_start):
    body = lines[body_start:]
    count = len(body)
    if count > BODY_MAX_LINES:
        rep.add("WARN", "short-body", "SKILL.md", [], "the SKILL.md body is %d lines; the limit is %d. Fix: move detail into "
                "reference files that SKILL.md links." % (count, BODY_MAX_LINES))
    budget = COMPACTION_KEEP_TOKENS * CHARS_PER_TOKEN
    used, cut = 0, None
    for i, text in enumerate(body):
        used += len(text) + 1
        if used > budget and cut is None:
            cut = body_start + i + 1
    tokens = used // CHARS_PER_TOKEN
    if cut:
        rep.add("NOTE", "key-rules-first", "SKILL.md", [cut], "the SKILL.md body is about {:,} tokens. After compaction Claude Code keeps "
                "only the first {:,}, which ends near line {}. Fix: put the rules that matter most above that line.".format(
                    tokens, COMPACTION_KEEP_TOKENS, cut))


def python_imports(text):
    """Top-level imports only. An indented import sits in a function or a try block, so it is
    optional or loaded from a path the script sets up itself; asking for an install line would be wrong."""
    names = []
    for number, line in enumerate(text.splitlines(), 1):
        if line[:1] in (" ", "\t"):
            continue
        m = PY_IMPORT.match(line)
        if not m:
            continue
        mods = [m.group(1)] if m.group(1) else [x.strip() for x in m.group(2).split(",")]
        for mod in mods:
            if not keyword.iskeyword(mod):
                names.append((mod, number))
    return names


def fenced_python_imports(text):
    """Imports inside ```python blocks of a Markdown file, with their line numbers."""
    names, in_python, fence = [], False, None
    for number, line in enumerate(text.splitlines(), 1):
        m = FENCE.match(line)
        if m:
            if fence is None:
                fence = m.group(1)[0]
                in_python = line.strip().lstrip("`~").strip().lower() in ("python", "py", "python3")
            elif m.group(1)[0] == fence:
                fence, in_python = None, False
            continue
        if in_python:
            p = PY_IMPORT.match(line)
            if p:
                mods = [p.group(1)] if p.group(1) else [x.strip() for x in p.group(2).split(",")]
                names.extend((mod, number) for mod in mods if not keyword.iskeyword(mod))
    return names


def check_skill(root, skipped, no_em_dash=False):
    root = Path(root)
    rep = Report(str(root), skipped)
    if not root.is_dir():
        rep.add("ERROR", "frontmatter-loads", "SKILL.md", [], "%s is not a folder." % root)
        return rep
    skill_md = root / "SKILL.md"
    if not skill_md.is_file():
        other = [p.name for p in root.iterdir() if p.name.lower() == "skill.md"]
        if other:
            rep.add("ERROR", "frontmatter-loads", other[0], [], "the file is named '%s'. Fix: rename it to SKILL.md exactly." % other[0])
        else:
            rep.add("ERROR", "frontmatter-loads", "SKILL.md", [], "this folder has no SKILL.md. A skill is a folder with a SKILL.md at its top. "
                    "Fix: add one, or delete the folder if it is not a skill.")
        return rep
    text = read_text(skill_md)
    if text is None:
        rep.add("ERROR", "frontmatter-loads", "SKILL.md", [], "SKILL.md cannot be read as text. Fix: save it as UTF-8.")
        return rep
    lines = text.splitlines()
    fields, end_line, problems = parse_frontmatter(lines)
    if fields is None:
        rep.add("ERROR", "frontmatter-loads", "SKILL.md", [1], "line 1 is not '---', so Claude Code finds no frontmatter and the skill "
                "cannot trigger on its own. Fix: start the file with the '---' frontmatter block.")
        fields, body_start = {}, 0
    else:
        for number, message in problems:
            rep.add("ERROR", "frontmatter-loads", "SKILL.md", [number], message)
        body_start = end_line or 0
    manual_only = check_header(rep, root.name, fields)
    check_trigger(rep, fields, manual_only)
    check_layout(rep, lines, body_start)

    files, nested = collect_files(root)
    if nested:
        rep.add("NOTE", "reachable-files", "SKILL.md", [], "%s hold(s) its own SKILL.md, so it is a separate skill and is not checked "
                "here. Fix: check it on its own; if it is a stale copy, delete it." % list_names(nested))
    rel = {f: f.relative_to(root).as_posix() for f in files}
    texts = {f: read_text(f) for f in files if f.suffix.lower() in TEXT_SUFFIXES}
    docs = [f for f in files if f.suffix.lower() == ".md" and f != skill_md and rel[f].lower() not in REPO_FILES]

    # Links: dead links, links that leave the folder, and how each reference file is reached.
    linked_from = {}
    outside = []
    for f in [skill_md] + docs:
        content = texts.get(f)
        if content is None:
            continue
        _, _, no_code = prose_views(content.splitlines(), body_start if f == skill_md else 0)
        for number, raw in links_in(no_code):
            target = local_target(raw)
            if target is None:
                continue
            path = (f.parent / target)
            if not inside(root, path):
                outside.append((rel[f], number, target))
                continue
            if not path.exists():
                rep.add("ERROR", "reachable-files", rel[f], [number], "the link to '%s' points at nothing. Fix: correct the path, or "
                        "delete the link." % short(target))
                continue
            if path.is_file():
                linked_from.setdefault(path.resolve(), []).append((f, number))
    if outside:
        first = outside[0][0]
        rep.add("NOTE", "reachable-files", first, [o[1] for o in outside if o[0] == first], "%d link(s) leave the skill folder (%s). The "
                "skill breaks if it is copied on its own. Fix: copy what it needs into the folder." % (len(outside), short(outside[0][2], 40)))

    from_skill = {p for p, srcs in linked_from.items() if any(s == skill_md for s, _ in srcs)}
    skill_body = "\n".join(lines[body_start:])
    for f in docs:
        key = f.resolve()
        if key in from_skill or mentions(skill_body, rel[f]):
            continue
        sources = linked_from.get(key, [])
        if sources:
            src, number = sources[0]
            rep.add("ERROR", "one-hop", rel[src], [n for s, n in sources if s == src], "%s is reached only through %s, never from "
                    "SKILL.md, so Claude may read only its start. Fix: link it from SKILL.md, or fold it into %s." % (rel[f], rel[src], rel[src]))

    # Orphans: files no file in the skill names.
    corpus = {f: t for f, t in texts.items() if t}
    orphans = []
    for f in files:
        name = rel[f]
        if BACKUP_NAME.search(f.name):
            continue  # reported once, as a backup
        if f == skill_md or name.lower() in REPO_FILES or f.name.lower() in MANIFESTS:
            continue
        if f.resolve() in linked_from:
            continue
        module = name[:-3].replace("/", ".") if name.endswith(".py") else None
        named = False
        for other, content in corpus.items():
            if other == f:
                continue
            if mentions(content, name) or (module and re.search(r"\b" + re.escape(module) + r"\b", content)):
                named = True
                break
        if not named:
            orphans.append(name)
    if orphans:
        rep.add("WARN", "reachable-files", "SKILL.md", [], "%d file(s) are named by no other file, so Claude never has a reason to open them: "
                "%s. Fix: link each one from SKILL.md with a line on when to read it, or delete it." % (len(orphans), list_names(orphans)))
    vague = [rel[f] for f in files if VAGUE_FILE_STEM.match(f.stem) and rel[f].lower() not in REPO_FILES]
    if vague:
        rep.add("NOTE", "reachable-files", "SKILL.md", [], "these file names do not say what the file holds: %s. Fix: rename them, for "
                "example 'form-field-rules.md' instead of 'doc2.md'." % list_names(vague))
    backups = [rel[f] for f in files if BACKUP_NAME.search(f.name)]
    if backups:
        rep.add("WARN", "reachable-files", "SKILL.md", [], "backup or old copies sit inside the skill: %s. Claude may read them as live "
                "instructions. Fix: delete them or move them out of the folder." % list_names(backups))

    # Per-file text checks.
    checklist_files, hard_rule_hits = [], []
    has_hooks = "hooks" in fields
    all_text = "\n".join(t for t in corpus.values())
    for f in [skill_md] + docs:
        content = texts.get(f)
        if content is None:
            continue
        name = rel[f]
        raw = content.splitlines()
        with_code, prose, _ = prose_views(raw, body_start if f == skill_md else 0)
        if f != skill_md and len(raw) > CONTENTS_MIN_LINES:
            if not any(CONTENTS_HEADING.match(x) for x in raw[:CONTENTS_LOOK_LINES]):
                rep.add("ERROR", "contents-list", name, [], "%s is %d lines with no contents list in its first %d lines. Fix: add a "
                        "'## Contents' list at the top, so a partial read still shows the whole file." % (name, len(raw), CONTENTS_LOOK_LINES))
        slashes = [(i + 1, m.group(1)) for i, x in enumerate(with_code) for m in BACKSLASH_PATH.finditer(x)]
        if slashes:
            rep.add("ERROR", "forward-slashes", name, [s[0] for s in slashes], "a path uses backslashes (%s). It breaks on Mac and Linux. "
                    "Fix: use forward slashes." % short(slashes[0][1], 40))
        old = old_sections(raw)
        phrases = [(i + 1, m.group(0)) for i, x in enumerate(prose) if i not in old for m in TIME_PHRASE.finditer(x)]
        if phrases:
            rep.add("WARN", "no-expiry-dates", name, [p[0] for p in phrases], "time-bound wording (\"%s\") goes stale without anyone "
                    "noticing. Fix: state today's method, and move the old one under an '## Old patterns' heading." % phrases[0][1])
        dates = [(i + 1, m.group(0)) for i, x in enumerate(prose) if i not in old for m in ISO_DATE.finditer(x)]
        if dates:
            rep.add("NOTE", "no-expiry-dates", name, [d[0] for d in dates], "%d date(s) such as %s. If a date stands in for the reason "
                    "behind a rule, write the reason instead." % (len(dates), dates[0][1]))
        # A comment marker counts anywhere; a "TODO:" label counts only outside quotes and code,
        # so an example such as a stub that logs "TODO: send email" is not flagged.
        todos = [i + 1 for i, x in enumerate(with_code) if TODO_COMMENT.search(x) or TODO_LABEL.search(prose[i])]
        if todos:
            rep.add("ERROR", "nothing-unfinished", name, todos, "an unfinished TODO or FIXME marker is left in the file. Fix: finish the work "
                    "or delete the marker.")
        floor = body_start if f == skill_md else 0
        # Inline code is left out, so a sentence that names the scaffold marker is not flagged.
        fills = [i + 1 for i, x in enumerate(with_code) if FILL_PLACEHOLDER.search(x) and i + 1 > floor]
        if fills:
            rep.add("WARN", "nothing-unfinished", name, fills, "a [FILL: ...] placeholder from the scaffold is still here. "
                    "Fix: replace it with real text.")
        transcript = [(i + 1, m.group(0)) for i, x in enumerate(prose) for m in REASONING_TRANSCRIPT.finditer(x)]
        if transcript:
            rep.add("WARN", "no-reasoning-transcript", name, [t[0] for t in transcript], "this asks Claude to write out its reasoning (\"%s\"). "
                    "Newer models may refuse it as reasoning extraction. Fix: ask for the answer and a short reason for it." % transcript[0][1])
        loud = [i + 1 for i, x in enumerate(prose) for _ in EMPHASIS.finditer(x)]
        if len(loud) > EMPHASIS_MAX:
            rep.add("WARN", "light-steering", name, sorted(set(loud)), "%d capitalised MUST, NEVER, ALWAYS, CRITICAL or IMPORTANT. When "
                    "everything shouts, nothing stands out. Fix: keep capitals for the few hard lines; write the rest plainly." % len(loud))
        if not has_hooks:
            for i, x in enumerate(prose):
                m = HARD_RULE.search(x)
                if m:
                    hard_rule_hits.append((name, i + 1, m.group(0)))
        if any(CHECKBOX.match(x) for x in with_code):
            checklist_files.append(name)
        if no_em_dash:
            dashes = [i + 1 for i, x in enumerate(raw) if "\u2014" in x]
            if dashes:
                rep.add("WARN", "STYLE", name, dashes, "%d line(s) use an em dash. Fix: use a comma, a colon or ' - '." % len(dashes))
    if hard_rule_hits:
        first = hard_rule_hits[0][0]
        rep.add("NOTE", "hard-rules-in-hooks", first, [h[1] for h in hard_rule_hits if h[0] == first], "wording such as \"%s\" marks a rule "
                "that must hold on every run, and the skill has no hooks. Prose can be skipped or lost to compaction. Fix: if the "
                "rule truly cannot bend, enforce it with a hook in the frontmatter." % hard_rule_hits[0][2])
    if checklist_files and not GO_BACK.search(all_text):
        rep.add("NOTE", "checklist", checklist_files[0], [], "there is a checklist but no line that says where to go back when a "
                "check fails. Fix: add one, such as 'If the check fails, return to step 2'.")

    # Scripts: unfinished markers and packages with no install line.
    needed = {}
    local_modules = {p.stem for p in files if p.suffix == ".py"} | {part for p in files for part in p.relative_to(root).parts[:-1]}
    for f in files:
        content = texts.get(f)
        if content is None or rel[f].lower() in REPO_FILES:
            continue
        suffix = f.suffix.lower()
        if suffix in (".py", ".js", ".mjs", ".cjs", ".ts", ".mts", ".jsx", ".tsx", ".sh", ".bash"):
            todos = [i + 1 for i, x in enumerate(content.splitlines()) if re.search(r"(#|//|/\*)\s*(TODO|FIXME|XXX)\b", x)]
            if todos:
                rep.add("ERROR", "nothing-unfinished", rel[f], todos, "an unfinished TODO or FIXME comment is left in the script. Fix: finish "
                        "the work or delete the comment.")
            # In code, a marker counts only in a comment line; code that holds the marker as data
            # (a scaffolder's template, a checker's pattern) is not unfinished.
            fills = [i + 1 for i, x in enumerate(content.splitlines())
                     if x.strip().startswith(("#", "//")) and FILL_PLACEHOLDER.search(x)]
            if fills:
                rep.add("WARN", "nothing-unfinished", rel[f], fills, "a [FILL: ...] placeholder from the scaffold is still here. "
                        "Fix: replace it with real text.")
        if suffix == ".md":
            for mod, number in fenced_python_imports(content):
                if mod in STDLIB or mod in local_modules:
                    continue
                needed.setdefault(PY_PACKAGE_FOR.get(mod, mod), (rel[f], number, "pip install"))
        if suffix == ".py":
            for mod, number in python_imports(content):
                if mod in STDLIB or mod in local_modules:
                    continue
                needed.setdefault(PY_PACKAGE_FOR.get(mod, mod), (rel[f], number, "pip install"))
        elif suffix in (".js", ".mjs", ".cjs", ".ts", ".mts", ".jsx", ".tsx"):
            for m in JS_IMPORT.finditer(content):
                pkg = m.group(1)
                if not re.fullmatch(r"(node:)?@?[a-z0-9][\w.-]*(/[\w.-]+)*", pkg):
                    continue  # not a package name (a template string or a placeholder)
                pkg = "/".join(pkg.split("/")[:2]) if pkg.startswith("@") else pkg.split("/")[0]
                if pkg.replace("node:", "") in NODE_BUILTINS or pkg.startswith("node:"):
                    continue
                needed.setdefault(pkg, (rel[f], content[: m.start()].count("\n") + 1, "npm install"))
    if needed:
        manifest_text = "\n".join(texts.get(f) or "" for f in files if f.name.lower() in MANIFESTS)
        missing = []
        for pkg, (file, number, tool) in sorted(needed.items()):
            if re.search(r"\b(pip3?|uv|npm|pnpm|yarn|brew)\s+(install|add)\b[^\n]*\b" + re.escape(pkg) + r"\b", all_text, re.I):
                continue
            if re.search(r"(^|[\s\"'])" + re.escape(pkg) + r"([\s\"'=<>~@:,]|$)", manifest_text, re.I | re.M):
                continue
            missing.append(pkg)
            rep.add("WARN", "install-lines", file, [number], "%s needs the package '%s', and no install line or manifest lists it. "
                    "Fix: add '%s %s' next to the step that runs the script." % (file, pkg, tool, pkg))
        rep.add("NOTE", "install-lines", "SKILL.md", [], "this skill needs packages outside the standard library (%s). Claude Code and "
                "claude.ai can install them; the Claude API cannot, so the skill will not run there." % list_names(needed))
    return rep


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def check_rule_names(skips, source):
    unknown = sorted(r for r in skips if r not in ALL_RULES and r != "STYLE")
    if unknown:
        print("%s names rule(s) the checker does not know: %s. Fix: use a name from this list: %s."
              % (source, ", ".join(unknown), ", ".join(ALL_RULES)), file=sys.stderr)
        sys.exit(2)


def load_skips(*folders):
    skips = {}
    for folder in folders:
        config = Path(folder) / "skill-builder.json"
        if config.is_file():
            try:
                data = json.loads(config.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                print("skill-builder.json in %s cannot be read: %s. Fix: make it valid JSON." % (folder, error), file=sys.stderr)
                sys.exit(2)
            found = {rule: str(reason) for rule, reason in (data.get("skip") or {}).items()}
            check_rule_names(found, str(config))
            skips.update(found)
    return skips


def summary(rep):
    return "%d error(s), %d warning(s), %d note(s)" % (rep.count("ERROR"), rep.count("WARN"), rep.count("NOTE"))


def print_report(rep):
    print("Skill: %s%s" % (rep.path, " (name: %s)" % rep.name if rep.name else ""))
    for f in rep.sorted_findings():
        print("  %-5s  %-24s %s  %s" % (f["level"], f["rule"], where(f["file"], f["lines"]), f["message"]))
    for rule, reason in sorted(rep.skipped.items()):
        print("  SKIP   %-24s %s" % (rule, reason))
    print("Passed (no error or warning): %s" % (" ".join(rep.passed()) or "none"))
    verdict = "fix the errors first." if rep.count("ERROR") else ("no errors; review the warnings." if rep.count("WARN") else "clean.")
    print("Result: %s - %s" % (summary(rep), verdict))
    print()


def print_table(reports):
    width = max([len("Skill")] + [len(Path(r.path).name) for r in reports])
    print("%-*s  Errors  Warnings  Notes  Rules with errors or warnings" % (width, "Skill"))
    print("%s  ------  --------  -----  -----------------------------" % ("-" * width))
    order = sorted(reports, key=lambda r: (-r.count("ERROR"), -r.count("WARN"), Path(r.path).name))
    for r in order:
        rules = sorted({f["rule"] for f in r.findings if f["level"] in ("ERROR", "WARN")},
                       key=lambda x: RULE_ORDER.index(x) if x in RULE_ORDER else 99)
        print("%-*s  %6d  %8d  %5d  %s" % (width, Path(r.path).name, r.count("ERROR"), r.count("WARN"), r.count("NOTE"), " ".join(rules)))
    print()
    print("%d skill(s) checked: %d with errors, %d with only warnings, %d clean." % (
        len(reports), sum(1 for r in reports if r.count("ERROR")),
        sum(1 for r in reports if not r.count("ERROR") and r.count("WARN")),
        sum(1 for r in reports if not r.count("ERROR") and not r.count("WARN"))))


def as_json(rep):
    return {"path": rep.path, "name": rep.name,
            "counts": {"error": rep.count("ERROR"), "warn": rep.count("WARN"), "note": rep.count("NOTE")},
            "passed": rep.passed(), "skipped": rep.skipped, "findings": rep.sorted_findings()}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check Agent Skill folders against the script-checkable rules in references/rules.md.")
    parser.add_argument("path", help="a skill folder, or with --all a folder of skill folders")
    parser.add_argument("--all", action="store_true", help="check every subfolder of PATH as a skill and print one table")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--skip", action="append", default=[], metavar="RULE", help="leave a rule out (repeatable)")
    parser.add_argument("--no-em-dash", action="store_true", help="also flag em dashes (house style, not an Anthropic rule)")
    args = parser.parse_args(argv)

    base = Path(args.path).expanduser()
    if not base.is_dir():
        print("%s is not a folder. Fix: pass the path to a skill folder, or a folder of skills with --all." % base, file=sys.stderr)
        return 2
    cli_skips = {rule: "skipped with --skip" for rule in args.skip}
    check_rule_names(cli_skips, "--skip")
    if args.all:
        folders = sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name not in NOT_FOR_CLAUDE)
        if not folders:
            print("%s holds no subfolders. Fix: pass the folder that holds your skill folders." % base, file=sys.stderr)
            return 2
        shared = load_skips(base)
        reports = [check_skill(p, dict(shared, **load_skips(p), **cli_skips), args.no_em_dash) for p in folders]
    else:
        # The parent folder's file applies too, so one skill checks the same way as with --all.
        reports = [check_skill(base, dict(load_skips(base.resolve().parent, base), **cli_skips), args.no_em_dash)]

    if args.json:
        print(json.dumps({"skills": [as_json(r) for r in reports]}, indent=1))
    elif args.all:
        print_table(reports)
    else:
        print_report(reports[0])
    return 1 if any(r.count("ERROR") for r in reports) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
