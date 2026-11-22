import json
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


if __name__ == "__main__":
    unittest.main()
