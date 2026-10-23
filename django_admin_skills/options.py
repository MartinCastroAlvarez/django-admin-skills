"""Rendering options — plain data, validated once, no Django required."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit

Interface = Literal["rest", "mcp"]
INTERFACES: tuple[Interface, ...] = ("rest", "mcp")

# Agent Skills spec: 1–64 chars, lowercase alphanumerics and single hyphens,
# no leading/trailing hyphen. Anthropic additionally reserves two words.
_SKILL_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9]|-(?!-)){0,62}[a-z0-9]$|^[a-z0-9]$")
RESERVED_WORDS = ("anthropic", "claude")
_PATH = re.compile(r"^/(?:[A-Za-z0-9._~-]+/)*$")
_ENV = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_MCP_SERVER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class OptionsError(ValueError):
    """An option value would produce an invalid or unsafe skill."""


def validate_skill_name(name: str) -> str:
    """Return ``name`` if it is a valid Agent Skills ``name``, else raise."""
    if not isinstance(name, str) or not _SKILL_NAME.match(name):
        raise OptionsError(
            f"Invalid skill name {name!r}: use 1-64 lowercase letters, digits and single "
            "hyphens, not starting or ending with a hyphen."
        )
    for word in RESERVED_WORDS:
        if word in name:
            raise OptionsError(f"Invalid skill name {name!r}: {word!r} is a reserved word.")
    return name


@dataclass(frozen=True, slots=True)
class SkillOptions:
    """How the generated skill tells an agent to reach the admin.

    :param interfaces: which wire protocols to document — ``"rest"``
        (django-admin-rest-api) and/or ``"mcp"`` (django-admin-mcp-api).
    :param base_url: absolute origin of the Django site (``https://admin.example.com``).
        Empty by default: the skill then tells the agent to read it from the
        ``base_url_env`` environment variable, so no host is ever baked into
        a committed file unless the operator opts in.
    :param base_url_env: environment variable that holds the origin.
    :param rest_prefix: where ``django_admin_rest_api.urls`` is mounted plus
        ``api/v1/`` (the rest-api README mounts it at ``/admin-api/``).
    :param mcp_path: where ``django_admin_mcp_api.urls`` is mounted.
    :param mcp_server: the MCP server name the agent's client registered,
        used for fully-qualified tool names (``django-admin:admin.list``).
    """

    interfaces: tuple[Interface, ...] = INTERFACES
    base_url: str = ""
    base_url_env: str = "DJANGO_ADMIN_URL"
    rest_prefix: str = "/admin-api/api/v1/"
    mcp_path: str = "/mcp/"
    mcp_server: str = "django-admin"

    def __post_init__(self) -> None:
        interfaces = tuple(dict.fromkeys(self.interfaces))
        if not interfaces or any(i not in INTERFACES for i in interfaces):
            raise OptionsError(f"interfaces must be a non-empty subset of {INTERFACES}")
        object.__setattr__(self, "interfaces", tuple(i for i in INTERFACES if i in interfaces))
        if self.base_url:
            parts = urlsplit(self.base_url)
            if parts.scheme not in ("http", "https") or not parts.hostname:
                raise OptionsError("base_url must be an absolute http(s) origin")
            if parts.username or parts.password:
                raise OptionsError("base_url must not contain credentials")
            if parts.query or parts.fragment or parts.path not in ("", "/"):
                raise OptionsError("base_url must be an origin only (no path, query or fragment)")
            object.__setattr__(self, "base_url", f"{parts.scheme}://{parts.netloc}")
        if not _ENV.match(self.base_url_env):
            raise OptionsError("base_url_env must be an UPPER_SNAKE_CASE variable name")
        for label, value in (("rest_prefix", self.rest_prefix), ("mcp_path", self.mcp_path)):
            if not _PATH.match(value):
                raise OptionsError(f"{label} must be an absolute path ending in '/'")
        if not _MCP_SERVER.match(self.mcp_server):
            raise OptionsError("mcp_server must be a short name (letters, digits, '.', '_', '-')")

    @property
    def origin(self) -> str:
        """The origin as the agent should write it (a literal or ``$ENV``)."""
        return self.base_url or f"${self.base_url_env}"

    def rest(self, path: str = "") -> str:
        return f"{self.origin}{self.rest_prefix}{path}"

    def mcp(self) -> str:
        return f"{self.origin}{self.mcp_path}"

    def tool(self, name: str) -> str:
        return f"{self.mcp_server}:{name}"
