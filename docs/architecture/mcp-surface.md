# MCP 工具面(第三阶段,模板未实现)

## 这一层解决什么

Markdown 规则只能"建议"模型去更新 todo、去检查文档是否过期。模型可以不听,而且没有任何东西能发现它没听。
MCP 把这些动作变成真正的调用:工具要么被调用并返回结果,要么没被调用 —— 这是可观测的。

模板不实现 server,只把接口定下来,这样以后实现时不用重新设计。`.ai/config.yaml` 里 `mcp.enabled: false`。

## 为什么不现在做

- server 是要跑起来的进程,不是 `git pull` 就能用的骨架。
- 不是每个 harness 都说 MCP。规则层必须在没有 MCP 时也完整可用,否则就是给一部分工具留了空洞。
- 客户端配置(哪个工具怎么注册 server)本身又是一层适配,应该等规则层稳定之后再加。

## 接口契约

Server 名:`project-context`。按 MCP 规范([2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28))
暴露三类原语。

### Resources

只读,把项目状态暴露给模型,替代"把整份文档塞进上下文":

```text
project://config                  .ai/config.yaml 的解析结果
project://architecture            架构文档索引,不是正文
project://architecture/{domain}   单个领域的架构文档
project://module/{name}           单个模块文档
project://todo                    分层 todo 的聚合视图
project://rules/{path}            对给定路径生效的规则集合(按 applies_to 解析)
```

`project://rules/{path}` 是关键一条:它把"按目录加载规则"从各家工具各自的机制,变成一次统一查询。

### Tools

有副作用,必须收窄,每个都对应一个已有技能:

```text
project_create_todo        参数 level, item             -> 写入对应层的 todo 文件
project_update_todo        参数 level, item, state      -> 勾掉/上提/标记 dropped
project_update_document    参数 path, section, content  -> 只改指定小节
project_check_consistency  无参数                        -> 等价于 scripts/ai-check
project_get_impact         参数 changed_paths           -> 返回受影响的文档、规则、消费方
```

约束:

- `project_update_document` 只接受"路径 + 小节",不接受整篇替换。这在协议层面落实了
  `update-project-doc` 技能里"只改受影响小节"的规则。
- 不提供 `project_delete_*`。删除由人执行。
- 不暴露任何读取生产凭据或触达生产环境的工具。

### Prompts

把多步工作流固化成可调用的模板:

```text
implement_feature
modify_existing_feature
complete_iteration
review_architecture_impact
```

## 与技能层的关系

不是替代关系。技能描述判断和步骤,MCP 提供执行动作。一个技能在有 MCP 时调用工具,没有 MCP 时按
Markdown 里写的步骤手工做同样的事。两条路径的结果必须一致 —— 这是实现 server 时的验收标准。

## 安全

MCP 规范明确要求:工具即任意代码执行,工具描述在来源不可信时应视为不可信。因此:

- server 只在本仓库工作目录内读写,不接受绝对路径参数。
- 写操作遵守 `.ai/policies/` 里的 `enforcement: blocking` 约束,由 server 自己校验,不依赖模型自觉。
- `visibility: restricted` 的文档不通过任何 resource 暴露。
