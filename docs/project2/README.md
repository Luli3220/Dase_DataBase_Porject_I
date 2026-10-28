# Project 2 材料索引

第二阶段在原问卷系统上增加题目复用、共享、版本管理、题库和跨问卷统计。本目录整理需求、设计演进及开发记录；系统和接口的完整说明见[文档导航](../README.md)。

## 设计与实施

|材料|内容|
|---|---|
|[需求追踪](requirements-traceability.md)|八项需求对应的数据模型、接口、页面和测试|
|[数据库演进](database-evolution.md)|从问卷内嵌题目到独立题目版本的设计选择|
|[升级与回退](migration.md)|数据兼容、升级步骤及回退方法|
|[变更记录](change-log.md)|主要改动与代码入口|
|[AI 使用日志](ai-usage-log.md)|设计讨论、Codex 实现及后续检查与修改|

## 测试与运行记录

2026-10-27 完整回归 **167 项通过，耗时 64.21 秒**。在首轮 150 项的基础上，新增 17 项测试覆盖统一保存、归档分页和统计边界。

|材料|内容|
|---|---|
|[测试用例](test-cases.md)|测试步骤、输入与预期结果|
|[测试记录](test-report.md)|各轮结果、问题处理和运行环境|
|[保存、分页与统计修复](fixes-2026-10-27.md)|后续检查中发现的问题及具体修改|
|[日志与截图](evidence/README.md)|控制台输出、JUnit、环境信息和页面截图|
|[测试代码导航](../../source/tests/README.md)|第一阶段测试与第二阶段新增用例|

## 报告与使用入口

- [项目报告](final-report.md) · [LaTeX 与 PDF](report/README.md)
- [安装与演示](../../source/README.md) · [系统设计](../system-design.md) · [数据库设计](../database-design.md) · [API](../api.md)

当前成果位于 `main`，第一阶段基线为 `project1-baseline-61e2263`。首轮实现及后续修复的版本记录见[变更记录](change-log.md)。
