# 问卷工坊 · MongoDB 在线问卷系统

课程第一阶段项目。支持注册登录、四类题目、可配置跳转与校验、版本发布、登录填写、匿名与重复提交、单题及整卷统计。

## 仓库索引

|目录|内容|入口|
|---|---|---|
|[requirements/](requirements/)|课程原始要求|[作业PDF](requirements/project1.pdf)|
|[prompts/](prompts/)|开发Prompt与分阶段规格，保留原文|[规格阅读顺序](prompts/README.md)|
|[source/](source/)|后端、网页、测试、脚本、依赖及Docker配置|[安装、启动与测试](source/README.md)|
|[docs/](docs/)|系统/数据库/API设计、测试证据、AI日志、完成报告|[文档总索引](docs/README.md)|

```text
Project1/
├── README.md                 # 总索引
├── requirements/             # 原始课程文件
├── prompts/                  # 开发规格及Prompt
├── source/
│   ├── app/                  # FastAPI、业务服务、规则与网页
│   ├── tests/                # 单元 / MongoDB集成 / 浏览器测试
│   ├── scripts/              # 安装、初始化、演示、测试、打包
│   ├── README.md             # 运行手册
│   ├── requirements*.txt     # 依赖及精确版本
│   ├── .env.example          # 配置样例
│   └── docker-compose.yml    # Docker替代配置
└── docs/
    ├── README.md             # 文档导航
    ├── report/               # 作者完成的正式PDF报告
    ├── archive/              # 旧完成记录与开发过程档案
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

## 验收入口

- [正式实验报告](docs/report/DataBase_Project_1.pdf)与[课程要求核对](docs/requirements-traceability.md)
- [测试报告](docs/test-report.md)与[证据总索引](docs/evidence/README.md)：最近一次完整验收113项通过，早期102项记录作为历史保留。
- [数据库设计](docs/database-design.md)、[API说明](docs/api.md)、[需求追踪](docs/requirements-traceability.md)
- [AI使用说明与Prompt/产物索引](docs/ai-usage-log.md) · [ChatGPT前期讨论](https://chatgpt.com/share/6ad37dad-75c4-83ec-b5d6-765759cca816)

业务数据只使用MongoDB。匿名保护、问卷内容版本、重复填写统计口径遵循既定规格。Docker容器运行、公网部署和容量压测未验证，详情见测试报告。

本机 `.venv/`、`.local/`、`source/.env`、缓存及 `delivery/` 为忽略项，不进入Git。打包在source目录执行 `python -m scripts.package_delivery`，输出到仓库根目录delivery。
