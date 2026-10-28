# 数据库升级与回退

第二阶段升级安装题目定义、题目版本和题库的验证器与索引，并为问卷题目增加可选来源字段。原问卷版本和答卷继续保留其内容与含义。

## 升级前准备

安排暂停业务写入，备份配置与数据库。使用 MongoDB Database Tools 时，可按实际连接和目录执行：

```powershell
mongodump --uri '<副本集URI>' --db survey_dev --out '<备份路径>'
```

升级脚本会比较前后文档指纹；需要回退时，使用升级前的备份恢复数据。

## 执行升级

保留原 `.env`，在 `source/` 运行：

```powershell
..\.venv\Scripts\python.exe -m scripts.migrate_project2
```

脚本安装或更新七集合的验证器和索引，对原四集合按固定顺序、规范 BSON JSON 计算 SHA256，比较执行前后的指纹。文档内容变化时会报错，因此核对期间需要暂停其他写入。初始化和迁移均可重复执行。

source 可选，statisticsContribution 缺省按 false 解释，旧题与旧答卷无需补写。题目来源由明确的导入或保存操作建立，标题不作为题目身份。

## 已执行的检查

2026-10-26 在开发库 `survey_dev` 连续执行两次升级，均返回 oldDocumentsUnchanged=true。

|原集合|文档数|
|---|---:|
|users|6|
|surveys|3|
|survey_versions|6|
|submissions|6|

完整前后指纹见[首次结果](evidence/migration-first.json)和[再次结果](evidence/migration-second.json)。本轮检查了 Schema、索引及开发数据，备份恢复列入后续验证。

## 回退方式

1. 暂停业务写入，保存第二阶段数据库备份。
2. 在独立目录检出 `project1-baseline-61e2263`。
3. 向独立数据库恢复升级前备份，并将旧应用配置指向该数据库。
4. 验证问卷读取、提交和统计后再切换运行入口。

回退时，应用代码与数据库备份应使用同一阶段的版本。第一阶段模型只识别当时的字段，新增 source 的文档由第二阶段应用处理；回退前保存的第二阶段备份用于后续恢复。
