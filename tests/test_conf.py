from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from django_admin_skills import conf


def test_defaults() -> None:
    assert conf.get_options().interfaces == ("rest", "mcp")


@override_settings(
    DJANGO_ADMIN_SKILLS={"INTERFACES": ["mcp"], "MCP_SERVER": "shop", "REST_PREFIX": "/api/v1/"}
)
def test_settings_are_read() -> None:
    o = conf.get_options()
    assert o.interfaces == ("mcp",)
    assert o.mcp_server == "shop"
    assert o.rest_prefix == "/api/v1/"


@override_settings(DJANGO_ADMIN_SKILLS={"INTERFACES": ["mcp"]})
def test_overrides_win_and_none_keeps() -> None:
    assert conf.get_options(interfaces=("rest",), base_url=None).interfaces == ("rest",)


@pytest.mark.parametrize(
    "value",
    [["rest"], {"NOPE": 1}, {"BASE_URL": "https://u:p@x.example"}],
)
def test_bad_settings(value: object) -> None:
    with override_settings(DJANGO_ADMIN_SKILLS=value), pytest.raises(ImproperlyConfigured):
        conf.get_options()
