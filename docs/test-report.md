# 实际测试报告

最近一次完整功能验收为 **113 passed / 0 failed / 0 errors / 0 skipped，37.82秒**。原始[终端汇总](evidence/respondent-username/full.txt)、[JUnit](evidence/respondent-username/full.xml)和[逐项索引](evidence/case-results.md)对应同一轮执行。不同阶段的测试数量不能累加。

## 环境与实际结果

执行环境：Windows、Python3.11.5、MongoDB8.3.11单节点副本集rs0（27018）；FastAPI0.115.7、PyMongo4.19.0、Pydantic2.12.5、pytest8.4.2、Playwright1.64.0，使用真实Chromium。依赖版本见[source/requirements-lock.txt](../source/requirements-lock.txt)，虚拟环境没有继承系统包。

|执行范围|实际结果|当前保留证据|
|---|---|---|
|全部现有及新增测试|113项通过，37.82秒；72单元、39数据库/API/并发、2浏览器|[full.txt](evidence/respondent-username/full.txt)、[full.xml](evidence/respondent-username/full.xml)|
|用户名修正新增测试|11项通过，7.02秒|[targeted.txt](evidence/respondent-username/targeted.txt)|
|首次新增测试，Mongo未启动|4通过、7项setup errors，41.03秒；连接错误10061|[initial-no-mongo.txt](evidence/respondent-username/initial-no-mongo.txt)|
|独立真实HTTP演示|22个请求检查PASS，包括预期403/409；不计入pytest113项|[final-http.json](evidence/final-http.json)|
|Phase A数据库/规则阶段|72项通过，2.75秒|[phase-a.txt](evidence/phase-a.txt)|
|Phase B API阶段|17项通过，14.90秒|[phase-b-api.txt](evidence/phase-b-api.txt)|
|首次完整交付|102项通过，31.36秒|[final.txt](evidence/final.txt)，这是历史命名|

目录整理阶段另有102项通过（31.82秒）；旧浏览器/中间回归、目录检查及详细安装日志已精简，可在[对应提交](https://github.com/Luli3220/Dase_DataBase_Porject_I/tree/795c8b8c9a34ecf4275aa295325a201f3e1014de/docs/evidence)回溯。没有把被精简文件当作当前目录中的附件。

## 覆盖内容

- 课程六项：创建问卷、添加题目、跳转、校验、提交、统计；步骤、输入、预期和实际结果见[测试用例](test-cases.md)。
- 权限/认证：注册、登录、退出、过期、复制Cookie撤销、CSRF、12类所有者越权操作和请求大小限制。
- 版本/并发：草稿revision冲突、并发派生、冻结后发布恢复、关闭/切版与提交竞争、策略首份成功后锁定。
- 答卷/统计：幂等、每次追加、latest_only跨版本先去重后筛选、multiple、分页、均值、单题与全卷一致。
- 身份显示：非匿名新增注册用户名，匿名严格省略ID及用户名，双向跨版本保持提交快照；真实Mongo命令监听确认本页只执行一次去重用户查询，匿名/空页不查询。
- 浏览器：编辑四类题和跳转规则、预览不入库、登录返回公开链接、非法输入提示、切换分支清除旧答案、重复填写、版本变化、关闭及390px手机表单。

## 实际问题与修复

1. conda db为Python3.10.21且启动器异常，依赖不全。使用独立3.11.5环境，关闭系统包继承，pip check通过。
2. 沙箱pip网络异常、Docker daemon未运行、后台Mongo进程曾无法持续连接。调整依赖安装方式并使用常驻本机rs0，不以模拟数据库代替真实集成。
3. 审查发现日期严格解析和极大整数转换的边界风险。仅允许必要的日期解析、仍拒绝无时区时间；数值先判断安全范围再判断有限性，加入10**1000用例。此项不虚称已经发生过测试失败。
4. 页面曾直接显示选项ID和非匿名填写者ID。选项按历史版本映射标签；注册用户名通过当前页批量查询补充，继续按anonymousAtSubmission过滤，保持原ID兼容。
5. 用户名修正的首次测试因Mongo未启动出现准备错误；复用原目录启动数据库后，新增11项和完整113项均通过。原始错误文本保留，没有改写为PASS。

发布中断由测试主动注入，是预期故障恢复验证。更完整的需求/修改过程见[第一人称AI使用说明](ai-usage-log.md)。

## 界面证据与复现

只保留最新一轮的一组真实截图：[编辑器](evidence/respondent-username/editor.png)、[发布结果](evidence/respondent-username/published.png)、[统计界面](evidence/respondent-username/statistics.png)、[手机表单](evidence/respondent-username/mobile.png)。图片含随机测试账号，不是真实用户账号，亦不是合成截图。

在source目录、Mongo副本集及Chromium可用时执行：

```powershell
$env:TEST_EVIDENCE_DIR='../docs/evidence/respondent-username'
..\.venv\Scripts\python.exe -m pytest -q --junitxml=../docs/evidence/respondent-username/full.xml
..\.venv\Scripts\python.exe -m scripts.build_evidence --index-only
```

也可从仓库根运行source/scripts/run-tests.ps1。测试每例只清理本次随机分配的survey_test_库，不清空survey_dev。--index-only只从已有JUnit生成索引，不运行测试，也不要求Mongo在线。

## 未验证范围与文档维护

Docker仅配置解析通过，容器构建/运行未验证；未单独运行Mongo7/8.0兼容性、公网HTTPS部署、多节点故障转移、容量压测或其他浏览器引擎。单节点副本集不代表高可用生产部署。

2026-10-18报告核对只解析历史结果并收集当前113项；本次证据清理同样没有重新执行功能测试。清理将48个证据文件减少到15个，保留最新完整成功、必要阶段摘要和一份失败输出，删除重复格式及多轮相同页面截图；原始保留文件未改内容，旧文件可由Git历史找回。必要的索引工具和测试输出路径同步调整，业务代码及测试断言不变。
