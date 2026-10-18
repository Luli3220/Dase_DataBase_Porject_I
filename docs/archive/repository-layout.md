# 目录整理与路径迁移

按用户“Prompt放一个目录，source放一个目录，目录干净并做好索引”的要求整理。根目录README为总入口；每个主要目录均有README索引。

|原位置|当前位置|
|---|---|
|project1.pdf|requirements/project1.pdf|
|00/01/02/03及完整实施Prompt.md|prompts/（原文不变）|
|docs/original-specification-readme.md|prompts/original-specification-readme.md（原文不变）|
|app/、tests/、scripts/|source/app/、source/tests/、source/scripts/|
|依赖、pytest、Docker、配置样例|source/中的同名文件|
|原根README的运行说明|source/README.md，已更新相对路径|
|设计、报告、证据|docs/，增加总索引|

当前工作目录约定：Python模块、pytest、Docker Compose均在source执行；虚拟环境仍在仓库根目录.venv，Windows解释器为`../.venv/Scripts/python.exe`。安装/启动/测试脚本会自动定位source或仓库根，不依赖调用者当前目录。本机.env移到source并继续忽略，MongoDB打开的数据目录.local保留原位，未迁移或清空业务数据。

网页模板/静态资源使用应用文件位置定位，包内部导入保持app/tests，不因外部目录移动改名。浏览器测试的临时服务cwd为source，证据默认写到仓库docs/evidence；本轮通过TEST_EVIDENCE_DIR写入独立restructure目录，避免覆盖初始验收截图。打包脚本显式定位仓库根，仍完整包含需求、Prompt、代码与文档，排除.git/.env/.venv/.local和缓存。

原始PDF与Prompt内容保持字节一致。原始测试日志中的旧路径表示当时实际执行位置，不改写历史记录；当前运行命令以source/README为准。此次不修改数据库模型、规则语义或业务接口。验证结果见 [整理后回归](../evidence/restructure/README.md)。
