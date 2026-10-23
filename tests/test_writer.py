from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from django_admin_skills import SkillWriteError
from django_admin_skills import check_skill
from django_admin_skills import render_skill
from django_admin_skills import write_skill
from django_admin_skills.render import SkillBundle


def test_write_then_check_is_clean(site_graph: Any, tmp_path: Path) -> None:
    bundle = render_skill(site_graph, name="library-admin")
    out = tmp_path / "library-admin"
    assert write_skill(bundle, out) == sorted(bundle.files)
    assert check_skill(bundle, out) == []
    assert write_skill(bundle, out) == []  # idempotent
    assert (out / "references" / "library.book.md").read_text() == bundle.reference("library.book")


def test_check_reports_missing_stale_and_unexpected(site_graph: Any, tmp_path: Path) -> None:
    bundle = render_skill(site_graph, name="library-admin")
    out = tmp_path / "library-admin"
    assert check_skill(bundle, out)[0] == "missing: SKILL.md"
    write_skill(bundle, out)
    (out / "references" / "library.book.md").write_text("edited\n")
    (out / "references" / "old.thing.md").write_text("left over\n")
    problems = check_skill(bundle, out)
    assert "stale: references/library.book.md" in problems
    assert "unexpected: references/old.thing.md" in problems
    assert any("does not match" in p for p in check_skill(bundle, tmp_path / "other"))


def test_write_removes_its_own_stale_references_only(site_graph: Any, tmp_path: Path) -> None:
    out = tmp_path / "library-admin"
    write_skill(render_skill(site_graph, name="library-admin"), out)
    (out / "references" / "notes.md").write_text("hand-written\n")
    smaller = render_skill(site_graph, name="library-admin", app_labels=[])
    changed = write_skill(smaller, out)
    assert "references/library.book.md" in changed
    assert not (out / "references" / "library.book.md").exists()
    assert (out / "references" / "notes.md").exists()


def test_refuses_to_overwrite_a_hand_written_skill(site_graph: Any, tmp_path: Path) -> None:
    out = tmp_path / "library-admin"
    out.mkdir()
    (out / "SKILL.md").write_text("---\nname: library-admin\n---\nmine\n")
    with pytest.raises(SkillWriteError, match="not generated"):
        write_skill(render_skill(site_graph, name="library-admin"), out)


def test_folder_must_match_name(site_graph: Any, tmp_path: Path) -> None:
    with pytest.raises(SkillWriteError, match="named after the skill"):
        write_skill(render_skill(site_graph, name="library-admin"), tmp_path / "other")


@pytest.mark.parametrize("bad", ["../escape.md", "/etc/x.md", "a/../../x.md", "a\\b.md", ""])
def test_path_traversal_refused(tmp_path: Path, bad: str) -> None:
    bundle = SkillBundle(name="s", files={"SKILL.md": "x", bad: "evil"})
    with pytest.raises(SkillWriteError):
        write_skill(bundle, tmp_path / "s")
    assert not (tmp_path / "escape.md").exists()


@pytest.mark.skipif(os.name == "nt", reason="symlinks")
def test_symlinked_references_outside_refused(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "s"
    root.mkdir()
    (root / "references").symlink_to(outside)
    bundle = SkillBundle(name="s", files={"SKILL.md": "x", "references/a.b.md": "y"})
    with pytest.raises(SkillWriteError, match="outside"):
        write_skill(bundle, root)
    assert list(outside.iterdir()) == []
