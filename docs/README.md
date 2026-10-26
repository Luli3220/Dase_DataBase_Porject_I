# 文档导航

当前系统的设计与接口说明放在本目录；两个阶段的需求、测试和开发过程分别归档。可以先阅读系统设计，再按需要查看数据库、规则或接口细节。

## 当前技术文档

|文档|内容|
|---|---|
|[系统设计](system-design.md)|模块职责、数据流、保存与发布流程、身份和并发处理|
|[数据库设计](database-design.md)|七集合模型、字段、索引、快照、共享与统计口径|
|[API 说明](api.md)|接口、请求示例、返回字段和错误码|
|[OpenAPI](openapi.json)|由应用导出的接口定义|
|[规则说明](rule-specification.md)|题型约束、条件跳转和填写路径|
|[设计决策](adr/README.md)|事务、发布恢复及业务约定|
|[运行手册](../source/README.md)|安装、配置、升级、测试与演示|
|[源码导航](../source/app/README.md)|API、服务、模型、规则和前端文件入口|

## 第二阶段材料

[Project 2 索引](project2/README.md)集中整理需求追踪、数据库演进、迁移、变更和 AI 使用过程。

|用途|入口|
|---|---|
|查看当前验证结果|[测试记录](project2/test-report.md)、[按轮次查证据](project2/evidence/README.md)|
|了解最近的修复|[2026-10-27 保存、分页与统计说明](project2/fixes-2026-10-27.md)|
|阅读实验报告|[Markdown](project2/final-report.md)、[LaTeX / PDF](project2/report/README.md)|

## 第一阶段材料

|文档|内容|
|---|---|
|[需求对应表](requirements-traceability.md)|第一阶段课程要求与实现、测试的对应关系|
|[测试用例](test-cases.md)|步骤、输入和预期结果|
|[测试记录](test-report.md)|第一阶段执行结果与问题处理|
|[原始证据](evidence/README.md)|JUnit、HTTP 输出和浏览器截图|
|[AI 使用日志](ai-usage-log.md)|第一阶段提示词、代码产物和修正过程|

第一阶段技术文档的历史版本可通过 Git 标签 `project1-baseline-61e2263` 查阅，例如：

```powershell
git show project1-baseline-61e2263:docs/database-design.md
```

## 需求与开发资料

- [课程任务书和变更要求](../requirements/README.md)
- [两阶段 Prompt 索引](../prompts/README.md)
