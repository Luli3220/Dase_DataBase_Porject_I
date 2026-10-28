# 安装与运行

[仓库首页](../README.md) · [源码导航](app/README.md) · [脚本说明](scripts/README.md) · [测试导航](tests/README.md)

运行需要 Python 3.11 及以上版本和 MongoDB 副本集。以下以 Windows PowerShell 为例，Python 模块命令均在 `source/` 目录执行。

## 1. 安装与配置

在仓库根目录运行：

```powershell
.\source\scripts\setup.ps1 -Python 'python'
```

脚本创建 `.venv/`，安装[锁定版本依赖](requirements-lock.txt)，并根据 [.env.example](.env.example)生成 `source/.env` 和随机会话密钥；已有配置继续使用。`-Python` 可指定本机解释器路径。

手动安装时，在 `source/` 执行：

```powershell
python -m venv ..\.venv
..\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
..\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

将生成的随机值填入 `.env` 的 SESSION_SECRET。

|配置项|说明|
|---|---|
|MONGO_URI|配置样例为 mongodb://127.0.0.1:27018；连接本机 rs0 副本集|
|MONGO_DB|默认 survey_dev|
|SESSION_SECRET|至少 32 字符的随机密钥|
|APP_BASE_URL|默认 http://127.0.0.1:8000，用于分享链接与 Origin 检查|
|SESSION_MAX_AGE|默认 28,800 秒|
|COOKIE_SECURE|开发环境 false；production 使用 true 和 HTTPS|
|ENVIRONMENT|development 或 production|
|TEST_MONGO_URI|测试连接，默认 mongodb://127.0.0.1:27018/?replicaSet=rs0|

## 2. 启动数据库

跨集合事务需要 MongoDB 副本集。本机演示采用单节点 rs0，数据位于仓库的 `.local/mongo/`。

在仓库根目录调用启动脚本，MongoDB 路径按本机调整：

```powershell
.\source\scripts\start-local.ps1 -MongoExe 'F:\MongoDB\bin\mongod.exe'
```

也可以在 `source/` 用一个常驻终端运行 mongod，在另一个终端初始化：

```powershell
# 终端 1
New-Item -ItemType Directory -Force ..\.local\mongo | Out-Null
& F:\MongoDB\bin\mongod.exe --dbpath "$PWD\..\.local\mongo" --port 27018 --bind_ip 127.0.0.1 --replSet rs0

# 终端 2
..\.venv\Scripts\python.exe -m scripts.init_replica
..\.venv\Scripts\python.exe -m scripts.init_db
```

初始化安装集合验证器与索引，保留已有文档。已有第一阶段数据可执行以下升级检查；备份和回退步骤见[升级说明](../docs/project2/migration.md)。

```powershell
..\.venv\Scripts\python.exe -m scripts.migrate_project2
```

## 3. 启动应用

在 `source/` 执行：

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

页面入口：[注册](http://127.0.0.1:8000/register)、[登录](http://127.0.0.1:8000/login)、[工作台](http://127.0.0.1:8000/dashboard)、[题目](http://127.0.0.1:8000/questions)、[题库](http://127.0.0.1:8000/question-banks)、[API](http://127.0.0.1:8000/docs)、[健康检查](http://127.0.0.1:8000/health)。

Docker 配置见 [docker-compose.yml](docker-compose.yml) 和 [Dockerfile](Dockerfile)。准备 `.env` 后，`docker compose up -d mongo` 启动数据库，`docker compose --profile full up --build -d` 启动数据库和应用。Docker 与本机演示使用相同端口，按实际环境选择启动方式。

## 4. 测试

快速验证某一层：

```powershell
..\.venv\Scripts\python.exe -m pytest tests/unit -q
..\.venv\Scripts\python.exe -m pytest tests/integration -q
..\.venv\Scripts\python.exe -m pytest tests/project2 -q
```

首次运行浏览器测试时安装 Chromium，或设置 PLAYWRIGHT_CHROMIUM_EXECUTABLE 使用已有浏览器：

```powershell
..\.venv\Scripts\python.exe -m playwright install chromium
```

完整回归按时间创建输出目录，保存 JUnit、控制台输出与截图：

```powershell
$TaskRunDir = "../docs/project2/evidence/runs/$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Force "$TaskRunDir/browser" | Out-Null
$env:TEST_EVIDENCE_DIR = (Resolve-Path "$TaskRunDir/browser").Path
..\.venv\Scripts\python.exe -m pytest -q --junitxml="$TaskRunDir/full.xml" 2>&1 | Tee-Object -FilePath "$TaskRunDir/full.txt"
```

单元测试可独立执行；集成测试使用 27018 副本集；浏览器测试在 8001 启动临时服务。每个数据库用例创建随机 `survey_test_<uuid>` 数据库并在结束后清理。

2026-10-27 完整回归 **167 项通过**，包含第一阶段 113 项和第二阶段新增 54 项。结果见[测试记录](../docs/project2/test-report.md)，输出和截图见[日志索引](../docs/project2/evidence/README.md)，测试脚本的用法见[脚本导航](scripts/README.md)。

## 5. 演示流程

### 问卷基础流程

1. 注册 A，创建问卷，添加单选、多选、文本和数字题，设置校验与跳转。
2. 保存并预览，发布后复制公开链接。
3. 用另一浏览器会话注册 B，按不同路径填写，并尝试新一轮提交。
4. A 查看原始和有效统计，派生 V2 草稿并发布，再切回历史版本查看。
5. 设置截止时间或关闭问卷，观察填写入口状态。

### 题目复用与统计

1. A 在“题目”创建年龄题 v1，并按 B 的用户名共享。
2. A 创建题库，添加固定 v1 成员，或设置选题时使用最新版。
3. A、B 分别创建问卷，从题库选用具体版本，保存、发布和填写。
4. A 修改题目生成 v2，再从 v1 恢复生成 v3；旧问卷继续使用原版本。新草稿可选择其他版本，或解除关联后编辑本地题目。
5. 在题目页查看使用关系、mine 和已授权贡献范围，以及当前有效和历史原始口径。B 可在问卷编辑页开启贡献，每份外部问卷至少 3 次实际回答后加入聚合。
6. 试用共享撤销、归档与贡献撤销，查看新引用、历史快照和统计范围的相应变化。

`python -m scripts.seed_demo` 可在 development、名称以 `_dev` 结尾的数据库生成四题样例和随机账号。服务运行后，`python -m scripts.http_demo` 可执行 22 项基础 HTTP 检查。

## 6. 继续阅读

- [系统与数据库](../docs/README.md)、[API](../docs/api.md)
- [第二阶段材料](../docs/project2/README.md)、[最近修复](../docs/project2/fixes-2026-10-27.md)
- [源码](app/README.md)、[脚本](scripts/README.md)、[测试](tests/README.md)
- [依赖范围](requirements.txt)、[锁定版本](requirements-lock.txt)

Linux/macOS 可在仓库根创建 `.venv`，进入 `source/` 后使用 `../.venv/bin/python` 执行相同模块命令。
