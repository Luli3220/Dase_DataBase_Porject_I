# 测试报告

完整功能验收结果为 **113 passed、0 failed、0 skipped，耗时37.82秒**。其中包括72项单元测试、39项数据库及接口集成测试，以及2项浏览器测试。执行输出和各测试实例可通过[原始汇总](evidence/respondent-username/full.txt)、[JUnit](evidence/respondent-username/full.xml)及[逐项记录](evidence/case-results.md)查看。

## 测试环境

测试在Windows、Python3.11.5和MongoDB8.3.11单节点副本集rs0环境下执行。后端使用FastAPI0.115.7、PyMongo4.19.0和Pydantic2.12.5；测试工具为pytest8.4.2、httpx与Playwright1.64.0，浏览器流程使用Chromium。

项目采用独立虚拟环境，依赖版本见[requirements-lock.txt](../source/requirements-lock.txt)。集成测试使用随机survey_test_<uuid>数据库，各用例结束后清理自己的测试数据。

## 执行结果

|测试范围|结果|记录|
|---|---|---|
|完整功能验收|113项通过，37.82秒|[full.txt](evidence/respondent-username/full.txt)、[full.xml](evidence/respondent-username/full.xml)|
|用户名修正新增测试|11项通过，7.02秒|[targeted.txt](evidence/respondent-username/targeted.txt)|
|新增测试首次执行|4项通过、7项准备错误，41.03秒；MongoDB未启动|[环境错误](evidence/respondent-username/initial-no-mongo.txt)|
|独立HTTP检查|22项请求检查通过|[final-http.json](evidence/final-http.json)|
|数据库与规则阶段|72项通过，2.75秒|[phase-a.txt](evidence/phase-a.txt)|
|API阶段|17项通过，14.90秒|[phase-b-api.txt](evidence/phase-b-api.txt)|
|首次完整交付|102项通过，31.36秒|[final.txt](evidence/final.txt)|

各行对应不同阶段的执行结果。当前完整功能验收以113项为准，22项HTTP检查单独记录。

## 测试范围

- **基本功能**：创建问卷、添加四类题目、条件跳转、答案校验、提交与统计。详细步骤和输入输出见[测试用例](test-cases.md)。
- **身份与权限**：注册登录、会话过期、退出撤销、CSRF、12类管理越权操作和请求大小限制。
- **版本与并发**：草稿修订冲突、并发派生、发布中断恢复、提交与关闭/切版竞争、首次提交后的策略锁定。
- **答卷与统计**：幂等提交、追加保存、跨版本latest_only、multiple策略、分页、均值及单题/全卷一致性。
- **用户名与匿名**：实名答卷展示用户名，历史匿名保持隐藏，关联账号缺失回退，当前页批量查询。
- **浏览器流程**：编辑、预览、发布、登录返回、逐题填写、分支修改、重复填写、版本变化及390px手机表单。

## 问题处理

初期环境中的Python版本和依赖不一致，随后改用3.11.5独立环境并固定依赖；pip check通过。MongoDB后台进程曾无法持续连接，因此采用常驻本机副本集完成数据库测试。

代码检查还发现了日期输入解析和极大整数判断的边界风险。修正后补充了无时区日期、非法数字及10**1000等用例。页面显示方面，选项由内部ID映射为对应版本的标签，非匿名填写者则通过批量查询显示注册用户名。

用户名修正首次测试因MongoDB未启动产生准备错误，数据库启动后新增11项及完整113项均通过。发布恢复测试采用故障注入，检查冻结后中断的版本能否继续完成发布。相关需求和修改过程见[AI使用说明](ai-usage-log.md)。

## 界面与复现

[问卷编辑](evidence/respondent-username/editor.png) · [发布结果](evidence/respondent-username/published.png) · [统计页面](evidence/respondent-username/statistics.png) · [手机表单](evidence/respondent-username/mobile.png)

在source目录准备好Mongo副本集和Chromium后执行：

```powershell
$env:TEST_EVIDENCE_DIR='../docs/evidence/respondent-username'
..\.venv\Scripts\python.exe -m pytest -q --junitxml=../docs/evidence/respondent-username/full.xml
..\.venv\Scripts\python.exe -m scripts.build_evidence --index-only
```

也可从仓库根运行source/scripts/run-tests.ps1。第二条命令读取JUnit并更新结果索引。

## 后续验证

本轮验证以本机环境为主。Docker已完成配置解析，后续还需验证容器运行、其他MongoDB版本和浏览器引擎的兼容性，并进一步评估公网HTTPS部署、容量及多节点故障恢复。
