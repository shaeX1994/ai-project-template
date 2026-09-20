"""Workspace model: loads .ai/ into documents, adapters, and schemas."""

from __future__ import annotations

from pathlib import Path

from .yamlmini import ConfigError, digest, parse_yaml, read_text, split_front_matter

VISIBILITY_ORDER = {"public": 0, "internal": 1, "restricted": 2}
BANNER = "GENERATED FILE - do not edit. Source: .ai/  Regenerate: scripts/ai-sync"


class Doc:
    """A hand-written markdown document under .ai/ with YAML front matter."""

    def __init__(self, root, path, kind):
        self.root = root
        self.path = path
        self.kind = kind
        self.rel = path.relative_to(root).as_posix()
        self.meta, self.body = split_front_matter(read_text(path), self.rel)

    @property
    def name(self):
        return self.meta.get("name") or self.path.stem

    @property
    def description(self):
        return self.meta.get("description") or ""

    @property
    def visibility(self):
        return self.meta.get("visibility") or "public"

    @property
    def globs(self):
        value = self.meta.get("applies_to") or self.meta.get("scope") or []
        return value if isinstance(value, list) else [value]

    def list_field(self, key):
        value = self.meta.get(key) or []
        return value if isinstance(value, list) else [value]


class Workspace:
    """Everything hand-written under .ai/, plus the resolved adapter definitions."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.ai = self.root / ".ai"
        if not self.ai.is_dir():
            raise ConfigError(f"{self.root}: no .ai/ directory found")
        self.config = self._load_yaml(self.ai / "config.yaml")
        self.core = self._load_docs(".ai/core/*.md", "core")
        self.agents = self._load_docs(".ai/agents/*.md", "agent")
        self.policies = self._load_docs(".ai/policies/*.md", "policy")
        self.skills = self._load_docs(".ai/skills/*/SKILL.md", "skill")
        self.projects = self._load_docs(".ai/projects/*/rules.md", "project")
        index_path = self.ai / "skills" / "index.yaml"
        self.skill_index = self._load_yaml(index_path) if index_path.exists() else {}
        schema_path = self.ai / "schemas" / "documents.yaml"
        self.schemas = self._load_yaml(schema_path) if schema_path.exists() else {}

    def _load_yaml(self, path):
        if not path.exists():
            raise ConfigError(f"{path}: required file is missing")
        return parse_yaml(read_text(path), path.relative_to(self.root).as_posix()) or {}

    def _load_docs(self, pattern, kind):
        return [Doc(self.root, p, kind) for p in sorted(self.root.glob(pattern))]

    @property
    def project_name(self):
        return (self.config.get("project") or {}).get("name") or "unnamed-project"

    @property
    def project_description(self):
        return (self.config.get("project") or {}).get("description") or ""

    def adapter_ids(self):
        return self.config.get("adapters") or []

    def load_adapter(self, adapter_id):
        path = self.ai / "adapters" / f"{adapter_id}.yaml"
        if not path.exists():
            raise ConfigError(
                f".ai/config.yaml lists adapter '{adapter_id}' "
                f"but .ai/adapters/{adapter_id}.yaml does not exist")
        data = self._load_yaml(path)
        data.setdefault("id", adapter_id)
        return data

    def adapters(self):
        return [self.load_adapter(a) for a in self.adapter_ids()]

    def enabled_skills(self, role=None):
        """Return the set of skill names active for a given role (or project-wide).

        Resolution order:
        1. If skills.enabled is absent from config, all skills are enabled.
        2. If role is given and skills.role_overrides.<role>.enabled exists, use that.
        3. Otherwise use skills.enabled.
        """
        skill_cfg = self.config.get("skills") or {}
        project_enabled = skill_cfg.get("enabled")
        if project_enabled is None:
            # No enabled list → every skill that has a directory is active.
            return {d.name for d in self.skills}
        if role:
            overrides = (skill_cfg.get("role_overrides") or {}).get(role) or {}
            role_list = overrides.get("enabled")
            if role_list is not None:
                return set(role_list)
        return set(project_enabled)

    def skill_meta(self, name):
        for entry in self.skill_index.get("skills") or []:
            if entry.get("name") == name:
                return entry
        return {}

    def source_files(self):
        """Hand-written files that generated output depends on."""
        result = []
        for path in sorted(self.ai.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self.root).as_posix()
            if rel == ".ai/manifest.yaml" or rel.startswith(".ai/generated/"):
                continue
            result.append(path)
        return result

    def source_hash(self):
        parts = []
        for path in self.source_files():
            rel = path.relative_to(self.root).as_posix()
            parts.append(f"{rel}:{digest(read_text(path))}")
        return digest("\n".join(parts))


def may_embed(doc, adapter):
    """Restricted content is never embedded. Internal depends on the adapter."""
    level = VISIBILITY_ORDER.get(doc.visibility, 0)
    if level >= VISIBILITY_ORDER["restricted"]:
        return False
    ceiling = VISIBILITY_ORDER.get(adapter.get("max_visibility", "public"), 0)
    return level <= ceiling


def shift_headings(body, extra):
    """Demote markdown headings so an embedded document nests under its section."""
    if extra <= 0:
        return body
    out, in_fence = [], False
    for line in body.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
        elif not in_fence and stripped.startswith("#"):
            out.append("#" * extra + line)
            continue
        out.append(line)
    return "\n".join(out)
