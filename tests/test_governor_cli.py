import json
import subprocess
import sys
from pathlib import Path

from jsonschema import validate

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "governed_cli.cli", *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_route_high_risk_is_manual_review() -> None:
    result = run_cli("route", "--policy", "strict", "--risk", "high")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["route"] == "manual-review"


def test_preflight_sample_is_valid() -> None:
    result = run_cli("preflight", "--artifact", str(ROOT / "artifacts" / "preflight.sample.json"))
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["valid"] is True


def test_compliance_sample_is_valid() -> None:
    result = run_cli(
        "compliance",
        "--artifact",
        str(ROOT / "artifacts" / "compliance.sample.json"),
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["valid"] is True


def test_schema_matches_sample_artifacts() -> None:
    preflight_schema = _read_json(ROOT / "schemas" / "preflight.schema.json")
    compliance_schema = _read_json(ROOT / "schemas" / "compliance.schema.json")
    preflight_sample = _read_json(ROOT / "artifacts" / "preflight.sample.json")
    compliance_sample = _read_json(ROOT / "artifacts" / "compliance.sample.json")

    validate(instance=preflight_sample, schema=preflight_schema)
    validate(instance=compliance_sample, schema=compliance_schema)
