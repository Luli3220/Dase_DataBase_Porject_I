# 测试导航

测试覆盖规则、真实 MongoDB、HTTP API 和 Chromium 页面流程。最近完整结果为 **167 项通过**，原始输出见[2026-10-27 验证目录](../../docs/project2/evidence/fixes-2026-10-27/README.md)。

|目录 / 文件|内容|
|---|---|
|[unit/](unit/)|规则引擎、数值边界和答卷响应字段|
|[integration/](integration/)|数据库、API、匿名、幂等、并发和用户名查询|
|[web/test_browser.py](web/test_browser.py)|第一阶段桌面与移动端流程|
|[project2/](project2/README.md)|题目、题库、版本、跨问卷统计及本次修复|
|[conftest.py](conftest.py)|每个测试独立的 MongoDB 数据库|
|[fixtures.py](fixtures.py)|四题样例和答案输入|

前面三个目录对应第一阶段的 113 项测试；`project2/` 包含首轮 37 项及后续修复 17 项。完整回归会一起收集。

## 执行方式

在 `source/` 目录运行：

```powershell
..\.venv\Scripts\python.exe -m pytest tests/unit -q
..\.venv\Scripts\python.exe -m pytest tests/project2 -q
```

集成测试需要本机 MongoDB 副本集，浏览器测试还需 Chromium。完整回归、依赖安装和按轮次保存输出的命令见[运行手册](../README.md#4-测试)。

各用例使用随机 `survey_test_<uuid>` 数据库并在结束后清理。测试步骤与输入见[第二阶段测试用例](../../docs/project2/test-cases.md)，历史执行记录见[证据索引](../../docs/project2/evidence/README.md)。
