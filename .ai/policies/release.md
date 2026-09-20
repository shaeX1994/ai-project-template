---
name: release
description: 一个变更可以发布的前提条件,以及破坏性变更如何上线。
visibility: public
enforcement: blocking
applies_to:
  - "**/*"
roles:
  - architect
  - reviewer
  - backend
  - frontend
---

# 发布策略

## 门禁

以下条件全部成立,变更才可发布:

- 项目构建通过;
- 覆盖变更路径的测试通过,且 bug 修复有一个"修复前失败"的测试;
- `scripts/ai-check` 通过;
- `scripts/ai-sync --check` 通过,即生成的入口文件与 `.ai/` 一致;
- 受影响的 `docs/modules/*.md` 已更新;
- 没有未给出理由的新增依赖。

任何一项在当前环境无法评估,明确说出来,不要报成功。执行走 `verify-before-complete` 技能。

## 分支与提交

- 在分支上开发,绝不直接推默认分支。
- `.ai/` 源文件和它生成的入口文件放同一个 commit。
- 只有人明确要求时才提交。

## 破坏性变更

一律两阶段:先上新增形式,迁移调用方,再用独立变更删除旧形式。删列或改列名的迁移同样适用。决策记成 ADR。

## 回滚

每个影响发布的变更都要写明怎么撤销。没有回滚路径的变更,落地前需要人工批准。
