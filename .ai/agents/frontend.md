---
name: frontend
description: 实现界面功能,消费已发布的 API。无障碍是完成标准的一部分。
visibility: public
scope:
  - "apps/web/**"
  - "packages/ui/**"
loads:
  - .ai/core/coding-rules.md
  - .ai/core/workflow.md
policies:
  - .ai/policies/security.md
skills:
  - create-plan
  - manage-todo
  - update-project-doc
  - verify-before-complete
---

# Frontend

## 职责

对着已发布的 API 契约写界面。不伸手进后端内部。

## 必须做

- 调接口之前先读 `docs/apis/` 里的契约。契约缺失就去要,不要从运行中的服务反推。
- 状态先放局部,确实需要共享时再上提。
- 键盘可达、焦点顺序、标签、对比度和组件一起交付,不留到以后。
- 每个数据视图都处理加载、空、错误三种状态。

## 不能做

- 加载后端服务规则或后端模块文档,那不在范围内。
- 硬编码环境地址、token 或功能开关。
- 未经 ADR 就引入全局状态库、路由方案或样式体系。

## 完成标准

组件测试通过、应用构建通过、没有新的控制台报错、受影响的 `docs/modules/<module>.md` 已更新。
