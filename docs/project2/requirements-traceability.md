# 第二阶段需求追踪

根据[需求变更说明](../../requirements/project2-changes.pdf)，第二阶段共有八项新增需求。下表整理数据结构、接口、页面和测试的对应关系，具体开发约定见[实施 Prompt](../../prompts/Project2_Implementation_Prompt.md)。

|需求|数据结构|接口|页面|测试组|
|---|---|---|---|---|
|1 常用题复用|definitions + versions + source|questions / draft/import-question|题目、问卷编辑器|library/import|
|2 跨用户共享|ownerId / sharedWith|sharing / fork|共享用户、独立派生|permissions|
|3 旧问卷稳定|sealed 内嵌快照|旧 public/submit 保留|来源及解除关联|snapshots|
|4 历史恢复|parentVersion / restoredFromVersion|versions / restore|历史、恢复|lineage|
|5 多版并存|精确 questionVersion|import-question 替换实例|导入与显式升级|versions|
|6 使用查询|source 多键索引|usage|使用情况|usage|
|7 题库管理|banks.items 固定/最新|question-banks / items|题库管理、选题|banks|
|8 跨问卷统计|source + submissions + contribution|statistics|范围、口径、数字分布|statistics|

执行结果见[测试记录](test-report.md)，原始输出按轮次保存在[证据目录](evidence/README.md)。


## 测试与证据

|需求|测试文件|对应证据|
|---|---|---|
|R1 复用|[test_import.py](../../source/tests/project2/test_import.py)|[stage-d.xml](evidence/stage-d.xml)|
|R2 共享|[test_library.py](../../source/tests/project2/test_library.py)、[边界](../../source/tests/project2/test_boundaries.py)|[stage-c.xml](evidence/stage-c.xml)、[boundaries.xml](evidence/boundaries.xml)|
|R3 稳定快照|[test_import.py](../../source/tests/project2/test_import.py)|[浏览器快照](evidence/full-browser/p2-frozen-snapshot.png)|
|R4 历史恢复|[test_library.py](../../source/tests/project2/test_library.py)|[历史与统计页](evidence/full-browser/p2-question-history-statistics.png)|
|R5 多版本并存|[test_statistics.py](../../source/tests/project2/test_statistics.py)|[stage-e.xml](evidence/stage-e.xml)|
|R6 使用反查|[test_statistics.py](../../source/tests/project2/test_statistics.py)|[聚合审计](evidence/aggregation-audit.json)|
|R7 题库|[test_library.py](../../source/tests/project2/test_library.py)|[题库截图](evidence/full-browser/p2-bank.png)|
|R8 跨问卷统计|[test_statistics.py](../../source/tests/project2/test_statistics.py)、[浏览器](../../source/tests/project2/test_browser.py)|[完整JUnit](evidence/full.xml)、[1000份答卷审计](evidence/aggregation-audit.json)|

上表对应首轮 150 项回归。2026-10-27 又补充 17 项保存、分页和统计边界测试，完整回归共 167 项通过，详见[修复说明](fixes-2026-10-27.md)与[测试记录](test-report.md)。
