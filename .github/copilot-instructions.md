# Copilot instructions

<!-- GENERATED FILE - do not edit. Source: .ai/  Regenerate: scripts/ai-sync -->

项目:**example-platform**

Reference layout for a multi-agent, multi-model repository.

## 规则优先级

冲突时高优先级胜出:

```text
1. company-standards
2. project-standards
3. subproject-standards
4. module-standards
5. current-task
```

本文件是生成物。改规则请改 `.ai/` 下的源文件,然后执行 `scripts/ai-sync`。

## 统一规则

<!-- source: .ai/core/architecture.md -->
### 架构规则

#### 边界

- 服务独占自己的数据。不允许跨服务直连数据库读写。
- 跨服务通信走已发布的 API 或事件,不走共享表。
- 共享代码放进带版本的内部包,不靠复制粘贴。

#### 分层

服务内部依赖只能向内:

```text
transport (http / rpc / cli)
  -> application (用例)
    -> domain (实体、规则)
      <- infrastructure (db、cache、第三方) 实现 domain 定义的端口
```

- domain 层不 import transport 和 infrastructure 的任何东西。
- infrastructure 在组装根处注入,不在用例内部直接 new。

#### Agent 的变更规则

- 新增跨服务依赖,需要在 `docs/decisions/` 留一份 ADR。
- 改动公开 API 契约,落地前先走 `review-api-change` 技能。
- 引入新的数据存储、队列或第三方依赖,需要人工批准。
- 变更只涉及某一个服务时,只读该服务的 `.ai/projects/<service>/rules.md` 加本文件。不要加载无关领域。

#### 明确不做

- 不为假想需求预留抽象层。
- 一个函数能解决的问题,不引入框架。

<!-- source: .ai/core/coding-rules.md -->
### 编码规则

#### 范围纪律

- 只实现被要求的东西。
- 只改和任务直接相关的代码,不顺手重构。
- 只在本次变更导致 import、变量、辅助函数不再被使用时才删除它们。
- 选择能完整满足需求的最简方案。
- 不为假想的未来需求加抽象层、配置项或扩展点。

#### 风格

- 与周围文件保持一致:命名、错误处理、注释密度、import 顺序。
- 新建和修改的文件保持 UTF-8 无 BOM。
- 代码注释写英文,简洁,只在能提供有效上下文时才写。
- 不留注释掉的代码;不留在 `.ai/todo/` 里没有对应条目的 TODO 注释。

#### 正确性

- 在信任边界校验输入。
- 用参数化查询。绝不用字符串拼接构造 SQL。
- 固定依赖版本。
- 绝不记录密钥、token,或包含用户数据的完整请求体。

#### 验证底线

每次变更先声明成功条件,然后证明它:

| 变更类型 | 最低证明 |
| --- | --- |
| Bug 修复 | 先有失败的测试,修完通过 |
| 新功能 | 新路径的单元测试 + 构建通过 |
| 重构 | 既有测试通过,行为无差异 |
| 配置或基础设施 | 附上 dry run 或 plan 输出 |

如果当前环境跑不了构建或测试,明确说出来,不要声称成功。收口动作走 `verify-before-complete` 技能。

新增一条规则。

<!-- source: .ai/core/documentation.md -->
### 文档规则

#### 归属

| 路径 | 谁维护 | Agent 能否修改 |
| --- | --- | --- |
| `docs/architecture/` | architect 角色,按领域拆分 | 只能改受影响的那个领域文件 |
| `docs/modules/<module>.md` | 该模块的负责 agent | 可以,当模块内代码变更时 |
| `docs/apis/` | 从代码或 schema 生成 | 不可以,要重新生成 |
| `docs/decisions/` | ADR,只追加 | 只能新增,绝不改写历史 |

#### 硬性规则

- 不存在一份"全局设计文档"让 agent 随意重写。架构按领域拆分,这样一次变更的影响是局部且可审的。
- Agent 只更新自己这次变更真正触及的模块文档。
- API 文档是生成的。`.ai/config.yaml` 里 `docs.api_docs_generated` 为 true 时,手改 `docs/apis/` 属于违规。
- 重要架构决策写成 ADR,模板是 `docs/decisions/0000-template.md`。编号连续,状态取
  `proposed` / `accepted` / `superseded` / `rejected` 之一。

#### 验证

`scripts/ai-check` 会校验:

- `docs/**` 和 `.ai/**` 里的相对链接指向真实存在的文件;
- 每个 ADR 有数字前缀和合法状态;
- `.ai/config.yaml` 引用的文件都存在。

CI 跑同一个命令,所以坏链会让构建失败,而不是悄悄烂在那里。

<!-- source: .ai/core/workflow.md -->
### 工作流

#### 任务循环

1. 按范围加载上下文:先读 `.ai/core/`,再读 `.ai/agents/` 里对应的角色文件,然后只读与本次要改的
   路径匹配的 `.ai/projects/<name>/rules.md`。
2. 复述任务和它的成功条件。有歧义就摆出来,不要默默选一个。
3. 超过单文件的变更,先跑 `create-plan` 技能。
4. 小步实现。第一处实质修改之后立刻做一次验证。
5. 结束前跑 `verify-before-complete` 技能。
6. 按 `todo.update_after_task` 的配置,用 `manage-todo` 技能更新待办;用 `update-project-doc`
   更新受影响的模块文档。

#### 重新生成模型入口

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

#### 升级到人工

以下情况停下来问人:

- 任务需要新增服务、数据存储或第三方依赖;
- `.ai/policies/` 里的策略与请求冲突;
- 变更涉及生产访问、认证授权或密钥。

## 强制策略

- `.ai/policies/production-access.md` — 受限。生产环境与凭据处理规则,永不写入生成的模型入口文件。 (visibility: restricted, 正文未内联,需要时按角色打开该文件)
<!-- source: .ai/policies/release.md -->
### 发布策略

#### 门禁

以下条件全部成立,变更才可发布:

- 项目构建通过;
- 覆盖变更路径的测试通过,且 bug 修复有一个"修复前失败"的测试;
- `scripts/ai-check` 通过;
- `scripts/ai-sync --check` 通过,即生成的入口文件与 `.ai/` 一致;
- 受影响的 `docs/modules/*.md` 已更新;
- 没有未给出理由的新增依赖。

任何一项在当前环境无法评估,明确说出来,不要报成功。执行走 `verify-before-complete` 技能。

#### 分支与提交

- 在分支上开发,绝不直接推默认分支。
- `.ai/` 源文件和它生成的入口文件放同一个 commit。
- 只有人明确要求时才提交。

#### 破坏性变更

一律两阶段:先上新增形式,迁移调用方,再用独立变更删除旧形式。删列或改列名的迁移同样适用。决策记成 ADR。

#### 回滚

每个影响发布的变更都要写明怎么撤销。没有回滚路径的变更,落地前需要人工批准。

- `.ai/policies/security.md` — 本仓库所有变更的强制性安全约束。 (visibility: internal, 正文未内联,需要时按角色打开该文件)

> `enforcement: blocking` 的策略优先于任务要求。与策略冲突时停下来问人。

## 技能

技能是可复用的工作流。触发条件匹配时读取对应 `SKILL.md` 并按步骤执行:

| 技能 | 用途 | 适用范围 | 文件 |
| --- | --- | --- | --- |
| check-security | 对 diff 做限定范围的安全检查。当变更涉及认证、授权、输入解析、路径或文件处理、子进程调用、反序列化、密钥、依赖,或任何开放网络监听的地方时使用。Use when a change touches auth, input parsing, secrets, or network surface. | `**/*` | `.ai/skills/check-security/SKILL.md` |
| create-plan | 把任务转成可执行计划,包含范围、步骤、每步的验证命令和文档影响。当变更涉及多个文件、改动契约、或存在多种合理实现方式时使用。Use before any change touching more than one file or altering a contract. | `**/*` | `.ai/skills/create-plan/SKILL.md` |
| manage-todo | 读取、创建和更新分层 todo 文件,遵守 .ai/config.yaml 里的 todo mode。任务开始时、任务结束时,或用户询问当前在做什么、接下来做什么时使用。Use when starting or finishing a task. | `.ai/todo/**` | `.ai/skills/manage-todo/SKILL.md` |
| project-bootstrap | 在一个仓库里落地 .ai 配置体系:填写项目身份、用真实领域规则替换示例规则、生成各模型入口文件。接入新项目或新增服务时执行一次。Use once when onboarding a project or adding a new service. | `.ai/**` | `.ai/skills/project-bootstrap/SKILL.md` |
| review-api-change | 判定 API 或契约变更是兼容还是破坏性,破坏性变更必须先有迁移方案才能落地。当 schema、proto、OpenAPI 文档、handler 签名、响应结构或枚举发生变化时使用。Use when a contract changes. | `services/**/api/**`, `**/*.proto`, `**/openapi*.yaml`, `docs/apis/**` | `.ai/skills/review-api-change/SKILL.md` |
| update-project-doc | 只更新本次变更真正影响到的模块文档和架构文档,决策发生变化时新建 ADR。在功能、API、模块边界、配置或工作流发生变更后使用。绝不整体重写全局设计文档。Use after a feature, API, module boundary, or workflow change. | `docs/**` | `.ai/skills/update-project-doc/SKILL.md` |
| verify-before-complete | 在声称任务完成之前执行项目验证门禁:构建、测试、lint、ai-check 和配置漂移检测。每次变更结束时、以及在声称任何东西能工作之前使用。Use at the end of every change before claiming it works. | `**/*` | `.ai/skills/verify-before-complete/SKILL.md` |

## 领域规则(按目录加载)

**只加载与本次要改的路径匹配的那几行。** 不匹配的领域规则不要读,这是控制上下文长度和错误率的主要手段。

| 匹配路径 | 领域 | 规则文件 |
| --- | --- | --- |
| `services/payment-service/**` | payment-service | `.ai/projects/payment-service/rules.md` |
| `docs/modules/payment-service.md` | payment-service | `.ai/projects/payment-service/rules.md` |
| `services/user-service/**` | user-service | `.ai/projects/user-service/rules.md` |
| `docs/modules/user-service.md` | user-service | `.ai/projects/user-service/rules.md` |
