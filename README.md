# governed-cli

A spec-first blueprint for a governed CLI that runs agentic repository workflows with explicit policy, routing, session control, and auditability.

This repository is intentionally educational before it is executable. It describes the shape of a Waldo-like governance layer for agentic work: every task is classified, validated, executed inside a bounded session, and recorded for later review.

## Why this exists

Most agent tooling is optimized for capability first. `governed-cli` is a reference for the opposite constraint: how to make autonomous or semi-autonomous workflows predictable, reviewable, and safe enough for repository operations.

The project models a governed workflow where an operator or orchestrator can answer four questions for every action:

1. **What was the agent allowed to do?**
2. **Why was this route selected?**
3. **What checks ran before execution?**
4. **What evidence exists after execution?**

## Core concepts

### 1. Repo contract
A machine-readable contract that declares repository-specific permissions and operating rules.

A contract should define:
- allowed and protected paths
- permitted actions (`read`, `edit`, `test`, `commit`, `open-pr`)
- required approvals for risky operations
- required checks before mutation
- logging and retention expectations

The contract is the primary control surface. Sessions, routing, and preflight all depend on it.

### 2. Session control
A session is one governed unit of work, such as "triage failing CI" or "update docs for feature X".

A session should capture:
- session identity and timestamps
- actor, requester, and execution mode
- requested intent and resolved route
- state transitions (`planned`, `validated`, `running`, `blocked`, `completed`, `failed`, `cancelled`)
- artifacts produced during execution
- approvals, exceptions, and stop reasons

### 3. Routing
Routing decides which workflow or policy path should handle a task.

Typical routing inputs:
- task intent
- repository risk profile
- requested capabilities
- current branch/repo state
- contract restrictions

Typical routing outputs:
- documentation-only workflow
- read-only analysis workflow
- low-risk code change workflow
- privileged/escalated workflow
- reject/manual-review outcome

### 4. Preflight validation
Preflight validates that the requested action is safe and admissible before the agent mutates anything.

Preflight commonly checks:
- repository cleanliness and branch policy
- contract existence and schema validity
- task-to-route compatibility
- required approvals or human gates
- availability of required tools/tests
- forbidden files, secrets exposure, or policy conflicts

### 5. Compliance and audit logging
Every governed action should emit durable, queryable evidence.

Minimum audit record:
- who/what initiated the session
- the contract version used
- the selected route and why
- preflight results
- actions attempted and outcomes
- approvals, overrides, and exceptions
- final status and references to outputs

## How the pieces fit together

```text
request
  -> route candidate selection
  -> contract-aware preflight
  -> governed session start
  -> bounded execution
  -> evidence + compliance record
  -> completion, escalation, or rollback path
```

A practical implementation should refuse to execute when the contract is missing, the route is incompatible with policy, or preflight cannot prove the repository is in a safe state.

## Suggested repository structure

```text
.
├── README.md
├── docs/
│   ├── architecture.md
│   └── implementation-plan.md
├── examples/
│   ├── repo-contract.example.json
│   └── session.example.json
├── schemas/
│   ├── repo-contract.schema.json
│   └── session.schema.json
├── cmd/
│   └── governed/           # future CLI entrypoint
└── internal/
    ├── contract/           # contract loading and validation
    ├── session/            # session lifecycle and persistence
    ├── routing/            # intent classification and route selection
    ├── preflight/          # safety and admissibility checks
    └── compliance/         # audit events and reporting
```

Only the documentation, schemas, and examples are present today. The `cmd/` and `internal/` paths show the intended shape for a future implementation.

## Example artifacts in this repository

- `schemas/repo-contract.schema.json` — schema for repository governance rules
- `schemas/session.schema.json` — schema for governed session state and evidence
- `examples/repo-contract.example.json` — example contract for a documentation-safe repository workflow
- `examples/session.example.json` — example session showing routing, preflight, and audit outcomes

## Minimal governed workflow

1. Load and validate the repo contract.
2. Normalize the incoming task request.
3. Classify the request into a route.
4. Run preflight checks required by that route.
5. Start a session only if the route and checks are admissible.
6. Execute bounded actions allowed by the contract.
7. Emit audit events and final session status.

## Waldo-style governance model

This repository uses "Waldo-style" as shorthand for an agent workflow that is not just powerful, but also:
- **policy-scoped** — agents act inside declared boundaries
- **sessionized** — work happens in resumable, inspectable units
- **routed** — the system chooses the correct workflow instead of treating every task the same
- **preflighted** — risky actions are rejected before execution
- **auditable** — every important decision leaves evidence

## Initial implementation milestones

1. **Contract loader and validator**
   - load repo contract from a standard path
   - validate against schema
   - expose effective permissions to the runtime
2. **Session store**
   - create, update, stop, resume, and inspect sessions
   - persist transitions and artifacts
3. **Routing engine**
   - classify tasks into workflow families
   - provide reason codes for every route decision
4. **Preflight engine**
   - run reusable checks before any mutation
   - block execution on policy or state failures
5. **Compliance pipeline**
   - emit structured audit events
   - support review, retention, and exception reporting

## Non-goals for the blueprint phase

- shipping a production agent runtime
- choosing a single language or framework prematurely
- embedding provider-specific model logic in the spec

## Who should use this repo

- teams designing governed agent workflows before implementation
- contributors who need a common vocabulary for policy and safety
- platform engineers evaluating how to make repository automation auditable

See `docs/architecture.md` for the component model and `docs/implementation-plan.md` for a staged build-out plan.
