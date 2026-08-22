from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from governed_cli import __version__
from governed_cli.contract import ValidationError, load_and_validate_contract, load_json
from governed_cli.preflight import run_preflight
from governed_cli.routing import explain_route, normalize_task
from governed_cli.session import SessionStore


def _load_task(path: str | Path) -> dict[str, Any]:
    return normalize_task(load_json(path))


def _emit(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="governed", description="Governed CLI blueprint prototype")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="group", required=True)

    contract = subparsers.add_parser("contract")
    contract_sub = contract.add_subparsers(dest="action", required=True)
    contract_validate = contract_sub.add_parser("validate")
    contract_validate.add_argument("--contract", required=True)

    route = subparsers.add_parser("route")
    route_sub = route.add_subparsers(dest="action", required=True)
    route_explain = route_sub.add_parser("explain")
    route_explain.add_argument("--contract", required=True)
    route_explain.add_argument("--task", required=True)

    preflight = subparsers.add_parser("preflight")
    preflight_sub = preflight.add_subparsers(dest="action", required=True)
    preflight_run = preflight_sub.add_parser("run")
    preflight_run.add_argument("--contract", required=True)
    preflight_run.add_argument("--task", required=True)
    preflight_run.add_argument("--repo-root", default=".")

    session = subparsers.add_parser("session")
    session_sub = session.add_subparsers(dest="action", required=True)
    session_start = session_sub.add_parser("start")
    session_start.add_argument("--contract", required=True)
    session_start.add_argument("--task", required=True)
    session_start.add_argument("--repo-root", default=".")
    session_start.add_argument("--state-dir", default=".governed")

    session_status = session_sub.add_parser("status")
    session_status.add_argument("--id", required=True)
    session_status.add_argument("--state-dir", default=".governed")

    audit = subparsers.add_parser("audit")
    audit_sub = audit.add_subparsers(dest="action", required=True)
    audit_show = audit_sub.add_parser("show")
    audit_show.add_argument("--id", required=True)
    audit_show.add_argument("--state-dir", default=".governed")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.group == "contract" and args.action == "validate":
            contract = load_and_validate_contract(args.contract)
            return _emit({"status": "ok", "contractVersion": contract["version"]})

        if args.group == "route" and args.action == "explain":
            contract = load_and_validate_contract(args.contract)
            route = explain_route(contract, _load_task(args.task))
            return _emit(route)

        if args.group == "preflight" and args.action == "run":
            contract = load_and_validate_contract(args.contract)
            task = _load_task(args.task)
            route = explain_route(contract, task)
            result = run_preflight(contract, task, route, args.repo_root)
            return _emit(result)

        if args.group == "session" and args.action == "start":
            contract = load_and_validate_contract(args.contract)
            task = _load_task(args.task)
            route = explain_route(contract, task)
            preflight = run_preflight(contract, task, route, args.repo_root)
            session = SessionStore(args.state_dir).create(contract, task, route, preflight)
            return _emit(session)

        if args.group == "session" and args.action == "status":
            session = SessionStore(args.state_dir).read(args.id)
            return _emit(session)

        if args.group == "audit" and args.action == "show":
            session = SessionStore(args.state_dir).read(args.id)
            return _emit({"sessionId": session["sessionId"], "events": session["audit"]["events"]})
    except (ValidationError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, indent=2))
        return 1

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
