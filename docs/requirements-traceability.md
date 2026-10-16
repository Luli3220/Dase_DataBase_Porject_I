# 课程需求—模型—服务—接口—测试追踪

原始依据project1.pdf第7–11页“初始用户需求”，第4–7页数据库/AI/测试/交付要求；三份实施规格补充明确语义，没有删除原功能。

|课程/规格需求|集合/字段|核心实现|API/网页|实际测试/证据|
|---|---|---|---|---|
|注册/登录/注册时间|users.username/passwordHash/createdAt|AuthService|auth API、register/login|test_auth_and_csrf、session_expiry、logout_revokes|
|只看自己创建的问卷|surveys.ownerId|SurveyService.owned|GET surveys、dashboard|test_ownership 12实例|
|创建/标题/说明|surveys+survey_versions|create事务|POST surveys、new/editor|C01/C02、full_browser_flow|
|匿名且填写先登录|respondentId内部、anonymousAtSubmission|current_user+owner_submission|public API、统计/答卷|C05、idempotency_stats_versions_privacy|
|发布链接|publicId/publishedVersion|publish/public|publish、/survey/publicId|C07、22步HTTP|
|截止/关闭|status/deadlineAt|public/close/patch|PATCH/close、dashboard|multiple_concurrency_and_deadlines、submission_state_race|
|单选选项/必答|questions.options/required|validate_answer|editor/radio|single_invalid、fixed_paths、browser|
|多选数量限制/恰好2个|validation.min/maxSelections|静态/动态校验|editor/checkbox|multiselect_boundaries、R07/R15|
|文本长度/查看全部内容|validation.min/maxLength、answers|Unicode规范化+分页|textarea/统计明细|text_unicode_and_boundary、分页测试|
|数字范围/整数/均值|number validation/value|validate_answer、StatisticsService|数字控件、均值和回答明细|number_bounds/rejects、integer_and_negative、C06|
|单选/多选/数字跳转|routingRules|静态检查/evaluate/next/trace|可视化规则/逐题填写|R01–R15、operators、browser|
|按顺序、即时错误、提交|嵌入questions/answers|trace_path_and_validate_submission|fill、本地校验+服务端复核|C04/C05、browser非法-1|
|每次填写保存/多人/多次|submissions独立文档|submit事务、幂等唯一索引|submissions API、新一轮按钮|concurrency、multiple_same_user|
|按题/全卷自动统计|版本题目+answers|StatisticsService Mongo聚合|statistics API/页面|C06、分页单题一致测试|
|MongoDB设计/只用Mongo|四集合、BSON、索引、schema|db.mongo/models.documents|init_db|schema_indexes_bson|
|内容版本不可变|sealed/revision/指针|edit CAS/publish/derive|versions/draft/publish|recovery、concurrent_draft、API链路|
|旧版409/历史解释|submission.surveyVersion|提交版本检查/版本过滤|public/submissions/statistics|API链路、browser V1→V2|
|跨版本latest_only|survey.submissionPolicy|先sort/group再版本match|mode/version选择|V1有效0历史2验证|
|匿名承诺不追溯解除|anonymousAtSubmission|allowlist DTO|owner列表/统计|V1匿名→V2实名验证|
|六类测试输入输出|非业务文件|pytest+Playwright|文档/证据|test-cases、final.xml|
|AI日志与项目报告|非业务文件|真实工具/提示引用|docs|ai-usage-log、project-report|
|阶段二不推倒重做|schemaVersion与内容version分离|模块化规则/服务/模型|扩展现有入口|全套回归、ADR|

测试别名为源函数名省略test_前缀，精确名称及每个参数化实例在evidence/case-results.md。业务实现没有问卷特定ID/跳转硬编码；q1..q4仅位于固定测试fixture及演示样例，前端使用随机稳定ID。
