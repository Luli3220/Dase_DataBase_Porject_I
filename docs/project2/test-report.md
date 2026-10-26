# 第二阶段独立测试报告

执行日期：2026-10-26（Asia/Shanghai）。基线 Commit `61e226387140ee7ca9f985bf010769c823253a1c`，Tag `project1-baseline-61e2263`；新实现位于独立分支 `project2/question-library` 的未提交工作树。最终验收：**150 passed / 0 failed / 0 errors / 0 skipped，43.57秒**。其中原测试113项、新增37项。完整 [输出](evidence/full.txt)、[JUnit](evidence/full.xml)、[逐项结果](evidence/case-results.md)、[环境](evidence/environment.json)。第一阶段历史记录不覆盖。

环境：Windows，Python3.11.5，MongoDB8.3.11单节点rs0，PyMongo4.19.0，FastAPI0.115.7，Pydantic2.12.5，pytest8.4.2，Playwright1.64.0及Chromium。使用原 .venv 和已有 Mongo 数据目录；测试采用独立随机数据库，浏览器服务在8001临时启动。

从 source 执行的最终命令：

```powershell
$env:TEST_EVIDENCE_DIR='../docs/project2/evidence/full-browser'
..\.venv\Scripts\python.exe -m pytest -q --junitxml=../docs/project2/evidence/full.xml
..\.venv\Scripts\python.exe -m scripts.build_evidence
```

|执行|真实结果|证据|
|---|---|---|
|A 原系统基线|113 passed，29.55s|baseline.txt/xml；截图baseline/|
|B 模型、验证器、索引|2 passed，0.41s|stage-b.txt/xml|
|C 题目、共享、版本、题库|16 passed，6.09s|stage-c.txt/xml|
|D 导入、快照与来源|3 passed，1.67s|stage-d.txt/xml|
|E 使用关系与跨问卷统计|6 passed，2.91s|stage-e.txt/xml|
|增量UI后原系统回归|113 passed，25.27s|regression.txt/xml|
|双账号UI含真实提交、移动端|1 passed，10.02s|browser.txt/xml；browser/p2-*.png|
|权限与竞态补充|8 passed，3.12s|boundaries.txt/xml|
|1000份答卷聚合与执行计划|1 passed，0.99s|aggregation.txt/xml；aggregation-audit.json|
|最终全套|150 passed，43.57s|full.txt/xml；full-browser/|

阶段结果不能相加作为总数；有些用例在后续完整回归中重复执行，full.xml是最终权威汇总。

真实失败及修正：初次Mongo后台启动不稳定，改用现有目录的前台托管进程后基线通过；B阶段第一次1 failed/1 passed是BSON毫秒与Python微秒比较，改为比较持久化前后记录；E阶段首次5 passed/1 failed是本机explain返回非UTF8主机名，仅对诊断显式指定宽容解码；最终全套首次2 collection errors是新旧测试文件同名，通过新增project2/__init__.py修正。原输出保留 [B失败](evidence/stage-b-first.txt)、[E失败](evidence/stage-e-first.txt)、[收集错误](evidence/full-first.txt)。没有将首次错误计为通过。

真实浏览器证据为 full-browser/p2-bank.png、p2-frozen-snapshot.png、p2-question-history-statistics.png、p2-mobile.png。所有账号为随机测试账号。A拥有的问卷年龄18；B的multiple问卷年龄24、30、45并贡献，mine均值18，共享范围均值29.25；v2更新和恢复为v3后已发布v1不变。页面无JavaScript异常，390px无水平溢出。原浏览器流程也在同次运行执行。

聚合审计：1000份数字答卷0..999，answeredCount=1000、mean=499.5、分桶总和=1000。来源反查查询执行计划IXSCAN，nReturned=1、keysExamined=1、docsExamined=1。该样本只验证持久化聚合与索引可用性，不是生产压测，也不证明全量统计具有固定延迟。

迁移实际连续执行2次，原四集合共21份文档前后SHA256指纹一致，详见 [迁移](migration.md)。最终还执行pip check、JavaScript语法、OpenAPI与路由一致性、旧API保留、历史文件校验及Markdown本地链接检查，机器可复核汇总见 [delivery-audit.json](evidence/delivery-audit.json)。

未验证：Docker容器构建/运行、公网HTTPS部署、Firefox/WebKit、多节点故障转移、生产容量、数据库备份恢复及部署回滚。小样本阈值是基础数据抑制规则，不构成差分隐私或防所有差分查询攻击的证明。
