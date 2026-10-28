# 问卷工坊 · MongoDB 在线问卷系统

数据库课程项目，使用 MongoDB、FastAPI 和原生 JavaScript 实现问卷创建、发布、填写与统计。用户可以配置四类题型和条件跳转，按版本管理问卷，并查看填写结果。

第二阶段增加常用题目复用、跨用户共享、版本恢复、题库管理和跨问卷统计。题目独立维护，问卷保存选用版本的完整内容，后续改题时，已发布问卷及历史回答保持稳定。

## 从这里开始

|想了解什么|入口|
|---|---|
|安装、启动和操作演示|[运行手册](source/README.md)|
|系统结构与代码组织|[系统设计](docs/system-design.md)、[源码导航](source/app/README.md)|
|数据库模型与统计口径|[数据库设计](docs/database-design.md)|
|接口与字段|[API 说明](docs/api.md)、[OpenAPI](docs/openapi.json)|
|第二阶段需求与改动|[Project 2 材料索引](docs/project2/README.md)|
|测试结果、日志和截图|[测试记录](docs/project2/test-report.md)、[日志索引](docs/project2/evidence/README.md)|
|课程要求与开发提示|[需求文件](requirements/README.md)、[Prompt 索引](prompts/README.md)|
|实验报告|[Markdown 报告](docs/project2/final-report.md)、[LaTeX 与 PDF](docs/project2/report/README.md)|

## 快速启动

以下命令在仓库根目录运行，需要 Python 3.11 及以上版本。MongoDB 路径按本机安装位置调整。

```powershell
.\source\scripts\setup.ps1 -Python 'python'
.\source\scripts\start-local.ps1 -MongoExe 'F:\MongoDB\bin\mongod.exe'
cd source
..\.venv\Scripts\python.exe -m scripts.init_db
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动后访问[工作台](http://127.0.0.1:8000/dashboard)、[题目](http://127.0.0.1:8000/questions)、[题库](http://127.0.0.1:8000/question-banks)或[交互式 API 文档](http://127.0.0.1:8000/docs)。已有数据的升级方法和完整测试命令见[运行手册](source/README.md)。

## 目录结构

```text
Project1-1/
├── requirements/             # 课程任务书与变更要求
├── prompts/                  # 两阶段实施 Prompt
├── source/
│   ├── app/                  # API、业务服务、规则与网页
│   ├── tests/                # 单元、集成和浏览器测试
│   ├── scripts/              # 环境、数据库与验证工具
│   └── README.md             # 安装与运行
└── docs/
    ├── README.md             # 文档导航
    ├── *.md / openapi.json   # 系统、数据库和接口说明
    ├── adr/                  # 设计决策
    ├── evidence/             # 第一阶段测试记录
    └── project2/             # 第二阶段设计演进与开发材料
        ├── evidence/         # 各轮测试日志、JUnit 和截图
        └── report/           # LaTeX 源文件与 PDF
```

本地 Python 环境位于 `.venv/`，MongoDB 数据位于 `.local/mongo/`，应用配置位于 `source/.env`。

## 开发与测试

第一阶段完成账号、问卷、规则引擎和答卷统计，完整测试为 113 项。第二阶段首轮完成题目与题库功能，通过 150 项测试；随后根据使用检查改进保存、归档分页和统计说明，新增 17 项测试。

最近一次完整回归于 **2026-10-27** 完成，**167 项全部通过**。步骤与结果见[测试记录](docs/project2/test-report.md)，AI 辅助设计和修改过程见[AI 使用日志](docs/project2/ai-usage-log.md)。

当前成果位于 `main`，第一阶段版本保存在 `project1-baseline-61e2263` 标签中。主要改动可通过[变更记录](docs/project2/change-log.md)查阅。
