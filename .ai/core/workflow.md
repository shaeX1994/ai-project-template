---
name: workflow
description: 所有 agent 遵循的任务循环,以及 AI 配置如何重新生成。
visibility: public
applies_to:
  - "**/*"
---

# 工作流

## 任务循环

1. 按范围加载上下文:先读 `.ai/core/`,再读 `.ai/agents/` 里对应的角色文件,然后只读与本次要改的
   路径匹配的 `.ai/projects/<name>/rules.md`。
2. 复述任务和它的成功条件。有歧义就摆出来,不要默默选一个。
3. 超过单文件的变更,先跑 `create-plan` 技能。
4. 小步实现。第一处实质修改之后立刻做一次验证。
5. 结束前跑 `verify-before-complete` 技能。
6. 按 `todo.update_after_task` 的配置,用 `manage-todo` 技能更新待办;用 `update-project-doc`
   更新受影响的模块文档。

## 重新生成模型入口

面向模型的文件是生成的,不是手写的:

```bash
scripts/ai-sync            # 从 .ai/ 生成 AGENTS.md、CLAUDE.md、.cursor/rules 等
scripts/ai-sync --check    # 生成物过期就失败(CI 用)
scripts/ai-check           # 校验规则、todo、文档一致性
```

规则:

- 带 `GENERATED FILE` 标记的文件绝不手改。改 `.ai/` 下的源文件,然后重新跑 `scripts/ai-sync`。
- `.ai/manifest.yaml` 是锁文件,记录内容哈希,用于检测漂移。
- `.ai/` 和生成的入口文件放在同一个 commit 里提交。

## 升级到人工

以下情况停下来问人:

- 任务需要新增服务、数据存储或第三方依赖;
- `.ai/policies/` 里的策略与请求冲突;
- 变更涉及生产访问、认证授权或密钥。
