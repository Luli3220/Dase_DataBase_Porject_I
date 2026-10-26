# 第二阶段测试

|测试文件|实例数|覆盖内容|
|---|---|---|
|[test_data.py](test_data.py)|2|来源字段、BSON 映射、验证器与索引|
|[test_library.py](test_library.py)|16|四题型、版本、共享、fork、恢复、题库与并发|
|[test_import.py](test_import.py)|3|固定版本导入、来源一致性、快照与草稿竞争|
|[test_statistics.py](test_statistics.py)|6|精确版本、频数、分布、贡献授权与使用查询|
|[test_boundaries.py](test_boundaries.py)|8|私有接口、规模约束、共享撤销和发布竞态|
|[test_browser.py](test_browser.py)|1|双账号题目复用、恢复、填写和统计流程|
|[test_aggregation_plan.py](test_aggregation_plan.py)|1|1,000 份答卷的聚合与来源索引执行计划|
|[test_fixes_20261027.py](test_fixes_20261027.py)|15|原子保存回滚、归档分页及 surveyCount 边界|
|[test_fixes_browser_20261027.py](test_fixes_browser_20261027.py)|2|保存冲突输入保留与混合归档分页|

共 54 项，与第一阶段 113 项一起构成当前 167 项完整回归。参数化测试的每组输入单独计为一个实例。

[返回测试导航](../README.md) · [逐项结果](../../../docs/project2/evidence/fixes-2026-10-27/case-results.md) · [修复步骤](../../../docs/project2/fixes-2026-10-27.md)
