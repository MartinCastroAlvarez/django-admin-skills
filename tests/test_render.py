from __future__ import annotations

import json
from typing import Any

import pytest
from django_admin_graph.schema import AdminGraph

from django_admin_skills import OptionsError
from django_admin_skills import SkillOptions
from django_admin_skills import generate_skill
from django_admin_skills import generate_skills_per_app
from django_admin_skills import render_skill
from django_admin_skills import render_skills_per_app
from django_admin_skills.render import MARKER
from tests.helpers import frontmatter


def test_layout(site_graph: Any) -> None:
    bundle = render_skill(site_graph, name="library-admin")
    assert list(bundle.files) == sorted(bundle.files)
    assert set(bundle.files) == {
        "SKILL.md",
        "references/library.author.md",
        "references/library.authorprofile.md",
        "references/library.book.md",
        "references/library.notice.md",
        "references/library.publisher.md",
        "references/library.review.md",
        "references/library.tag.md",
    }
    # inline-only and unregistered models get no reference of their own
    assert bundle.reference("library.Chapter") is None
    assert bundle.reference("library.auditentry") is None
    assert all(MARKER in text for text in bundle.files.values())


def test_deterministic(site_graph: Any) -> None:
    a = render_skill(site_graph, name="library-admin")
    b = render_skill(
        AdminGraph.from_dict(json.loads(json.dumps(site_graph.to_dict()))), name="library-admin"
    )
    assert a.files == b.files


def test_book_reference_content(site_graph: Any) -> None:
    ref = render_skill(site_graph, name="library-admin").reference("library.book")
    assert ref is not None
    # fields + types + requiredness
    assert (
        "| `title` | `title` | `CharField` | string | required | editable | max 200 chars |" in ref
    )
    assert "| `created_at` |" in ref and "read-only" in ref
    assert "`internal_notes`" not in ref  # excluded by the ModelAdmin
    # choices
    assert "### Choices: `status`" in ref
    assert '| `"draft"` | `Draft` |' in ref
    # relations link to the target's reference
    assert "→ `library.author` ([reference](library.author.md))" in ref
    assert "list of primary keys" in ref  # m2m tags
    # changelist
    assert "matches: `title`, `author__name`" in ref
    assert "| `band` | — | `PriceFilter` | `price band` |" in ref
    assert "| `publisher` | `publisher` | `RelatedOnlyFieldListFilter` |" in ref
    assert "Page size: 25" in ref
    assert "Date drill-down on `created_at`" in ref
    # forms
    assert "`slug` is prepopulated from `title`" in ref
    assert "Look up values for `author`" in ref
    # actions, inlines, custom permissions
    assert "| `mark_published` | `Publish selected books` | publish |" in ref
    assert "actions/mark_published/" in ref
    assert "`delete_selected` deletes every selected object" in ref
    assert "### `library.review` (tabular) via `book`" in ref
    assert "### `library.chapter` (stacked) via `book`" in ref
    assert "At most 50 per parent" in ref
    assert "| `publish_book` | `Can publish book` |" in ref


def test_publisher_cannot_be_added(site_graph: Any) -> None:
    ref = render_skill(site_graph, name="library-admin").reference("library.publisher")
    assert ref is not None
    assert "| yes | no | yes | yes |" in ref
    assert "admin.create" not in ref and "Add form accepts" not in ref
    assert "| `country` |" in ref and '| `"AR"` | `Argentina` |' in ref


def test_review_fieldsets_and_tag_without_search(site_graph: Any) -> None:
    bundle = render_skill(site_graph, name="library-admin")
    review = bundle.reference("library.review")
    assert review is not None and "`Text`: `body`" in review
    profile = bundle.reference("library.authorprofile")
    assert profile is not None and "Search: not enabled" in profile


def test_skill_md_lists_models_and_both_interfaces(site_graph: Any) -> None:
    md = render_skill(site_graph, name="library-admin").skill_md
    assert "| `library.book` | `book` | view, add, change, delete |" in md
    assert "[library.book.md](references/library.book.md)" in md
    assert "## REST: django-admin-rest-api" in md
    assert "## MCP: django-admin-mcp-api" in md
    assert "`$DJANGO_ADMIN_URL/admin-api/api/v1/`" in md
    assert "`django-admin:admin.action`" in md
    assert "**Scope:** generated for the whole site" in md
    assert frontmatter(md)["metadata"]["scope"] == "site"


def test_interfaces_and_base_url(site_graph: Any) -> None:
    rest = render_skill(
        site_graph,
        name="library-admin",
        options=SkillOptions(interfaces=("rest",), base_url="https://admin.example.com"),
    )
    assert "## MCP" not in rest.skill_md and "django-admin:" not in "".join(rest.files.values())
    assert "`https://admin.example.com/admin-api/api/v1/`" in rest.skill_md
    assert "DJANGO_ADMIN_URL" not in rest.skill_md
    mcp = render_skill(
        site_graph,
        name="library-admin",
        options=SkillOptions(interfaces=("mcp",), mcp_server="lib"),
    )
    assert "## REST" not in mcp.skill_md
    assert "`lib:admin.list`" in mcp.skill_md
    ref = mcp.reference("library.book")
    assert ref is not None and "GET library/book/" not in ref and "`lib:admin.update`" in ref


def test_app_filter_and_unknown_app(site_graph: Any) -> None:
    assert render_skill(site_graph, name="x", app_labels=["nope"]).files.keys() == {"SKILL.md"}
    assert "No models are available" in render_skill(site_graph, name="x", app_labels=[]).skill_md


def test_invalid_name_rejected(site_graph: Any) -> None:
    with pytest.raises(OptionsError):
        render_skill(site_graph, name="Library Admin")


@pytest.mark.django_db
def test_per_app_and_api_helpers(superuser: Any) -> None:
    bundles = generate_skills_per_app(prefix="shop", user=superuser)
    names = [b.name for b in bundles]
    assert names == ["shop-auth", "shop-library"]
    auth = bundles[0]
    assert "references/auth.user.md" in auth.files
    assert not any(p.startswith("references/library.") for p in auth.files)
    one = generate_skill(name="library-admin", app_labels=["library"])
    assert frontmatter(one.skill_md)["metadata"]["scope"] == "site"


def test_per_app_names_are_normalised(site_graph: Any) -> None:
    data = site_graph.to_dict()
    for node in data["nodes"]:
        for key in ("id", "model", "app", "admin"):
            if isinstance(node.get(key), str):
                node[key] = node[key].replace("library", "my_lib")
    graph = AdminGraph.from_dict(data)
    assert [b.name for b in render_skills_per_app(graph, prefix="a-")] == ["a-my-lib"]


def test_malformed_identifiers_in_a_saved_graph_are_dropped(site_graph: Any) -> None:
    data = site_graph.to_dict()
    for node in data["nodes"]:
        if node["id"] == "admin:library.book":
            node["list_display"].append("x); DROP TABLE")
            node["actions"].append({"name": "zz bad act", "description": "bad"})
            node["inlines"].append("inline:missing")
        if node["id"] == "model:library.book":
            node["fields"].append({"name": "bad name", "type": "CharField"})
            node["fields"].append({"name": "odd", "type": "Weird Type", "field_class": "?"})
            node["pk"] = "1bad"
    data["nodes"].append(
        {
            "id": "model:../etc.passwd",
            "kind": "model",
            "app": "app:x",
            "label": "x",
            "object_name": "X",
            "pk": "id",
        }
    )
    data["nodes"].append(
        {
            "id": "admin:../etc.passwd",
            "kind": "admin",
            "model": "model:../etc.passwd",
            "class_name": "X",
            "permissions": {"view": True, "add": True, "change": True, "delete": True},
        }
    )
    bundle = render_skill(AdminGraph.from_dict(data), name="library-admin")
    text = "\n".join(bundle.files.values())
    assert "DROP TABLE" not in text and "zz bad act" not in text and "bad name" not in text
    assert "passwd" not in text
    ref = bundle.reference("library.book")
    assert ref is not None and "| `odd` |" in ref and "`unknown`" in ref
    assert "Primary key: `pk`" in ref
