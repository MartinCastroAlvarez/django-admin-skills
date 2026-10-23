# Architecture

## One-line summary

`render_skill(graph)` turns a `django-admin-graph` `AdminGraph` — already
filtered to what one user may see — into an Agent Skill folder, quoting every
author-controlled string as data.

```
AdminSite ─▶ django_admin_graph.build_graph(site, request) ─▶ AdminGraph ─┐
graph.json ─▶ AdminGraph.from_dict ───────────────────────────────────────┤
                                                                          ▼
                        render.render_skill ◀── sanitize (clean · quote · yaml_string)
                                │
                          SkillBundle {path: text}
                         ┌──────┴──────┐
                  writer.write_skill  writer.check_skill   (manage.py admin_skills [--check])
```

## Package layout

```
django_admin_skills/
├── __init__.py   — public API + __version__ (Django-side helpers loaded lazily)
├── api.py        — generate_skill / generate_skills_per_app / graph_for: the only
│                   module that asks django-admin-graph for a graph
├── conf.py       — DJANGO_ADMIN_SKILLS settings → SkillOptions
├── options.py    — SkillOptions (interfaces, origin, REST prefix, MCP path/server),
│                   skill-name validation; no Django
├── sanitize.py   — untrusted text → inert text / code spans / YAML scalars;
│                   identifier and lookup validation
├── render.py     — graph → SKILL.md + references/<app>.<model>.md; pure, no DB
├── writer.py     — write_skill / check_skill, confined to the skill folder
└── management/commands/admin_skills.py — CLI
```

## Output

```
<name>/
├── SKILL.md                    frontmatter: name, description, compatibility, metadata
│                               body: scope, untrusted-text notice, model table, rules,
│                               REST and/or MCP call tables (only granted operations),
│                               change checklist
└── references/
    └── <app>.<model>.md        contents, permissions, operations (REST path + MCP tool),
                                fields (type, value hint, on add / on change, notes),
                                choices, changelist (columns, search, filters, ordering,
                                page size, date drill-down), forms, actions, inlines,
                                custom permissions
```

Progressive disclosure follows the spec: an agent loads only `name` +
`description` at startup, `SKILL.md` when the skill triggers, and one
reference when it touches that model.

## Decisions

- **Graph only.** Consuming the graph (instead of re-reading the admin)
  keeps permission logic in one place, lets CI render from a saved JSON file,
  and makes rendering query-free and deterministic.
- **Placeholders over hosts.** The origin is `$DJANGO_ADMIN_URL` by default
  so a committed skill works across environments and leaks no internal host.
- **Quote, don't trust.** Rather than trying to decide which help texts are
  "safe", every author string is normalised, scrubbed and shown as a code
  span; SKILL.md tells the agent such spans are data.
- **Generated files are owned.** A marker comment lets `write_skill` refuse
  to clobber a hand-written skill and delete only its own stale references.
