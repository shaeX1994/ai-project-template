---
name: review-api-change
description: 判定 API 或契约变更是兼容还是破坏性,破坏性变更必须先有迁移方案才能落地。当 schema、proto、OpenAPI 文档、handler 签名、响应结构或枚举发生变化时使用。Use when a contract changes.
metadata:
  x-template-version: "1"
---

<!-- GENERATED FILE - do not edit. Source: .ai/  Regenerate: scripts/ai-sync -->

# review-api-change

## 判定

除非能证明落在"兼容"一栏,否则按破坏性处理。

| 变更 | 判定 |
| --- | --- |
| 新增可选响应字段 | 兼容 |
| 新增带默认值的可选请求字段 | 兼容 |
| 新增接口 | 兼容 |
| 删除或重命名字段、接口、枚举值 | 破坏性 |
| 收窄类型、加严校验、把字段改为必填 | 破坏性 |
| 改动状态码、错误结构、分页、默认排序 | 破坏性 |
| 类型不变但字段含义变了 | 破坏性,且最难发现 |

## 输出契约

```markdown
- Verdict: compatible | breaking
- Consumers: <已知调用方,或 "unknown - 合并前必须查清">
- Contract diff: <字段级列表>
- Migration: <n/a,或两阶段方案>
- Recorded in: <ADR 路径,或版本说明位置>
```

## 破坏性变更怎么落

分两阶段:先上新增形式,迁移调用方,再用另一次独立变更删掉旧形式。决策记入 `docs/decisions/` 的 ADR。

## 禁止

- 从运行中的服务反推契约。去读 schema。
- 手改 `docs/apis/**`。从事实源重新生成。
