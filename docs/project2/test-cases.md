# 第二阶段测试用例

测试全部使用独立随机 survey_test_<uuid> 数据库，结束只清理自己创建的测试库；不清理开发数据。新用例在 source/tests/project2；旧用例未删除、跳过或弱化。最终每个测试实例的状态在 [逐项结果](evidence/case-results.md)，执行命令及总数见 [报告](test-report.md)。

|测试组 / 步骤|输入|预期输出|实际与证据|
|---|---|---|---|
|data：反复初始化、模型/BSON回读|旧用户；无source/有source题；非法routingRules入库|7集合；旧文档不变；BSON ObjectId无损；唯一键拒重|test_data.py，stage-b.xml及full.xml|
|library：逐题型创建/检索|四题型；空标题、矛盾上下限、bool数值、极大数、额外字段|合法201；非法422；搜索.*按字面处理|test_library.py，stage-c.xml及full.xml|
|lineage：v1→v2，再由v1创建v3，恢复v1|expectedCurrentVersion、任意parentVersion|单调版本、正确父链；恢复追加；旧记录不变|test_lineage_restore_fork_and_conflict|
|sharing：A私有→分享B→撤销|合法/缺失用户、大小写重复用户名|私有404；共享可读；B不能改写；撤销后不可新增引用|sharing及private_endpoints用例|
|bank：创建两题库、加入同一题、更新成员、移除|固定v1、未固定最新、过期revision|不重复；固定不漂移；最新选择解析v2；移除不删原题|sharing_permissions_banks / import_limits用例|
|import：同一题导入A/B并发布|相同全局Q/v1、不同局部ID|快照内容相同、局部ID不同、历史冻结|test_import.py，stage-d.xml|
|source：关联题改标题、删除source再编辑|伪造source、合法路由、重复全局题|假来源409；解除后200；路由独立；重复422|source_forgery / snapshots用例|
|history stability：更新v2、撤销、归档|已发布v1、派生新草稿|旧公开题不变；已保留快照可保存；新引用拒绝|snapshots_sources_upgrade_detach_and_archive|
|usage：跨元素组合及私有问卷查询|同数组Q/v1与R/v2；查询Q/v2|不得误配；私有记录/数量不泄漏；自有草稿/发布正确区分|usage_visibility_elem_match用例|
|statistics：数字多次提交再升级版本|18→30，v2再60；multiple负数/小数/边界/安全最大值|先全问卷去重再筛版本；v1有效0；原始2；分桶不重不漏|test_statistics.py，stage-e.xml|
|choice：跨三问卷汇总单选/多选|a,b,a；[a,b],[b],[a]|单选2/1，多选2/2；单位为提交，不称独立人数|choice_across_surveys两参数实例|
|path：前题触发结束跳过目标题|存在目标快照但无目标答案|submissionCount=1、answeredCount=0、mean=null|usage_visibility_elem_match_and_skipped_answers|
|privacy：外部文本问卷贡献授权开关|2份/3份实际回答、贡献false→true→false|2份抑制；3份计入；无文本原文/ID/私密标题；撤销排除|cross_user_consent_suppression用例|
|concurrency：并发追加/题库/导入|同expected版本或revision|仅一成功，另一显式409；不丢更新、无重复版本|concurrent_append_and_bank / import_concurrency|
|races：撤销共享对导入，发布对导入|两线程同时操作同定义/草稿|可串行解释；成功快照完整；失败需刷新重试|test_boundaries.py|
|query audit：真实聚合1000份合成答卷|数字0..999、同一精确题目版本|count1000，mean499.5；分桶合计1000；来源索引IXSCAN、examined=1|aggregation-audit.json；不称容量压测|
|browser：双账号全链路|A共享/B导入，年龄18/24/30/45，v2与恢复v3|旧问卷v1；mine均值18、贡献后29.25；390px无溢出；无JS异常|test_browser.py、full-browser/p2-*.png|
|Project1完整回归|原113项原样执行|注册、编辑、发布、四题型、跳转、校验、匿名、幂等、统计继续通过|regression.xml、最终full.xml|

新测试对实际输出使用明确断言，失败不会静默跳过。最终 full.xml 为权威汇总；阶段文件记录各阶段执行，不重复相加充当测试总数。
