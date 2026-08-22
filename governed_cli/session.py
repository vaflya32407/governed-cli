from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class SessionStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.sessions_dir = self.root / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create(self, contract: dict, task: dict, route: dict, preflight: dict) -> dict:
        session_id = f"sess_{uuid4().hex[:12]}"
        if preflight["status"] == "passed":
            state = "validated"
        elif preflight["status"] == "skipped":
            state = "planned"
        else:
            state = "blocked"
        session = {
            "sessionId": session_id,
            "task": {
                "intent": task["intent"],
                "requestedBy": task["requestedBy"],
            },
            "route": {
                "name": route["name"],
                "risk": route["risk"],
                "reasonCodes": route["reasonCodes"],
            },
            "state": state,
            "preflight": preflight,
            "audit": {
                "contractVersion": contract["version"],
                "events": [
                    {"type": "session.created", "timestamp": utc_now(), "summary": "Session created"},
                    {"type": "route.selected", "timestamp": utc_now(), "summary": f"Route {route['name']} selected"},
                    {
                        "type": "preflight.completed",
                        "timestamp": utc_now(),
                        "summary": f"Preflight {preflight['status']}",
                    },
                ],
            },
        }
        self.write(session)
        return session

    def write(self, session: dict) -> None:
        (self.sessions_dir / f"{session['sessionId']}.json").write_text(json.dumps(session, indent=2) + "\n")

    def read(self, session_id: str) -> dict:
        return json.loads((self.sessions_dir / f"{session_id}.json").read_text())
