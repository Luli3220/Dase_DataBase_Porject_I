# 第二阶段变更记录

第一阶段基线为 `61e226387140ee7ca9f985bf010769c823253a1c`，标签为 `project1-baseline-61e2263`。第二阶段在 `project2/question-library` 分支演进，首轮提交为 `7261649`。

## 2026-10-26：题目复用与题库

保留账号、问卷、问卷版本和答卷四集合，新增题目定义、题目版本与题库。问卷题目增加可选 source，问卷增加默认关闭的统计贡献设置。题目内容固定到版本，问卷继续保存完整快照。

### 扩展的原文件

|文件|改动|
|---|---|
|[models/domain.py](../../source/app/models/domain.py)|来源及题目、题库请求模型|
|[models/documents.py](../../source/app/models/documents.py)|新文档与 BSON 映射|
|[db/mongo.py](../../source/app/db/mongo.py)|新集合验证器和索引|
|[services/surveys.py](../../source/app/services/surveys.py)|来源校验、固定版本导入与事务保存|
|[api/routes.py](../../source/app/api/routes.py)|预览来源序列化|
|[main.py](../../source/app/main.py)|新路由与页面入口|
|[static/app.js](../../source/app/static/app.js)|题目、历史、共享、题库、使用关系与统计界面|
|[static/style.css](../../source/app/static/style.css)|新增页面和移动端样式|
|[templates/index.html](../../source/app/templates/index.html)|题目与题库导航|
|[scripts/build_evidence.py](../../source/scripts/build_evidence.py)|第二阶段结果索引与 OpenAPI 导出|
|[scripts/run-tests.ps1](../../source/scripts/run-tests.ps1)|第二阶段测试输出路径|

### 新增模块

|文件|职责|
|---|---|
|[services/questions.py](../../source/app/services/questions.py)|稳定身份、版本、共享、恢复、fork 与来源检查|
|[services/question_banks.py](../../source/app/services/question_banks.py)|题库和成员引用|
|[services/question_statistics.py](../../source/app/services/question_statistics.py)|反查与跨问卷聚合|
|[api/question_routes.py](../../source/app/api/question_routes.py)|题目与题库 HTTP 入口|
|[scripts/migrate_project2.py](../../source/scripts/migrate_project2.py)|升级与原文档指纹比较|
|[scripts/audit_project2.py](../../source/scripts/audit_project2.py)|首轮交付核对|
|[tests/project2/](../../source/tests/project2/README.md)|首轮 37 项新增测试|

当前技术文档在原 docs 路径更新；设计演进、迁移、测试、AI 日志和报告集中到本目录。首轮 API 操作为 22→40，完整测试为 113→150。原测试和阶段材料的核对结果见[首轮审计](evidence/delivery-audit.json)。

## 2026-10-27：推送首轮成果

按用户授权，将已有提交 `7261649` 推送到原仓库的 `project2/question-library`，核对远程与本地一致。第一阶段 main 和基线标签保留。

## 2026-10-27：保存、分页与统计说明

|位置|改动|
|---|---|
|domain.py、routes.py、surveys.py|统一 `POST /surveys/{id}/save`，元信息与草稿同事务提交|
|questions.py、question_routes.py|列表增加默认 false 的 activeOnly|
|app.js|使用原子保存和后端归档过滤，显示参与统计的问卷数说明|
|question_statistics.py|补充 surveyCount 计算注释，保留聚合逻辑|
|[后端修复测试](../../source/tests/project2/test_fixes_20261027.py)|15 项回滚、权限、并发、分页和统计边界|
|[浏览器修复测试](../../source/tests/project2/test_fixes_browser_20261027.py)|2 项保存冲突与归档分页|

API 操作为 40→41，完整回归为 150→167。96 份原文件的指纹核对、输出与截图见[本轮证据](evidence/fixes-2026-10-27/README.md)，实现说明见[修复记录](fixes-2026-10-27.md)。该轮同时更新技术说明和报告。

## 2026-10-27：文档与导航

整理当前系统、数据库和 API 章节，将后续补充融入对应流程。更新仓库、文档、需求与 Prompt 首页，增加源码、脚本、测试、设计决策和各轮证据的 README。后续运行目录见 [evidence/runs](evidence/runs/README.md)。

本轮只调整文档与索引，业务代码、既有测试、原始证据和实验报告内容保持原状。当前结果见[测试记录](test-report.md)，报告入口见[排版报告](report/README.md)。
