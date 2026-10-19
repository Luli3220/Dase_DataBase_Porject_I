# 测试记录

完整验收结果为 **113项通过，耗时37.82秒**，包括72项单元测试、39项数据库及接口集成测试，以及2项浏览器测试。

## 完整验收

|文件|内容|
|---|---|
|[执行输出](respondent-username/full.txt)|完整测试的终端汇总|
|[逐项结果](case-results.md)|测试名称、状态及耗时|
|[JUnit](respondent-username/full.xml)|机器可读的完整执行记录|
|[用户名修正验证](respondent-username/README.md)|匿名、实名、跨版本与批量查询的测试说明|
|[HTTP检查](final-http.json)|22项独立HTTP请求检查|

## 阶段记录

|文件|结果|
|---|---|
|[数据库与规则阶段](phase-a.txt)|72项通过|
|[API阶段](phase-b-api.txt)|17项通过|
|[首次完整交付](final.txt)|102项通过|
|[用户名修正新增测试](respondent-username/targeted.txt)|11项通过|
|[环境错误记录](respondent-username/initial-no-mongo.txt)|MongoDB未启动时出现7项测试准备错误，启动后重跑通过|

## 界面截图

[问卷编辑](respondent-username/editor.png) · [发布结果](respondent-username/published.png) · [统计页面](respondent-username/statistics.png) · [手机表单](respondent-username/mobile.png)

## 更新记录

测试命令见[运行手册](../../source/README.md)。完成测试后，在source目录生成逐项索引：

```powershell
..\.venv\Scripts\python.exe -m scripts.build_evidence --index-only
```

该命令读取full.xml，更新case-results.md。测试步骤和结果分析分别见[测试用例](../test-cases.md)与[测试报告](../test-report.md)。
