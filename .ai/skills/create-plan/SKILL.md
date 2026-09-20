---
name: create-plan
description: 把任务转成可执行计划,包含范围、步骤、每步的验证命令和文档影响。当变更涉及多个文件、改动契约、或存在多种合理实现方式时使用。Use before any change touching more than one file or altering a contract.
metadata:
  x-template-version: "1"
---

# create-plan

## 何时使用

涉及多个文件、改动契约、或有多种合理实现的任务。单行修复不需要。

## 步骤

1. 用一句话复述任务,然后把成功条件写成可观测的东西:某个测试通过、某个接口返回 X、构建成功。
2. 确定范围。列出你要改的路径,并指明每个路径对应哪个 `.ai/projects/<name>/rules.md`。只加载这些。
3. 列出假设。如果某个假设错了会改变实现方式,就去问,不要往下走。
4. 拆成步骤,每步可独立验证,最小的先做。
5. 给每步写明验证命令。
6. 列出这次变更需要动的文档和 todo 条目。

## 输出契约

写入 `.ai/todo/current-task.md`:

```markdown
# Current task: <一句话>

- Success condition: <可观测条件>
- Scope: <路径> (rules: <项目规则文件>)
- Assumptions: <列表,或 none>

## Steps
- [ ] 1. <步骤> -> verify: <命令>
- [ ] 2. <步骤> -> verify: <命令>

## Doc impact
- <docs/modules/...,或 none>
```

## 禁止

- 计划没写完就开始改代码。
- 写进无法验证的步骤。
- 规划请求范围之外的工作。
