---
description: 与模型无关的架构约束,所有 agent 都必须遵守。
globs: 
alwaysApply: true
---

<!-- GENERATED FILE - do not edit. Source: .ai/  Regenerate: scripts/ai-sync -->

# 架构规则

## 边界

- 服务独占自己的数据。不允许跨服务直连数据库读写。
- 跨服务通信走已发布的 API 或事件,不走共享表。
- 共享代码放进带版本的内部包,不靠复制粘贴。

## 分层

服务内部依赖只能向内:

```text
transport (http / rpc / cli)
  -> application (用例)
    -> domain (实体、规则)
      <- infrastructure (db、cache、第三方) 实现 domain 定义的端口
```

- domain 层不 import transport 和 infrastructure 的任何东西。
- infrastructure 在组装根处注入,不在用例内部直接 new。

## Agent 的变更规则

- 新增跨服务依赖,需要在 `docs/decisions/` 留一份 ADR。
- 改动公开 API 契约,落地前先走 `review-api-change` 技能。
- 引入新的数据存储、队列或第三方依赖,需要人工批准。
- 变更只涉及某一个服务时,只读该服务的 `.ai/projects/<service>/rules.md` 加本文件。不要加载无关领域。

## 明确不做

- 不为假想需求预留抽象层。
- 一个函数能解决的问题,不引入框架。
