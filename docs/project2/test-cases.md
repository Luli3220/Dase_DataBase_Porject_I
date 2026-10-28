# 第二阶段测试用例

第二阶段新增 54 项测试，与第一阶段的 113 项一起执行。用例覆盖题目复用、共享、版本、题库、统计和后续修复，代码见 [source/tests/project2](../../source/tests/project2/README.md)。数据库测试使用独立的随机测试库。

## 题目、题库与问卷集成

|步骤|输入|预期结果|测试入口|
|---|---|---|---|
|初始化数据库并读写来源字段|旧用户、无来源及带来源的题目、重复版本|七集合初始化可重复执行；旧文档不变；来源保存为 BSON ObjectId；唯一索引拒绝重复版本|[数据模型](../../source/tests/project2/test_data.py)|
|创建和搜索四类题目|合法配置、空标题、矛盾范围、非法数字、额外字段及搜索词 .*|合法请求返回 201，非法配置返回 422；搜索按字面匹配|[题目管理](../../source/tests/project2/test_library.py)|
|创建历史版本、恢复和 fork|v1→v2，再从 v1 派生；恢复 v1|版本递增并记录实际父版本；恢复追加版本；fork 获得独立身份|[版本与题库](../../source/tests/project2/test_library.py)|
|共享、使用并撤销|已注册及不存在的用户名、大小写重复用户名、非所有者请求|私有题目返回 404；共享后可读可用；修改权由所有者持有；撤销后新引用被拒绝|[权限边界](../../source/tests/project2/test_boundaries.py)、[共享](../../source/tests/project2/test_library.py)|
|将同一题加入多个题库，再修改或移除成员|固定 v1、选题时最新、过期 revision|同库成员不重复；固定版本保持不变；最新成员解析新版本；移除只改变成员关系|[题库管理](../../source/tests/project2/test_library.py)|
|同一题导入两份问卷并发布|相同全局题目和版本|来源相同、局部 ID 不同，发布内容固定|[问卷导入](../../source/tests/project2/test_import.py)|
|修改关联题的内容、路由或来源|改标题、删除 source、增加局部规则、重复引用同一全局题|内容不一致返回 SOURCE_MISMATCH；解除后可本地编辑；路由独立校验；重复引用被拒绝|[来源校验](../../source/tests/project2/test_import.py)|
|更新库题、撤销共享和归档|已发布 v1 及其派生草稿|旧问卷继续使用原内容，已有快照可保存，新引用按当前权限判断|[快照稳定性](../../source/tests/project2/test_import.py)|
|查询使用关系|同数组包含 Q/v1 与 R/v2，查询 Q/v2；查看他人私有问卷|身份与版本匹配同一元素；只返回可见问卷及版本|[使用关系](../../source/tests/project2/test_statistics.py)|

## 统计与并发

|步骤|输入|预期结果|测试入口|
|---|---|---|---|
|重复填写后升级问卷版本|旧版依次提交 18、30，新版提交 60|latest_only 先跨版本选最新提交；旧版有效数为 0，历史原始数为 2|[统计口径](../../source/tests/project2/test_statistics.py)|
|跨三份问卷汇总选择题|单选 a、b、a；多选 [a,b]、[b]、[a]|单选频数 2/1，多选频数 2/2，按提交次数统计|[选项频数](../../source/tests/project2/test_statistics.py)|
|检查数字边界、空数据和跳题|负数、小数、分桶边界、安全极值；前题直接结束|分桶完整且无重复；跳题回答数为 0，空均值为 null|[数值与路径](../../source/tests/project2/test_statistics.py)|
|切换外部问卷贡献授权|2 次及 3 次文本回答；贡献 false→true→false|2 次样本抑制，3 次计入，撤销后排除；跨问卷结果仅返回聚合字段|[贡献权限](../../source/tests/project2/test_statistics.py)|
|并发追加版本、修改题库或导入草稿|相同的期望版本或 revision|一个请求成功，另一个返回冲突；版本唯一且更新完整|[版本与题库](../../source/tests/project2/test_library.py)、[导入](../../source/tests/project2/test_import.py)|
|共享撤销、发布与导入同时进行|两线程操作同一题目或草稿|结果对应完整的先后顺序，发布快照一致，冲突可刷新重试|[并发边界](../../source/tests/project2/test_boundaries.py)|
|检查聚合结果与来源索引|1,000 份数字答卷，取值 0–999|回答数 1,000、均值 499.5、分桶合计 1,000；来源查询使用 IXSCAN|[查询检查](../../source/tests/project2/test_aggregation_plan.py)|

## 浏览器流程与后续修复

[双账号浏览器测试](../../source/tests/project2/test_browser.py)串联创建、共享、题库选题、发布、填写、版本更新和恢复。年龄输入为 18、24、30、45，检查本人范围均值 18、贡献范围均值 29.25，以及旧问卷 v1 内容和 390px 布局。

2026-10-27 新增 15 项后端和 2 项浏览器测试，覆盖联合保存回滚、冲突时保留输入、归档分页和统计问卷数。详细步骤、输入与结果见[修复测试表](fixes-2026-10-27.md#测试步骤与结果)。

## 执行结果

首轮完整回归为 150 项，后续修复后为 167 项，均全部通过。原认证、四题型、跳转、校验、发布、匿名、幂等提交和单问卷统计一同回归。执行命令与环境见[测试记录](test-report.md)，各项状态见[167 项结果](evidence/fixes-2026-10-27/case-results.md)，各轮输出见[日志索引](evidence/README.md)。
