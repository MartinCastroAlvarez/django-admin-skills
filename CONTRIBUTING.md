# Contributing to django-admin-skills

## TL;DR

```bash
poetry install
poetry run pytest
poetry run ruff check django_admin_skills tests examples && poetry run ruff format --check django_admin_skills tests examples
poetry run mypy django_admin_skills
poetry run bandit -c pyproject.toml -q -r django_admin_skills
poetry run pip-audit
poetry run python examples/quickstart/manage.py admin_skills --out examples/skills/library-admin --app library --check
```

Open a PR against `main` from a `feat/…`, `fix/…`, `docs/…` or `chore/…`
branch.

## What this package will not accept

- Reading the admin directly (`_meta`, `ModelAdmin` attributes, `has_perm`).
  If the skill needs something the graph lacks, add it to
  [django-admin-graph](https://github.com/MartinCastroAlvarez/django-admin-graph) first.
- Record data, usernames, hosts or secrets in generated files.
- Author-controlled text rendered without `sanitize`.

## What it does accept

- Better instructions for agents (clearer workflows, new interfaces), with
  tests and a regenerated example.
- Support for more agent clients' conventions, as long as the output stays
  [Agent Skills](https://agentskills.io/specification)-valid.
- New Django versions (CI matrix + classifiers), docs, examples and tests.

## House rules

1. Every folder has a `README.md` (generated skill folders excepted).
2. Tests alongside features; permission-sensitive changes need anonymous,
   non-staff and limited-staff cases in `tests/test_security.py`; new
   rendered strings need a hostile case.
3. Regenerate `examples/skills/library-admin` in the same change.
4. No secrets in commits.

## Releasing

1. Make sure `django-admin-graph` is a PyPI version pin, not a git pin
   (`publish.yml` refuses otherwise).
2. Bump `version` in `pyproject.toml` and `__version__` in
   `django_admin_skills/__init__.py`; regenerate the example (its metadata
   carries the version); move `Unreleased` in `CHANGELOG.md` under the new version.
3. Merge, tag the merge commit `vX.Y.Z`, push the tag. `publish.yml`
   checks tag == version, runs the tests, scans the artefacts and publishes
   through PyPI Trusted Publishing, then creates the GitHub Release.
