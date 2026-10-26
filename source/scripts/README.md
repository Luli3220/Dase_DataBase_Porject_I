# 运行与验证脚本

PowerShell 安装和启动脚本可以从仓库根目录调用；Python 模块在 `source/` 目录通过 `python -m scripts.<模块名>` 执行。

## 环境与数据库

|脚本|作用|
|---|---|
|[setup.ps1](setup.ps1)|创建虚拟环境、安装依赖并生成本地配置|
|[start-local.ps1](start-local.ps1)|启动本机 mongod，准备 rs0 副本集|
|[init_replica.py](init_replica.py)|等待 MongoDB 就绪并初始化副本集|
|[init_db.py](init_db.py)|创建或更新集合验证器与索引|
|[migrate_project2.py](migrate_project2.py)|安装第二阶段结构并比较原四集合文档指纹|

## 演示与测试

|脚本|作用与输出|
|---|---|
|[seed_demo.py](seed_demo.py)|在开发库生成问卷样例与随机账号|
|[http_demo.py](http_demo.py)|对运行中的服务执行 22 项基础 HTTP 检查|
|[run-tests.ps1](run-tests.ps1)|运行全套 pytest；默认写入 `docs/project2/evidence/full.xml` 和 `full-browser/`|
|[build_evidence.py](build_evidence.py)|读取默认 `full.xml` 生成逐项索引；完整模式同时记录环境并导出 OpenAPI|
|[audit_project2.py](audit_project2.py)|核对首轮 150 项交付的历史文件、接口、链接及报告同步情况|

后三个脚本沿用首轮验收的默认路径。新一轮回归可按[运行手册](../README.md#4-测试)选择独立输出目录，执行记录将按轮次保存在[证据目录](../../docs/project2/evidence/README.md)。
