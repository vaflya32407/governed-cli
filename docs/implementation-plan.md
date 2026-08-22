# Implementation plan

This repository is intentionally spec-first, but it now includes a minimal runnable local prototype. A fuller implementation can still be built in small layers.

## Phase 1: Spec and artifact validation
- finalize repo contract schema
- finalize session schema
- define canonical file locations
- provide validators and example fixtures

## Phase 2: Local session control
- prototype status: basic `session start` and `session status` commands are implemented with local JSON storage
- add a CLI entrypoint
- implement `session start`, `session status`, `session stop`, and `session resume`
- persist sessions locally as structured records

## Phase 3: Route-aware execution
- add task classification and route selection
- map routes to allowed capabilities from the contract
- expose route reason codes in CLI output

## Phase 4: Preflight and enforcement
- add reusable preflight checks
- block mutations when repository state or policy is invalid
- support manual approval gates for elevated routes

## Phase 5: Compliance and export
- emit append-only audit events
- render human-readable audit summaries
- support export to external compliance systems if needed

## Current concrete CLI surface

The current prototype exposes:

```text
governed contract validate
governed route explain --task task.json
governed preflight run --task task.json
governed session start --task task.json
governed session status --id sess_123
governed audit show --id sess_123
```

## Success criteria for an initial implementation
- a repository can declare a valid contract
- a task can be routed with an explainable result
- a session cannot start until preflight succeeds
- every session produces a durable audit trail
