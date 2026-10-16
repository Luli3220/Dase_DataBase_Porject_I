# 问卷工坊 · MongoDB 在线问卷系统

课程第一阶段的完整可运行实现：Python 3.11 / FastAPI / PyMongo / MongoDB / 原生 JavaScript。支持注册登录、个人工作台、四类题的可视化编辑、校验与条件跳转、草稿预览、版本发布和公开链接、登录填写、匿名身份保护、重复填写与幂等重试、截止/关闭、单题/全卷统计及历史答卷。

## 本机启动（Windows PowerShell，已实际验证）

```powershell
cd E:\DBMS\Lab\Project1
# 本工作区已准备 .venv 和本机 .env；新环境先执行下方安装步骤。

# 终端1：启动独立MongoDB，保持终端运行
New-Item -ItemType Directory -Force .local\mongo | Out-Null
& F:\MongoDB\bin\mongod.exe --dbpath "$PWD\.local\mongo" --port 27018 --bind_ip 127.0.0.1 --replSet rs0

# 终端2：初始化副本集/集合（可重复，不删数据），然后启动应用
.\.venv\Scripts\python.exe -m scripts.init_replica
.\.venv\Scripts\python.exe -m scripts.init_db
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

已验证访问：[登录](http://127.0.0.1:8000/login)、[注册](http://127.0.0.1:8000/register)、[工作台](http://127.0.0.1:8000/dashboard)、[API交互文档](http://127.0.0.1:8000/docs)、[健康检查](http://127.0.0.1:8000/health)。这是本机服务，没有部署到公网。若端口已有本项目服务运行，直接访问，不启动重复实例。

普通PowerShell也可 `./scripts/start-local.ps1 -MongoExe '你的mongod.exe路径'` 后台启动Mongo；自动化宿主可能回收后台子进程，常驻终端更易诊断。MongoDB必须配置副本集，不支持standalone：跨集合事务保证创建、策略锁定和提交竞态一致性，见 [ADR](docs/adr/001-consistency.md)。

## 新环境安装

需要Python3.11+与MongoDB7+/8+。

```powershell
./scripts/setup.ps1 -Python 'F:\Anaconda\python.exe'
# 或手动：
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
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
.\.venv\Scripts\python.exe -m pytest tests/unit -q
.\.venv\Scripts\python.exe -m pytest tests/integration -q
# 首次准备浏览器（也可通过PLAYWRIGHT_CHROMIUM_EXECUTABLE指定已有Chromium）
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pytest -q --junitxml=docs/evidence/final.xml
```

单元测试不依赖Mongo；集成测试需要27018副本集；浏览器测试自动在8001启动隔离HTTP服务。每个测试分配独立随机survey_test_<uuid>数据库，仅清理本次新建库，不清空survey_dev。数据库缺失会明确失败，不伪装通过或静默跳过。完整结果见[测试报告](docs/test-report.md)、[逐项结果](docs/evidence/case-results.md)。

演示：注册A→创建四类题及规则→保存预览→发布复制链接→另一浏览器会话注册B填写不同路径→主动新一轮填写→A查看有效/历史统计→派生V2并发布→旧表单409→关闭后拒绝新提交。匿名版本隐藏账号身份；latest_only跨整份问卷保留每人最新有效记录，历史不删除。

`python -m scripts.seed_demo`仅允许development且数据库名以_dev结尾，创建四题样例和两个随机账号，新密码只打印到当前终端，不提供固定账号。`python -m scripts.http_demo`对已运行的8000服务执行22个真实HTTP检查，生成随机演示数据且不输出密码；记录保留，不自动删除业务数据。

## 代码与交付文档

app/core：配置/会话/CSRF/错误/请求限制；app/models：请求模型和BSON映射；app/db：schema/索引/事务；app/rules：纯函数规则；app/services：认证/版本/提交/统计；app/api：REST；app/static与templates：原生网页；scripts：安装、启动、初始化、测试与演示；tests：unit/integration/web。

[系统设计](docs/system-design.md) · [数据库设计](docs/database-design.md) · [规则说明](docs/rule-specification.md) · [API文档](docs/api.md) · [测试用例](docs/test-cases.md) · [需求追踪](docs/requirements-traceability.md) · [AI使用日志](docs/ai-usage-log.md) · [完成报告](docs/project-report.md)。

设计边界：匿名只隐藏账号身份，回答可能自带身份线索；题目/选项语义根本变化须新建ID；不跨版本合并统计；只允许向后跳或结束；关闭不可重开。没有作业未要求的文件题/邀请邮件。单节点副本集无高可用，未进行容量压测或公网HTTPS部署。

第二阶段：新增题型扩展models/domain.py、rules/engine.py、static/app.js控件、services/statistics.py；新增运算符扩展白名单/静态验证/解释器；新数据库格式使用schemaVersion和迁移脚本，保留旧格式/内容版本解释能力。在现有模块上修改并重跑回归，不推倒重做。

---

## 原始规格导读（保留）

本目录是第一阶段开发规格（以课程作业 `project1.pdf` 为准）。请将原始作业 PDF 一并提供给 Coding Agent，以便逐项对照。本文档是实施计划，不是已完成代码、测试记录或实际运行结果。

## 使用顺序

1. **`00-总控Prompt.md`**：先交给 Coding Agent；要求检查仓库、形成执行清单并按阶段执行。
2. **`01-数据库与规则引擎.md`**：数据库文档模型、索引、版本管理、校验、跳转、提交策略；先完成并通过相关测试。
3. **`02-后端API与网页.md`**：REST API、鉴权、前端交互和可运行的业务闭环。
4. **`03-测试文档与验收.md`**：单元/集成/回归测试、边界条件、运行证据、报告与 AI 使用日志。
5. **`完整实施Prompt.md`**：以上四份内容的合并版，适合只能发送单个 Markdown 文档的 Coding Agent。

## 核心业务约定（项目讨论确定）

- 使用 MongoDB（全部**持久化业务数据**进入 MongoDB），Python + FastAPI + PyMongo + HTML/CSS/原生 JavaScript；其他等价方案仅在给出书面理由后采用。
- 四个核心集合：`users`、`surveys`、`survey_versions`、`submissions`。题目及规则嵌入问卷版本，答案嵌入独立答卷。
- 已发布问卷版本不可修改；问卷发布指针 `publishedVersion` 与编辑指针 `draftVersion` 分离；历史答卷引用确定版本。
- 登录是填写前提；`anonymous=true` 只表示创建者不能看到身份，系统仍保存提交者 ID 并用于权限与重复提交判断。不能将“隐藏 ID”等同于绝对匿名。
- 每次成功提交均生成独立答卷，不覆盖历史。`latest_only` 统计同一用户**整份问卷**的最新提交；`multiple` 统计每次提交。当前有效统计与历史原始提交统计严格区分。
- 四种内部题型：`single_choice`、`multiple_choice`、`text`、`number`。前两者使用选项 ID；数值答案使用真正的数字类型。
- 规则声明式配置，不执行动态代码；单选、多选、数字条件跳转；同题规则优先级唯一、数值越小越先执行；未命中则下一题；仅允许向后跳或结束；非必答题缺失时不触发该题条件规则；只有有效路径上的必答题必须回答。
- 旧版填写遇到新的 `publishedVersion` 时，第一阶段采用 `409 SURVEY_VERSION_CHANGED`，不偷偷把答案写入新版。
- 所有实际测试结果、AI 使用情况必须真实记录，不可虚构。

**注意：** 如果实施发现本规格有歧义，优先保持上述业务语义，并以 ADR（架构决策记录）说明取舍；不可自行删减课程明确要求的功能。
