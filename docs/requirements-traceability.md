# 需求与实现对应

本表将[课程任务书](../requirements/project1.pdf)中的要求，与实验报告、代码和测试对应起来。报告通过课程平台提交，代码及技术文档由报告中的GitHub链接访问。课程页码指11页任务书，报告页码指7页实验报告。

## 提交内容

|提交项|对应内容|
|---|---|
|代码|[后端实现](../source/app/)、[MongoDB Schema与索引](../source/app/db/mongo.py)、[配置样例](../source/.env.example)及[启动说明](../source/README.md)|
|文档|[系统说明](system-design.md)、[数据库设计](database-design.md)、[API说明](api.md)和[关键规则](rule-specification.md)|
|测试用例|[测试用例表](test-cases.md)列出步骤、输入、预期输出、实际结果及对应测试；[执行记录](evidence/README.md)提供原始结果|
|项目完成报告|通过课程平台提交，包含项目目标、系统设计等章节，报告中的GitHub链接对应本仓库|

## 功能需求

|课程要求|报告位置|实现与验证|
|---|---|---|
|注册、登录、账号信息（7–8页）|第1页1.1、第2页表2、第6页|AuthService、users；test_auth_and_csrf|
|个人问卷列表与所有者权限（8页）|第1页1.1、第6页表6|SurveyService.owned、GET /api/surveys；12类test_ownership|
|创建标题、说明和匿名设置（8页）|第1页1.1、第4页3.5|SurveyService.create、版本settings；创建API及浏览器流程|
|发布与公开链接（8页）|第1页1.1、第4页发布流程|publish/publicId、管理与填写页面；API及浏览器流程|
|截止时间与关闭（8页）|第1页1.1、第6页|patch/close/public；过期、关闭及状态竞态测试|
|登录后通过链接填写（8页）|第1页1.1、第4页3.5|current_user、公开API；登录后返回原问卷链接|
|单选选项与必答（8–9页）|第4页表4、第5页4.3|single_choice校验；R01/R06、single_invalid|
|多选数量限制（9页）|第4页表4|validation.minSelections/maxSelections；边界及恰好2项测试|
|文本长度（9–10页）|第4页表4、第5页4.3|trim、Unicode长度；test_text_unicode_and_boundary|
|数字范围与整数（10页）|第4页表4、第7页|number校验；bounds/rejects/integer用例|
|单选、多选及数字跳转（10页）|第4–5页第4章|规则引擎与声明式配置；R01–R15及操作符测试|
|顺序作答与非法提示（10–11页）|第5页图6|服务器trace路径及逐题页面；缺失必答、路径外答案和分支修改测试|
|保存每次提交（11页）|第4页3.5|submissions追加写、UUID幂等；重复提交测试|
|多人同时填写（11页）|第6页表6|不同respondentId的服务层并发调用、唯一索引与事务|
|匿名及重复填写（11页）|第4页3.5、第6–7页|anonymousAtSubmission、两种提交策略及用户名修正测试|
|单选次数与回答数（11页）|第6页5.1|StatisticsService的options与answeredCount|
|多选各项次数（11页）|第6页5.1|MongoDB unwind/group及选项计数断言|
|查看填空内容与数字均值（11页）|第6页5.1|values分页、mean、空结果及分页测试|
|全卷与单题统计（11页）|第1页1.1、第6页5.1|统计API及题目选择；单题与全卷一致性断言|

具体步骤与输入输出见[测试用例](test-cases.md)。完整执行记录包含113个实例，详见[逐项结果](evidence/case-results.md)。

## 设计与交付材料

|课程要求|对应材料|
|---|---|
|MongoDB建模、嵌入与引用、索引及设计理由（4页）|报告第3章、[数据库设计](database-design.md)、[Schema与索引代码](../source/app/db/mongo.py)|
|AI工具、Prompt、代码产物、修改与个人参与（4–5页）|报告第6章、[AI使用说明](ai-usage-log.md)、[Prompt目录](../prompts/README.md)|
|创建、题目、跳转、校验、提交、统计六类测试（5页）|[测试用例](test-cases.md)C01–C06、[测试代码](../source/tests/)|
|后端代码、Schema与配置说明（6页）|[源码](../source/app/)、[配置样例](../source/.env.example)、[运行手册](../source/README.md)|
|系统、数据库、API及关键逻辑（6页）|[系统设计](system-design.md)、[数据库设计](database-design.md)、[API](api.md)、[规则](rule-specification.md)|
|目标、设计、AI、测试、问题与解决（6–7页）|课程平台提交的实验报告第1–8章|
|基于第一阶段继续扩展（2–3页）|报告1.3及第8章、内容版本与schemaVersion的区分、模块化实现与回归测试|

## 测试结果

完整验收包含113个实例：72项单元测试、39项数据库/API测试和2项浏览器测试，详见[JUnit](evidence/respondent-username/full.xml)。另有22项独立HTTP检查，结果见[final-http.json](evidence/final-http.json)。
