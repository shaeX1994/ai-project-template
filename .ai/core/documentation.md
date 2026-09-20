---
name: documentation
description: 规定 agent 可以写哪些文档,以及文档变更如何被验证。
visibility: public
applies_to:
  - "docs/**"
  - "**/*.md"
---

# 文档规则

## 归属

| 路径 | 谁维护 | Agent 能否修改 |
| --- | --- | --- |
| `docs/architecture/` | architect 角色,按领域拆分 | 只能改受影响的那个领域文件 |
| `docs/modules/<module>.md` | 该模块的负责 agent | 可以,当模块内代码变更时 |
| `docs/apis/` | 从代码或 schema 生成 | 不可以,要重新生成 |
| `docs/decisions/` | ADR,只追加 | 只能新增,绝不改写历史 |

## 硬性规则

- 不存在一份"全局设计文档"让 agent 随意重写。架构按领域拆分,这样一次变更的影响是局部且可审的。
- Agent 只更新自己这次变更真正触及的模块文档。
- API 文档是生成的。`.ai/config.yaml` 里 `docs.api_docs_generated` 为 true 时,手改 `docs/apis/` 属于违规。
- 重要架构决策写成 ADR,模板是 `docs/decisions/0000-template.md`。编号连续,状态取
  `proposed` / `accepted` / `superseded` / `rejected` 之一。

## 验证

`scripts/ai-check` 会校验:

- `docs/**` 和 `.ai/**` 里的相对链接指向真实存在的文件;
- 每个 ADR 有数字前缀和合法状态;
- `.ai/config.yaml` 引用的文件都存在。

CI 跑同一个命令,所以坏链会让构建失败,而不是悄悄烂在那里。
