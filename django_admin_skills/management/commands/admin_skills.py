"""``manage.py admin_skills`` — generate (or check) an Agent Skill from the admin.

    manage.py admin_skills --out .claude/skills/library-admin --app library
    manage.py admin_skills --out .claude/skills/library-admin --as-user ops-bot
    manage.py admin_skills --out .claude/skills/library-admin --check      # CI
    manage.py admin_skills --out .claude/skills --per-app --name admin     # admin-<app>/
    manage.py admin_skills --graph graph.json --out skills/library-admin   # no admin access

Without ``--as-user`` the skill describes the whole site (django-admin-graph's
system mode). With it, the graph — and therefore the skill — holds only what
that user's ModelAdmin permissions allow.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import PermissionDenied
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.utils.module_loading import import_string
from django_admin_graph.schema import AdminGraph
from django_admin_graph.schema import SchemaVersionError

from django_admin_skills import conf
from django_admin_skills.api import graph_for
from django_admin_skills.options import INTERFACES
from django_admin_skills.options import OptionsError
from django_admin_skills.render import SkillBundle
from django_admin_skills.render import render_skill
from django_admin_skills.render import render_skills_per_app
from django_admin_skills.writer import SkillWriteError
from django_admin_skills.writer import check_skill
from django_admin_skills.writer import write_skill

MAX_GRAPH_BYTES = 20 * 1024 * 1024


class Command(BaseCommand):
    help = "Generate an Agent Skill (SKILL.md + references/) from the Django admin graph."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--out",
            required=True,
            help="Skill folder, e.g. .claude/skills/library-admin (with --per-app: the parent).",
        )
        parser.add_argument(
            "--name",
            default=None,
            help="Skill name (default: the --out folder name; with --per-app the prefix, "
            "default 'admin').",
        )
        parser.add_argument(
            "--app",
            action="append",
            dest="apps",
            default=None,
            help="Only include this app label (repeatable).",
        )
        parser.add_argument(
            "--per-app", action="store_true", help="Write one skill per app: <out>/<name>-<app>/."
        )
        parser.add_argument(
            "--as-user",
            default=None,
            metavar="USERNAME",
            help="Build the skill with this user's admin permissions.",
        )
        parser.add_argument(
            "--graph",
            default=None,
            metavar="FILE",
            help="Render a saved django-admin-graph JSON file instead of building one.",
        )
        parser.add_argument(
            "--site",
            default=None,
            help="Dotted path to an AdminSite (default: django-admin-graph's ADMIN_SITE).",
        )
        parser.add_argument(
            "--interface",
            action="append",
            dest="interfaces",
            choices=INTERFACES,
            default=None,
            help="Document this API (repeatable; default: the INTERFACES setting).",
        )
        parser.add_argument(
            "--base-url",
            default=None,
            help="Bake this origin into the skill (default: read $DJANGO_ADMIN_URL at run time).",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="Write nothing; exit non-zero if the skill on disk is missing or stale.",
        )

    # ------------------------------------------------------------------ #
    def handle(self, *args: Any, **options: Any) -> None:
        try:
            skill_options = conf.get_options(
                interfaces=tuple(options["interfaces"]) if options["interfaces"] else None,
                base_url=options["base_url"],
            )
        except ImproperlyConfigured as exc:
            raise CommandError(str(exc)) from exc
        graph = self._graph(options)
        out = Path(options["out"])
        try:
            if options["per_app"]:
                bundles = render_skills_per_app(
                    graph,
                    prefix=options["name"] or "admin",
                    options=skill_options,
                    app_labels=options["apps"],
                )
                targets = [(b, out / b.name) for b in bundles]
            else:
                name = options["name"] or out.resolve().name
                bundle = render_skill(
                    graph, name=name, options=skill_options, app_labels=options["apps"]
                )
                targets = [(bundle, out)]
        except OptionsError as exc:
            raise CommandError(str(exc)) from exc
        if options["check"]:
            self._check(targets)
        else:
            self._write(targets)

    def _graph(self, options: dict[str, Any]) -> AdminGraph:
        if options["graph"]:
            if options["as_user"] or options["site"]:
                raise CommandError("--graph cannot be combined with --as-user or --site")
            path = Path(options["graph"])
            try:
                if path.stat().st_size > MAX_GRAPH_BYTES:
                    raise CommandError(f"{path} is larger than {MAX_GRAPH_BYTES} bytes")
                return AdminGraph.from_dict(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError, KeyError, TypeError, SchemaVersionError) as exc:
                raise CommandError(f"Cannot read graph {path}: {exc}") from exc
        site = self._site(options["site"])
        user = None
        if options["as_user"]:
            manager = get_user_model()._default_manager
            try:
                user = manager.get_by_natural_key(options["as_user"])
            except get_user_model().DoesNotExist as exc:
                raise CommandError(f"No user {options['as_user']!r}") from exc
        try:
            return graph_for(site=site, user=user, app_labels=options["apps"])
        except PermissionDenied as exc:
            raise CommandError(
                f"User {options['as_user']!r} cannot use this admin site: {exc}"
            ) from exc

    @staticmethod
    def _site(dotted: str | None) -> AdminSite | None:
        if not dotted:
            return None
        try:
            site = import_string(dotted)
        except ImportError as exc:
            raise CommandError(f"Cannot import admin site {dotted!r}: {exc}") from exc
        if not isinstance(site, AdminSite):
            raise CommandError(f"{dotted!r} is not an AdminSite")
        return site

    def _check(self, targets: list[tuple[SkillBundle, Path]]) -> None:
        problems = [f"{path}: {p}" for bundle, path in targets for p in check_skill(bundle, path)]
        if problems:
            for line in problems:
                self.stderr.write(line)
            raise CommandError(
                "Skill is out of date with the admin. Regenerate it with "
                "`manage.py admin_skills` (same options, without --check) and commit the result."
            )
        self.stdout.write(f"{len(targets)} skill(s) up to date.")

    def _write(self, targets: list[tuple[SkillBundle, Path]]) -> None:
        for bundle, path in targets:
            try:
                changed = write_skill(bundle, path)
            except SkillWriteError as exc:
                raise CommandError(str(exc)) from exc
            self.stdout.write(
                f"{bundle.name}: {len(bundle.files)} file(s) in {path}, {len(changed)} changed."
            )
