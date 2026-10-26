# Project 2 材料索引

第二阶段围绕题目复用、共享、版本管理、题库和跨问卷统计展开。这里整理设计演进与开发过程；当前完整系统说明见[系统设计](../system-design.md)、[数据库设计](../database-design.md)和[API](../api.md)。

## 最近一次验证

2026-10-27 完整回归 **167 项通过，耗时 64.21 秒**。本次新增统一原子保存、归档题目分页过滤，并说明 `surveyCount` 的统计口径。

- [修复说明与测试步骤](fixes-2026-10-27.md)
- [本轮日志、JUnit 和截图](evidence/fixes-2026-10-27/README.md)
- [各轮证据总索引](evidence/README.md)

## 设计与实施

|材料|阅读重点|
|---|---|
|[需求追踪](requirements-traceability.md)|八项需求与数据模型、接口、页面和测试的对应关系|
|[数据库演进](database-evolution.md)|从问卷内嵌题目到独立题目身份的设计选择|
|[升级与回退](migration.md)|Schema、索引更新、旧数据检查和回退步骤|
|[变更记录](change-log.md)|各轮改动、文件入口和版本基线|
|[AI 使用日志](ai-usage-log.md)|提示来源、工具、代码产物和问题处理|

## 测试与报告

|材料|内容|
|---|---|
|[测试用例](test-cases.md)|功能、权限、并发和统计边界用例|
|[测试记录](test-report.md)|当前结果及首轮 150 项历史验收|
|[测试代码导航](../../source/tests/README.md)|原测试与第二阶段新增测试|
|[证据目录](evidence/README.md)|各轮输出、逐项结果、环境与截图|
|[项目报告](final-report.md)|第二阶段完整实验报告|
|[排版报告](report/README.md)|LaTeX 源文件和 7 页 PDF|

首轮第二阶段提交为 `7261649`，第一阶段基线为 `project1-baseline-61e2263`。运行和演示可从[运行手册](../../source/README.md)开始。
