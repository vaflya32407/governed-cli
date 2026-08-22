# Architecture

`governed-cli` models agentic execution as a policy-constrained control plane around repository work. The current repository includes a minimal local Python prototype for contract validation, route explanation, preflight, session persistence, and audit inspection.

## Control surfaces

### Repo contract
The repo contract is the authoritative policy input for a repository. It should be versioned with the repo and reviewed like code.

Responsibilities:
- describe allowed actions and protected areas
- declare required preflight checks
- define escalation thresholds
- set audit requirements

### Router
The router maps an incoming task to a workflow class.

Responsibilities:
- classify intent
- attach a risk level
- explain route selection with reason codes
- deny unsupported or ambiguous requests

### Preflight engine
The preflight engine proves whether a route can execute safely under the current repository state.

Responsibilities:
- validate contract presence and shape
- inspect repository state
- verify approvals and actor permissions
- enforce route-specific readiness checks

### Session controller
The session controller is the lifecycle owner for a governed unit of work.

Responsibilities:
- create a session record before execution
- track state transitions and checkpoints
- stop, resume, or cancel execution
- attach outputs, evidence, and exceptions

Prototype note:
- the current scaffold persists sessions as local JSON files under `.governed/sessions/`
- sessions currently materialize as `validated` or `blocked` after preflight
- future phases can add resumed and cancelled transitions

### Compliance logger
The compliance logger emits the evidence needed for later review.

Responsibilities:
- record route decisions and preflight outcomes
- capture action attempts and results
- preserve approval and override history
- support audit export and retention policies

## Reference execution flow

```text
operator/requester
  -> task request
  -> router
  -> preflight engine
  -> session controller
  -> bounded executor
  -> compliance logger
  -> session finalization
```

## State model

Recommended session states:
- `planned`
- `validated`
- `running`
- `blocked`
- `completed`
- `failed`
- `cancelled`

Transitions should be append-only in the audit trail even if the current materialized session view is updated in place.

## Governance rules of thumb

1. No mutation without a valid contract.
2. No execution without a route decision.
3. No risky route without required approvals.
4. No session completion without final audit emission.
5. Any override must be explicit, attributable, and reviewable.
