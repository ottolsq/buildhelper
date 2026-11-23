import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("check_docs.py")


class RequiredHeadingTests(unittest.TestCase):
    def check_readme(self, text):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "checks.json"
            config.write_text(json.dumps({
                "stages": {"founding": ["README.md"]},
                "files": {"README.md": {"sections": ["# ", "## Required"]}},
            }), encoding="utf-8")
            (root / "README.md").write_text(text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPT), "-root", str(root), "-config", str(config)],
                capture_output=True, encoding="utf-8",
            )

    def test_accepts_real_headings_after_a_fenced_example(self):
        result = self.check_readme("# Project\n\n```text\n## Other\n```\n\n   ##\tRequired ###\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_mentions_that_are_not_the_required_heading(self):
        for example in (
            "Example: `## Required`\n",
            "### Required\n",
            "## Required example\n",
            "    ## Required\n",
            "<!--\n## Required\n-->\n",
            "````markdown\n```\n## Required\n````\n",
            "~~~markdown\n## Required\n~~~\n",
        ):
            with self.subTest(example=example):
                result = self.check_readme("# Project\n\n" + example)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("missing section in README.md: ## Required", result.stdout)


class PublishedBoundaryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.config = self.write("checks.json", json.dumps({
            "stages": {"founding": ["README.md"]},
            "files": {"README.md": {"sections": ["# "]}},
        }))
        self.write("README.md", "# Project\n")

    def write(self, relative_path, text):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def check_project(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "-root", str(self.root), "-config", str(self.config), *args],
            capture_output=True, encoding="utf-8",
        )

    def test_published_ignores_local_adrs_but_checks_visible_adrs(self):
        self.write(".gitignore", "*-local.md\n")
        self.write("docs/adr/001-visible.md", "# Visible\n")
        self.write("docs/adr/001-local.md", "# Local\n")

        local = self.check_project()
        self.assertEqual(local.returncode, 1, local.stdout + local.stderr)
        self.assertIn("duplicate adr number 1", local.stdout)
        published = self.check_project("--published")
        self.assertEqual(published.returncode, 0, published.stdout + published.stderr)
        self.assertIn("adr numbering contiguous: 1 file(s)", published.stdout)

        self.write("docs/adr/001-second-visible.md", "# Second visible\n")
        published = self.check_project("--published")
        self.assertEqual(published.returncode, 1, published.stdout + published.stderr)
        self.assertIn("duplicate adr number 1", published.stdout)
        self.assertNotIn("001-local.md", published.stdout)

    def test_root_relative_ignore_patterns_warn_only_for_matching_links(self):
        self.write(".gitignore", "docs/drafts/\ndocs/*/scratch/\n")
        ignored = ("docs/drafts/note.md", "docs/team/scratch/note.md")
        visible = ("nested/docs/drafts/note.md", "docs/team/deep/scratch/note.md")
        for path in ignored + visible:
            self.write(path, "# Note\n")
        self.write("README.md", "# Project\n\n" + "\n".join(
            f"[Note]({path})" for path in ignored + visible
        ))

        result = self.check_project("--published")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            [line for line in result.stdout.splitlines() if line.startswith("WARN")],
            [f"WARN  published file README.md links to ignored path: {path}" for path in ignored],
        )


class ScanScopeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.config = self.write("checks.json", json.dumps({
            "stages": {"founding": ["README.md", "docs/goal.md"]},
            "files": {
                "README.md": {"sections": ["# "]},
                "docs/goal.md": {"sections": ["## Goal"]},
            },
        }))
        self.write("README.md", "# Project\n")
        self.write(".gitignore", "docs/\nstudy/\n")

    def write(self, relative_path, text):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def check_project(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "-root", str(self.root), "-config", str(self.config), *args],
            capture_output=True, encoding="utf-8",
        )

    def test_local_mode_reads_the_local_doc_set_and_skips_the_rest(self):
        self.write("docs/goal.md", "## Goal\n\n[gone](missing-doc.md)\n")
        self.write("study/note.md", "[noise](missing-study.md)\n")

        result = self.check_project()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("WARN  broken link in docs/goal.md: missing-doc.md", result.stdout)
        self.assertNotIn("missing-study.md", result.stdout)
        self.assertIn("skip  gitignored (not scanned): 1 path(s) (study/note.md)", result.stdout)
        self.assertIn("local doc set still read: docs", result.stdout)

    def test_published_mode_does_not_read_ignored_docs(self):
        self.write("docs/goal.md", "## Goal\n\n[gone](missing-doc.md)\n")

        result = self.check_project("--published")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("missing-doc.md", result.stdout)
        self.assertIn("skip  local-only (not published): docs/goal.md", result.stdout)


class FenceTests(unittest.TestCase):
    def test_example_links_inside_fences_are_not_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "checks.json"
            config.write_text(json.dumps({
                "stages": {"founding": ["README.md"]},
                "files": {"README.md": {"sections": ["# "]}},
            }), encoding="utf-8")
            (root / "README.md").write_text(
                "# Project\n\n```text\n[example](missing-by-example.md)\n```\n\n[real](gone.md)\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "-root", str(root), "-config", str(config)],
                capture_output=True, encoding="utf-8",
            )

            warnings = [line for line in result.stdout.splitlines() if line.startswith("WARN")]
            self.assertEqual(warnings, ["WARN  broken link in README.md: gone.md"])


class StagedTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.config = self.write("checks.json", json.dumps({
            "stages": {"founding": ["README.md", "docs/goal.md"]},
            "files": {
                "README.md": {"sections": ["# "]},
                "docs/goal.md": {"sections": ["## Goal"]},
            },
        }))
        self.write(".gitignore", "docs/\n")
        self.write("README.md", "# Project\n")
        self.git("init")
        self.git("add", "README.md", ".gitignore", "checks.json")

    def git(self, *args):
        result = subprocess.run(
            ["git", *args], cwd=str(self.root), capture_output=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def write(self, relative_path, text):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def check_project(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "-root", str(self.root), "-config", str(self.config), *args],
            capture_output=True, encoding="utf-8",
        )

    def test_index_wins_over_gitignore_for_tracked_files(self):
        self.write("docs/goal.md", "## Goal\n")
        self.git("add", "-f", "docs/goal.md")

        staged = self.check_project("--staged")
        self.assertEqual(staged.returncode, 0, staged.stdout + staged.stderr)
        self.assertNotIn("skip  local-only", staged.stdout)
        self.assertIn("ok    sections: docs/goal.md", staged.stdout)

        published = self.check_project("--published")
        self.assertIn("skip  local-only (not published): docs/goal.md", published.stdout)

    def test_untracked_files_are_reported_but_not_checked(self):
        self.write("notes.md", "[gone](missing.md)\n")

        result = self.check_project("--staged")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("skip  untracked (not in git index): 1 file(s) (notes.md)", result.stdout)
        self.assertNotIn("missing.md", result.stdout)

    def test_worktree_changes_are_announced(self):
        self.write("README.md", "# Project\n\nlocal edit\n")

        result = self.check_project("--staged")

        self.assertIn("note  worktree differs from git index for 1 file(s)", result.stdout)

    def test_staged_requires_a_git_work_tree(self):
        # A subdirectory of a repo *is* inside its work tree, so use a plain
        # directory outside it to stand for "no repository here".
        with tempfile.TemporaryDirectory() as directory:
            plain = Path(directory)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "-root", str(plain), "-config", str(self.config), "--staged"],
                capture_output=True, encoding="utf-8",
            )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("error: --staged needs a git work tree", result.stderr)

    def test_published_and_staged_are_mutually_exclusive(self):
        result = self.check_project("--published", "--staged")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("mutually exclusive", result.stderr)


class SecretScanTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.config = self.write("checks.json", json.dumps({
            "stages": {"founding": ["README.md"]},
            "files": {"README.md": {"sections": ["# "]}},
            "secrets": {
                "enabled": True,
                "rules": [
                    {"name": "github-token", "pattern": "gh[pousr]_[A-Za-z0-9]{20,}"},
                    {"name": "assigned-credential",
                     "pattern": "(?i)(?:token|password)\\s*[:=]\\s*[\"']?([A-Za-z0-9_\\-]{12,})",
                     "valueGroup": 1},
                ],
                "allow": "(?i)x{3,}|<[^>]*>|your[_-][A-Za-z0-9_-]*|placeholder|example",
            },
        }))

    def write(self, relative_path, text):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def check_project(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "-root", str(self.root), "-config", str(self.config), *args],
            capture_output=True, encoding="utf-8",
        )

    def warnings(self, output):
        return [line for line in output.splitlines() if line.startswith("WARN")]

    def test_reports_location_and_rule_only(self):
        token = "ghp_" + "a" * 24
        self.write("README.md", "# Project\n\ntoken: " + token + "\n")

        result = self.check_project()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            self.warnings(result.stdout),
            ["WARN  possible secret (github-token) at README.md:3",
             "WARN  possible secret (assigned-credential) at README.md:3"],
        )
        self.assertNotIn(token, result.stdout)
        self.assertIn("not exhaustive", result.stdout)

    def test_placeholders_are_allowed(self):
        self.write("README.md", "# Project\n\ntoken: ghp_" + "x" * 24 + "\npassword: <your-password>\n")

        result = self.check_project()

        self.assertEqual(self.warnings(result.stdout), [], result.stdout)
        self.assertIn("ok    no obvious secrets", result.stdout)

    def test_strict_turns_secrets_into_failures(self):
        self.write("README.md", "# Project\n\ntoken: ghp_" + "a" * 24 + "\n")

        result = self.check_project("--strict")

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL  possible secret (github-token) at README.md:3", result.stdout)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.config = self.write("checks.json", json.dumps({
            "stages": {"founding": ["README.md", "docs/goal.md", "docs/architecture.md"]},
            "files": {
                "README.md": {"sections": ["# "]},
                "docs/goal.md": {"sections": ["## Goal"]},
                "docs/architecture.md": {"sections": ["## Parts"]},
            },
            "scopes": {"api": {"match": ["*_api.md"], "allow": ["docs/api", "API.md"]}},
        }))
        self.write("README.md", "# Project\n")
        self.write("docs/goal.md", "## Goal\n")
        self.write("docs/architecture.md", "## Parts\n")

    def write(self, relative_path, text):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def inventory(self, *args):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-root", str(self.root), "-config", str(self.config), "--inventory", *args],
            capture_output=True, encoding="utf-8",
        )
        return result

    def row(self, output, name):
        for line in output.splitlines():
            match = re.match(r"^  (keep|merge|archive|review)\s+(\S+)", line)
            if match and (match.group(2) == name or match.group(2).endswith("/" + name)):
                return line
        return ""

    def test_proposes_keep_merge_and_archive_without_touching_files(self):
        self.write("modules/user_api.md", "# User API\n")
        self.write("docs/superpowers/plans/2026-11-21-p1.md", "# Plan\n")
        self.write("docs/adr/001-choice.md", "# Choice\n")

        result = self.inventory()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("inventory  6 markdown file(s) in scope", result.stdout)
        self.assertEqual(self.row(result.stdout, "user_api.md").split()[0], "merge")
        self.assertIn("docs/api", self.row(result.stdout, "user_api.md"))
        self.assertEqual(self.row(result.stdout, "2026-11-21-p1.md").split()[0], "archive")
        self.assertEqual(self.row(result.stdout, "001-choice.md").split()[0], "keep")
        self.assertIn("note  inventory is a proposal", result.stdout)
        self.assertTrue((self.root / "modules" / "user_api.md").is_file())

    def test_files_in_a_role_home_keep_even_without_the_name_pattern(self):
        self.write("API.md", "# API\n")
        self.write("docs/api/user.md", "# User API\n")

        result = self.inventory()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.row(result.stdout, "API.md").split()[0], "keep")
        self.assertIn("api", self.row(result.stdout, "API.md"))
        self.assertEqual(self.row(result.stdout, "user.md").split()[0], "keep")

    def test_inventory_respects_published_scope(self):
        self.write(".gitignore", "docs/\n")
        self.write("modules/user_api.md", "# User API\n")

        result = self.inventory("--published")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("skip  local-only (not published): docs/goal.md, docs/architecture.md", result.stdout)
        self.assertNotIn("docs/goal.md", result.stdout.split("inventory", 1)[1])


class ScopeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.config = self.write("checks.json", json.dumps({
            "stages": {"founding": ["README.md"]},
            "files": {"README.md": {"sections": ["# "]}},
            "scopes": {"api": {"match": ["*_api.md", "api_*.md"], "allow": ["docs/api"]}},
        }))
        self.write("README.md", "# Project\n")

    def write(self, relative_path, text):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def check_project(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "-root", str(self.root), "-config", str(self.config), *args],
            capture_output=True, encoding="utf-8",
        )

    def test_api_documents_outside_their_home_are_flagged(self):
        self.write("modules/user_api.md", "# User API\n")
        self.write("docs/api/order_api.md", "# Order API\n")

        result = self.check_project()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        warnings = [line for line in result.stdout.splitlines() if line.startswith("WARN")]
        self.assertEqual(warnings, ["WARN  duplicate scope (api): modules/user_api.md belongs in docs/api"])

    def test_no_warning_when_every_document_is_at_home(self):
        self.write("docs/api/user_api.md", "# User API\n")

        result = self.check_project()

        self.assertIn("ok    one home per document scope", result.stdout)


class BudgetTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.config = self.write("checks.json", json.dumps({
            "stages": {"founding": ["README.md"]},
            "files": {"README.md": {"sections": ["# "]}},
            "budgets": {"docs": 2},
        }))
        self.write("README.md", "# Project\n")

    def write(self, relative_path, text):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def check_project(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "-root", str(self.root), "-config", str(self.config), *args],
            capture_output=True, encoding="utf-8",
        )

    def test_growing_doc_set_warns_and_archives_do_not_count(self):
        for name in ("goal.md", "architecture.md", "notes.md"):
            self.write("docs/" + name, "# Doc\n")
        for name in ("01-first.md", "02-second.md", "03-third.md"):
            self.write("docs/history/" + name, "# Phase\n")

        result = self.check_project()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        warnings = [line for line in result.stdout.splitlines() if line.startswith("WARN")]
        self.assertEqual(
            warnings,
            ["WARN  budget (docs): 3 file(s), limit 2; merge or archive before adding more"],
        )

    def test_budget_within_limit_is_reported_as_ok(self):
        self.write("docs/goal.md", "# Doc\n")

        result = self.check_project()

        self.assertIn("ok    budget (docs): 1/2 file(s)", result.stdout)


class ConfigExtendsTests(unittest.TestCase):
    def test_child_config_overrides_only_its_own_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "base.json").write_text(json.dumps({
                "stages": {"founding": ["README.md"]},
                "files": {"README.md": {"sections": ["# "], "maxLines": 5}},
            }), encoding="utf-8")
            child = root / "child.json"
            child.write_text(json.dumps({"extends": "base.json", "files": {"README.md": {"maxLines": 50}}}), encoding="utf-8")
            (root / "README.md").write_text("# Project\n" + "line\n" * 20, encoding="utf-8")

            args = [sys.executable, str(SCRIPT), "-root", str(root), "-config", str(child)]
            relaxed = subprocess.run(args, capture_output=True, encoding="utf-8")
            self.assertEqual(relaxed.returncode, 0, relaxed.stdout + relaxed.stderr)
            self.assertNotIn("WARN", relaxed.stdout)
            self.assertIn("ok    sections: README.md", relaxed.stdout)

            base = subprocess.run(
                [sys.executable, str(SCRIPT), "-root", str(root), "-config", str(root / "base.json")],
                capture_output=True, encoding="utf-8",
            )
            self.assertIn("WARN  length 21/5 lines in README.md", base.stdout)

    def test_extends_loop_is_a_config_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.json").write_text(json.dumps({"extends": "b.json"}), encoding="utf-8")
            (root / "b.json").write_text(json.dumps({"extends": "a.json"}), encoding="utf-8")
            (root / "README.md").write_text("# Project\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "-root", str(root), "-config", str(root / "a.json")],
                capture_output=True, encoding="utf-8",
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("error: config extends loop", result.stderr)


if __name__ == "__main__":
    unittest.main()
