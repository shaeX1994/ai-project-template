# AI 工程配置模板

一个仓库里同时用 Claude Code、Cursor、Copilot、Codex 等多个 AI 工具时,每个工具都要有自己的规则文件:
`CLAUDE.md`、`.cursor/rules/`、`.github/copilot-instructions.md`……过去要么维护八份互相矛盾的副本,要么
只有一个工具拿到了完整规则。

这个模板把规则收敛成 **`.ai/` 下的一份事实源**,再由工具生成各家的入口文件。你只维护 `.ai/`,改完跑一条
命令,31 个入口文件全部同步。

```text
.ai/core/          与模型无关的统一规则 ─┐
.ai/policies/      强制约束(带分级)      ├─→ 适配器 ─→ AGENTS.md / CLAUDE.md / GEMINI.md
.ai/agents/        角色定义               │           .cursor/rules/*.mdc
.ai/skills/        可复用工作流           │           .github/copilot-instructions.md
.ai/projects/      领域局部规则           │           .claude/skills/*/SKILL.md
.ai/adapters/      每个工具生成什么形态 ──┘           .ai/generated/*.md
                    ↑                                            ↑
              你维护这里                                  ai-sync 生成,不要手改
```

## 前置要求

**Python 3.8+**。没有第三方依赖,不需要 Node,不需要 `pip install`。

## 快速开始

### 新项目

```bash
git clone <this-repo> my-app && cd my-app
rm -rf .git && git init
python scripts/ai.py init . --name "my-app" --drop-examples
```

`init` 会填好项目身份、删掉示例规则、生成全部入口文件。**不要加 `--update`**——那是给已有 `.ai/`
的项目刷新模板自带部分的,在还没有 `.ai/` 的目录上会直接报错。

### 接入已有项目(只加文件,不动业务代码)

```bash
git clone <this-repo> ~/ai-template
cd /path/to/existing-project
python ~/ai-template/scripts/ai.py init . --name "existing-project" --drop-examples
```

### 模板升级后回灌

只刷新 `core`/`skills`/`schemas`/`adapters`/`scripts`,不碰你的 `config.yaml`、`agents/`、
`policies/`、`projects/`、`todo/`:

```bash
python ~/ai-template/scripts/ai.py init /path/to/project --update
```

### 日常两个命令

```bash
scripts/ai-sync          # 改完 .ai/ 后重新生成入口文件(Windows: scripts\ai-sync.ps1)
scripts/ai-check         # 校验规则、文档链接、ADR、todo、编码
scripts/ai-sync --check  # CI 用:生成物过期就失败
```

`ai-sync` 是**唯一会写盘**的命令。`ai-check` 和 `ai-sync --check` 只报告不修改。

## 初始化必须先于打开 AI CLI

**是的,而且这一点很重要。** `init` 和 `ai-sync` 必须在第一次在项目里启动 Claude Code 之前跑完。

原因:CLI 在**会话启动那一刻**读取入口文件。`CLAUDE.md` 在整个会话里只加载一次——如果你的项目还没有
这个文件,或者内容还是模板占位符,那个会话就是空载的。之后再 `ai-sync` 也没用,**已经开着的会话不会
重新读取**,你得退出重启。

正确的顺序:

```bash
cd my-app
python scripts/ai.py init . --name "my-app" --drop-examples   # 先物化入口文件
python scripts/ai.py check                                    # 确认通过
claude                                                        # 再打开 CLI
```

后续每次改完 `.ai/`,同样先 `ai-sync` 再重启会话。会话中途改了规则,当前会话用不到新规则。

## 目录结构

```text
.ai/
├── core/           与模型无关的统一规则(架构/编码/文档/工作流)
├── agents/         角色定义:architect / reviewer / backend / frontend
├── skills/         可复用技能,SKILL.md 遵循 Agent Skills 规范
│   └── index.yaml  技能的路由元数据(规范外的字段放这里)
├── projects/       子项目规则,按 applies_to glob 匹配目录时才加载
├── policies/       强制约束,带 enforcement 和 visibility
├── schemas/        front matter 契约,ai-check 据此校验
├── adapters/       每个工具一个文件,决定生成什么形态
├── generated/      无配置文件约定的 harness 用的上下文包
├── config.yaml     项目身份、优先级、todo 策略、启用的适配器
└── manifest.yaml   锁文件,记录内容哈希用于漂移检测

docs/
├── architecture/   按领域拆分,没有单一全局设计文档
├── modules/        每个模块一份
├── apis/           从代码或 schema 生成,不手改
├── decisions/      ADR,只追加
└── skill-config.html   技能开关配置页,拨完复制 YAML 贴回 config.yaml

scripts/
├── ai.py           命令行入口(sync / check / init)
├── ai-sync  ai-check        POSIX 启动器
├── ai-sync.ps1  ai-check.ps1  Windows 启动器
└── aitool/         实现:model / render / sections / checks / yamlmini
```

生成物(已提交,不要手改):

```text
AGENTS.md  CLAUDE.md  GEMINI.md
.cursor/rules/  .windsurf/rules/  .github/copilot-instructions.md
.github/instructions/  .claude/skills/  .ai/generated/
```

## 新人接入清单

模板是给机器读的,但接入是给人做的。完整流程写在
[`.ai/skills/project-bootstrap/SKILL.md`](.ai/skills/project-bootstrap/SKILL.md) 里,交给 Claude Code 执行即可。
要手动做的话是这七步:

1. **身份。** 填 `.ai/config.yaml` 的 `project.name`、`description`、`repo_url`。别留 `example-platform`。
2. **勘察。** 从项目里找出真实的构建、测试、lint 命令,记进 `.ai/core/`。不要编命令。
3. **划领域。** 每个有自己不变量的服务建一份 `.ai/projects/<name>/rules.md`,用 `applies_to` glob 覆盖路径。
4. **定策略。** 用真实规则替换 `.ai/policies/production-access.md`,保留 `visibility: restricted`。
5. **选适配器。** 把 `config.yaml` 的 `adapters:` 裁成实际在用的工具。
6. **生成并验证。** `scripts/ai-sync` 然后 `scripts/ai-check`,两者都必须通过。
7. **提交** `.ai/` 和生成的入口文件,放同一个 commit。

想调技能开关,打开 `docs/skill-config.html`,拨完开关复制右栏 YAML 贴回 `config.yaml`,再 `ai-sync`。

## 三个设计要点

**规则分层与优先级。** `config.yaml` 里的 `precedence` 会渲进每个入口文件,所有 agent 用同一套
冲突解决顺序:公司规范 > 项目规范 > 子项目规范 > 模块规范 > 当前任务。

**按目录加载。** `.ai/projects/<name>/rules.md` 的 `applies_to` glob 决定何时加载。改支付服务时
不加载前端规则。Cursor 和 Windsurf 的 glob、Codex 的就近 `AGENTS.md` 原生支持这点;其他工具靠
生成的规则表约定。

**敏感内容分级。** `visibility` 取 `public` / `internal` / `restricted`。`restricted` 的正文
**永远不会**写进任何生成物,只留一个指针;`internal` 只进入 `max_visibility: internal` 的适配器。
注意这是约定加校验,不是权限边界:agent 有读文件的能力就能读到那个文件,分级的作用是让敏感规则
不进入每个模型的默认上下文,并让 CI 能发现泄漏。

## 加一个新工具

写一个 `.ai/adapters/<id>.yaml`,在 `config.yaml` 的 `adapters` 里加上 id,跑 `ai-sync`。
核心内容一行不改。可用的输出类型:

| 类型 | 产出 | 适用 |
| --- | --- | --- |
| `single_file` | 一个合并的 Markdown | AGENTS.md / CLAUDE.md / GEMINI.md |
| `mdc_rules` | 每条规则一个文件,带 glob | Cursor、Windsurf |
| `instructions_dir` | 带 applyTo 的说明文件 | Copilot |
| `skill_dir` | 规范形态的 SKILL.md 目录 | Claude Code 及支持 Agent Skills 的工具 |
| `nested_agents` | 各领域目录下的 AGENTS.md | Codex 等就近加载的 agent |
| `prompt_bundle` | 自包含上下文包 | DeepSeek、Grok 等无约定的 harness |

## 与现有生态的关系

- `AGENTS.md` 和 `SKILL.md` 是采纳的标准,不是自造格式。`SKILL.md` 的 front matter 严格遵循
  [Agent Skills 规范](https://agentskills.io/specification)(只有 `name`、`description` 及少量
  可选字段),可以直接过 `skills-ref validate`。
- [Rulesync](https://github.com/dyoshikawa/rulesync) 覆盖约 50 个目标,还支持 hooks 和 permissions。
  本模板不依赖它(会引入 Node 依赖,且事实源会被它的格式绑定),但它的 `rulesync import` 适合
  接入存量项目时把旧的 CLAUDE.md / .cursorrules 抽出来当起草材料。
- MCP 是第三阶段。接口契约已在 `docs/architecture/mcp-surface.md` 定好,`config.yaml` 里
  `mcp.enabled: false`。Markdown 规则层必须独立完整 —— 不是每个 harness 说 MCP。

## 已验证的行为

| 行为 | 结果 |
| --- | --- |
| 8 个适配器生成 31 个文件 | 通过 |
| `restricted` 正文不出现在任何生成物 | 通过 |
| `internal` 正文进 Claude 不进 Copilot | 通过 |
| 手改生成物被 `ai-check` 发现 | 通过 |
| 改 `.ai/` 源文件被 `sync --check` 发现 | 通过 |
| CRLF 检出不产生误报漂移 | 通过 |
| `--drop-examples` 删掉的示例不被 `--update` 拉回 | 通过 |
| 全新目录误用 `--update` 报出可操作的错误 | 通过 |
| 新项目 `init --drop-examples` 后生成物零残留示例引用 | 通过 |

生成物是**有意提交**的:新克隆开箱即用,CI 里的 `ai-sync --check` 负责证明它们和 `.ai/` 一致。
`.gitignore` 里写明了这一点,不要把它们加进忽略列表。
