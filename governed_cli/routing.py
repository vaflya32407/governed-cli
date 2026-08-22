from __future__ import annotations

from governed_cli.contract import ValidationError


SUPPORTED_INTENTS = {
    "documentation": "low",
    "schema-or-policy": "moderate",
    "analysis": "low",
    "code-change": "moderate",
}


def normalize_task(task: dict) -> dict:
    if "intent" not in task or "requestedBy" not in task:
        raise ValidationError("task.intent and task.requestedBy are required")
    task = dict(task)
    task.setdefault("targetPaths", [])
    task.setdefault("desiredActions", [])
    task.setdefault("approvals", [])
    return task


def explain_route(contract: dict, task: dict) -> dict:
    task = normalize_task(task)
    for route in contract["routing"]["routes"]:
        if task["intent"] == route["intent"]:
            return {
                "name": route["name"],
                "risk": route["risk"],
                "allowedActions": route["allowedActions"],
                "reasonCodes": [
                    f"intent={task['intent']}",
                    f"route={route['name']}",
                    f"risk={route['risk']}",
                ],
            }

    if task["intent"] in SUPPORTED_INTENTS:
        return {
            "name": "manual-review",
            "risk": SUPPORTED_INTENTS[task["intent"]],
            "allowedActions": ["read"],
            "reasonCodes": [
                f"intent={task['intent']}",
                "route-not-defined-in-contract",
                "manual-review-required",
            ],
        }

    raise ValidationError(f"no route found for intent '{task['intent']}'")
