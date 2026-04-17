from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _status_ok(items: list[dict[str, Any]], key: str) -> bool:
    return bool(items) and all(item.get(key) in {"pass", "allow"} for item in items)


def validate_preflight(artifact: dict[str, Any]) -> tuple[bool, str]:
    if artifact.get("contract") != "governed.preflight/v1":
        return False, "invalid contract"
    if not artifact.get("repo") or not artifact.get("route"):
        return False, "missing repo or route"
    checks = artifact.get("checks")
    if not isinstance(checks, list):
        return False, "checks must be a list"
    if not _status_ok(checks, "status"):
        return False, "one or more checks did not pass"
    return True, "ok"


def validate_compliance(artifact: dict[str, Any]) -> tuple[bool, str]:
    if artifact.get("contract") != "governed.compliance/v1":
        return False, "invalid contract"
    decision = artifact.get("decision")
    if decision not in {"allow", "block"}:
        return False, "invalid decision"
    controls = artifact.get("controls")
    if not isinstance(controls, list):
        return False, "controls must be a list"
    controls_ok = _status_ok(controls, "status")
    if decision != "allow":
        return False, "decision blocks merge"
    if not controls_ok:
        return False, "one or more controls are blocking"
    return True, "ok"


def _route(policy: str, risk: str) -> str:
    if policy == "strict" and risk in {"medium", "high"}:
        return "manual-review"
    if risk == "high":
        return "manual-review"
    return "merge"


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, sort_keys=True))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="governor")
    subcommands = parser.add_subparsers(dest="command", required=True)

    route = subcommands.add_parser("route", help="Resolve governance route")
    route.add_argument("--policy", choices=["strict", "advisory"], default="strict")
    route.add_argument("--risk", choices=["low", "medium", "high"], required=True)

    preflight = subcommands.add_parser("preflight", help="Validate preflight artifact")
    preflight.add_argument("--artifact", required=True)

    compliance = subcommands.add_parser("compliance", help="Validate compliance artifact")
    compliance.add_argument("--artifact", required=True)

    hook = subcommands.add_parser("hook", help="Emit hook surface payload")
    hook.add_argument("--name", required=True)
    hook.add_argument("--payload", default="{}")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "route":
        _print_json(
            {
                "policy": args.policy,
                "risk": args.risk,
                "route": _route(args.policy, args.risk),
            }
        )
        return 0

    if args.command == "preflight":
        artifact = _load_json(args.artifact)
        valid, reason = validate_preflight(artifact)
        _print_json({"artifact": "preflight", "valid": valid, "reason": reason})
        return 0 if valid else 2

    if args.command == "compliance":
        artifact = _load_json(args.artifact)
        valid, reason = validate_compliance(artifact)
        _print_json({"artifact": "compliance", "valid": valid, "reason": reason})
        return 0 if valid else 3

    if args.command == "hook":
        payload = json.loads(args.payload)
        _print_json({"hook": args.name, "payload": payload})
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
