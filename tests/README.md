# tests/

`pytest` suite against `test_project/` (the same library catalogue
django-admin-graph uses, plus a hostile `Notice` model).
`test_security.py` covers permission tiers, record data, secrets and
prompt injection; `test_spec.py` validates output against the Agent Skills rules.
