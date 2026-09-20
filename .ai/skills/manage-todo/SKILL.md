---
name: manage-todo
description: 读取、创建和更新分层 todo 文件,遵守 .ai/config.yaml 里的 todo mode。任务开始时、任务结束时,或用户询问当前在做什么、接下来做什么时使用。Use when starting or finishing a task.
metadata:
  x-template-version: "1"
---

# manage-todo

## 配置门禁

写任何东西之前先读 `.ai/config.yaml` 的 `todo` 段:

- `mode: off` — 不写,也不创建 todo 文件。
- `mode: ask` — 先给出改动方案,等确认。
- `mode: on` — 直接写。
- `prefer_existing: true` — 追加到已有文件,不另建一份平行的。
- `update_after_task: true` — 每个任务结束时执行本技能。

## 分层

| 文件 | 内容 | 时间跨度 |
| --- | --- | --- |
| `.ai/todo/roadmap.md` | 主题和里程碑 | 季度 |
| `.ai/todo/project.md` | 跨角色的项目级工作 | 周 |
| `.ai/todo/<role>.md` | 角色或领域范围内的工作 | 天 |
| `.ai/todo/current-task.md` | 当前唯一在做的任务 | 现在 |

每个条目只写在一层。如果一个条目同时属于两层,说明它太粗,拆开。

## 步骤

1. 写之前先读目标文件,不要凭记忆假设内容。
2. 任务开始时:确认 `current-task.md` 是空的,或者里面的任务就是当前这个。绝不静默覆盖在做的任务。
3. 任务结束时:勾掉完成项,把剩余项带原因上提一层,把 `current-task.md` 清回只剩标题。
4. 绝不静默删除条目。要么勾掉,要么上移,要么标 `dropped: <原因>`。
5. 每个改动的文件用一行报告变化。

## 禁止

- 在根目录建 `TODO.md`。分层文件是唯一的 todo 载体。
- 同一条目在两层重复出现。
- 给刚做完的事写一条待办。它应该记为已完成。
