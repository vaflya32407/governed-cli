# governed-cli
Reference patterns for governed CLI workflows: repo contracts, session control, routing, preflight, and compliance.

Minimal public Python reference project for governed CLI workflows.

## Quickstart

```bash
python -m pip install -e .[dev]
governor route --policy strict --risk high
governor preflight --artifact artifacts/preflight.sample.json
governor compliance --artifact artifacts/compliance.sample.json
governor hook --name on_preflight --payload '{"repo":"vaflya32407/governed-cli"}'
python -m pytest -q
```

## Included reference assets

- Governance CLI surface: `governor` (`route`, `preflight`, `compliance`, `hook`)
- JSON Schemas:
  - `schemas/preflight.schema.json`
  - `schemas/compliance.schema.json`
- Sample artifacts:
  - `artifacts/preflight.sample.json`
  - `artifacts/compliance.sample.json`
