#!/usr/bin/env python3
"""Validate a project's documentation set.

Checks required files, required sections, relative links, ADR numbering and
leftover template placeholders. Rules live in ``references/checks.json`` next
to this script, so the script itself carries no project knowledge.

Exit codes
    0  clean (warnings allowed)
    1  findings: at least one FAIL
    2  usage or configuration error: never a traceback

Runs on Windows, macOS and Linux with the Python 3.8+ standard library only.
"""

import argparse
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


class Finding:
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


def load_config(path):
    try:
        return json.loads(read_text(path))
    except (json.JSONDecodeError, ValueError) as exc:
        raise ConfigError("invalid JSON in {0}: {1}".format(path, exc))


class ConfigError(Exception):
    pass


def iter_markdown(root, material_root):
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        try:
            if material_root is not None and material_root in path.resolve().parents:
                continue
        except OSError:
            continue
        yield path


def check_required(root, settings, report):
    required = settings.get("requiredFiles") or {}
    if not required:
        report.warn("checks.json lists no required files")
        return
    for name, sections in required.items():
        path = root / name
        if not path.is_file():
            report.fail("missing file: " + name)
            continue
        text = read_text(path)
        missing = [section for section in (sections or []) if section not in text]
        if missing:
            report.fail("missing section in {0}: {1}".format(name, ", ".join(missing)))
        else:
            report.ok("sections: " + name)


def check_links(root, material_root, report):
    broken = 0
    for path in iter_markdown(root, material_root):
        for target in LINK_RE.findall(read_text(path)):
            target = target.strip()
            if not target or SCHEME_RE.match(target):
                continue
            if target.startswith("#") or target.startswith("/"):
                continue
            clean = target.split("#", 1)[0].strip("<>")
            if not clean:
                continue
            if not (path.parent / clean).exists():
                broken += 1
                report.warn("broken link in {0}: {1}".format(relative(path, root), target))
    if broken == 0:
        report.ok("relative links resolve")


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


def check_placeholders(root, material_root, settings, strict, report):
    marker = settings.get("placeholderMarker") or "<!-- fill"
    hits = 0
    for path in iter_markdown(root, material_root):
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

    settings = load_config(config)
    material_root = Path(__file__).resolve().parent.parent / "references"

    report = Finding()
    check_required(root, settings, report)
    check_links(root, material_root, report)
    check_adr(root, report)
    check_placeholders(root, material_root, settings, args.strict, report)

    print("")
    print("{0} failure(s), {1} warning(s) under {2}".format(report.failures, report.warnings, root))
    return EXIT_FINDINGS if report.failures else EXIT_OK


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a project's documentation set.")
    parser.add_argument("-root", "--root", default=".", help="project root (default: current directory)")
    parser.add_argument("-config", "--config", default=None, help="path to checks.json (default: ../references/checks.json)")
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
