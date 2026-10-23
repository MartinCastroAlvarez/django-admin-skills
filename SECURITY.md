# Security

`django-admin-skills` writes files that an AI agent reads as instructions.
The design goal: a generated skill never tells an agent more than the admin
would show the user it was built for, never carries data or secrets, and
never lets text from the project become an instruction.

## Reporting a vulnerability

Open a private security advisory at
<https://github.com/MartinCastroAlvarez/django-admin-skills/security/advisories/new>.
Do **not** open a public issue for a suspected vulnerability. We acknowledge
within 5 business days and aim to ship a fix within 30 days; you are credited
in the advisory unless you ask otherwise.

Supported versions: the latest minor release.

## 1. Threat model

**Assets.** The schema of your admin (models, fields, choices, help texts,
relations, filters, actions, permissions) as written into `SKILL.md` and
`references/`, and the agent's behaviour when it reads them. Not record
data — nothing here queries rows.

**Actors.**

| Actor | Can reach | Must get |
| --- | --- | --- |
| Anonymous / non-staff / inactive user (`--as-user`, `request=`) | `generate_skill` | `NotAuthenticated` / `PermissionDenied` (from django-admin-graph), no files |
| Staff user with limited permissions | a skill built `--as-user` them | only the models, fields, operations and actions the admin grants them |
| Operator with shell access | `manage.py admin_skills` without `--as-user` | the whole site (system mode) — treat that skill like source code |
| A developer writing `help_text`, `verbose_name`, choices, action descriptions | text that lands in the skill | quoted data, never instructions |
| The agent reading the skill | the files, then the live API | a map, not a grant: the server re-checks every call |

**Threats and controls.**

| Threat | Control |
| --- | --- |
| Prompt injection through author-controlled strings | `sanitize.clean`: NFKC, control/format characters (zero-width, bidi) removed, newlines collapsed, runs of `-=_*~`` ` collapsed, `<`/`>` neutralised, instruction-like phrases (role markers, "ignore previous instructions", chat-template tokens, `<system>` tags) replaced; every such string is rendered inside a code span with backticks and pipes neutralised, never in a heading or the YAML keys. SKILL.md tells the agent quoted text is data. |
| Injected structure (fake frontmatter, headings, table cells, links) | Frontmatter values are double-quoted YAML; identifiers (app, model, field, action, filter names) are validated with a regex and dropped otherwise; tests parse the frontmatter and check headings and table shapes. |
| Secrets in help texts | Token-shaped strings (GitHub, OpenAI-style, Slack, AWS, Google, JWT, PEM, `password=…`) become `[redacted]`. |
| Internal hosts / contacts in the skill | URLs and e-mail addresses in author text are removed; the API origin is a `$DJANGO_ADMIN_URL` placeholder unless the operator passes `--base-url` (credentials, paths and queries refused). |
| An agent learning operations it may not perform | `--as-user` builds the graph with that user's request; operation rows exist only for granted permissions; actions come from `get_actions(request)` via the graph. |
| Re-implemented permission logic drifting from the admin | No `_meta`, `has_perm`, `.objects`, `get_model_perms`, `admin.site` in the package; a test scans the source. |
| Record data or identity in the skill | The graph has none; a test creates rows and a uniquely named user and asserts none of it appears, and that rendering issues zero queries. |
| Writing outside the skill folder / clobbering files | `write_skill` validates relative POSIX paths, resolves symlinks, refuses paths outside the folder, refuses to overwrite a `SKILL.md` without the generator marker, and only deletes its own marked references. |
| A hostile saved graph (`--graph`) | Read with `json` (no YAML/pickle), size-capped (20 MB), unknown major schema refused by `AdminGraph.from_dict`, identifiers validated during rendering. |
| A stale skill promising operations that were revoked | `--check` in CI; and the skill tells the agent that a `403` is final. |

**Out of scope.** Your ModelAdmin permission methods being wrong (the skill
faithfully reports what the graph says), an operator publishing a
system-mode skill, and the agent ignoring its instructions — the server-side
permission checks in django-admin-rest-api / django-admin-mcp-api are the
real boundary.

## 2. Non-negotiable rules

Enforced by `tests/test_security.py`; if one fails, fix the code, never the test.

1. **The graph is the only source.** No admin introspection, no `has_perm`, no row queries in `django_admin_skills/`.
2. **Never name what the user cannot see.** No reference, row or link for a model outside the graph.
3. **Untrusted text is quoted data.** Every author-controlled string goes through `sanitize`.
4. **No dangerous constructs.** No `mark_safe`, `csrf_exempt`, `eval`, `exec`, `pickle`, `yaml.load`, `subprocess`, `shell=True`.
5. **No identity, hosts or secrets** in generated files unless the operator opts in with `--base-url`.

## 3. Supply chain

CI runs `bandit` and `pip-audit` on every push; Dependabot watches pip and
GitHub Actions; releases use PyPI Trusted Publishing (no API tokens), the
built artefacts are scanned for token-shaped strings, and `publish.yml`
refuses to release while any dependency is a direct git/URL reference.
