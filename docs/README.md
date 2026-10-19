# 提交文档与阅读索引

本目录是“正式报告 + 技术附件 + 测试证据”，不是要求逐一阅读的多份报告。建议先看正式PDF，再按需要查下表。

## 课程提交入口

|阅读顺序|入口|解决什么问题|
|---|---|---|
|1|[正式实验报告](report/DataBase_Project_1.pdf)|作者完成的7页报告：目标、方案比较、数据库、跳转/校验、测试、AI、问题与解决、阶段二展望；原样收录，未改PDF|
|2|[课程要求逐项核对](requirements-traceability.md)|原始任务书页码→报告章节→实现/证据；含本次审阅的改进建议|
|3|[安装与运行](../source/README.md)|依赖、配置、MongoDB副本集、启动、测试、演示|
|4|[数据库设计](database-design.md) / [系统设计](system-design.md)|完整BSON字段、索引、嵌入/引用、身份和并发；是PDF的技术附件|
|5|[API说明](api.md) / [规则说明](rule-specification.md)|实际接口、错误码、版本/匿名行为、校验与跳转语法|
|6|[测试用例](test-cases.md) / [测试报告](test-report.md)|课程六项测试的步骤、输入、输出及真实结果|
|7|[AI使用说明与索引](ai-usage-log.md)|使用工具、Prompt、得到的代码、修改、作者/AI分工及验证|

AI前期讨论入口：[作者提供的ChatGPT分享记录](https://chatgpt.com/share/6ad37dad-75c4-83ec-b5d6-765759cca816)。仓库Prompt、实现及执行证据的对应关系见AI使用说明。本次工具未能读取分享页全文，不把链接收录等同于内容核验。

## 测试证据只看一个入口

先看 [evidence/README.md](evidence/README.md)。当前代码最近一次完整功能验收是 **113 passed / 0 failed / 0 skipped（37.82秒）**，对应[用户名修正后的记录](evidence/respondent-username/README.md)。证据目录已从48个文件精简为15个：保留完整验收、少量阶段摘要、HTTP记录、一次错误输出和一组最新截图。

2026-10-18本次工作是报告/文档核对：已逐页阅读两份PDF、解析历史JUnit，并执行测试收集（113项）；没有重新执行数据库/浏览器功能测试，不将旧结果表述为本次重跑结果。

## 为什么文件多，哪些可以略过

|类别|位置|是否需要逐份阅读|
|---|---|---|
|正式报告与技术附件|本页上方7个入口|提交/复核的主要内容|
|机器可读附件|[openapi.json](openapi.json)、[delivery-manifest.json](delivery-manifest.json)|按需查接口或文件校验，不是额外报告|
|设计决策|[事务/发布恢复](adr/001-consistency.md)、[歧义澄清](adr/002-clarifications.md)|需要追问设计原因时再读|
|原始执行证据|evidence/中的txt/xml/json/png|用于复核结论，不是几十份独立文档|

旧阶段计划、自动完成报告、目录迁移和GitHub提交过程说明不再单独保留，其必要信息已由正式报告、运行手册、AI说明及测试报告覆盖。旧版本可从Git历史回溯；PDF已引用的证据路径和失败记录保留。

原始课程要求与开发规格分别见 [requirements/](../requirements/README.md) 和 [prompts/](../prompts/README.md)。正式报告、代码和附件应一并提交；若只交PDF，其API、配置及详细测试步骤需另补附件。
