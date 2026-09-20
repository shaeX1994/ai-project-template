---
name: verify-before-complete
description: 在声称任务完成之前执行项目验证门禁:构建、测试、lint、ai-check 和配置漂移检测。每次变更结束时、以及在声称任何东西能工作之前使用。Use at the end of every change before claiming it works.
metadata:
  x-template-version: "1"
---

<!-- GENERATED FILE - do not edit. Source: .ai/  Regenerate: scripts/ai-sync -->

# verify-before-complete

说"做完了"的唯一合法途径。

## 门禁

按顺序执行,第一个失败处停下:

| 步骤 | 命令 | 阻断 |
| --- | --- | --- |
| 1. 配置漂移 | `scripts/ai-sync --check` | 是 |
| 2. 规则与文档一致性 | `scripts/ai-check` | 是 |
| 3. lint / 格式 | 项目自身的 linter | 是 |
| 4. 变更路径的测试 | 覆盖本次变更的最小命令 | 是 |
| 5. 项目构建 | 项目自身的构建命令 | 是 |
| 6. 全量测试 | 项目自身的测试命令 | 跨切面变更时 |

真实命令从项目清单里找(`package.json`、`pyproject.toml`、`Makefile`、`pom.xml` 等)。不要猜命令名。

## 报告规则

- 引用真实的失败输出,不要转述。
- bug 修复要报告:修复前失败、修复后通过的那个测试。
- 某步在当前环境跑不了,要说明是哪一步、为什么。绝不用一句"通过"代替没执行的步骤。
- 有意跳过某步,要说明并给出原因。

## 完成声明

只有所有阻断步骤都通过后:

```markdown
- Verified: <实际执行的步骤及命令>
- Not verified: <跑不了的步骤及原因,或 none>
- Docs updated: <路径,或 none>
- Todo updated: <路径,或 none>
```

## 禁止

- 靠读代码就判定成功。
- 削弱测试、标记 skip、或放宽断言来让门禁变绿。
- 顺手修掉路上发现的无关失败。报告它们。
