"""Tests for the stdlib AST SKILL.md generator and drift verifier."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.check import FORBIDDEN_PATTERNS
from scripts.generate_skill import extract_cli_specs, render_skill_markdown

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestGenerateSkill(unittest.TestCase):
    def test_ast_extraction_covers_all_three_harmos_clis(self):
        specs = extract_cli_specs(REPO_ROOT)
        by_source = {spec.source_path: spec for spec in specs}

        self.assertEqual(
            set(by_source.keys()),
            {"core/compiler/cli.py", "scripts/audit.py", "scripts/check.py"},
        )

        cli_spec = by_source["core/compiler/cli.py"]
        self.assertTrue(any("--json" in arg.flags for arg in cli_spec.root_args))
        subcommand_names = {sub.name for sub in cli_spec.subcommands}
        self.assertEqual(
            subcommand_names,
            {"compile", "extract", "verify-provenance", "bench", "harvest", "diff", "doc"},
        )

        audit_spec = by_source["scripts/audit.py"]
        audit_flags = {flag for arg in audit_spec.root_args for flag in arg.flags}
        self.assertTrue({"--patcher", "--ir", "--timeout", "--json"}.issubset(audit_flags))

        check_spec = by_source["scripts/check.py"]
        check_flags = {flag for arg in check_spec.root_args for flag in arg.flags}
        self.assertIn("--json", check_flags)

    def test_rendered_markdown_invariants_and_determinism(self):
        specs_a = extract_cli_specs(REPO_ROOT)
        specs_b = extract_cli_specs(REPO_ROOT)
        md_a = render_skill_markdown(specs_a)
        md_b = render_skill_markdown(specs_b)

        self.assertEqual(md_a, md_b)
        self.assertNotIn("\r", md_a)
        self.assertTrue(md_a.endswith("\n"))

        frontmatter_match = re.match(r"^---\n(.*?)\n---\n", md_a, re.DOTALL)
        self.assertIsNotNone(frontmatter_match, "Missing YAML frontmatter")
        frontmatter = frontmatter_match.group(1)

        self.assertRegex(frontmatter, r"(?m)^name:\s*harmos-cli$")
        self.assertRegex(frontmatter, r"(?m)^license:\s*Apache-2\.0$")
        self.assertRegex(frontmatter, r"(?m)^metadata:\n\s+author:\s*.+\n\s+version:\s*.+$")

        desc_match = re.search(r'(?m)^description:\s*"([^"\n]+)"$', frontmatter)
        self.assertIsNotNone(desc_match, "description must be a single-line quoted YAML string")
        description = desc_match.group(1)
        self.assertTrue(description.startswith("Trigger: "))
        self.assertLessEqual(len(description), 160)

        required_sections = [
            "## Activation Contract",
            "## Hard Rules",
            "## Decision Gates",
            "## Execution Steps",
            "## Output Contract",
            "## References",
        ]
        positions = [md_a.index(section) for section in required_sections]
        self.assertEqual(positions, sorted(positions))

        self.assertNotIn("## Keywords", md_a)
        self.assertNotIn("Keywords:", md_a)

        for pattern, desc in FORBIDDEN_PATTERNS:
            self.assertIsNone(
                re.search(pattern, md_a),
                f"Generated SKILL.md matched forbidden pattern ({desc})",
            )

    def test_cli_generate_and_check_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_file = Path(tmp) / "harmos-cli" / "SKILL.md"

            res_missing = subprocess.run(
                [sys.executable, "scripts/generate_skill.py", "--check", "--output", str(skill_file), "--json"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_missing.returncode, 1)
            missing_env = json.loads(res_missing.stdout)
            self.assertEqual(missing_env["status"], "MISSING")
            self.assertEqual(missing_env["command"], "generate-skill")
            self.assertEqual(missing_env["exit_code"], 1)

            res_write = subprocess.run(
                [sys.executable, "scripts/generate_skill.py", "--output", str(skill_file)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_write.returncode, 0, res_write.stderr)
            self.assertTrue(skill_file.is_file())

            res_ok = subprocess.run(
                [sys.executable, "scripts/generate_skill.py", "--check", "--output", str(skill_file)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_ok.returncode, 0, res_ok.stderr)

            res_ok_json = subprocess.run(
                [sys.executable, "scripts/generate_skill.py", "--check", "--output", str(skill_file), "--json"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_ok_json.returncode, 0, res_ok_json.stderr)
            ok_env = json.loads(res_ok_json.stdout)
            self.assertEqual(ok_env["status"], "PASS")
            self.assertEqual(ok_env["exit_code"], 0)

            skill_file.write_text(skill_file.read_text(encoding="utf-8") + "\n<!-- drift -->\n", encoding="utf-8")
            res_drift = subprocess.run(
                [sys.executable, "scripts/generate_skill.py", "--check", "--output", str(skill_file), "--json"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_drift.returncode, 1)
            drift_env = json.loads(res_drift.stdout)
            self.assertEqual(drift_env["status"], "DRIFT")
            self.assertEqual(drift_env["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
