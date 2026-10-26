# 问卷工坊 · MongoDB 在线问卷系统

本项目是数据库课程两阶段持续演进的在线问卷系统，使用MongoDB、FastAPI和JavaScript实现注册登录、问卷编辑与发布、条件跳转、匿名填写、重复提交及结果统计。

## 仓库索引

|目录|内容|入口|
|---|---|---|
|[requirements/](requirements/)|课程原始要求|[作业PDF](requirements/project1.pdf)|
|[prompts/](prompts/)|开发Prompt与分阶段规格|[规格阅读顺序](prompts/README.md)|
|[source/](source/)|后端、网页、测试、脚本、依赖及Docker配置|[安装、启动与测试](source/README.md)|
|[docs/](docs/)|系统/数据库/API设计、测试记录及AI使用说明|[文档总索引](docs/README.md)|

```text
Project1/
├── README.md                 # 总索引
├── requirements/             # 原始课程文件
├── prompts/                  # 开发规格及Prompt
├── source/
│   ├── app/                  # FastAPI、业务服务、规则与网页
│   ├── tests/                # 单元 / MongoDB集成 / 浏览器测试
│   ├── scripts/              # 安装、初始化、演示与测试
│   ├── README.md             # 运行手册
│   ├── requirements*.txt     # 依赖及精确版本
│   ├── .env.example          # 配置样例
│   └── docker-compose.yml    # Docker替代配置
└── docs/
    ├── README.md             # 文档导航
    ├── adr/                  # 设计决策
    └── evidence/             # 真实测试结果与截图
```

## 快速开始（PowerShell）

```powershell
# 在仓库根目录安装；使用Python 3.11+
.\source\scripts\setup.ps1 -Python 'python'
# 启动本机MongoDB副本集（修改为实际mongod路径）
.\source\scripts\start-local.ps1 -MongoExe 'F:\MongoDB\bin\mongod.exe'
cd source
..\.venv\Scripts\python.exe -m scripts.init_db
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

访问 [登录](http://127.0.0.1:8000/login)、[注册](http://127.0.0.1:8000/register)、[API文档](http://127.0.0.1:8000/docs)。完整配置、常驻Mongo启动、Docker、测试和演示操作见 [运行手册](source/README.md)。

## 项目资料

- [课程要求与提交材料对应](docs/requirements-traceability.md)
- [测试报告](docs/test-report.md)与[测试记录](docs/evidence/README.md)：第一阶段历史验收113项通过。
- [数据库设计](docs/database-design.md)、[API说明](docs/api.md)、[需求追踪](docs/requirements-traceability.md)
- [AI使用说明与Prompt/产物索引](docs/ai-usage-log.md) · [ChatGPT前期讨论](https://chatgpt.com/share/6ad37dad-75c4-83ec-b5d6-765759cca816)

项目报告通过课程平台提交，报告中的GitHub链接对应本仓库。本地Python环境位于.venv，MongoDB数据位于.local，应用配置位于source/.env。


## 第二阶段：版本化题目与题库

系统沿原四集合增量演进为七集合，支持常用题复用、用户间共享、旧快照稳定、版本血缘与恢复、多版本并存、使用反查、题库管理及跨问卷精确版本统计。旧认证、规则、匿名、幂等和问卷统计继续保留。没有复制第二套应用。

当前完整规范仍是 [数据库设计](docs/database-design.md)、[系统设计](docs/system-design.md)、[API](docs/api.md) 与 [OpenAPI](docs/openapi.json)。阶段材料见 [Project2 索引](docs/project2/README.md)、[完整报告](docs/project2/final-report.md)、[实测结果](docs/project2/test-report.md)。第一阶段测试与 AI 证据原样保留，Git 基线为 `project1-baseline-61e2263`。

已有环境进入 source，运行 `../.venv/Scripts/python.exe -m scripts.migrate_project2` 原地安装验证器/索引；不会更新旧文档。启动命令和双账号演示见 [source/README.md](source/README.md)。第二阶段在独立分支 `project2/question-library` 上开发与交付。
