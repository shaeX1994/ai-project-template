---
description: 用户服务的领域规则。示例内容,采用模板时替换掉。
globs: services/user-service/**, docs/modules/user-service.md
alwaysApply: false
---

<!-- GENERATED FILE - do not edit. Source: .ai/  Regenerate: scripts/ai-sync -->

# user-service

示例领域规则,只在变更位于 `services/user-service/**` 下时加载。

## 不变量

- 用户 id 是不透明且稳定的。邮箱可变,绝不作主键。
- 邮箱唯一性由数据库约束保证,不只靠应用层代码。
- 密码材料用项目配置的 KDF 哈希。不自造密码学。
- 删除用户是软删除加计划清理,绝不立即硬删。

## 每次变更都要做

- 涉及认证或会话处理的改动,跑 `check-security` 技能。
- schema 变更按 expand-migrate-contract 分多次发布。
- 改动对外的用户表示结构时,跑 `review-api-change`。

## 禁止

- 在 API 响应里返回内部字段(哈希、token、审计列)。
- 记录邮箱、token 或密码材料。
- 跨服务 join。其他服务通过已发布的 API 或事件消费。
