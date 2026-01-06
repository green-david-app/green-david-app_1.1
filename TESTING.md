# Testing

Run locally:

```bash
python3 run_tests.py
```

What it checks:

- `/api/search` never returns HTTP 500 and keeps a stable JSON structure.
- Contract test with deterministic seeded data (jobs/tasks/employees; issues when available).
- Smoke tests for key list endpoints: `/api/jobs`, `/api/tasks`, `/api/issues`, `/api/employees`, `/api/me`.
- Hard-fail on dangerous bootstrap warnings (e.g., migrations warnings, missing tables, OperationalError).
