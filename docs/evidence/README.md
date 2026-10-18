# 测试证据索引：当前结论与历史过程

## 当前代码最近一次完整验收

|入口|内容|
|---|---|
|[respondent-username/README.md](respondent-username/README.md)|用户名修正的功能范围、测试命令与兼容性|
|[full.txt](respondent-username/full.txt) / [full.xml](respondent-username/full.xml)|113 passed，0失败/错误/跳过，37.82秒；72单元+39数据库/API+2浏览器|
|[targeted.txt](respondent-username/targeted.txt) / [targeted.xml](respondent-username/targeted.xml)|11个新增实例通过，7.02秒|
|[原始环境错误](respondent-username/initial-no-mongo.txt) / [JUnit](respondent-username/initial-no-mongo.xml)|Mongo未启动时4通过、7个setup errors；保留错误记录，不计为成功|

该目录的截图及browser-server.log来自真实Chromium测试。桌面流程覆盖编辑、预览、发布、填写、跨版本统计，手机流程验证390px表单；不是113个浏览器测试，也不是113轮完整流程。

## 其他历史证据

|文件/目录|当时作用|结果/定位|
|---|---|---|
|phase-a.txt/xml|数据库/规则阶段验收|72项通过|
|phase-b-api.txt/xml|API阶段验收|17项通过|
|phase-b-http.json、[final-http.json](final-http.json)|真实HTTP独立演示|22个请求检查；不计入pytest的113项|
|browser.txt/xml|首次浏览器验收|2项通过|
|regression.txt/xml|边界测试扩充后的中间回归|98项通过|
|[final.txt](final.txt)、[final.xml](final.xml)、[case-results.md](case-results.md)|首轮完整验收|102项；文件名final是当时命名，不代表当前最新数量|
|environment.json、static-checks.json|首次测试环境/静态检查|时间点记录，不能当作当前部署状态|
|[restructure/](restructure/README.md)|目录迁移后独立回归|102项通过，31.82秒；保留迁移证据|
|根目录png、上述两轮目录png|不同阶段实际界面|按对应测试轮次查阅，无需逐一阅读|

2026-10-18报告审核解析了原始JUnit和当前测试收集，确认数量一致，机器核对摘要见[document-review-2026-10-18.json](document-review-2026-10-18.json)；本次没有重跑MongoDB/API/浏览器测试。当前结果仍引用最近一次真实完整执行，不虚构新执行时间。详细测试步骤和结果解释见 [test-cases](../test-cases.md) 与 [test-report](../test-report.md)。
