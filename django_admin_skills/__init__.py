"""django-admin-skills — Agent Skills (SKILL.md) generated from the Django admin.

>>> from django_admin_skills import generate_skill, write_skill
>>> bundle = generate_skill(name="library-admin", user=staff_user)
>>> write_skill(bundle, ".claude/skills/library-admin")

Or, Django-free, from a saved django-admin-graph JSON file:

>>> from django_admin_graph import AdminGraph
>>> from django_admin_skills import render_skill
>>> render_skill(AdminGraph.from_dict(data), name="library-admin")
"""

from __future__ import annotations

__version__ = "0.1.0"

from django_admin_skills.options import OptionsError
from django_admin_skills.options import SkillOptions
from django_admin_skills.options import validate_skill_name
from django_admin_skills.render import SkillBundle
from django_admin_skills.render import render_skill
from django_admin_skills.render import render_skills_per_app
from django_admin_skills.writer import SkillWriteError
from django_admin_skills.writer import check_skill
from django_admin_skills.writer import write_skill


def __getattr__(name: str) -> object:
    # The Django-side helpers import django.contrib.admin; load them lazily so
    # ``render_skill`` works on a saved graph without configured settings.
    if name in ("generate_skill", "generate_skills_per_app", "graph_for"):
        from django_admin_skills import api

        return getattr(api, name)
    raise AttributeError(name)


__all__ = [
    "OptionsError",
    "SkillBundle",
    "SkillOptions",
    "SkillWriteError",
    "__version__",
    "check_skill",
    "generate_skill",
    "generate_skills_per_app",
    "graph_for",
    "render_skill",
    "render_skills_per_app",
    "validate_skill_name",
    "write_skill",
]
