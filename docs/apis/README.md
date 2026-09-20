# API 文档

**本目录是生成的,不要手改。**

`.ai/config.yaml` 里 `docs.api_docs_generated: true` 时,手改这里的文件属于违规,`ai-check` 会告警。

## 为什么

契约的事实源是代码或 schema(OpenAPI 文档、`.proto` 文件、类型定义)。手写的 API 文档必然和实现漂移,
而且模型会读到过期契约后按错的写代码 —— 这种错误比没有文档更难查。

## 怎么接

在项目的构建或 CI 里加一步生成,输出到本目录。常见形态:

```text
openapi.yaml / *.proto  ->  生成器  ->  docs/apis/<service>.md
```

生成的文件顶部应带一行标记,说明它是生成物和事实源路径,这样 `ai-check` 能识别。

## Agent 规则

- 调接口之前读这里的契约,不要从运行中的服务反推(见 `.ai/agents/frontend.md`)。
- 契约缺失时去要,不要猜。
- 契约要变,改事实源再重新生成,并走 `review-api-change` 技能。
