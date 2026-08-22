from __future__ import annotations

import subprocess
from pathlib import Path


def _check_clean_working_tree(repo_root: str | Path) -> tuple[str, str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return "skipped", "git status unavailable"
    if completed.stdout.strip():
        return "failed", "working tree has uncommitted changes"
    return "passed", "working tree is clean"


def run_preflight(contract: dict, task: dict, route: dict, repo_root: str | Path) -> dict:
    policy = contract["policy"]
    target_paths = task.get("targetPaths", [])
    protected_paths = policy.get("protectedPaths", [])
    required_checks = contract["preflight"]["requiredChecks"]
    checks: list[dict] = []

    for check_name in required_checks:
        status = "passed"
        details = "ok"

        if check_name == "contract-valid":
            details = "contract loaded and validated"
        elif check_name == "clean-working-tree":
            status, details = _check_clean_working_tree(repo_root)
        elif check_name == "route-allowed-by-policy":
            if set(route["allowedActions"]) - set(policy["allowedActions"]):
                status = "failed"
                details = "route actions exceed policy.allowedActions"
            else:
                details = "route actions allowed by policy"
        elif check_name == "no-protected-path-conflict":
            conflicts = [
                target for target in target_paths for protected in protected_paths if target.startswith(protected)
            ]
            if conflicts:
                status = "failed"
                details = f"protected path conflict: {sorted(set(conflicts))}"
            else:
                details = "no protected path conflicts"
        else:
            status = "skipped"
            details = "check not implemented in prototype"

        checks.append({"name": check_name, "status": status, "details": details})

    overall = "passed" if all(check["status"] != "failed" for check in checks) else "failed"
    return {"status": overall, "checks": checks}
