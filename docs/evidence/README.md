# 测试证据索引

本目录保留15个必要文件。最新完整功能验收是 **113 passed / 0 failed / 0 errors / 0 skipped，37.82秒**；旧轮次的重复截图、重复XML和安装/服务器日志已精简，历史版本仍可从Git回溯。

## 建议阅读顺序

|入口|作用|
|---|---|
|[full.txt](respondent-username/full.txt)|最新113项完整验收的原始终端汇总；正式PDF已引用|
|[逐项结果](case-results.md) / [full.xml](respondent-username/full.xml)|113个实例的名称、状态、耗时；索引由已有JUnit生成，不是新一轮测试|
|[本轮验证说明](respondent-username/README.md)|用户名修正、匿名/跨版本、批量查询与兼容性|
|[final-http.json](final-http.json)|22项真实HTTP请求检查；独立于pytest，正式PDF已引用|
|[测试用例](../test-cases.md) / [测试报告](../test-report.md)|步骤、输入、预期/实际结果、环境与问题说明|

113项包括72单元、39真实MongoDB/API/并发、2浏览器实例。不是113个浏览器测试，也不能把不同阶段数量累加成总数。

## 其他保留材料

|材料|保留理由|
|---|---|
|[phase-a.txt](phase-a.txt)、[phase-b-api.txt](phase-b-api.txt)、[final.txt](final.txt)|少量原始阶段摘要：72、17、首轮102项通过；final.txt是历史命名，不是当前最新结果|
|[targeted.txt](respondent-username/targeted.txt)|11项新增测试单独执行的汇总|
|[initial-no-mongo.txt](respondent-username/initial-no-mongo.txt)|首次Mongo未启动时4通过、7项准备错误的原始输出，保留问题及恢复过程|
|[editor.png](respondent-username/editor.png)、[published.png](respondent-username/published.png)、[statistics.png](respondent-username/statistics.png)、[mobile.png](respondent-username/mobile.png)|只保留最新一轮的一组真实页面截图；统计截图已被正式PDF引用|

目录整理回归、初次浏览器测试等中间记录可查看[对应历史提交](https://github.com/Luli3220/Dase_DataBase_Porject_I/tree/795c8b8c9a34ecf4275aa295325a201f3e1014de/docs/evidence)。当前目录不再同时维护多套相同页面截图。失败记录只保留原始txt，完整成功验收保留txt和机器可读XML；这些格式承担不同用途。

## 如何更新

从仓库根目录运行`source/scripts/run-tests.ps1`，或按[source/README](../../source/README.md)执行测试；结果和截图写入保留的同一目录。随后在source中执行：

```powershell
..\.venv\Scripts\python.exe -m scripts.build_evidence --index-only
```

该命令只根据已有full.xml重建逐项索引，不连接MongoDB、不生成新的环境/OpenAPI文件，也不执行测试。本次清理保留原始日志/截图内容，未重新运行功能测试，未将旧记录日期改为本次清理日期。
