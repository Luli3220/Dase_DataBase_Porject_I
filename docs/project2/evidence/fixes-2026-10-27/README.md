# 2026-10-27 测试日志

本轮检查统一保存、归档分页和统计数量说明，完整回归 **167 项通过，耗时 64.21 秒**。

|文件 / 目录|内容|
|---|---|
|[full.txt](full.txt)、[full.xml](full.xml)|完整回归输出与 JUnit|
|[case-results.md](case-results.md)|167 项逐项结果，标出原 150 项和本次 17 项|
|[environment.json](environment.json)|运行环境、基线、命令及数量|
|[targeted.txt](targeted.txt)、[targeted.xml](targeted.xml)|15 项后端定向验证|
|[targeted-browser.txt](targeted-browser.txt)、[targeted-browser.xml](targeted-browser.xml)|2 项浏览器定向验证|
|[full-browser/](full-browser/)|完整回归的截图与 HTTP 服务日志|
|[targeted-browser/](targeted-browser/)|定向验证中的截图与服务日志|
|[aggregation-audit.json](aggregation-audit.json)|随完整回归再次执行的聚合和索引审计|
|[protected-before.json](protected-before.json)、[audit.json](audit.json)|原文件指纹与本轮核对结果|
|[report-compile.log](report-compile.log)|修订报告的编译记录|

保存冲突页面见 [fix-atomic-conflict.png](full-browser/fix-atomic-conflict.png)：输入保留，保存提示显示冲突；对应测试还检查了数据库内容和请求顺序。

测试步骤和输入见[修复说明](../../fixes-2026-10-27.md)，其他轮次见[日志总索引](../README.md)。
