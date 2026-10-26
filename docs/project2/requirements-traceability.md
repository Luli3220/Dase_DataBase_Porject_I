# 第二阶段需求追踪

基线：`61e226387140ee7ca9f985bf010769c823253a1c`，本地 Tag `project1-baseline-61e2263`；开发分支 `project2/question-library`。需求来源为用户提供《大作业一：需求变更.pdf》，其原样副本保存在 [project2-changes.pdf](../../requirements/project2-changes.pdf)，实施契约见 [Prompt](../../prompts/Project2_Implementation_Prompt.md)。

|需求|结构|接口|页面|测试组|
|---|---|---|---|---|
|1 常用题复用|definitions + versions + source|questions / draft/import-question|题目、问卷编辑器|library/import|
|2 跨用户共享|ownerId / sharedWith|sharing / fork|共享用户、独立派生|permissions|
|3 旧问卷稳定|sealed 内嵌快照|旧 public/submit 保留|来源及解除关联|snapshots|
|4 历史恢复|parentVersion / restoredFromVersion|versions / restore|历史、恢复|lineage|
|5 多版并存|精确 questionVersion|import-question 替换实例|导入与显式升级|versions|
|6 使用查询|source 多键索引|usage|使用情况|usage|
|7 题库管理|banks.items 固定/最新|question-banks / items|题库管理、选题|banks|
|8 跨问卷统计|source + submissions + contribution|statistics|范围、口径、数字分布|statistics|

执行结果和可复现证据在 [测试报告](test-report.md) 中补齐；不以第一阶段历史结果替代本阶段执行。


## 最终验收映射（八项均已完成）

|需求|真实测试文件|对应证据|
|---|---|---|
|R1 复用|[test_import.py](../../source/tests/project2/test_import.py)|[stage-d.xml](evidence/stage-d.xml)|
|R2 共享|[test_library.py](../../source/tests/project2/test_library.py)、[边界](../../source/tests/project2/test_boundaries.py)|[stage-c.xml](evidence/stage-c.xml)、[boundaries.xml](evidence/boundaries.xml)|
|R3 稳定快照|[test_import.py](../../source/tests/project2/test_import.py)|[浏览器快照](evidence/full-browser/p2-frozen-snapshot.png)|
|R4 历史恢复|[test_library.py](../../source/tests/project2/test_library.py)|[历史与统计页](evidence/full-browser/p2-question-history-statistics.png)|
|R5 多版本并存|[test_statistics.py](../../source/tests/project2/test_statistics.py)|[stage-e.xml](evidence/stage-e.xml)|
|R6 使用反查|[test_statistics.py](../../source/tests/project2/test_statistics.py)|[聚合审计](evidence/aggregation-audit.json)|
|R7 题库|[test_library.py](../../source/tests/project2/test_library.py)|[题库截图](evidence/full-browser/p2-bank.png)|
|R8 跨问卷统计|[test_statistics.py](../../source/tests/project2/test_statistics.py)、[浏览器](../../source/tests/project2/test_browser.py)|[完整JUnit](evidence/full.xml)、[1000份答卷审计](evidence/aggregation-audit.json)|

最终同次运行150 passed/43.57s（原113+新增37），无失败/错误/跳过，见 [test-report.md](test-report.md)。
