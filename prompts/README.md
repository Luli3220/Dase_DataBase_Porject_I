# 开发 Prompt 索引

Prompt 按项目阶段组织。课程原始要求与变更文件见[需求目录](../requirements/README.md)。

## 第一阶段

|顺序|文件|内容|
|---|---|---|
|00|[总控 Prompt](00-总控Prompt.md)|实施顺序、整体约束和阶段验收|
|01|[数据库与规则引擎](01-数据库与规则引擎.md)|MongoDB 模型、版本、匿名、重复填写和规则语义|
|02|[后端 API 与网页](02-后端API与网页.md)|认证、权限、接口和网页交互|
|03|[测试文档与验收](03-测试文档与验收.md)|测试步骤、证据和交付材料|

辅助资料：[完整合并 Prompt](完整实施Prompt.md)、[最初规格导读](original-specification-readme.md)。

## 第二阶段

[Project2_Implementation_Prompt.md](Project2_Implementation_Prompt.md)说明题目复用、共享、不可变版本、题库、反向查询和跨问卷统计的实施约定，也规定了代码、当前技术文档和阶段证据的组织方式。

实施结果见[第二阶段材料](../docs/project2/README.md)，最近修复见[保存、分页与统计说明](../docs/project2/fixes-2026-10-27.md)。

Prompt 中的 `app/`、`scripts/` 和 `tests/` 路径对应仓库的 `source/` 目录。实际启动命令见[运行手册](../source/README.md)。
