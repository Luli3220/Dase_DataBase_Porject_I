# Project 2 独立交付材料

本目录记录第二阶段增量演进，不维护第二套当前 API/数据库规范。

|材料|用途|
|---|---|
|[完整项目报告](final-report.md)|需求、原设计、演进、实现、测试与 AI 过程|
|[LaTeX/PDF](report/)|与工作区 report1/1.2.tex 同步的独立报告及图片|
|[需求追踪](requirements-traceability.md)|八项需求到模型、接口、UI、测试及证据|
|[数据库演进](database-evolution.md)|为什么从四集合演进为七集合|
|[迁移与回退](migration.md)|实测升级、旧数据指纹与回退边界|
|[代码变更](change-log.md)|基线、原位改动、新模块及兼容性|
|[测试用例](test-cases.md)|步骤、输入、预期输出、实际证据|
|[测试报告](test-report.md)|本阶段真实执行结果与失败修复|
|[AI 日志](ai-usage-log.md)|真实工具、提示、代码产物与人工参与边界|
|[逐项结果](evidence/case-results.md)|最终完整 JUnit 的每项状态|

唯一现行规范：[系统](../system-design.md)、[数据库](../database-design.md)、[API](../api.md)、[OpenAPI](../openapi.json)、[规则](../rule-specification.md)、[运行](../../source/README.md)。第一阶段历史测试/AI 材料在父目录及 `../evidence/` 原样保留。原代码和技术文档可用 `git show project1-baseline-61e2263:<path>` 查阅。
