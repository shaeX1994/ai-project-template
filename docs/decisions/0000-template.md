# NNNN. <决策标题>

- Status: proposed
- Date: YYYY-MM-DD
- Deciders: <人名或角色>
- Supersedes: <被取代的 ADR 编号,或 none>

## 背景

有哪些约束力在起作用?是什么约束、事故或需求让这个决策成为必要?写事实,不写偏好。

## 决策

一段话,主动语态。"我们将……"

## 后果

- 正面:<什么变容易了>
- 负面:<什么变难了,放弃了什么>
- 中性:<发生了变化但无明显好坏>

## 考虑过的备选方案

| 方案 | 为什么不选 |
| --- | --- |
| <方案> | <原因> |

## 迁移

现有代码和数据如何过渡到新状态,包含回滚路径。只有在确实无既有状态时才写 "n/a"。

<!--
Status 取值: proposed | accepted | superseded | rejected
文件名: NNNN-kebab-case-title.md,编号连续且绝不复用。
已 accepted 的 ADR 绝不改写,用新 ADR supersede 它。
scripts/ai-check 会校验数字前缀和 status 取值。
-->
