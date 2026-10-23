# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### To do before the first PyPI release
- `django-admin-graph` is pinned from git
  (`rev = f907ce77ab76a48d97f64729fda39c953af442ab`) because it is not on PyPI
  yet. Switch the dependency to `django-admin-graph = "^0.1.0"` once it is
  published; `publish.yml` refuses to release while a git dependency remains
  (PyPI rejects direct-URL requirements).

## [0.1.0] — unreleased

### Added
- `render_skill(graph, *, name, options=None, app_labels=None) -> SkillBundle`:
  an Agent Skill (`SKILL.md` + `references/<app>.<model>.md`) from a
  `django-admin-graph` `AdminGraph` — fields, value hints, requiredness,
  choices, relations, list columns, search, filters with their query
  parameters, forms, actions, inlines and custom permissions.
- `render_skills_per_app` (one skill per app) and the Django-side
  `generate_skill` / `generate_skills_per_app` (`user=` or `request=`).
- REST (django-admin-rest-api) and MCP (django-admin-mcp-api) call
  instructions, configurable interfaces, origin (`$DJANGO_ADMIN_URL` by
  default), REST prefix, MCP path and server name.
- Prompt-injection hardening in `sanitize`: invisible characters, structure,
  secrets, URLs, e-mails and instruction-like phrases neutralised; quoted
  rendering.
- `write_skill` / `check_skill` with path, symlink and overwrite guards.
- `manage.py admin_skills --out DIR [--name] [--app ...] [--per-app]
  [--as-user USERNAME] [--graph FILE] [--site] [--interface] [--base-url] [--check]`.
- Django 4.2–6.1 on Python 3.11–3.13.
