"""Generated skills follow the Agent Skills spec and Anthropic's authoring rules."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

from django_admin_skills import render_skill
from django_admin_skills.render import SkillBundle
from tests.helpers import frontmatter
from tests.helpers import links

NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _bundle(site_graph: Any) -> SkillBundle:
    return render_skill(site_graph, name="library-admin")


def test_frontmatter_fields(site_graph: Any) -> None:
    meta = frontmatter(_bundle(site_graph).skill_md)
    assert set(meta) == {"name", "description", "compatibility", "metadata"}
    assert meta["name"] == "library-admin"
    assert NAME.match(meta["name"]) and len(meta["name"]) <= 64
    assert 0 < len(meta["description"]) <= 1024
    assert 0 < len(meta["compatibility"]) <= 500
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in meta["metadata"].items())
    assert meta["metadata"]["generator"] == "django-admin-skills"


def test_description_is_third_person_and_tag_free(site_graph: Any) -> None:
    description = frontmatter(_bundle(site_graph).skill_md)["description"]
    assert not re.search(r"<[^>]*>", description)
    assert not re.search(r"\b(I|you|You)\b", description)
    assert "Use when" in description


def test_skill_md_is_short(site_graph: Any) -> None:
    body = _bundle(site_graph).skill_md
    assert len(body.splitlines()) < 500


def test_every_link_resolves_one_level_deep(site_graph: Any) -> None:
    bundle = _bundle(site_graph)
    for target in links(bundle.skill_md):
        assert target in bundle.files, target
        assert len(PurePosixPath(target).parts) == 2  # references/<file>.md
    for path, text in bundle.files.items():
        if path == "SKILL.md":
            continue
        base = PurePosixPath(path).parent
        for target in links(text):
            resolved = PurePosixPath(*(base / target).parts)
            normal = str(resolved).replace("references/../", "")
            assert normal in bundle.files, (path, target)


def test_long_references_have_contents(site_graph: Any) -> None:
    for path, text in _bundle(site_graph).files.items():
        if path.startswith("references/") and len(text.splitlines()) > 100:
            assert "## Contents" in text, path


def test_paths_are_posix_and_safe(site_graph: Any) -> None:
    for path in _bundle(site_graph).files:
        assert "\\" not in path and ".." not in path and not path.startswith("/")
        assert path == "SKILL.md" or re.match(r"^references/[a-z0-9_]+\.[a-z0-9_]+\.md$", path)
