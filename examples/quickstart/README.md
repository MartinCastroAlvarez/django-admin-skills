# examples/

```bash
# Generate (or refresh) the committed example skill from the bundled test project
python examples/quickstart/manage.py admin_skills --out examples/skills/library-admin --app library

# CI-style freshness check: exits non-zero when the committed skill is stale
python examples/quickstart/manage.py admin_skills --out examples/skills/library-admin --app library --check

# The same skill from a saved graph, without the Django project
python examples/quickstart/manage.py admin_graph --app library -o graph.json
python examples/generate_from_graph.py graph.json /tmp/skills/library-admin
```

- `quickstart/manage.py` runs the bundled test project from a source checkout.
- `skills/library-admin/` is real generator output, checked in CI with `--check`.
  Its `library.notice` reference shows the prompt-injection fixture neutralised.
