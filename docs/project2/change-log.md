# 第二阶段变更记录

第二阶段从第一阶段基线 `61e2263` 继续开发，现已合入 `main`。第一阶段版本保存在 `project1-baseline-61e2263` 标签中，以下按开发轮次整理主要改动。

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

首轮增加 18 个 API 操作，接口总数为 40；新增 37 项测试，完整回归为 150 项。文件与接口检查见[首轮记录](evidence/delivery-audit.json)。

首轮成果提交为 `7261649`。

## 2026-10-27：保存、分页与统计说明

|位置|改动|
|---|---|
|domain.py、routes.py、surveys.py|统一 `POST /surveys/{id}/save`，元信息与草稿同事务提交|
|questions.py、question_routes.py|列表增加默认 false 的 activeOnly|
|app.js|使用原子保存和后端归档过滤，显示参与统计的问卷数说明|
|question_statistics.py|补充 surveyCount 计算注释，保留聚合逻辑|
|[后端修复测试](../../source/tests/project2/test_fixes_20261027.py)|15 项回滚、权限、并发、分页和统计边界|
|[浏览器修复测试](../../source/tests/project2/test_fixes_browser_20261027.py)|2 项保存冲突与归档分页|

本轮新增统一保存接口，API 共 41 个操作；新增 17 项测试，完整回归共 167 项。步骤和结果见[修复记录](fixes-2026-10-27.md)，日志与截图见[本轮目录](evidence/fixes-2026-10-27/README.md)。

## 2026-10-27：文档与导航

整理当前系统、数据库和 API 章节，将后续补充融入对应流程。更新仓库、文档、需求与 Prompt 首页，增加源码、脚本、测试、设计决策和各轮证据的 README。后续运行目录见 [evidence/runs](evidence/runs/README.md)。

这一轮整理了文档表达和阅读入口。当前结果见[测试记录](test-report.md)，报告入口见[排版报告](report/README.md)。

## 2026-10-27：统一交付分支

首轮 `7261649` 经 PR #1 合入 `main`，随后合入修复与文档整理提交 `71150c8`。课程提交和日常查看统一使用主分支，第一阶段通过基线标签查阅。
