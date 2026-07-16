# Contributing

Thanks for taking a look! This project favours small, well-tested changes.

## Dev setup

```bash
python -m venv .venv && . .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install ruff pytest
cp .env.example .env
```

## Before you push

```bash
ruff check .        # lint (CI enforces this)
ruff format .       # auto-format
pytest -q           # unit tests (CI enforces this)
```

CI (GitHub Actions) runs **ruff** + **pytest** on every push and pull request —
please keep both green.

## Conventions

- Configuration comes from environment variables (`config/settings.py`) — never
  hardcode credentials or hosts.
- Each layer is a package (`ingestion`, `spark`, `dq`, `warehouse`, `ml`, …);
  put new code in the layer it belongs to.
- New data-quality rules go in `dq/expectations.yaml` (declarative first).
- Add a unit test for any new pure-Python logic under `tests/`.

## Commit messages

Use clear, imperative summaries (e.g. `feat(dq): add currency-range expectation`).
