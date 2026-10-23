"""Settings for django-admin-skills, read from one optional dict.

.. code-block:: python

    DJANGO_ADMIN_SKILLS = {
        "INTERFACES": ["rest", "mcp"],          # which APIs the skill documents
        "BASE_URL": "",                          # "" → agent reads $DJANGO_ADMIN_URL
        "BASE_URL_ENV": "DJANGO_ADMIN_URL",
        "REST_PREFIX": "/admin-api/api/v1/",     # django_admin_rest_api mount + api/v1/
        "MCP_PATH": "/mcp/",                     # django_admin_mcp_api mount
        "MCP_SERVER": "django-admin",            # MCP server name in the agent's client
    }

The admin site itself is chosen by django-admin-graph's ``ADMIN_SITE``
setting — this package never resolves or inspects an ``AdminSite`` itself.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from django_admin_skills.options import OptionsError
from django_admin_skills.options import SkillOptions

NAMESPACE = "DJANGO_ADMIN_SKILLS"

_KEYS = {
    "INTERFACES": "interfaces",
    "BASE_URL": "base_url",
    "BASE_URL_ENV": "base_url_env",
    "REST_PREFIX": "rest_prefix",
    "MCP_PATH": "mcp_path",
    "MCP_SERVER": "mcp_server",
}


def user_settings() -> dict[str, Any]:
    value = getattr(settings, NAMESPACE, None) or {}
    if not isinstance(value, dict):
        raise ImproperlyConfigured(f"{NAMESPACE} must be a dict, got {type(value).__name__}")
    unknown = sorted(set(value) - set(_KEYS))
    if unknown:
        raise ImproperlyConfigured(f"Unknown {NAMESPACE} keys: {', '.join(unknown)}")
    return value


def get_options(**overrides: Any) -> SkillOptions:
    """:class:`SkillOptions` from settings, with keyword overrides (``None`` = keep)."""
    kwargs: dict[str, Any] = {_KEYS[k]: v for k, v in user_settings().items()}
    kwargs.update({k: v for k, v in overrides.items() if v is not None})
    if "interfaces" in kwargs:
        kwargs["interfaces"] = tuple(kwargs["interfaces"])
    try:
        return SkillOptions(**kwargs)
    except OptionsError as exc:
        raise ImproperlyConfigured(f"{NAMESPACE}: {exc}") from exc
