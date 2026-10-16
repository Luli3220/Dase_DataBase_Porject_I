# 源码、安装与运行手册

[返回仓库总索引](../README.md) · [文档总索引](../docs/README.md)

课程第一阶段的完整可运行实现：Python 3.11 / FastAPI / PyMongo / MongoDB / 原生 JavaScript。支持注册登录、个人工作台、四类题的可视化编辑、校验与条件跳转、草稿预览、版本发布和公开链接、登录填写、匿名身份保护、重复填写与幂等重试、截止/关闭、单题/全卷统计及历史答卷。

## 本机启动（Windows PowerShell，已实际验证）

```powershell
cd E:\DBMS\Lab\Project1\source
# 本工作区已准备仓库根目录的 .venv 和 source/.env；新环境先执行下方安装步骤。

# 终端1：启动独立MongoDB，保持终端运行
New-Item -ItemType Directory -Force ..\.local\mongo | Out-Null
& F:\MongoDB\bin\mongod.exe --dbpath "$PWD\..\.local\mongo" --port 27018 --bind_ip 127.0.0.1 --replSet rs0

# 终端2：初始化副本集/集合（可重复，不删数据），然后启动应用
..\.venv\Scripts\python.exe -m scripts.init_replica
..\.venv\Scripts\python.exe -m scripts.init_db
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

已验证访问：[登录](http://127.0.0.1:8000/login)、[注册](http://127.0.0.1:8000/register)、[工作台](http://127.0.0.1:8000/dashboard)、[API交互文档](http://127.0.0.1:8000/docs)、[健康检查](http://127.0.0.1:8000/health)。这是本机服务，没有部署到公网。若端口已有本项目服务运行，直接访问，不启动重复实例。

普通PowerShell也可 `./scripts/start-local.ps1 -MongoExe '你的mongod.exe路径'` 后台启动Mongo；自动化宿主可能回收后台子进程，常驻终端更易诊断。MongoDB必须配置副本集，不支持standalone：跨集合事务保证创建、策略锁定和提交竞态一致性，见 [ADR](../docs/adr/001-consistency.md)。

## 新环境安装

需要Python3.11+与MongoDB7+/8+。

```powershell
./scripts/setup.ps1 -Python 'F:\Anaconda\python.exe'
# 或手动：
python -m venv ..\.venv
..\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
..\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
# 将生成的随机值填入.env的SESSION_SECRET。不要提交.env。
```

setup脚本会自动生成随机密钥且不覆盖已有.env。`requirements-lock.txt`是实际验收的精确依赖版本；requirements.txt为兼容范围。本机conda的db环境为Python3.10.21，低于规格3.11+，因此使用项目内Python3.11.5隔离环境，不修改原conda环境。

|配置|说明|
|---|---|
|MONGO_URI|默认mongodb://127.0.0.1:27018；本机副本集rs0|
|MONGO_DB|默认survey_dev|
|SESSION_SECRET|必填，至少32字符随机值；拒绝样例占位符|
|APP_BASE_URL|默认http://127.0.0.1:8000；分享URL和Origin检查依据|
|SESSION_MAX_AGE|默认28800秒|
|COOKIE_SECURE|开发false；production必须true且APP_BASE_URL为https|
|ENVIRONMENT|development / production|
|TEST_MONGO_URI|默认mongodb://127.0.0.1:27018/?replicaSet=rs0|

提供Docker替代方案：先生成.env，`docker compose up -d mongo`只启动数据库；`docker compose --profile full up --build -d`启动数据库和应用。避免和本机实例端口冲突。Compose自动初始化单节点副本集，绑定本机端口；数据volume不可随意删除。**当前Docker daemon未运行，因此容器启动未验证。**

## 测试与演示

```powershell
..\.venv\Scripts\python.exe -m pytest tests/unit -q
..\.venv\Scripts\python.exe -m pytest tests/integration -q
# 首次准备浏览器（也可通过PLAYWRIGHT_CHROMIUM_EXECUTABLE指定已有Chromium）
..\.venv\Scripts\python.exe -m playwright install chromium
..\.venv\Scripts\python.exe -m pytest -q --junitxml=../docs/evidence/final.xml
```

单元测试不依赖Mongo；集成测试需要27018副本集；浏览器测试自动在8001启动隔离HTTP服务。每个测试分配独立随机survey_test_<uuid>数据库，仅清理本次新建库，不清空survey_dev。数据库缺失会明确失败，不伪装通过或静默跳过。完整结果见[测试报告](../docs/test-report.md)、[逐项结果](../docs/evidence/case-results.md)。

演示：注册A→创建四类题及规则→保存预览→发布复制链接→另一浏览器会话注册B填写不同路径→主动新一轮填写→A查看有效/历史统计→派生V2并发布→旧表单409→关闭后拒绝新提交。匿名版本隐藏账号身份；latest_only跨整份问卷保留每人最新有效记录，历史不删除。

`python -m scripts.seed_demo`仅允许development且数据库名以_dev结尾，创建四题样例和两个随机账号，新密码只打印到当前终端，不提供固定账号。`python -m scripts.http_demo`对已运行的8000服务执行22个真实HTTP检查，生成随机演示数据且不输出密码；记录保留，不自动删除业务数据。

## 代码与交付文档

app/core：配置/会话/CSRF/错误/请求限制；app/models：请求模型和BSON映射；app/db：schema/索引/事务；app/rules：纯函数规则；app/services：认证/版本/提交/统计；app/api：REST；app/static与templates：原生网页；scripts：安装、启动、初始化、测试与演示；tests：unit/integration/web。

[系统设计](../docs/system-design.md) · [数据库设计](../docs/database-design.md) · [规则说明](../docs/rule-specification.md) · [API文档](../docs/api.md) · [测试用例](../docs/test-cases.md) · [需求追踪](../docs/requirements-traceability.md) · [AI使用日志](../docs/ai-usage-log.md) · [完成报告](../docs/project-report.md)。

设计边界：匿名只隐藏账号身份，回答可能自带身份线索；题目/选项语义根本变化须新建ID；不跨版本合并统计；只允许向后跳或结束；关闭不可重开。没有作业未要求的文件题/邀请邮件。单节点副本集无高可用，未进行容量压测或公网HTTPS部署。

第二阶段：新增题型扩展models/domain.py、rules/engine.py、static/app.js控件、services/statistics.py；新增运算符扩展白名单/静态验证/解释器；新数据库格式使用schemaVersion和迁移脚本，保留旧格式/内容版本解释能力。在现有模块上修改并重跑回归，不推倒重做。

## 源码导航

以下路径以本目录source为根；运行Python模块、pytest和Docker Compose前先进入source。虚拟环境和MongoDB数据位于仓库根目录的隐藏目录，配置文件在source/.env。

|入口|内容|
|---|---|
|[app/](app/)|后端、规则、业务服务及网页|
|[tests/](tests/)|单元、真实MongoDB集成、浏览器测试|
|[scripts/](scripts/)|环境安装、初始化、演示、测试及交付打包|
|[依赖范围](requirements.txt) / [精确版本](requirements-lock.txt)|运行及测试依赖|
|[配置样例](.env.example)|本机.env生成依据|
|[Docker配置](docker-compose.yml) / [镜像构建](Dockerfile)|容器替代方案|

Linux/macOS可在仓库根目录运行 `python3.11 -m venv .venv`，进入source后用 `../.venv/bin/python` 执行同样的模块命令。Windows脚本默认使用仓库根目录的.venv。
