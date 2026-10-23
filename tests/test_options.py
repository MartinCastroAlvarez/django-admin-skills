from __future__ import annotations

import pytest

from django_admin_skills.options import OptionsError
from django_admin_skills.options import SkillOptions
from django_admin_skills.options import validate_skill_name


@pytest.mark.parametrize("name", ["a", "library-admin", "x1-y2", "a" * 64])
def test_valid_names(name: str) -> None:
    assert validate_skill_name(name) == name


@pytest.mark.parametrize(
    "name",
    ["", "A", "-a", "a-", "a--b", "a_b", "a.b", "a" * 65, "claude-admin", "my-anthropic", "../x"],
)
def test_invalid_names(name: str) -> None:
    with pytest.raises(OptionsError):
        validate_skill_name(name)


def test_defaults_use_an_env_placeholder() -> None:
    o = SkillOptions()
    assert o.interfaces == ("rest", "mcp")
    assert o.origin == "$DJANGO_ADMIN_URL"
    assert o.rest("registry/") == "$DJANGO_ADMIN_URL/admin-api/api/v1/registry/"
    assert o.mcp() == "$DJANGO_ADMIN_URL/mcp/"
    assert o.tool("admin.list") == "django-admin:admin.list"


def test_interfaces_are_deduplicated_and_ordered() -> None:
    assert SkillOptions(interfaces=("mcp", "rest", "mcp")).interfaces == ("rest", "mcp")


def test_base_url_normalised() -> None:
    assert SkillOptions(base_url="https://admin.example.com/").origin == "https://admin.example.com"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"interfaces": ()},
        {"interfaces": ("graphql",)},
        {"base_url": "ftp://x.example"},
        {"base_url": "https://user:pw@x.example"},
        {"base_url": "https://x.example/admin"},
        {"base_url": "https://x.example?token=1"},
        {"base_url": "not a url"},
        {"base_url_env": "lower"},
        {"rest_prefix": "admin-api"},
        {"rest_prefix": "/a b/"},
        {"mcp_path": "/mcp"},
        {"mcp_server": "bad server"},
    ],
)
def test_invalid_options(kwargs: dict[str, object]) -> None:
    with pytest.raises(OptionsError):
        SkillOptions(**kwargs)  # type: ignore[arg-type]
