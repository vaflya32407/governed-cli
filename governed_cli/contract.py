from __future__ import annotations

import json
from pathlib import Path

ALLOWED_ACTIONS = {"read", "edit", "test", "commit", "open-pr"}
REQUIRED_CONTRACT_KEYS = {"version", "repository", "policy", "routing", "preflight", "compliance"}


class ValidationError(ValueError):
    """Raised when a governance artifact is invalid."""


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def validate_contract(contract: dict) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_CONTRACT_KEYS - set(contract)
    if missing:
        errors.append(f"missing top-level keys: {sorted(missing)}")

    repository = contract.get("repository", {})
    if not isinstance(repository, dict) or not repository.get("name") or not repository.get("defaultBranch"):
        errors.append("repository.name and repository.defaultBranch are required")

    policy = contract.get("policy", {})
    allowed_actions = policy.get("allowedActions", [])
    if not isinstance(allowed_actions, list) or not allowed_actions:
        errors.append("policy.allowedActions must be a non-empty array")
    else:
        invalid = sorted(set(allowed_actions) - ALLOWED_ACTIONS)
        if invalid:
            errors.append(f"policy.allowedActions contains unsupported actions: {invalid}")

    routing = contract.get("routing", {})
    routes = routing.get("routes", [])
    if not isinstance(routes, list) or not routes:
        errors.append("routing.routes must be a non-empty array")
    else:
        for index, route in enumerate(routes):
            if not isinstance(route, dict):
                errors.append(f"routing.routes[{index}] must be an object")
                continue
            for field in ("name", "intent", "risk", "allowedActions"):
                if field not in route:
                    errors.append(f"routing.routes[{index}] missing {field}")
            route_actions = route.get("allowedActions", [])
            invalid = sorted(set(route_actions) - ALLOWED_ACTIONS)
            if invalid:
                errors.append(f"routing.routes[{index}].allowedActions contains unsupported actions: {invalid}")
            if set(route_actions) - set(allowed_actions):
                errors.append(
                    f"routing.routes[{index}].allowedActions must be a subset of policy.allowedActions"
                )

    required_checks = contract.get("preflight", {}).get("requiredChecks", [])
    if not isinstance(required_checks, list) or not required_checks:
        errors.append("preflight.requiredChecks must be a non-empty array")

    audit_fields = contract.get("compliance", {}).get("auditFields", [])
    if not isinstance(audit_fields, list) or not audit_fields:
        errors.append("compliance.auditFields must be a non-empty array")

    return errors


def load_and_validate_contract(path: str | Path) -> dict:
    contract = load_json(path)
    errors = validate_contract(contract)
    if errors:
        raise ValidationError("; ".join(errors))
    return contract
