# 项目文档

本目录包含系统设计、接口说明和测试记录。项目报告通过课程平台提交，并在报告中提供GitHub仓库链接。

## 设计与说明

|文档|内容|
|---|---|
|[需求对应表](requirements-traceability.md)|课程要求与报告章节、代码和测试的对应关系|
|[系统设计](system-design.md)|模块划分、数据流、身份认证与并发处理|
|[数据库设计](database-design.md)|七集合模型、BSON字段、嵌入与引用、索引和版本管理|
|[规则说明](rule-specification.md)|题型、校验条件、跳转规则和填写路径|
|[API文档](api.md)|接口、请求示例、返回字段和错误码|
|[AI使用说明](ai-usage-log.md)|前期讨论、Prompt、代码产物、问题修正与个人参与|

第一阶段历史证据见下表；第二阶段材料集中在 [project2/](project2/README.md)，现行系统、数据库和 API 规范仍在原路径维护。

## 运行与测试

|文档|内容|
|---|---|
|[运行手册](../source/README.md)|安装、配置、启动、测试与演示|
|[测试用例](test-cases.md)|测试步骤、输入、预期结果与实际结果|
|[测试报告](test-report.md)|执行环境、测试结果及问题处理|
|[测试记录](evidence/README.md)|原始输出、JUnit和界面截图|

## 技术附件

- [事务与发布恢复](adr/001-consistency.md)、[业务约定](adr/002-clarifications.md)
- [OpenAPI定义](openapi.json)
- [课程任务书](../requirements/README.md)、[开发Prompt](../prompts/README.md)
