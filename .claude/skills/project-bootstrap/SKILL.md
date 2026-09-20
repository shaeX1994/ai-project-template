---
name: project-bootstrap
description: "在一个仓库里落地 .ai 配置体系:填写项目身份、用真实领域规则替换示例规则、生成各模型入口文件。接入新项目或新增服务时执行一次。Use once when onboarding a project or adding a new service."
metadata:
  x-template-version: "1"
---

<!-- GENERATED FILE - do not edit. Source: .ai/  Regenerate: scripts/ai-sync -->

# project-bootstrap

## 何时使用

每个仓库一次,在 `.ai/` 刚拷进来之后。新增一个需要独立规则的服务时也用。

## 步骤

1. **身份。** 确认 `.ai/config.yaml` 里的 `project.name`、`description`、`repo_url` 是真实值,不是模板占位符。
2. **勘察。** 从项目清单里找出真实的构建、测试、lint 命令,记进对应的 `.ai/core/` 文件。不要编命令。
3. **划领域。** 每个有自己不变量的服务或应用,建一份 `.ai/projects/<name>/rules.md`,用 `applies_to` glob
   覆盖它的路径。删掉示例的 `user-service` 和 `payment-service`,或执行
   `python scripts/ai.py init . --drop-examples`(示例清单在 `config.yaml` 的 `template.examples`)。
   不要加 `--update`:那是给已有 `.ai/` 的项目刷新模板自带部分的,在还没有 `.ai/` 的目录上会直接报错。
4. **定策略。** 用真实规则替换 `.ai/policies/production-access.md`,保留 `visibility: restricted`,
   这样它的正文不会进入生成的入口文件。
5. **选适配器。** 把 `.ai/config.yaml` 的 `adapters:` 裁剪成实际在用的工具。
6. **生成并验证。** 执行 `scripts/ai-sync`,再执行 `scripts/ai-check`,两者都必须通过。
7. **提交** `.ai/` 和生成的入口文件,放在同一个 commit。

## 输出

报告:项目身份已设置、启用了哪些适配器、创建了哪些领域规则文件、示例是否已删除、`ai-check` 的结果。

## 禁止

- 写下你没有从代码或人那里确认过的领域不变量。
- 任何地方残留 `example-platform`。
- 手改生成的入口文件来绕过 bootstrap 问题。改 `.ai/` 然后重新 sync。
