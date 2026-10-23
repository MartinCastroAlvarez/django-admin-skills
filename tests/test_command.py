from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from django.core.management import CommandError
from django.core.management import call_command
from django.test import override_settings
from django_admin_graph import build_graph

from tests.helpers import frontmatter


def run(*args: str) -> str:
    out = StringIO()
    call_command("admin_skills", *args, stdout=out, stderr=StringIO())
    return out.getvalue()


@pytest.mark.django_db
def test_write_and_check(tmp_path: Path) -> None:
    out = tmp_path / ".claude" / "skills" / "library-admin"
    assert "8 file(s)" in run("--out", str(out), "--app", "library")
    assert (out / "SKILL.md").is_file()
    assert "up to date" in run("--out", str(out), "--app", "library", "--check")
    (out / "references" / "library.book.md").write_text("tampered\n")
    with pytest.raises(CommandError, match="out of date"):
        run("--out", str(out), "--app", "library", "--check")


@pytest.mark.django_db
def test_check_fails_when_admin_changes(tmp_path: Path) -> None:
    out = tmp_path / "library-admin"
    run("--out", str(out), "--app", "library")
    with pytest.raises(CommandError):
        run("--out", str(out), "--app", "library", "--app", "auth", "--check")


@pytest.mark.django_db
def test_name_interface_base_url(tmp_path: Path) -> None:
    out = tmp_path / "ops"
    run(
        "--out", str(out), "--name", "ops", "--interface", "rest", "--base-url", "https://a.example"
    )
    md = (out / "SKILL.md").read_text()
    assert frontmatter(md)["metadata"]["interfaces"] == "rest"
    assert "https://a.example/admin-api/api/v1/" in md


@pytest.mark.django_db
def test_per_app(tmp_path: Path) -> None:
    run("--out", str(tmp_path), "--per-app", "--name", "shop")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["shop-auth", "shop-library"]
    assert "2 skill(s) up to date" in run(
        "--out", str(tmp_path), "--per-app", "--name", "shop", "--check"
    )


@pytest.mark.django_db
def test_as_user(tmp_path: Path, limited_staff: Any) -> None:
    out = tmp_path / "viewer-skill"
    run("--out", str(out), "--as-user", "viewer")
    assert sorted(p.name for p in (out / "references").iterdir()) == ["library.book.md"]
    assert frontmatter((out / "SKILL.md").read_text())["metadata"]["scope"] == "user"


@pytest.mark.django_db
def test_as_user_errors(tmp_path: Path, non_staff: Any) -> None:
    with pytest.raises(CommandError, match="No user"):
        run("--out", str(tmp_path / "x"), "--as-user", "ghost")
    with pytest.raises(CommandError, match="cannot use this admin site"):
        run("--out", str(tmp_path / "x"), "--as-user", "customer")
    assert not (tmp_path / "x").exists()


@pytest.mark.django_db
def test_from_saved_graph(tmp_path: Path) -> None:
    graph_file = tmp_path / "graph.json"
    graph_file.write_text(json.dumps(build_graph(app_labels=["library"]).to_dict()))
    out = tmp_path / "library-admin"
    run("--graph", str(graph_file), "--out", str(out))
    direct = tmp_path / "direct" / "library-admin"
    run("--out", str(direct), "--app", "library")
    assert (out / "SKILL.md").read_text() == (direct / "SKILL.md").read_text()
    with pytest.raises(CommandError, match="cannot be combined"):
        run("--graph", str(graph_file), "--out", str(out), "--as-user", "x")
    graph_file.write_text('{"schema_version": "9.0"}')
    with pytest.raises(CommandError, match="Cannot read graph"):
        run("--graph", str(graph_file), "--out", str(out))
    with pytest.raises(CommandError, match="Cannot read graph"):
        run("--graph", str(tmp_path / "missing.json"), "--out", str(out))


@pytest.mark.django_db
def test_graph_size_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from django_admin_skills.management.commands import admin_skills

    monkeypatch.setattr(admin_skills, "MAX_GRAPH_BYTES", 1)
    graph_file = tmp_path / "graph.json"
    graph_file.write_text("{}")
    with pytest.raises(CommandError, match="larger than"):
        run("--graph", str(graph_file), "--out", str(tmp_path / "s"))


@pytest.mark.django_db
def test_site_option(tmp_path: Path) -> None:
    out = tmp_path / "ops-admin"
    run("--out", str(out), "--site", "tests.test_project.library.admin.ops_site")
    assert sorted(p.name for p in (out / "references").iterdir()) == ["library.tag.md"]
    assert "site `ops`" in (out / "SKILL.md").read_text()
    with pytest.raises(CommandError, match="Cannot import"):
        run("--out", str(out), "--site", "nope.site")
    with pytest.raises(CommandError, match="not an AdminSite"):
        run("--out", str(out), "--site", "tests.test_project.library.admin.PriceFilter")


@pytest.mark.django_db
def test_bad_inputs(tmp_path: Path) -> None:
    with pytest.raises(CommandError, match="Invalid skill name"):
        run("--out", str(tmp_path / "Bad_Name"))
    with pytest.raises(CommandError, match="reserved"):
        run("--out", str(tmp_path / "claude-admin"))
    with pytest.raises(CommandError, match="base_url"):
        run("--out", str(tmp_path / "s"), "--base-url", "https://u:p@x.example")
    hand = tmp_path / "mine"
    hand.mkdir()
    (hand / "SKILL.md").write_text("mine\n")
    with pytest.raises(CommandError, match="refusing to overwrite"):
        run("--out", str(hand))


@pytest.mark.django_db
@override_settings(DJANGO_ADMIN_SKILLS={"INTERFACES": ["mcp"], "MCP_SERVER": "lib"})
def test_settings_drive_the_command(tmp_path: Path) -> None:
    out = tmp_path / "s"
    run("--out", str(out), "--app", "library")
    md = (out / "SKILL.md").read_text()
    assert "## REST" not in md and "`lib:admin.list`" in md
