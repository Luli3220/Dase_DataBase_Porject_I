# 测试用例、步骤、输入、实际结果

最终真实结果：102 PASS / 0 FAIL / 0 SKIP。所有参数化实例、耗时和原始JUnit名称见 [逐项结果](evidence/case-results.md)，原始报告 [final.xml](evidence/final.xml)。下表是业务级摘要，不把计划当作执行结果。执行源代码中的assert同时承担期望输出核对；PASS表示执行已达到这些断言。

环境/命令见 [测试报告](test-report.md)。纯规则无数据库；集成测试每例新建随机survey_test_库，真实MongoDB；浏览器自动启动8001临时服务，用真实Chromium。

## 课程六项及完整流程

|ID|目标/前提/步骤|输入|预期输出|实际/结果/证据|
|---|---|---|---|---|
|C01|创建：A注册并登录，POST /api/surveys，读草稿|title=四题样例，anonymous=true，latest_only|201；status=draft，draftVersion=1，publishedVersion=null，V1 revision=0|PASS；test_api_chain_versions_anonymity + test_version_cas_and_recovery；final.xml|
|C02|添加题目：创建草稿，PUT四题配置；浏览器逐个添加并编辑|tests/fixtures.py四类题；expectedRevision=0|200，revision=1，嵌套配置BSON读取一致；UI可配全部字段|PASS；test_schema_indexes_bson、test_full_browser_flow；editor.png|
|C03|跳转：依次执行固定R01..R15|下表给出的答案/非法配置|有效路径/优先级/提前结束符合规格|15/15 PASS；test_fixed_paths/invalid/bad_config；phase-a.xml/final.xml|
|C04|校验：构造合法/边界/错误答案，服务端重算|单/多选、Unicode、整数/分数、0、bool、NaN/Inf、极大整数|合法保存；非法拒绝DomainError/HTTP422；不丢有效0|PASS；test_rules.py及test_invalid_statuses_and_serialization|
|C05|提交：B通过公开URL填写；相同UUID重试；再次新UUID；并发请求|Q1=no,Q3=8；Q1=yes,Q2=[python,java]|201；同UUID同ID；新UUID新文档；非法路径422；无覆盖|PASS；test_multiple_concurrency_and_deadlines、test_idempotency_stats_versions_privacy、真实22步HTTP|
|C06|统计：同用户提交两份、切版后提交；查询两口径/单题|version=1/2，current_effective/historical_raw|原始2/有效1；新版本后V1有效0仍历史2；单题与全卷一致|PASS；test_api_chain_versions_anonymity、test_tie_breaker_pagination_and_numeric_text_samples|
|C07|完整浏览器：A可视化编辑→预览→发布；B注册返回链接→改分支→提交→再填；A统计→V2→关闭|4类题和3类跳转，非法-1，含HTML标签的文本|预览0答卷；非法即时提示；分支旧答案清除；XSS文本安全；旧版409；关闭拒绝|PASS；test_full_browser_flow；editor/published/statistics.png|
|C08|手机/键盘：390×844注册、Tab焦点、创建文本题|手机viewport；随机账号密码|密码框可Tab聚焦；页面无横向溢出；表单标签有效|PASS；test_mobile_keyboard_and_labels；mobile.png|

## 固定fixture R01–R15

Q1单选必答yes/no，no→Q3；Q2多选必答python/java/cpp，1..3，包含python+java(priority10)→Q4，含cpp(priority20)→END，否则Q3；Q3数字0..80必答，gte10→Q4，lt10→END；Q4可选文本0..500。

|ID|步骤与输入|预期|实际结果|
|---|---|---|---|
|R01|调用trace，Q1=no,Q3=8|q1,q3结束|相同路径，PASS|
|R02|Q1=no,Q3=12，不填Q4|q1,q3,q4结束，未答Q4不入answers|相同路径，PASS|
|R03|Q1=yes,Q2=[python,java]|q1,q2,q4结束|相同路径，PASS|
|R04|Q1=yes,Q2=[cpp]|q1,q2结束|相同路径，PASS|
|R05|Q1=yes,Q2=[python,java,cpp]|同时匹配，priority10→q4|q1,q2,q4，PASS|
|R06|Q1=no，缺Q3|必答拒绝|DomainError，PASS|
|R07|Q1=yes,Q2=[python,python]|重复选项拒绝|DomainError，PASS|
|R08|Q1=yes,Q2=[cpp]，额外Q3|无效路径答案拒绝|DomainError，PASS|
|R09|Q1=no,Q3=-1|低于下限拒绝|DomainError，PASS|
|R10|Q1=no,Q3="12"|数字字符串拒绝|DomainError，PASS|
|R11|配置Q2目标q99，静态验证|不存在目标拒绝|DomainError，PASS|
|R12|配置Q3回q1|回跳拒绝|DomainError，PASS|
|R13|配置Q2规则同priority10|冲突优先级拒绝|DomainError，PASS|
|R14|单选使用contains_all|运算符不适用拒绝|DomainError，PASS|
|R15|多选min3,max2|上下限矛盾拒绝|DomainError，PASS|

## 关键补充测试（均实际PASS）

|测试源/用例|前提、步骤、输入|预期及实际断言|
|---|---|---|
|test_auth_and_csrf|注册Test_A；重复TEST_A；错密码；缺token/外域Origin；退出再登录；用户名字典注入|username=test_a，Argon2id；409/401/403/403/200/422|
|test_session_expiry|签名时间回拨30000秒后GET /api/me|401 SESSION_EXPIRED|
|test_logout_revokes_copied_cookie|复制Cookie→退出→另客户端重放|401，旧Cookie失效|
|test_ownership（12参数实例）|B用A的ID访问管理读/写/发布/关闭/统计/答卷/预览|全部403；B管理列表0；公开填写200|
|test_invalid_statuses_and_serialization|坏ID、无版本、非法mode、sealed编辑、伪造身份、日期无时区、过期|404/404/422/409/422/422/409；错误不回显伪造输入|
|test_body_size_limit_even_without_content_length|2MiB+1普通请求及分块33×65536|都413|
|test_schema_indexes_bson|初始化3次；重复username/publicId/版本；缺Schema插入|重复键Mongo DuplicateKeyError；坏结构WriteError；ObjectId/date类型正确|
|test_version_cas_and_recovery|旧revision编辑；after_seal抛异常；重试publish；4线程派生|409；未公开半成品；恢复V1；所有线程同V2，无重复版本|
|test_concurrent_draft_revision_and_publish|4线程同revision编辑；再并发publish|仅一次编辑成功；一个权威sealed版本，冲突或幂等成功|
|test_publish_interruption_preserves_old_public_and_close_wins|V2冻结中断→公开读取→关闭→恢复发布|仍V1；关闭后不能恢复成published|
|test_idempotency_stats_versions_privacy|同UUID不同body；匿名V1改实名V2；跨版本最新|409；V1无账号字段；V2实名；V1有效0历史2|
|test_multiple_concurrency_and_deadlines|6线程相同逻辑请求；4账号同时填；截止/关闭|单ID+4新记录共5；唯一索引生效；过期/关闭拒绝|
|test_failed_submission_does_not_lock_policy|必答缺失提交失败，再改策略|未写hasSubmissions，允许改策略|
|test_policy_change_and_first_submission_race|策略修改与首份提交同时执行|修改先则multiple，否则POLICY_LOCKED；提交后策略不可改|
|test_submission_state_race（close/publish）|提交与关闭/切版并发|若提交先则有效V1，否则状态/版本409；状态变更后新提交拒绝|
|test_tie_breaker_pagination_and_numeric_text_samples|3份提交改为同时间戳，查不同分页/单题|按最大_id选最新；全历史均值11；分页1条；单题与全卷相同|
|test_multiple_same_user_all_count_and_idempotent_after_close|multiple同账号2次→关闭→重试旧UUID/新UUID|有效2；旧UUID返回原ID；新UUID拒绝|

## 复核步骤

在项目根目录运行README命令；查看final.txt汇总和final.xml每个testcase。运行`scripts.http_demo`需要8000服务，脚本实际断言22个HTTP状态与关键统计/匿名内容，输出无密码JSON。浏览器测试保存实际页面截图，不使用生成/合成截图。暂未执行的Docker启动、容量压测、HTTPS部署明确见test-report.md，不属于上述PASS范围。
