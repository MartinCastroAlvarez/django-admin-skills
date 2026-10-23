"""The Django-side entry point: build the graph, then render it.

``generate_skill`` is the only function here that touches Django, and it
does so solely through ``django_admin_graph.build_graph`` — the admin is
introspected once, by the graph package, with the permissions of the user
the skill is for.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django_admin_graph import build_graph
from django_admin_graph.schema import AdminGraph

from django_admin_skills.options import SkillOptions
from django_admin_skills.render import SkillBundle
from django_admin_skills.render import render_skill
from django_admin_skills.render import render_skills_per_app


def request_for_user(user: Any) -> HttpRequest:
    """A bare, offline GET request carrying ``user`` (for ``--as-user`` builds)."""
    request = HttpRequest()
    request.method = "GET"
    request.path = "/"
    request.META["SERVER_NAME"] = "localhost"
    request.META["SERVER_PORT"] = "80"
    request.user = user
    return request


def graph_for(
    *,
    site: AdminSite | None = None,
    request: HttpRequest | None = None,
    user: Any = None,
    app_labels: Iterable[str] | None = None,
) -> AdminGraph:
    """The admin graph for ``request`` / ``user`` (or the whole site when neither).

    Raises ``django_admin_graph.NotAuthenticated`` / ``PermissionDenied`` when
    that user may not use the admin site at all.
    """
    if request is None and user is not None:
        request = request_for_user(user)
    labels = list(app_labels) if app_labels is not None else None
    return build_graph(site, request, app_labels=labels)


def generate_skill(
    *,
    name: str,
    site: AdminSite | None = None,
    request: HttpRequest | None = None,
    user: Any = None,
    app_labels: Iterable[str] | None = None,
    options: SkillOptions | None = None,
) -> SkillBundle:
    """Build the graph for ``user`` (or ``request``) and render one skill."""
    labels = list(app_labels) if app_labels is not None else None
    graph = graph_for(site=site, request=request, user=user, app_labels=labels)
    return render_skill(graph, name=name, options=options, app_labels=labels)


def generate_skills_per_app(
    *,
    prefix: str = "admin",
    site: AdminSite | None = None,
    request: HttpRequest | None = None,
    user: Any = None,
    app_labels: Iterable[str] | None = None,
    options: SkillOptions | None = None,
) -> tuple[SkillBundle, ...]:
    """Like :func:`generate_skill`, one skill per app (``<prefix>-<app>``)."""
    labels = list(app_labels) if app_labels is not None else None
    graph = graph_for(site=site, request=request, user=user, app_labels=labels)
    return render_skills_per_app(graph, prefix=prefix, options=options, app_labels=labels)
