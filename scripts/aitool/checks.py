"""Validators for ai-check. Each takes (workspace, report) and records findings."""

from __future__ import annotations

import re

from .model import VISIBILITY_ORDER, BANNER
from .yamlmini import ConfigError, digest, read_text

SCHEMA_VERSION = 1
ADR_NAME = re.compile(r"^\d{4}-[a-z0-9]+(-[a-z0-9]+)*\.md$")
ADR_STATUS = re.compile(r"^-\s*Status:\s*(\S+)", re.MULTILINE)
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")
VALID_STATUS = {"proposed", "accepted", "superseded", "rejected"}


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, message):
        self.errors.append(f"{where}: {message}")

    def warn(self, where, message):
        self.warnings.append(f"{where}: {message}")


def check_schema(ws, report):
    version = ws.config.get("schema_version")
    if version != SCHEMA_VERSION:
        report.error(".ai/config.yaml",
                     f"schema_version is {version!r}, this tool supports {SCHEMA_VERSION}")
    for key in ("project", "precedence", "adapters"):
        if not ws.config.get(key):
            report.error(".ai/config.yaml", f"missing required key '{key}'")
    if ws.project_name == "example-platform":
        report.warn(".ai/config.yaml",
                    "project.name is still the template placeholder 'example-platform'")


def check_front_matter(ws, report):
    types = (ws.schemas.get("types") or {})
    levels = ws.schemas.get("visibility_levels") or list(VISIBILITY_ORDER)
    groups = {"core": ws.core, "agent": ws.agents, "policy": ws.policies,
              "skill": ws.skills, "project": ws.projects}
    for kind, docs in groups.items():
        rules = types.get(kind)
        if not rules:
            continue
        required = rules.get("required") or []
        allowed = set(required) | set(rules.get("optional") or [])
        for doc in docs:
            for field in required:
                if not doc.meta.get(field):
                    report.error(doc.rel, f"front matter missing required '{field}'")
            if rules.get("strict"):
                for field in doc.meta:
                    if field not in allowed:
                        report.error(doc.rel, (
                            f"front matter field '{field}' is not allowed by the Agent "
                            f"Skills specification; move it to .ai/skills/index.yaml"))
            if "visibility" in required and doc.visibility not in levels:
                report.error(doc.rel, f"visibility '{doc.visibility}' is not one of {levels}")
            for field, values in (rules.get("enum") or {}).items():
                actual = doc.meta.get(field)
                if actual and actual not in values:
                    report.error(doc.rel, f"{field} '{actual}' is not one of {values}")
            _check_constraints(doc, rules.get("constraints") or {}, report)


def _check_constraints(doc, constraints, report):
    if constraints.get("name_matches_dir") and doc.name != doc.path.parent.name:
        report.error(doc.rel,
                     f"name '{doc.name}' must equal the directory '{doc.path.parent.name}'")
    pattern = constraints.get("name_pattern")
    if pattern and not re.fullmatch(pattern, str(doc.name)):
        report.error(doc.rel, f"name '{doc.name}' does not match {pattern}")
    for field, key in (("name", "name_max"), ("description", "description_max")):
        limit = constraints.get(key)
        if limit and len(str(doc.meta.get(field) or "")) > int(limit):
            report.error(doc.rel, f"{field} exceeds {limit} characters")


def check_required(ws, report):
    names = {d.name for d in ws.agents}
    for required in ws.config.get("required_agents") or []:
        if required not in names:
            report.error(".ai/config.yaml",
                         f"required_agents lists '{required}' but .ai/agents/ has no such file")
    skill_names = {d.name for d in ws.skills}
    enabled = ws.enabled_skills()

    # required_skills must appear in skills.enabled (if that field exists).
    skill_cfg = ws.config.get("skills") or {}
    has_enabled_list = skill_cfg.get("enabled") is not None
    for required in ws.config.get("required_skills") or []:
        if required not in skill_names:
            report.error(".ai/config.yaml",
                         f"required_skills lists '{required}' but .ai/skills/ has no such directory")
        elif has_enabled_list and required not in enabled:
            report.error(".ai/config.yaml",
                         f"required_skills lists '{required}' but it is not in skills.enabled "
                         f"— required skills cannot be disabled")

    # skills.enabled entries must have a matching directory.
    if has_enabled_list:
        for name in skill_cfg.get("enabled") or []:
            if name not in skill_names:
                report.error(".ai/config.yaml",
                             f"skills.enabled lists '{name}' but .ai/skills/ has no such directory")
        # role_overrides entries must also exist.
        for role, overrides in (skill_cfg.get("role_overrides") or {}).items():
            for name in (overrides or {}).get("enabled") or []:
                if name not in skill_names:
                    report.error(".ai/config.yaml",
                                 f"skills.role_overrides.{role}.enabled lists '{name}' "
                                 f"but .ai/skills/ has no such directory")

    indexed = {e.get("name") for e in (ws.skill_index.get("skills") or [])}
    for missing in sorted(skill_names - indexed):
        report.error(".ai/skills/index.yaml", f"skill '{missing}' is not listed")
    for extra in sorted(indexed - skill_names):
        report.error(".ai/skills/index.yaml", f"lists '{extra}' but the directory is missing")


def check_references(ws, report):
    skill_names = {d.name for d in ws.skills}
    agent_names = {d.name for d in ws.agents}
    for doc in ws.agents:
        for field in ("loads", "policies"):
            for ref in doc.list_field(field):
                if not (ws.root / ref).exists():
                    report.error(doc.rel, f"{field} references missing file '{ref}'")
        for skill in doc.list_field("skills"):
            if skill not in skill_names:
                report.error(doc.rel, f"skills references unknown skill '{skill}'")
    for entry in ws.skill_index.get("skills") or []:
        for agent in entry.get("agents") or []:
            if agent not in agent_names:
                report.error(".ai/skills/index.yaml",
                             f"skill '{entry.get('name')}' references unknown agent '{agent}'")


def check_adapters(ws, report):
    for adapter_id in ws.adapter_ids():
        try:
            adapter = ws.load_adapter(adapter_id)
        except ConfigError as exc:
            report.error(".ai/config.yaml", str(exc))
            continue
        if not adapter.get("outputs"):
            report.error(f".ai/adapters/{adapter_id}.yaml", "declares no outputs")
        level = adapter.get("max_visibility", "public")
        if level not in VISIBILITY_ORDER:
            report.error(f".ai/adapters/{adapter_id}.yaml",
                         f"max_visibility '{level}' is invalid")


def check_freshness(ws, report):
    from .cli import read_manifest
    manifest_path = ws.ai / "manifest.yaml"
    if not manifest_path.exists():
        report.error(".ai/manifest.yaml", "missing, run scripts/ai-sync")
        return
    manifest = read_manifest(ws)
    if manifest.get("source_hash") != ws.source_hash():
        report.error(".ai/manifest.yaml",
                     "stale: .ai/ changed since the last sync, run scripts/ai-sync")
    for entry in manifest.get("outputs") or []:
        path = ws.root / entry["path"]
        if not path.exists():
            report.error(entry["path"], "listed in the manifest but missing on disk")
        elif digest(read_text(path)) != entry.get("hash"):
            report.error(entry["path"],
                         "hand-edited or stale; edit .ai/ and run scripts/ai-sync")


def check_visibility(ws, report):
    from .cli import read_manifest
    if not (ws.ai / "manifest.yaml").exists():
        return
    by_rel = {d.rel: d for d in ws.core + ws.policies + ws.projects + ws.skills}
    for entry in read_manifest(ws).get("outputs") or []:
        for source in entry.get("embeds") or []:
            doc = by_rel.get(source)
            if doc is not None and doc.visibility == "restricted":
                report.error(entry["path"],
                             f"embeds restricted source '{source}'")


def check_generated_banner(ws, report):
    from .cli import read_manifest
    if not (ws.ai / "manifest.yaml").exists():
        return
    for entry in read_manifest(ws).get("outputs") or []:
        path = ws.root / entry["path"]
        if path.exists() and BANNER not in read_text(path):
            report.warn(entry["path"], "generated output lost its GENERATED FILE banner")


def check_links(ws, report):
    if not (ws.config.get("docs") or {}).get("check_links", True):
        return
    for base in (".ai", "docs"):
        root = ws.root / base
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.md")):
            rel = path.relative_to(ws.root).as_posix()
            try:
                text = read_text(path)
            except ConfigError as exc:
                report.error(rel, str(exc))
                continue
            for target in MD_LINK.findall(text):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                if not (path.parent / target).resolve().exists():
                    report.error(rel, f"broken relative link '{target}'")


def check_adrs(ws, report):
    folder = (ws.config.get("docs") or {}).get("decisions_dir", "docs/decisions")
    root = ws.root / folder
    if not root.is_dir():
        report.warn(folder, "decisions_dir does not exist")
        return
    seen = {}
    for path in sorted(root.glob("*.md")):
        name = path.name
        if not ADR_NAME.match(name):
            report.error(f"{folder}/{name}",
                         "filename must be NNNN-kebab-case-title.md")
            continue
        number = name[:4]
        if number in seen and number != "0000":
            report.error(f"{folder}/{name}", f"duplicate ADR number, also {seen[number]}")
        seen[number] = name
        if number == "0000":
            continue
        match = ADR_STATUS.search(read_text(path))
        if not match:
            report.error(f"{folder}/{name}", "missing '- Status: <value>' line")
        elif match.group(1).lower() not in VALID_STATUS:
            report.error(f"{folder}/{name}",
                         f"status '{match.group(1)}' not in {sorted(VALID_STATUS)}")


def check_todo(ws, report):
    cfg = ws.config.get("todo") or {}
    mode = cfg.get("mode", "ask")
    if mode not in ("on", "off", "ask"):
        report.error(".ai/config.yaml", f"todo.mode '{mode}' must be on, off, or ask")
    for rel in cfg.get("files") or []:
        if not (ws.root / rel).exists():
            report.error(".ai/config.yaml", f"todo.files lists missing file '{rel}'")
    if (ws.root / "TODO.md").exists():
        report.warn("TODO.md",
                    "root TODO.md conflicts with the layered .ai/todo/ files")


def check_encoding(ws, report):
    for base in (".ai", "docs", "scripts"):
        root = ws.root / base
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix in (".md", ".yaml", ".yml", ".py"):
                try:
                    read_text(path)
                except ConfigError as exc:
                    report.error(path.relative_to(ws.root).as_posix(), str(exc))


def check_api_docs(ws, report):
    docs = ws.config.get("docs") or {}
    if not docs.get("api_docs_generated"):
        return
    root = ws.root / docs.get("apis_dir", "docs/apis")
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*.md")):
        if path.name == "README.md":
            continue
        text = read_text(path).lower()
        if "generated" not in text.split("\n\n")[0]:
            report.warn(path.relative_to(ws.root).as_posix(),
                        "api_docs_generated is true but the file has no generated marker")


ALL_CHECKS = [check_schema, check_front_matter, check_required, check_references,
              check_adapters, check_freshness, check_visibility, check_generated_banner,
              check_links, check_adrs, check_todo, check_encoding, check_api_docs]
