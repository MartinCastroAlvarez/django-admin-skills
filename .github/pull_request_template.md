## Summary

<!-- What changed and why. -->

## Checklist

- [ ] `poetry run pytest` passes; visibility changes have anonymous / non-staff / limited-staff tests
- [ ] ruff check, ruff format --check, mypy, bandit, pip-audit pass
- [ ] Nothing in `django_admin_skills/` reads the admin directly — the graph is the only source
- [ ] New author-controlled strings go through `sanitize.quote` / `sanitize.clean`, with a test in `tests/test_security.py`
- [ ] `examples/skills/library-admin` regenerated (`manage.py admin_skills ... --app library`)
- [ ] No secrets in the diff
