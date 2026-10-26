# 安装与运行

[仓库首页](../README.md) · [项目文档](../docs/README.md)

系统使用Python 3.11、FastAPI、PyMongo和MongoDB，网页由HTML、CSS及原生JavaScript实现。以下命令以Windows PowerShell为例，Python模块和Docker Compose均在source目录执行。

## 1. 安装与配置

在仓库根目录运行安装脚本，Python参数可指定本机3.11及以上版本的解释器：

```powershell
.\source\scripts\setup.ps1 -Python 'python'
```

脚本在仓库根创建.venv，安装[锁定版本依赖](requirements-lock.txt)，并根据[配置样例](.env.example)生成source/.env和随机会话密钥。已有配置会保留。

也可以进入source手动安装：

```powershell
python -m venv ..\.venv
..\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
..\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

将生成的随机值填入.env的SESSION_SECRET。

|配置项|说明|
|---|---|
|MONGO_URI|默认mongodb://127.0.0.1:27018，连接rs0副本集|
|MONGO_DB|默认survey_dev|
|SESSION_SECRET|至少32字符的随机密钥|
|APP_BASE_URL|默认http://127.0.0.1:8000，用于分享链接和Origin检查|
|SESSION_MAX_AGE|默认28800秒|
|COOKIE_SECURE|开发环境false；production使用true和HTTPS|
|ENVIRONMENT|development或production|
|TEST_MONGO_URI|测试连接，默认mongodb://127.0.0.1:27018/?replicaSet=rs0|

## 2. 启动MongoDB

系统的跨集合写入使用事务，需要MongoDB副本集。本机演示采用单节点rs0，数据保存在仓库根目录.local/mongo。

在仓库根目录启动：

```powershell
.\source\scripts\start-local.ps1 -MongoExe 'F:\MongoDB\bin\mongod.exe'
```

也可以在source目录打开一个终端，持续运行mongod，再在另一个终端初始化副本集和集合：

```powershell
# 终端1：修改为本机mongod路径
New-Item -ItemType Directory -Force ..\.local\mongo | Out-Null
& F:\MongoDB\bin\mongod.exe --dbpath "$PWD\..\.local\mongo" --port 27018 --bind_ip 127.0.0.1 --replSet rs0

# 终端2
..\.venv\Scripts\python.exe -m scripts.init_replica
..\.venv\Scripts\python.exe -m scripts.init_db
```

初始化脚本创建或更新集合校验器和索引，保留已有数据。

## 3. 启动应用

在source目录执行：

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

访问[注册](http://127.0.0.1:8000/register)、[登录](http://127.0.0.1:8000/login)、[工作台](http://127.0.0.1:8000/dashboard)、[API文档](http://127.0.0.1:8000/docs)和[健康检查](http://127.0.0.1:8000/health)。

Docker配置见[docker-compose.yml](docker-compose.yml)与[Dockerfile](Dockerfile)。准备.env后，`docker compose up -d mongo`启动数据库，`docker compose --profile full up --build -d`启动数据库和应用。Docker与本机实例使用同样的端口，运行时选择其中一种。

## 4. 测试

```powershell
..\.venv\Scripts\python.exe -m pytest tests/unit -q
..\.venv\Scripts\python.exe -m pytest tests/integration -q

# 首次安装Chromium；也可设置PLAYWRIGHT_CHROMIUM_EXECUTABLE使用已有浏览器
..\.venv\Scripts\python.exe -m playwright install chromium
$env:TEST_EVIDENCE_DIR='../docs/project2/evidence'
..\.venv\Scripts\python.exe -m pytest -q --junitxml=../docs/project2/evidence/full.xml
..\.venv\Scripts\python.exe -m scripts.build_evidence --index-only
```

从仓库根运行`source/scripts/run-tests.ps1`也可执行完整测试。单元测试可独立运行；集成测试使用27018副本集；浏览器测试自动在8001启动临时服务。测试数据库采用随机survey_test_<uuid>名称，各用例结束后清理自己的测试库。

第一阶段历史验收为113项通过，原记录保留。第二阶段实际全套结果见[独立测试报告](../docs/project2/test-report.md)与[逐项记录](../docs/project2/evidence/case-results.md)。

## 5. 演示流程

1. 注册账号A，创建问卷，添加单选、多选、文本和数字题，配置校验与跳转。
2. 保存并预览，发布后复制公开链接。
3. 用另一浏览器会话注册账号B，打开链接并按不同路径填写；通过“开始新一轮填写”再次提交。
4. A查看历史和有效统计，从发布版本派生V2草稿并发布，再检查旧版本记录。
5. 设置截止时间或关闭问卷，查看填写入口的状态提示。

在开发数据库中，`python -m scripts.seed_demo`可生成四题样例及两个随机账号，并在终端输出登录信息。运行中的服务还可通过`python -m scripts.http_demo`执行22项HTTP检查。seed脚本要求development环境和以_dev结尾的数据库名。

## 6. 源码与文档

|入口|内容|
|---|---|
|[app/](app/)|认证、API、业务服务、规则和网页|
|[tests/](tests/)|单元、MongoDB集成和浏览器测试|
|[scripts/](scripts/)|安装、初始化、演示与测试|
|[requirements.txt](requirements.txt) / [requirements-lock.txt](requirements-lock.txt)|依赖范围及验收使用的精确版本|
|[项目文档](../docs/README.md)|系统、数据库、接口和测试说明|

Linux/macOS可在仓库根创建.venv，进入source后使用`../.venv/bin/python`执行相同模块命令。


## 7. 第二阶段升级与演示

从已有 Project1 数据库继续运行，先停止业务写入并备份。保持原 .env，运行：

```powershell
..\.venv\Scripts\python.exe -m scripts.migrate_project2
..\.venv\Scripts\python.exe -m scripts.migrate_project2
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

升级仅安装七集合验证器和索引，输出原四集合前后文档指纹；重复执行仍不改写旧数据。首次启动本身也执行幂等 initialize。若 Mongo 由临时执行宿主启动后退出，可在单独终端前台运行 `mongod --dbpath <仓库绝对路径>/.local/mongo --port 27018 --bind_ip 127.0.0.1 --replSet rs0`，保留该终端；不要再启动第二个相同数据目录的进程。

1. 两个浏览器会话分别注册 A/B。A 在“题目”创建年龄题 v1，按 B 的用户名共享。
2. A 创建题库，从可用题目选择 v1；题库成员可固定版本，或在选题时使用最新版本。
3. A/B 创建不同问卷，点击“从题库添加题目”，搜索/预览并选择具体版本；保存、发布、填写。
4. A 创建 v2，再从 v1 恢复为 v3。旧问卷仍显示 v1；新草稿可显式替换版本，或解除关联编辑本地副本。
5. 题目页查看所选版本的使用关系和统计，切换 mine/已授权贡献、当前有效/历史原始。B 在问卷编辑页显式开启贡献，外部每份问卷至少3份实际回答才参与共享统计。撤销后新查询排除。
6. 共享撤销/归档后旧问卷可继续填写，新引用被拒绝。原问卷统计仍可看自己拥有的数据和按历史匿名快照过滤的答卷。

完整回归：`./scripts/run-tests.ps1`。新增测试：`../.venv/Scripts/python.exe -m pytest tests/project2 -q`。不要将本阶段输出写入 `docs/evidence`；当前脚本已默认写入 `docs/project2/evidence`。迁移/回滚详细限制见 [migration.md](../docs/project2/migration.md)。
