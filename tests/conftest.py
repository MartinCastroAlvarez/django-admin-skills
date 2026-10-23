"""Shared fixtures: one user per permission tier the skill must respect."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from django_admin_skills.api import graph_for

PASSWORD = "pw-not-real-not-for-prod"  # noqa: S105 — test-only


@pytest.fixture
def make_user(db: Any) -> Callable[..., Any]:
    def _make(username: str, *perms: str, **flags: Any) -> Any:
        user = get_user_model().objects.create_user(username=username, password=PASSWORD, **flags)
        for perm in perms:
            app_label, codename = perm.split(".")
            user.user_permissions.add(
                Permission.objects.get(content_type__app_label=app_label, codename=codename)
            )
        return get_user_model().objects.get(pk=user.pk)  # drop the perm cache

    return _make


@pytest.fixture
def superuser(db: Any) -> Any:
    return get_user_model().objects.create_superuser(username="root", password=PASSWORD)


@pytest.fixture
def staff_no_perms(make_user: Callable[..., Any]) -> Any:
    return make_user("bare", is_staff=True)


@pytest.fixture
def limited_staff(make_user: Callable[..., Any]) -> Any:
    """Staff who may only *view* books."""
    return make_user("viewer", "library.view_book", is_staff=True)


@pytest.fixture
def editor_staff(make_user: Callable[..., Any]) -> Any:
    """Staff who may change books, view authors and publish."""
    return make_user(
        "editor",
        "library.view_book",
        "library.change_book",
        "library.view_author",
        "library.publish_book",
        is_staff=True,
    )


@pytest.fixture
def non_staff(make_user: Callable[..., Any]) -> Any:
    return make_user("customer", "library.view_book", is_staff=False)


@pytest.fixture
def inactive_staff(make_user: Callable[..., Any]) -> Any:
    return make_user("gone", "library.view_book", is_staff=True, is_active=False)


@pytest.fixture
def site_graph(db: Any) -> Any:
    """The whole site's graph, restricted to the library app."""
    return graph_for(app_labels=["library"])
