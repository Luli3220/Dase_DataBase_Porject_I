# 项目文档索引

## 运行与交付

|文档|用途|
|---|---|
|[运行手册](../source/README.md)|安装、环境配置、MongoDB、应用启动、测试与演示|
|[完成报告](project-report.md)|项目目标、实现、测试、限制和第二阶段扩展|
|[实施计划](implementation-plan.md)|A/B/C阶段顺序及验收记录|
|[目录调整记录](repository-layout.md)|当前目录、迁移映射及路径兼容说明|
|[GitHub提交说明](repository-submission.md)|仓库提交授权及历史证据说明|

## 设计与接口

|文档|用途|
|---|---|
|[系统设计](system-design.md)|分层、数据流、身份、隐私与并发|
|[数据库设计](database-design.md)|四集合BSON、索引、版本指针、存储取舍|
|[规则说明](rule-specification.md)|题型校验、运算符、优先级与有效路径|
|[API说明](api.md)|权限、请求/响应、状态码与统计口径|
|[OpenAPI快照](openapi.json)|机器可读接口定义|
|[一致性决策](adr/001-consistency.md)|副本集、事务及发布中断恢复|
|[冲突与澄清](adr/002-clarifications.md)|原始要求、规格歧义和采用的解决方案|

## 测试与过程证据

|文档|用途|
|---|---|
|[测试用例](test-cases.md)|步骤、输入、预期、实际结果|
|[测试报告](test-report.md)|真实命令、环境、结果、修复及未验证项|
|[逐项结果](evidence/case-results.md)|原始102个测试实例及耗时|
|[原始JUnit](evidence/final.xml)|首次完整验收记录|
|[目录整理后回归](evidence/restructure/README.md)|迁移后的独立执行结果与截图|
|[需求追踪](requirements-traceability.md)|需求→模型→接口→测试|
|[AI使用日志](ai-usage-log.md)|实际Prompt、生成/修改、问题和验证|
|[交付清单](delivery-manifest.json)|打包文件及SHA256|

原始任务书和开发Prompt分别见 [requirements/](../requirements/) 与 [prompts/](../prompts/README.md)。历史测试命令按执行时目录保留；当前可运行命令统一从source/README.md查找。
