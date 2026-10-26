# 无损升级与回退

基线 `61e2263`，升级目标为本分支工作树。没有覆盖原 .env，没有重置 Mongo 数据目录，也没有批量填充 source。

升级前停止业务写入，备份 .env 与数据库；可使用本机 MongoDB Database Tools 的 `mongodump --uri <原副本集URI> --db survey_dev --out <备份路径>`。**本轮没有执行 mongodump，不把指纹校验当作可恢复备份。** 原始题库需求由用户给出，库题没有按标题从旧问卷自动合并。

在 source 目录执行：

```powershell
..\.venv\Scripts\python.exe -m scripts.migrate_project2
..\.venv\Scripts\python.exe -m scripts.migrate_project2
```

脚本安装/更新七集合验证器及索引；原四集合逐条以规范 BSON JSON 排序计算 SHA256，不输出用户内容。它不 insert/update/delete 原文档。比较前后指纹，不相等立即报错；审计期间应停止其他写入，否则并发业务变更也会被报告为不同。

本轮真实连接 `survey_dev`，连续执行两次，均 oldDocumentsUnchanged=true。保留了 users=6、surveys=3、survey_versions=6、submissions=6。见 [首次](evidence/migration-first.json) 与 [再次](evidence/migration-second.json)。这是现有开发数据的审计结果，不代表所有生产数据规模的迁移验证。

source 可选、statisticsContribution 缺省按false解释，因此旧文档无需改写，sealed 与 submissions 内容不动。初始化同样幂等，旧测试库仍可使用。新增题目版本由服务追加，无原地编辑或删除端点；数据库管理员直接操作不在服务保证内。

回退时先停止写入并保存第二阶段数据库备份。推荐在独立目录检出 `project1-baseline-61e2263`，在独立数据库恢复升级前备份，再指向旧代码。**不承诺第一阶段旧程序能完整编辑带 source 的新文档**：其严格 Pydantic 模型不识别 source，直接降级代码会丢失第二阶段能力。因此不通过删除 source、删除新集合或修改历史快照来伪造无损回退。本轮未实际执行数据库恢复或生产部署回滚。
