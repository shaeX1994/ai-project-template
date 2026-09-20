---
description: 支付服务的领域规则。示例内容,采用模板时替换掉。
globs: services/payment-service/**, docs/modules/payment-service.md
alwaysApply: false
---

<!-- GENERATED FILE - do not edit. Source: .ai/  Regenerate: scripts/ai-sync -->

# payment-service

示例领域规则。本文件只在变更触及 `services/payment-service/**` 时加载 —— 这正是按目录加载的意义:
一个前端任务不必为读它付上下文代价。

## 不变量

- 金额用整数最小单位加币种代码表示。绝不用浮点。
- 支付的每次状态流转都是追加写。已结算记录绝不原地修改。
- 每次调用外部渠道都带幂等键,由支付单 id 派生。
- 重试要么幂等,要么不重试。

## 每次变更都要做

- 改支付状态机需要 ADR,并由 `owners` 里的人审查。
- 新接入渠道走既有的 provider 端口。渠道 SDK 的类型不得越进 domain 层。
- 金额运算的改动需要覆盖进位取舍和币种不匹配的属性测试。

## 禁止

- 读其他服务的数据库,包括用户服务。
- 记录渠道完整响应、卡信息,或任何形似卡号的值。
- 删除或改写账目行。更正用冲正分录。
