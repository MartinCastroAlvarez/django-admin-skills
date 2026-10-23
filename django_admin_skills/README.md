# django_admin_skills/

The shipped package. `render.py` turns an `AdminGraph` into a skill (pure,
no Django access), `sanitize.py` neutralises author-controlled text,
`writer.py` writes/checks a skill folder, `api.py` is the only module that
asks django-admin-graph for a graph. See [`ARCHITECTURE.md`](../ARCHITECTURE.md).
