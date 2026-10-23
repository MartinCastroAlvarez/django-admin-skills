#!/usr/bin/env python
"""Render a skill from a saved django-admin-graph JSON file — no Django project needed.

python examples/quickstart/manage.py admin_graph --app library -o graph.json
python examples/generate_from_graph.py graph.json out/library-admin
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from django_admin_graph.schema import AdminGraph

from django_admin_skills import SkillOptions
from django_admin_skills import render_skill
from django_admin_skills import write_skill


def main(graph_file: str, out_dir: str) -> None:
    graph = AdminGraph.from_dict(json.loads(Path(graph_file).read_text(encoding="utf-8")))
    bundle = render_skill(
        graph,
        name=Path(out_dir).name,
        options=SkillOptions(interfaces=("rest", "mcp")),
    )
    changed = write_skill(bundle, out_dir)
    print(f"{bundle.name}: {len(bundle.files)} files, {len(changed)} changed")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
