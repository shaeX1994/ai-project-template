---
name: update-project-doc
description: "只更新本次变更真正影响到的模块文档和架构文档,决策发生变化时新建 ADR。在功能、API、模块边界、配置或工作流发生变更后使用。绝不整体重写全局设计文档。Use after a feature, API, module boundary, or workflow change."
metadata:
  x-template-version: "1"
---

<!-- GENERATED FILE - do not edit. Source: .ai/  Regenerate: scripts/ai-sync -->

# update-project-doc

## 范围规则

把变更路径映射到文档,只改映射到的那些:

```text
services/<svc>/**     -> docs/modules/<svc>.md
apps/web/**           -> docs/modules/web.md
跨服务变更             -> docs/architecture/<domain>.md + 新 ADR
schema 或接口变更       -> 重新生成 docs/apis/,不手改
```

如果一个变更映射不到任何文档,就什么都不加。

## 步骤

1. 检查变更的文件,列出路径。
2. 用上面的表把路径映射到文档。
3. 改之前先读目标文档的当前内容。
4. 只更新被这次变更作废的小节。其余部分逐字节保持不变,这样 diff 才可审。
5. 如果决策发生了变化,用 `docs/decisions/0000-template.md` 新建 `docs/decisions/NNNN-<slug>.md`。
   已 accepted 的 ADR 绝不修改,只能被新 ADR supersede。
6. 执行 `scripts/ai-check` 校验链接和 ADR 格式。
7. 报告改了哪些文档的哪些小节。

## 硬性限制

- `docs.api_docs_generated` 为 true 时不得手改 `docs/apis/**`,要重新生成。
- 不得新建顶层设计文档。
- 不得借着改一处的机会顺手重写整篇文档。
