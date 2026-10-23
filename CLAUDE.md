# CLAUDE.md

Contract between this repository and any AI agent contributing to it.

## Required reading

1. This file. 2. [`README.md`](README.md). 3. [`ARCHITECTURE.md`](ARCHITECTURE.md).
4. [`SECURITY.md`](SECURITY.md). 5. The [Agent Skills spec](https://agentskills.io/specification).

## Mission

`django-admin-skills` renders a `django-admin-graph` graph into an Agent
Skill. **The generated files are the product**, and an agent will obey them.

## The rules

1. **The graph is the only source of truth.** Never read `_meta`,
   `ModelAdmin`, `AdminSite` or permissions directly; if the graph lacks
   something, add it to django-admin-graph first.
2. **Every author-controlled string goes through `sanitize`** (`quote` in
   Markdown, `yaml_string` in frontmatter) and gets a hostile case in
   `tests/test_security.py`. Identifiers are validated, never quoted raw.
3. **List only what the graph grants.** No operation row without the permission.
4. **Deterministic output.** No timestamps, no dict-order or set-order
   surprises; regenerate `examples/skills/library-admin` in the same change.
5. **Spec-valid output.** `name` = folder name, ≤ 64 chars, no `claude` /
   `anthropic`; description ≤ 1024 chars, third person, no tags; SKILL.md
   under 500 lines; references one level deep.
6. **Every folder has a `README.md`** (generated skill folders excepted).

## Done means

`poetry run pytest` (coverage ≥ 90%), `ruff check`, `ruff format --check`,
`mypy` (strict), `bandit`, `pip-audit` all green; `admin_skills --check` on
the example passes; docs and CHANGELOG updated in the same change.

## Git

Small commits, imperative subjects, never force-push `main`, never commit
secrets, never bypass hooks.
