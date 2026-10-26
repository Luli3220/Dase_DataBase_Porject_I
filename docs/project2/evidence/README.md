# 第二阶段证据索引

验证结果按轮次阅读：2026-10-26 首轮为 150 项，2026-10-27 修复后为 167 项。日志、JUnit、环境信息和截图分别保存在各轮目录中。

## 当前验证：2026-10-27

**167 项通过，耗时 64.21 秒**，包含原有 150 项与新增 17 项。

- [本轮目录与文件说明](fixes-2026-10-27/README.md)
- [控制台输出](fixes-2026-10-27/full.txt) · [JUnit](fixes-2026-10-27/full.xml) · [逐项结果](fixes-2026-10-27/case-results.md)
- [环境](fixes-2026-10-27/environment.json) · [交付核对](fixes-2026-10-27/audit.json)
- [修复说明和测试步骤](../fixes-2026-10-27.md)

## 首轮验证：2026-10-26

|内容|结果 / 文件|
|---|---|
|第一阶段基线回归|113 项，[输出](baseline.txt)、[JUnit](baseline.xml)、[截图](baseline/)|
|B：模型与数据库|2 项，[输出](stage-b.txt)、[JUnit](stage-b.xml)|
|C：题目与题库|16 项，[输出](stage-c.txt)、[JUnit](stage-c.xml)|
|D：导入与来源|3 项，[输出](stage-d.txt)、[JUnit](stage-d.xml)|
|E：使用关系与统计|6 项，[输出](stage-e.txt)、[JUnit](stage-e.xml)|
|新增界面后的原功能回归|113 项，[输出](regression.txt)、[JUnit](regression.xml)、[截图](regression/)|
|双账号浏览器验证|1 项，[输出](browser.txt)、[JUnit](browser.xml)、[截图](browser/)|
|权限与竞态|8 项，[输出](boundaries.txt)、[JUnit](boundaries.xml)|
|查询计划与聚合|1 项，[输出](aggregation.txt)、[执行计划](aggregation-audit.json)|
|完整回归|150 项，[输出](full.txt)、[JUnit](full.xml)、[逐项结果](case-results.md)|
|完整回归截图|[full-browser/](full-browser/)|
|环境与核对|[环境](environment.json)、[交付检查](delivery-audit.json)|

阶段测试会在完整回归中再次执行，150 和 167 分别是两轮完整回归的实例数。

## 迁移与问题处理

- 升级指纹：[首次](migration-first.json)、[第二次](migration-second.json)。原四集合共 21 份文档前后一致。
- 数据层首次失败：[stage-b-first.txt](stage-b-first.txt)，对应 BSON 时间精度比较问题。
- 统计诊断首次失败：[stage-e-first.txt](stage-e-first.txt)，对应 explain 返回的主机名解码问题。
- 全套首次收集错误：[full-first.txt](full-first.txt)，对应新旧测试模块同名问题。
- 处理过程见[测试记录](../test-report.md)和[AI 使用日志](../ai-usage-log.md)。

## 后续运行

新运行可放入 [runs/](runs/README.md)，以时间命名子目录。生成命令见[运行手册](../../../source/README.md#4-测试)。

[返回第二阶段索引](../README.md)
