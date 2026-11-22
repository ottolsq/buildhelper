#!/usr/bin/env python3
"""Validate a project's documentation set.

Checks required files, required sections, page-length warnings, relative links,
ADR numbering and leftover template placeholders. Rules live in
``references/checks.json`` next to this script, so the script carries no project
knowledge.

Stages are cumulative: ``milestone`` also requires everything ``founding``
requires, ``release`` requires all three.

Exit codes
    0  clean (warnings allowed)
    1  findings: at least one FAIL
    2  usage or configuration error: never a traceback

Runs on Windows, macOS and Linux with the Python 3.8+ standard library only.
"""

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".dsh", ".agents", ".venv", "dist", "build", "__pycache__"}
LINK_RE = re.compile(r"\[[^\]]*\]\(\s*<?([^)>\s]+)")
INLINE_CODE_RE = re.compile(r"`[^`\r\n]*`")
ADR_NAME_RE = re.compile(r"^(\d{3})-")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2


class ConfigError(Exception):
    pass


class Report:
    def __init__(self):
        self.failures = 0
        self.warnings = 0

    def fail(self, message):
        print("FAIL  " + message)
        self.failures += 1

    def warn(self, message):
        print("WARN  " + message)
        self.warnings += 1

    def ok(self, message):
        print("ok    " + message)


def read_text(path):
    """Decode a file without ever raising: utf-8 first, then gb18030, then latin-1."""
    data = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace")


def load_rules(config_path):
    try:
        settings = json.loads(read_text(config_path))
    except (json.JSONDecodeError, ValueError) as exc:
        raise ConfigError("invalid JSON in {0}: {1}".format(config_path, exc))

    stages = settings.get("stages")
    files = settings.get("files")
    if isinstance(files, dict) and files:
        return settings, (stages or {"founding": sorted(files)}), files

    legacy = settings.get("requiredFiles")
    if isinstance(legacy, dict) and legacy:
        files = {}
        for name, sections in legacy.items():
            files[name] = {"sections": sections or [], "maxLines": None}
        return settings, {"founding": sorted(files)}, files

    raise ConfigError("config has neither 'stages'+'files' nor 'requiredFiles': " + str(config_path))


def required_files(stages, stage):
    order = list(stages)
    if stage not in stages:
        raise ConfigError("unknown stage {0!r}; known: {1}".format(stage, ", ".join(order)))
    names = []
    for current in order[: order.index(stage) + 1]:
        for name in stages[current]:
            if name not in names:
                names.append(name)
    return names


def load_gitignore(root):
    """Read the target's .gitignore into (pattern, dir_only, anchored) rules.

    Only the common forms are supported: comments, blank lines, trailing slash for
    directories, a leading slash to anchor at the root, and ``*`` / ``?`` globs.
    Negations (``!pattern``) are skipped, which can only make the scan wider.
    """
    path = Path(root) / ".gitignore"
    if not path.is_file():
        return []
    rules = []
    for line in read_text(path).splitlines():
        item = line.strip()
        if not item or item.startswith("#") or item.startswith("!"):
            continue
        dir_only = item.endswith("/")
        item = item.rstrip("/")
        anchored = item.startswith("/")
        item = item.lstrip("/")
        if item:
            rules.append((item, dir_only, anchored))
    return rules


def is_ignored(relative_path, rules):
    if not rules:
        return False
    parts = relative_path.split("/")
    for depth in range(1, len(parts) + 1):
        prefix = "/".join(parts[:depth])
        is_dir = depth < len(parts)
        name = parts[depth - 1]
        for pattern, dir_only, anchored in rules:
            if dir_only and not is_dir:
                continue
            candidate = prefix if anchored else name
            if fnmatch.fnmatchcase(candidate, pattern):
                return True
    return False


def iter_markdown(root, material_root, ignore_rules):
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if is_ignored(rel.as_posix(), ignore_rules):
            continue
        try:
            if material_root is not None and material_root in path.resolve().parents:
                continue
        except OSError:
            continue
        yield path


def check_required(root, files, names, report):
    if not names:
        report.warn("no files required by this stage")
        return
    for name in names:
        rule = files.get(name) or {}
        path = root / name
        if not path.is_file():
            report.fail("missing file: " + name)
            continue
        text = read_text(path)
        sections = rule.get("sections") or []
        missing = [section for section in sections if section not in text]
        if missing:
            report.fail("missing section in {0}: {1}".format(name, ", ".join(missing)))
        else:
            report.ok("sections: " + name)

        limit = rule.get("maxLines")
        if isinstance(limit, int) and limit > 0:
            lines = len(text.splitlines())
            if lines > limit:
                report.warn("length {0}/{1} lines in {2}".format(lines, limit, name))


def warn_if_container(root, report):
    """A directory without a README but with nested repositories is a workspace, not a project."""
    if (root / "README.md").is_file():
        return
    try:
        nested = sorted(p.name for p in root.iterdir() if p.is_dir() and (p / ".git").exists())
    except OSError:
        return
    if nested:
        report.warn(
            "looks like a workspace container, not a project: {0} nested repo(s) here ({1}); rerun with -root pointing at one of them".format(
                len(nested), ", ".join(nested)
            )
        )


def check_links(root, material_root, ignore_rules, report):
    broken = 0
    unpublished = 0
    for path in iter_markdown(root, material_root, ignore_rules):
        for target in LINK_RE.findall(read_text(path)):
            target = target.strip()
            if not target or SCHEME_RE.match(target):
                continue
            if target.startswith("#") or target.startswith("/"):
                continue
            clean = target.split("#", 1)[0].strip("<>")
            if not clean:
                continue
            candidate = path.parent / clean
            if not candidate.exists():
                broken += 1
                report.warn("broken link in {0}: {1}".format(relative(path, root), target))
                continue
            try:
                target_rel = candidate.resolve().relative_to(root).as_posix()
            except (ValueError, OSError):
                continue
            if is_ignored(target_rel, ignore_rules):
                unpublished += 1
                report.warn("published file {0} links to ignored path: {1}".format(relative(path, root), target))
    if broken == 0:
        report.ok("relative links resolve")
    if unpublished == 0:
        report.ok("no published file links into ignored paths")


def check_adr(root, report):
    adr_dir = root / "docs" / "adr"
    if not adr_dir.is_dir():
        return
    seen = {}
    for path in sorted(adr_dir.glob("*.md")):
        match = ADR_NAME_RE.match(path.name)
        if not match:
            report.warn("adr without number: " + path.name)
            continue
        number = int(match.group(1))
        if number in seen:
            report.fail("duplicate adr number {0}: {1} and {2}".format(number, seen[number], path.name))
        else:
            seen[number] = path.name
    if not seen:
        return
    highest = max(seen)
    if highest != len(seen):
        report.warn("adr numbering has gaps: {0} file(s), highest number {1}".format(len(seen), highest))
    else:
        report.ok("adr numbering contiguous: {0} file(s)".format(len(seen)))


def check_placeholders(root, material_root, settings, ignore_rules, strict, report):
    marker = settings.get("placeholderMarker") or "<!-- fill"
    hits = 0
    for path in iter_markdown(root, material_root, ignore_rules):
        body = INLINE_CODE_RE.sub("", read_text(path))
        count = body.count(marker)
        if count <= 0:
            continue
        hits += count
        message = "unfilled placeholder x{0} in {1}".format(count, relative(path, root))
        if strict:
            report.fail(message)
        else:
            report.warn(message)
    if hits == 0:
        report.ok("no unfilled placeholders")


def relative(path, root):
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def run(args):
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        raise ConfigError("-root is not a directory: " + str(root))

    config = Path(args.config).expanduser().resolve() if args.config else Path(__file__).resolve().parent.parent / "references" / "checks.json"
    if not config.is_file():
        raise ConfigError("config not found: " + str(config))

    settings, stages, files = load_rules(config)
    names = required_files(stages, args.stage)
    material_root = Path(__file__).resolve().parent.parent / "references"
    ignore_rules = load_gitignore(root)
    if args.published:
        skipped = [name for name in names if is_ignored(name, ignore_rules)]
        names = [name for name in names if not is_ignored(name, ignore_rules)]
        if skipped:
            print("skip  local-only (not published): " + ", ".join(skipped))

    report = Report()
    check_required(root, files, names, report)
    check_links(root, material_root, ignore_rules, report)
    check_adr(root, report)
    check_placeholders(root, material_root, settings, ignore_rules, args.strict, report)
    warn_if_container(root, report)

    print("")
    suffix = ", published only" if args.published else ""
    print("{0} failure(s), {1} warning(s) under {2} (stage: {3}{4})".format(report.failures, report.warnings, root, args.stage, suffix))
    return EXIT_FINDINGS if report.failures else EXIT_OK


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a project's documentation set.")
    parser.add_argument("-root", "--root", default=".", help="project root (default: current directory)")
    parser.add_argument("-config", "--config", default=None, help="path to checks.json (default: ../references/checks.json)")
    parser.add_argument("-stage", "--stage", default="founding", help="founding (default) / milestone / release; stages are cumulative")
    parser.add_argument("-published", "--published", action="store_true", help="check only files that a clone would receive (skips gitignored ones)")
    parser.add_argument("-strict", "--strict", action="store_true", help="treat unfilled placeholders as failures")
    args = parser.parse_args(argv)

    try:
        return run(args)
    except ConfigError as exc:
        print("error: " + str(exc), file=sys.stderr)
        return EXIT_USAGE
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return EXIT_USAGE
    except Exception as exc:  # never leak a traceback at the user
        print("error: unexpected failure: {0}: {1}".format(type(exc).__name__, exc), file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass
    sys.exit(main())
