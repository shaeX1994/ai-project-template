"""Renderers. One per output type; each returns ({path: content}, {path: [sources]}).

The second dict maps every output path to the list of source files it actually
embeds, so the manifest records accurate per-file provenance rather than the
aggregate set of everything the renderer touched.
"""

from __future__ import annotations

import fnmatch

from .model import BANNER, may_embed, shift_headings
from .sections import SECTIONS
from .yamlmini import ConfigError


def _header(ws, title):
    lines = [f"# {title}", "", f"<!-- {BANNER} -->", "",
             f"项目:**{ws.project_name}**"]
    if ws.project_description:
        lines.append("")
        lines.append(ws.project_description)
    return "\n".join(lines) + "\n"


def _compose(ws, adapter, spec, title):
    parts = [_header(ws, title)]
    embedded = []
    for name in spec.get("sections") or []:
        builder = SECTIONS.get(name)
        if builder is None:
            raise ConfigError(
                f"adapter '{adapter['id']}' requests unknown section '{name}'")
        text, refs = builder(ws, adapter)
        if text.strip():
            parts.append(text)
        embedded.extend(refs)
    return "\n".join(parts), embedded


def single_file(ws, adapter, spec):
    path = spec.get("path")
    if not path:
        raise ConfigError(f"adapter '{adapter['id']}': single_file output needs a path")
    title = spec.get("title") or f"{ws.project_name} 项目规则"
    text, embedded = _compose(ws, adapter, spec, title)
    return {path: text}, {path: embedded}


def prompt_bundle(ws, adapter, spec):
    path = spec.get("path")
    title = spec.get("title") or f"{ws.project_name} 上下文包"
    text, embedded = _compose(ws, adapter, spec, title)
    intro = (
        "> 自包含上下文包。适用于没有项目配置文件约定的 harness:\n"
        "> 整段作为 system prompt 粘贴,或由 harness 加载。\n"
        f"> 由 `scripts/ai-sync` 生成,请勿手改。\n\n")
    head, _, rest = text.partition("\n\n")
    return {path: f"{head}\n\n{intro}{rest}"}, {path: embedded}


def skill_dir(ws, adapter, spec):
    """Copy skills as spec-compliant SKILL.md files into the target's skill directory."""
    base = spec.get("path")
    enabled = ws.enabled_skills()
    files, embeds = {}, {}
    for doc in ws.skills:
        if doc.name not in enabled:
            continue
        if not may_embed(doc, adapter):
            continue
        meta = [f"name: {doc.name}", f"description: {doc.description}"]
        for key in ("license", "compatibility", "allowed-tools"):
            if doc.meta.get(key):
                meta.append(f"{key}: {doc.meta[key]}")
        extra = doc.meta.get("metadata") or {}
        if extra:
            meta.append("metadata:")
            meta.extend(f"  {k}: \"{v}\"" for k, v in extra.items())
        front = "---\n" + "\n".join(meta) + "\n---\n"
        body = f"\n<!-- {BANNER} -->\n\n{doc.body.rstrip()}\n"
        path = f"{base}/{doc.name}/SKILL.md"
        files[path] = front + body
        embeds[path] = [doc.rel]
    return files, embeds


def mdc_rules(ws, adapter, spec):
    """One rule file per source document, scoped by glob in front matter."""
    base = spec.get("path")
    ext = spec.get("extension") or ".mdc"
    always_core = bool(spec.get("always_apply_core", True))
    files, embeds = {}, {}
    groups = [("core", ws.core, always_core), ("policy", ws.policies, always_core),
              ("domain", ws.projects, False)]
    for prefix, docs, always in groups:
        for doc in docs:
            if not may_embed(doc, adapter):
                continue
            globs = "" if always else ", ".join(doc.globs)
            front = ["---", f"description: {doc.description}",
                     f"globs: {globs}", f"alwaysApply: {str(always).lower()}", "---"]
            content = "\n".join(front) + f"\n\n<!-- {BANNER} -->\n\n{doc.body.rstrip()}\n"
            path = f"{base}/{prefix}-{doc.name}{ext}"
            files[path] = content
            embeds[path] = [doc.rel]
    return files, embeds


def instructions_dir(ws, adapter, spec):
    """Copilot-style per-path instruction files using applyTo front matter."""
    base = spec.get("path")
    files, embeds = {}, {}
    for doc in ws.projects:
        if not may_embed(doc, adapter):
            continue
        apply_to = ",".join(doc.globs) or "**"
        front = ["---", f"applyTo: \"{apply_to}\"", "---"]
        path = f"{base}/{doc.name}.instructions.md"
        files[path] = (
            "\n".join(front) + f"\n\n<!-- {BANNER} -->\n\n{doc.body.rstrip()}\n")
        embeds[path] = [doc.rel]
    return files, embeds


def nested_agents(ws, adapter, spec):
    """An AGENTS.md at each domain directory, for agents that load the nearest file.

    Only written where the directory already exists, so the template does not scatter
    stub files into service trees that have not been created yet.
    """
    files, embeds = {}, {}
    for doc in ws.projects:
        if not may_embed(doc, adapter):
            continue
        for glob in doc.globs:
            head = glob.split("**")[0].rstrip("/")
            if not head or not (ws.root / head).is_dir():
                continue
            body = shift_headings(doc.body.rstrip(), 0)
            path = f"{head}/AGENTS.md"
            files[path] = (
                f"# {doc.name}\n\n<!-- {BANNER} -->\n\n"
                f"本目录的领域规则。仓库级规则见根目录 `AGENTS.md`。\n\n{body}\n")
            embeds[path] = [doc.rel]
            break
    return files, embeds


RENDERERS = {
    "single_file": single_file,
    "prompt_bundle": prompt_bundle,
    "skill_dir": skill_dir,
    "mdc_rules": mdc_rules,
    "instructions_dir": instructions_dir,
    "nested_agents": nested_agents,
}


def plan(ws):
    """Return (files, owners, embeds) for every adapter in config."""
    files, owners, embeds = {}, {}, {}
    for adapter in ws.adapters():
        for spec in adapter.get("outputs") or []:
            kind = spec.get("type")
            renderer = RENDERERS.get(kind)
            if renderer is None:
                raise ConfigError(
                    f"adapter '{adapter['id']}': unknown output type '{kind}'. "
                    f"Known types: {', '.join(sorted(RENDERERS))}")
            produced, embedded = renderer(ws, adapter, spec)
            for path, content in produced.items():
                if path in files and files[path] != content:
                    raise ConfigError(
                        f"output collision on '{path}' between adapters "
                        f"'{owners[path]}' and '{adapter['id']}'")
                files[path] = content
                owners[path] = adapter["id"]
                # Per-file provenance: each renderer reports exactly which sources
                # that output embeds, so a restricted source is attributed only to
                # the files that genuinely contain it.
                embeds[path] = sorted(set(embedded.get(path) or []))
    return files, owners, embeds


def matches(path, globs):
    return any(fnmatch.fnmatch(path, g) for g in globs)
