"""Assertions shared by the tests."""

from __future__ import annotations

import re
from typing import Any

import yaml

from django_admin_skills.render import SkillBundle


def frontmatter(text: str) -> dict[str, Any]:
    """Parse SKILL.md's YAML frontmatter (and assert there is exactly one)."""
    assert text.startswith("---\n")
    head, sep, _body = text[4:].partition("\n---\n")
    assert sep, "frontmatter is not closed"
    data = yaml.safe_load(head)
    assert isinstance(data, dict)
    return data


def everything(bundle: SkillBundle) -> str:
    return "\n".join(bundle.files.values())


def links(text: str) -> list[str]:
    return re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", text)
