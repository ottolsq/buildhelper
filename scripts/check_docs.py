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
import os
import re
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".dsh", ".agents", ".venv", "dist", "build", "__pycache__"}
LINK_RE = re.compile(r"\[[^\]]*\]\(\s*<?([^)>\s]+)")
INLINE_CODE_RE = re.compile(r"`[^`\r\n]*`")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
COMMENT_START_RE = re.compile(r"^ {0,3}<!--")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*)$")
HEADING_END_RE = re.compile(r"(?:^|[ \t]+)#+[ \t]*$")
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


def load_config_file(config_path, seen=None):
    """Read a config, merging ``extends`` so a project can override only what differs."""
    path = Path(config_path).resolve()
    seen = set(seen or ())
    if path in seen:
        raise ConfigError("config extends loop at {0}".format(path))
    seen.add(path)
    try:
        settings = json.loads(read_text(path))
    except (json.JSONDecodeError, ValueError) as exc:
        raise ConfigError("invalid JSON in {0}: {1}".format(path, exc))
    if not isinstance(settings, dict):
        raise ConfigError("config must be a JSON object: " + str(path))

    base = settings.get("extends")
    if not base:
        return settings
    base_path = (path.parent / base).resolve()
    if not base_path.is_file():
        raise ConfigError("config extends missing file: {0} (from {1})".format(base_path, path))
    parent = load_config_file(base_path, seen)
    merged = dict(parent)
    for key, value in settings.items():
        if key != "extends":
            merged[key] = value
    base_files = dict(parent.get("files") or {})
    for name, rule in (settings.get("files") or {}).items():
        combined = dict(base_files.get(name) or {})
        combined.update(rule or {})
        base_files[name] = combined
    if "files" in settings:
        merged["files"] = base_files
    return merged


def load_rules(config_path):
    settings = load_config_file(config_path)

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

    A leading or internal slash anchors a rule at the root; a trailing slash
    makes it directory-only. ``*`` and ``?`` match within one path component.
    Negations (``!pattern``) and recursive ``**`` matching are not supported.
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
        anchored = "/" in item
        item = item.lstrip("/")
        if item:
            rules.append((item, dir_only, anchored))
    return rules


def is_ignored(relative_path, rules):
    if not rules:
        return False
    parts = relative_path.split("/")
    for pattern, dir_only, anchored in rules:
        candidates = parts[:-1] if dir_only else parts
        if anchored:
            pattern_parts = pattern.split("/")
            if len(pattern_parts) <= len(candidates) and all(
                fnmatch.fnmatchcase(name, part_pattern)
                for name, part_pattern in zip(candidates, pattern_parts)
            ):
                return True
        elif any(fnmatch.fnmatchcase(name, pattern) for name in candidates):
            return True
    return False


def mask_fenced(text):
    """Blank out fenced code blocks, keeping line numbers.

    Example links and template markers live inside fences on purpose: they are
    illustrations, not real links or unfilled placeholders.
    """
    out = []
    fence = ""
    for line in text.splitlines(True):
        match = FENCE_RE.match(line.rstrip("\r\n"))
        if fence:
            if match and match.group(1).startswith(fence) and not match.group(2).strip(" \t"):
                fence = ""
            out.append(re.sub(r"[^\r\n]", " ", line))
            continue
        if match and (match.group(1).startswith("~") or "`" not in match.group(2)):
            fence = match.group(1)
            out.append(re.sub(r"[^\r\n]", " ", line))
            continue
        out.append(line)
    return "".join(out)


def repo_location(root):
    """Return (repository top, ``root`` prefix inside it) for the git work tree."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except (OSError, ValueError):
        raise ConfigError("--staged needs git on PATH: rev-parse --show-toplevel failed")
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip().splitlines()
        raise ConfigError("--staged needs a git work tree at {0}: {1}".format(
            root, detail[-1] if detail else result.returncode))
    top = Path(result.stdout.decode("utf-8", "replace").strip()).resolve()
    here = Path(root).resolve()
    if os.path.normcase(str(top)) == os.path.normcase(str(here)):
        return top, ""
    prefix = os.path.relpath(str(here), str(top))
    if prefix.startswith(".."):
        raise ConfigError("-root is not inside its git work tree: {0}".format(root))
    return top, prefix.replace("\\", "/")


def git_paths(top, args, what, prefix=""):
    """Run a command at the repository top and keep only paths under ``prefix``."""
    try:
        result = subprocess.run(
            ["git", "-C", str(top)] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except (OSError, ValueError):
        raise ConfigError("--staged needs git on PATH: " + what)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip().splitlines()
        raise ConfigError("--staged git {0}: {1}".format(what, detail[-1] if detail else result.returncode))
    paths = []
    for item in result.stdout.split(b"\0"):
        if not item:
            continue
        path = item.decode("utf-8", "replace").replace("\\", "/")
        if prefix:
            if not path.startswith(prefix + "/"):
                continue
            path = path[len(prefix) + 1:]
        paths.append(path)
    return paths


def index_paths(root):
    """Files in the git index: what a commit made now would contain."""
    top, prefix = repo_location(root)
    return set(git_paths(top, ["ls-files", "-z"], "ls-files failed", prefix=prefix))


def worktree_changes(root):
    """Tracked files whose worktree content differs from the index."""
    top, prefix = repo_location(root)
    return sorted(git_paths(top, ["diff", "--name-only", "-z"], "diff failed", prefix=prefix))


def under_roots(relative_posix, roots):
    return any(relative_posix == root or relative_posix.startswith(root + "/") for root in roots)


def collect_markdown(root, material_root, ignore_rules, scan_ignored_roots=()):
    """Return (files to scan, gitignored paths skipped).

    Local mode still reads documentation that the project keeps out of git (its
    ``docs/`` tree): the required files decide which ignored directory is the
    local document set, so build outputs and archived studies stay out.
    """
    files = []
    skipped = []
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        posix = rel.as_posix()
        if is_ignored(posix, ignore_rules) and not under_roots(posix, scan_ignored_roots):
            skipped.append(posix)
            continue
        try:
            if material_root is not None and material_root in path.resolve().parents:
                continue
        except OSError:
            continue
        files.append(path)
    return files, skipped


def markdown_headings(text):
    headings = set()
    active_fence = ""
    in_comment = False
    for line in text.splitlines():
        if in_comment:
            in_comment = "-->" not in line
            continue

        fence = FENCE_RE.match(line)
        if active_fence:
            if fence and fence[1].startswith(active_fence) and not fence[2].strip(" \t"):
                active_fence = ""
            continue
        if fence and (fence[1].startswith("~") or "`" not in fence[2]):
            active_fence = fence[1]
            continue
        if COMMENT_START_RE.match(line):
            in_comment = "-->" not in line
            continue

        heading = HEADING_RE.match(line)
        if heading:
            title = HEADING_END_RE.sub("", heading[2]).strip()
            if title:
                prefix = heading[1] + " "
                headings.update((prefix, prefix + title))
    return headings


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
        headings = markdown_headings(text) if sections else set()
        missing = [section for section in sections if section not in headings]
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


def check_links(root, files, report, unpublished=None, label="ignored path", clean_message="no published file links into ignored paths"):
    broken = 0
    leaked = 0
    for path in files:
        source_rel = relative(path, root)
        for target in LINK_RE.findall(mask_fenced(read_text(path))):
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
                report.warn("broken link in {0}: {1}".format(source_rel, target))
                continue
            try:
                target_rel = candidate.resolve().relative_to(root).as_posix()
            except (ValueError, OSError):
                continue
            if unpublished is not None and unpublished(source_rel, target_rel):
                leaked += 1
                report.warn("published file {0} links to {1}: {2}".format(source_rel, label, target))
    if broken == 0:
        report.ok("relative links resolve")
    if leaked == 0:
        report.ok(clean_message)


def check_adr(root, ignore_rules, report, tracked=None):
    adr_dir = root / "docs" / "adr"
    if not adr_dir.is_dir():
        return
    seen = {}
    for path in sorted(adr_dir.glob("*.md")):
        rel = path.relative_to(root).as_posix()
        if tracked is not None and rel not in tracked:
            continue
        if is_ignored(rel, ignore_rules):
            continue
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


def check_placeholders(root, files, settings, strict, report):
    marker = settings.get("placeholderMarker") or "<!-- fill"
    hits = 0
    for path in files:
        body = INLINE_CODE_RE.sub("", mask_fenced(read_text(path)))
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


def load_secret_rules(settings):
    section = settings.get("secrets") or {}
    if not section.get("enabled", True):
        return [], None
    allow = section.get("allow") or ""
    allow_re = None
    if allow:
        try:
            allow_re = re.compile(allow)
        except re.error as exc:
            raise ConfigError("invalid secrets allow pattern: {0}".format(exc))
    rules = []
    for item in section.get("rules") or []:
        pattern = item.get("pattern")
        name = item.get("name") or "secret"
        if not pattern:
            continue
        try:
            regex = re.compile(pattern)
        except re.error as exc:
            raise ConfigError("invalid secrets rule {0!r}: {1}".format(name, exc))
        group = int(item.get("valueGroup", 0) or 0)
        if group > (regex.groups or 0):
            group = 0
        rules.append((name, regex, group))
    return rules, allow_re


def check_secrets(root, files, rules, allow_re, strict, report):
    """Report the location and rule name only; never echo the matched value."""
    if not rules:
        return
    hits = 0
    for path in files:
        source_rel = relative(path, root)
        for number, line in enumerate(read_text(path).splitlines(), 1):
            for name, regex, group in rules:
                for match in regex.finditer(line):
                    value = match.group(group) if group else match.group(0)
                    if allow_re is not None and allow_re.search(value):
                        continue
                    hits += 1
                    message = "possible secret ({0}) at {1}:{2}".format(name, source_rel, number)
                    if strict:
                        report.fail(message)
                    else:
                        report.warn(message)
    if hits == 0:
        report.ok("no obvious secrets")
    print("note  secret scan: patterns only; git history and untracked files are not scanned; not exhaustive")


def run(args):
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        raise ConfigError("-root is not a directory: " + str(root))

    config = Path(args.config).expanduser().resolve() if args.config else Path(__file__).resolve().parent.parent / "references" / "checks.json"
    if not config.is_file():
        raise ConfigError("config not found: " + str(config))
    if args.published and args.staged:
        raise ConfigError("--published and --staged are mutually exclusive")

    settings, stages, files = load_rules(config)
    all_names = required_files(stages, args.stage)
    material_root = Path(__file__).resolve().parent.parent / "references"
    ignore_rules = load_gitignore(root)
    index = index_paths(root) if args.staged else None

    print("config " + str(config))

    names = all_names
    scan_ignored_roots = sorted({name.split("/")[0] for name in all_names if "/" in name and is_ignored(name, ignore_rules)})
    if args.published:
        skipped = [name for name in all_names if is_ignored(name, ignore_rules)]
        names = [name for name in all_names if not is_ignored(name, ignore_rules)]
        scan_ignored_roots = ()
        if skipped:
            print("skip  local-only (not published): " + ", ".join(skipped))
    elif args.staged:
        skipped = [name for name in all_names if name not in index]
        names = [name for name in all_names if name in index]
        scan_ignored_roots = ()
        if skipped:
            print("skip  local-only (not in git index): " + ", ".join(skipped))

    if index is not None:
        # The index decides what ships: tracked-but-ignored files are included,
        # untracked files are not, whatever .gitignore says.
        markdown, _ = collect_markdown(root, material_root, (), ())
        untracked = [relative(path, root) for path in markdown if relative(path, root) not in index]
        markdown = [path for path in markdown if relative(path, root) in index]
        if untracked:
            sample = ", ".join(untracked[:3]) + (", ..." if len(untracked) > 3 else "")
            print("skip  untracked (not in git index): {0} file(s) ({1})".format(len(untracked), sample))
        changed = worktree_changes(root)
        if changed:
            sample = ", ".join(changed[:3]) + (", ..." if len(changed) > 3 else "")
            print("note  worktree differs from git index for {0} file(s); checked content is the worktree ({1})".format(len(changed), sample))
        unpublished = lambda source, target: target not in index
        label = "unindexed path"
        clean_message = "no published file links into unindexed paths"
        skipped_paths = len(untracked)
    else:
        markdown, ignored_paths = collect_markdown(root, material_root, ignore_rules, scan_ignored_roots)
        # Only the local mode lists ignored paths: otherwise --published would
        # echo every local-only file back at someone checking a release.
        if ignored_paths and not args.published:
            sample = ", ".join(ignored_paths[:3]) + (", ..." if len(ignored_paths) > 3 else "")
            print("skip  gitignored (not scanned): {0} path(s) ({1})".format(len(ignored_paths), sample))
        unpublished = lambda source, target: is_ignored(target, ignore_rules) and not is_ignored(source, ignore_rules)
        label = "ignored path"
        clean_message = "no published file links into ignored paths"
        skipped_paths = len(ignored_paths)

    report = Report()
    check_required(root, files, names, report)
    check_links(root, markdown, report, unpublished, label, clean_message)
    check_adr(root, ignore_rules if args.published else (), report, tracked=index)
    check_placeholders(root, markdown, settings, args.strict, report)
    secret_rules, secret_allow = load_secret_rules(settings)
    check_secrets(root, markdown, secret_rules, secret_allow, args.strict, report)
    warn_if_container(root, report)

    scope = "{0} markdown file(s) scanned".format(len(markdown))
    if args.staged:
        scope += " from the git index"
    if scan_ignored_roots:
        scope += "; local doc set still read: " + ", ".join(scan_ignored_roots)
    if skipped_paths:
        scope += "; {0} path(s) skipped".format(skipped_paths)
    print("scan  " + scope)
    print("")
    modes = []
    if args.published:
        modes.append("published only")
    if args.staged:
        modes.append("git index only")
    suffix = ", " + ", ".join(modes) if modes else ""
    print("{0} failure(s), {1} warning(s) under {2} (stage: {3}{4})".format(report.failures, report.warnings, root, args.stage, suffix))
    return EXIT_FINDINGS if report.failures else EXIT_OK


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a project's documentation set.")
    parser.add_argument("-root", "--root", default=".", help="project root (default: current directory)")
    parser.add_argument("-config", "--config", default=None, help="path to checks.json (default: ../references/checks.json)")
    parser.add_argument("-stage", "--stage", default="founding", help="founding (default) / milestone / release; stages are cumulative")
    parser.add_argument("-published", "--published", action="store_true", help="check only files that a clone would receive (skips gitignored ones)")
    parser.add_argument("-staged", "--staged", action="store_true", help="check exactly what the git index would commit (needs a git work tree)")
    parser.add_argument("-strict", "--strict", action="store_true", help="treat unfilled placeholders and possible secrets as failures")
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
