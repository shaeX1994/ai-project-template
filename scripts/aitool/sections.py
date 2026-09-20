"""Section builders. Shared by every adapter so all targets get identical content."""

from __future__ import annotations

from .model import may_embed, shift_headings


def _rule_section(title, docs, adapter, level=2):
    """Embed each document's body, or leave a pointer when visibility forbids it."""
    lines = [f"{'#' * level} {title}", ""]
    embedded = []
    for doc in docs:
        if may_embed(doc, adapter):
            lines.append(f"<!-- source: {doc.rel} -->")
            lines.append(shift_headings(doc.body.rstrip(), level))
            lines.append("")
            embedded.append(doc.rel)
        else:
            lines.append(
                f"- `{doc.rel}` — {doc.description} "
                f"(visibility: {doc.visibility}, 正文未内联,需要时按角色打开该文件)")
    return "\n".join(lines).rstrip() + "\n", embedded


def precedence(ws, adapter):
    order = ws.config.get("precedence") or []
    lines = ["## 规则优先级", "", "冲突时高优先级胜出:", "", "```text"]
    lines.extend(f"{i}. {name}" for i, name in enumerate(order, 1))
    lines.append("```")
    lines.append("")
    lines.append("本文件是生成物。改规则请改 `.ai/` 下的源文件,然后执行 `scripts/ai-sync`。")
    return "\n".join(lines) + "\n", []


def core(ws, adapter):
    return _rule_section("统一规则", ws.core, adapter)


def policies(ws, adapter):
    text, embedded = _rule_section("强制策略", ws.policies, adapter)
    note = ("\n> `enforcement: blocking` 的策略优先于任务要求。与策略冲突时停下来问人。\n")
    return text + note, embedded


def agents(ws, adapter):
    lines = ["## Agent 角色", "",
             "按当前任务选一个角色,**动手前先完整读取该角色文件**:", "",
             "| 角色 | 职责 | 生效范围 | 文件 |", "| --- | --- | --- | --- |"]
    for doc in ws.agents:
        scope = ", ".join(f"`{g}`" for g in doc.globs) or "—"
        lines.append(f"| {doc.name} | {doc.description} | {scope} | `{doc.rel}` |")
    required = ws.config.get("required_agents") or []
    if required:
        lines.append("")
        lines.append("必须存在的角色:" + "、".join(f"`{r}`" for r in required))
    return "\n".join(lines) + "\n", []


def skills(ws, adapter, role=None):
    enabled = ws.enabled_skills(role)
    lines = ["## 技能", "",
             "技能是可复用的工作流。触发条件匹配时读取对应 `SKILL.md` 并按步骤执行:", "",
             "| 技能 | 用途 | 适用范围 | 文件 |", "| --- | --- | --- | --- |"]
    shown = 0
    for doc in ws.skills:
        if doc.name not in enabled:
            continue
        meta = ws.skill_meta(doc.name)
        applies = meta.get("applies_to") or []
        scope = ", ".join(f"`{g}`" for g in applies) or "—"
        lines.append(f"| {doc.name} | {doc.description} | {scope} | `{doc.rel}` |")
        shown += 1
    if shown == 0:
        lines.append("| — | 本项目未启用任何技能 | — | — |")
    return "\n".join(lines) + "\n", []


def projects(ws, adapter):
    if not ws.projects:
        return "", []
    lines = ["## 领域规则(按目录加载)", "",
             "**只加载与本次要改的路径匹配的那几行。** 不匹配的领域规则不要读,"
             "这是控制上下文长度和错误率的主要手段。", "",
             "| 匹配路径 | 领域 | 规则文件 |", "| --- | --- | --- |"]
    for doc in ws.projects:
        for glob in doc.globs:
            lines.append(f"| `{glob}` | {doc.name} | `{doc.rel}` |")
    return "\n".join(lines) + "\n", []


def todo(ws, adapter):
    cfg = ws.config.get("todo") or {}
    mode = cfg.get("mode", "ask")
    lines = ["## 待办策略", "",
             f"- 模式:`{mode}` " +
             {"on": "(直接写入)", "off": "(不要写待办文件)",
              "ask": "(先给出方案,等确认后再写)"}.get(mode, ""),
             f"- 优先使用已有文件:`{cfg.get('prefer_existing', True)}`",
             f"- 任务结束后更新:`{cfg.get('update_after_task', True)}`", "",
             "分层文件,一个条目只写在一层:", ""]
    for path in cfg.get("files") or []:
        lines.append(f"- `{path}`")
    lines.append("")
    lines.append("不要在仓库根目录创建 `TODO.md`。具体步骤见 `manage-todo` 技能。")
    return "\n".join(lines) + "\n", []


def skills(ws, adapter, role=None):
    enabled = ws.enabled_skills(role)
    lines = ["## 技能", "",
             "技能是可复用的工作流。触发条件匹配时读取对应 `SKILL.md` 并按步骤执行:", "",
             "| 技能 | 用途 | 适用范围 | 文件 |", "| --- | --- | --- | --- |"]
    shown = 0
    for doc in ws.skills:
        if doc.name not in enabled:
            continue
        meta = ws.skill_meta(doc.name)
        applies = meta.get("applies_to") or []
        scope = ", ".join(f"`{g}`" for g in applies) or "—"
        lines.append(f"| {doc.name} | {doc.description} | {scope} | `{doc.rel}` |")
        shown += 1
    if shown == 0:
        lines.append("| — | 本项目未启用任何技能 | — | — |")
    return "\n".join(lines) + "\n", []


SECTIONS = {
    "precedence": precedence,
    "core": core,
    "policies": policies,
    "agents": agents,
    "skills": skills,
    "projects": projects,
    "todo": todo,
}
