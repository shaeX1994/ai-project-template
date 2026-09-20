"""Commands: sync, check, init."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from .checks import ALL_CHECKS, Report
from .model import BANNER, Workspace
from .render import plan
from .yamlmini import (ConfigError, digest, normalize, parse_yaml, read_text,
                       write_text)

COPY_TREES = (".ai", "docs", "scripts")
SKIP_NAMES = {"__pycache__", ".git", ".pytest_cache"}
UPDATE_TREES = (".ai/core", ".ai/skills", ".ai/schemas", ".ai/adapters", "scripts")


def read_manifest(ws):
    path = ws.ai / "manifest.yaml"
    if not path.exists():
        return {}
    return parse_yaml(read_text(path), ".ai/manifest.yaml") or {}


def render_manifest(ws, files, owners, embeds):
    lines = ["# Lockfile written by scripts/ai-sync. Do not edit by hand.",
             "# source_hash covers every hand-written file under .ai/, so ai-check can tell",
             "# whether the generated entry points still match their source.",
             "schema_version: 1",
             f"project: {ws.project_name}",
             f"source_hash: {ws.source_hash()}",
             f"adapters: [{', '.join(ws.adapter_ids())}]",
             "outputs:"]
    for path in sorted(files):
        lines.append(f"  - path: {path}")
        lines.append(f"    adapter: {owners[path]}")
        lines.append(f"    hash: {digest(files[path])}")
        refs = embeds.get(path) or []
        if refs:
            lines.append("    embeds:")
            lines.extend(f"      - {ref}" for ref in refs)
    return "\n".join(lines) + "\n"


def cmd_sync(ws, check_only=False):
    files, owners, embeds = plan(ws)
    previous = read_manifest(ws)
    planned = set(files)
    orphans = [e["path"] for e in previous.get("outputs") or []
               if e["path"] not in planned]

    changed, missing = [], []
    for path, content in sorted(files.items()):
        target = ws.root / path
        if not target.exists():
            missing.append(path)
        elif normalize(read_text(target)) != normalize(content):
            changed.append(path)

    if check_only:
        stale = previous.get("source_hash") != ws.source_hash()
        for path in missing:
            print(f"missing:  {path}")
        for path in changed:
            print(f"outdated: {path}")
        for path in orphans:
            print(f"orphan:   {path}")
        if stale:
            print("outdated: .ai/manifest.yaml")
        if missing or changed or orphans or stale:
            print("\n生成物与 .ai/ 不一致,执行 scripts/ai-sync")
            return 1
        print(f"生成物与 .ai/ 一致({len(files)} 个文件)")
        return 0

    for path, content in files.items():
        write_text(ws.root / path, content)
    for path in orphans:
        target = ws.root / path
        # Only remove files this tool generated, identified by the banner.
        if target.exists() and BANNER in read_text(target):
            target.unlink()
            print(f"removed:  {path}")
    write_text(ws.ai / "manifest.yaml", render_manifest(ws, files, owners, embeds))
    for path in sorted(missing + changed):
        print(f"wrote:    {path}")
    print(f"\n{len(files)} 个文件已生成,{len(ws.adapter_ids())} 个适配器,"
          f"manifest 已更新")
    return 0


def cmd_check(ws):
    report = Report()
    for check in ALL_CHECKS:
        try:
            check(ws, report)
        except ConfigError as exc:
            report.error(check.__name__, str(exc))
    for warning in report.warnings:
        print(f"warning: {warning}")
    for error in report.errors:
        print(f"error:   {error}")
    if report.errors:
        print(f"\n失败:{len(report.errors)} 个错误,{len(report.warnings)} 个告警")
        return 1
    print(f"\n通过:0 个错误,{len(report.warnings)} 个告警")
    return 0


def _iter_template_files(source):
    for tree in COPY_TREES:
        base = source / tree
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(source)
            if any(part in SKIP_NAMES for part in rel.parts):
                continue
            if rel.as_posix() in (".ai/manifest.yaml",) or ".ai/generated/" in rel.as_posix():
                continue
            yield rel


def cmd_init(args):
    source = Path(__file__).resolve().parents[2]
    target = Path(args.target).resolve() if args.target else source
    added, skipped, updated = [], [], []

    # --update only refreshes the template-owned trees, and config.yaml is not one of
    # them. Without it the copy leaves no manifest behind, so fail with the actual
    # reason instead of the misleading "missing after copy" error below.
    if args.update and not (target / ".ai" / "config.yaml").exists():
        raise ConfigError(
            f"{target}: --update refreshes an existing .ai/ setup, but there is no "
            f".ai/config.yaml there. Drop --update for a first-time adoption, or point "
            f"--update at a project that already has one.")

    for rel in _iter_template_files(source):
        src, dst = source / rel, target / rel
        if src == dst:
            continue
        # --update only touches template-owned trees. Outside them a missing file is
        # either user-owned or a deliberately deleted example, so leave it alone.
        if args.update and not _in_update_scope(rel):
            continue
        if dst.exists():
            if args.update or args.force:
                if normalize(read_text(src)) != normalize(read_text(dst)):
                    write_text(dst, read_text(src))
                    updated.append(rel.as_posix())
            else:
                skipped.append(rel.as_posix())
            continue
        write_text(dst, read_text(src))
        added.append(rel.as_posix())

    config = target / ".ai" / "config.yaml"
    if not config.exists():
        raise ConfigError(f"{config}: missing after copy, cannot initialise")
    if args.name:
        set_project_fields(config, args.name, args.description, args.repo_url)
    if args.adapters:
        set_adapters(config, [a.strip() for a in args.adapters.split(",") if a.strip()])
    removed = drop_examples(target, config) if args.drop_examples else []

    print(f"目标目录: {target}")
    print(f"新增 {len(added)} 个文件,更新 {len(updated)} 个,跳过 {len(skipped)} 个已存在文件")
    for rel in removed:
        print(f"removed:  {rel}")
    if skipped and not args.update:
        print("跳过的文件未被改动。需要覆盖请加 --force,只刷新模板自带部分请加 --update")
    if args.no_sync:
        return 0
    return cmd_sync(Workspace(target))


def _in_update_scope(rel):
    text = rel.as_posix()
    return any(text.startswith(tree + "/") for tree in UPDATE_TREES)


def set_project_fields(config, name, description, repo_url):
    """Rewrite project.* in place, preserving comments and key order."""
    lines = read_text(config).splitlines()
    fields = {"name": name, "description": description, "repo_url": repo_url}
    inside = False
    for index, line in enumerate(lines):
        if line.startswith("project:"):
            inside = True
            continue
        if inside:
            if line and not line.startswith(("  ", "\t")):
                break
            key = line.strip().split(":", 1)[0]
            if key in fields and fields[key]:
                value = str(fields[key]).replace('"', "'")
                lines[index] = f'  {key}: "{value}"'
    write_text(config, "\n".join(lines) + "\n")


def set_adapters(config, adapters):
    lines = read_text(config).splitlines()
    out, inside, done = [], False, False
    for line in lines:
        if line.startswith("adapters:"):
            inside, done = True, True
            out.append("adapters:")
            out.extend(f"  - {a}" for a in adapters)
            continue
        if inside:
            if line.startswith("  - ") or not line.strip():
                if not line.strip():
                    inside = False
                    out.append(line)
                continue
            inside = False
        out.append(line)
    if not done:
        raise ConfigError(f"{config}: no 'adapters:' block found")
    write_text(config, "\n".join(out) + "\n")


def drop_examples(target, config):
    data = parse_yaml(read_text(config), "config.yaml") or {}
    removed = []
    for rel in (data.get("template") or {}).get("examples") or []:
        path = target / rel
        if path.is_dir():
            shutil.rmtree(path)
            removed.append(rel)
        elif path.exists():
            path.unlink()
            removed.append(rel)
    return removed


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ai", description="AI configuration toolchain")
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    sub = parser.add_subparsers(dest="command", required=True)

    sync = sub.add_parser("sync", help="generate model entry points from .ai/")
    sync.add_argument("--check", action="store_true",
                      help="report drift and exit non-zero instead of writing")

    sub.add_parser("check", help="validate rules, docs, and todo consistency")

    init = sub.add_parser("init", help="adopt the template in a project")
    init.add_argument("target", nargs="?", help="target directory (default: template root)")
    init.add_argument("--name", help="project name written into .ai/config.yaml")
    init.add_argument("--description", default="", help="project description")
    init.add_argument("--repo-url", default="", help="repository URL")
    init.add_argument("--adapters", help="comma separated adapter ids to enable")
    init.add_argument("--drop-examples", action="store_true",
                      help="remove the example rules and docs listed in template.examples")
    init.add_argument("--update", action="store_true",
                      help="refresh template-owned files (core, skills, schemas, adapters, scripts)")
    init.add_argument("--force", action="store_true", help="overwrite every existing file")
    init.add_argument("--no-sync", action="store_true", help="skip generation afterwards")

    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            if not args.name and not args.update:
                parser.error("init requires --name (or --update for an existing project)")
            return cmd_init(args)
        workspace = Workspace(args.root)
        if args.command == "sync":
            return cmd_sync(workspace, check_only=args.check)
        return cmd_check(workspace)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
