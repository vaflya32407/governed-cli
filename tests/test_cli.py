from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from governed_cli.preflight import run_preflight

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = REPO_ROOT / "examples" / "repo-contract.example.json"
TASK = REPO_ROOT / "examples" / "task.example.json"


class GovernedCliTests(unittest.TestCase):
    def run_cli(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "governed_cli.cli", *args],
            cwd=cwd or REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def init_git_repo(self, path: Path) -> None:
        subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True, capture_output=True, text=True)
        (path / "README.md").write_text("test\n")
        subprocess.run(["git", "add", "README.md"], cwd=path, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True, text=True)

    def test_contract_validate(self) -> None:
        completed = self.run_cli("contract", "validate", "--contract", str(CONTRACT))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "ok")

    def test_route_explain(self) -> None:
        completed = self.run_cli("route", "explain", "--contract", str(CONTRACT), "--task", str(TASK))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["name"], "docs-only")
        self.assertIn("intent=documentation", payload["reasonCodes"])

    def test_preflight_run(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir:
            repo_path = Path(repo_dir)
            self.init_git_repo(repo_path)
            completed = self.run_cli(
                "preflight",
                "run",
                "--contract",
                str(CONTRACT),
                "--task",
                str(TASK),
                "--repo-root",
                str(repo_path),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "passed")

    def test_run_preflight_empty_checks_is_skipped(self) -> None:
        contract = json.loads(CONTRACT.read_text())
        contract["preflight"]["requiredChecks"] = []
        task = json.loads(TASK.read_text())
        route = {
            "name": "docs-only",
            "risk": "low",
            "allowedActions": ["read", "edit", "commit"],
            "reasonCodes": ["intent=documentation"],
        }
        payload = run_preflight(contract, task, route, REPO_ROOT)
        self.assertEqual(payload["status"], "skipped")

    def test_preflight_run_all_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir:
            repo_path = Path(repo_dir)
            self.init_git_repo(repo_path)
            custom_contract = Path(repo_dir) / "contract.json"
            contract = json.loads(CONTRACT.read_text())
            contract["preflight"]["requiredChecks"] = ["future-check"]
            custom_contract.write_text(json.dumps(contract))
            completed = self.run_cli(
                "preflight",
                "run",
                "--contract",
                str(custom_contract),
                "--task",
                str(TASK),
                "--repo-root",
                str(repo_path),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "skipped")

    def test_session_start_with_skipped_preflight_is_planned(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as state_dir:
            repo_path = Path(repo_dir)
            self.init_git_repo(repo_path)
            custom_contract = Path(repo_dir) / "contract.json"
            contract = json.loads(CONTRACT.read_text())
            contract["preflight"]["requiredChecks"] = ["future-check"]
            custom_contract.write_text(json.dumps(contract))
            completed = self.run_cli(
                "session",
                "start",
                "--contract",
                str(custom_contract),
                "--task",
                str(TASK),
                "--repo-root",
                str(repo_path),
                "--state-dir",
                str(state_dir),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            session = json.loads(completed.stdout)
            self.assertEqual(session["state"], "planned")

    def test_session_start_and_audit_show(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as state_dir:
            repo_path = Path(repo_dir)
            self.init_git_repo(repo_path)
            completed = self.run_cli(
                "session",
                "start",
                "--contract",
                str(CONTRACT),
                "--task",
                str(TASK),
                "--repo-root",
                str(repo_path),
                "--state-dir",
                str(state_dir),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            session = json.loads(completed.stdout)
            self.assertEqual(session["state"], "validated")

            audit = self.run_cli("audit", "show", "--id", session["sessionId"], "--state-dir", str(state_dir))
            self.assertEqual(audit.returncode, 0, audit.stderr)
            payload = json.loads(audit.stdout)
            self.assertEqual(payload["sessionId"], session["sessionId"])
            self.assertGreaterEqual(len(payload["events"]), 3)

    def test_session_start_blocks_protected_path(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as state_dir:
            repo_path = Path(repo_dir)
            self.init_git_repo(repo_path)
            protected_task = Path(repo_dir) / "task.json"
            protected_task.write_text(
                json.dumps(
                    {
                        "intent": "documentation",
                        "requestedBy": "local-user",
                        "targetPaths": [".github/workflows/ci.yml"],
                        "desiredActions": ["read", "edit"],
                        "approvals": [],
                    }
                )
            )
            completed = self.run_cli(
                "session",
                "start",
                "--contract",
                str(CONTRACT),
                "--task",
                str(protected_task),
                "--repo-root",
                str(repo_path),
                "--state-dir",
                str(state_dir),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            session = json.loads(completed.stdout)
            self.assertEqual(session["state"], "blocked")

    def test_preflight_path_check_uses_path_segments(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as artifacts_dir:
            repo_path = Path(repo_dir)
            artifacts_path = Path(artifacts_dir)
            self.init_git_repo(repo_path)
            custom_contract = artifacts_path / "contract.json"
            contract = json.loads(CONTRACT.read_text())
            contract["policy"]["protectedPaths"] = [".github"]
            custom_contract.write_text(json.dumps(contract))
            custom_task = artifacts_path / "task.json"
            custom_task.write_text(
                json.dumps(
                    {
                        "intent": "documentation",
                        "requestedBy": "local-user",
                        "targetPaths": [".github-actions/workflow.txt"],
                        "desiredActions": ["read"],
                        "approvals": [],
                    }
                )
            )
            completed = self.run_cli(
                "preflight",
                "run",
                "--contract",
                str(custom_contract),
                "--task",
                str(custom_task),
                "--repo-root",
                str(repo_path),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "passed")


if __name__ == "__main__":
    unittest.main()
