# 问卷工坊 · MongoDB 在线问卷系统

数据库课程项目，使用 MongoDB、FastAPI 和原生 JavaScript 实现问卷创建、发布、填写与统计。第二阶段在问卷版本与答卷模型上增加题目复用、共享、历史恢复、题库管理和跨问卷统计。

最近一次完整回归于 **2026-10-27** 完成：**167 项通过**，包含首轮 150 项和本次修复新增的 17 项。详细结果见[测试记录](docs/project2/test-report.md)。

## 从这里开始

|想了解什么|入口|
|---|---|
|安装、启动和操作演示|[运行手册](source/README.md)|
|系统如何组织|[系统设计](docs/system-design.md)、[源码导航](source/app/README.md)|
|数据库模型与查询口径|[数据库设计](docs/database-design.md)|
|接口、字段和错误码|[API 说明](docs/api.md)、[OpenAPI](docs/openapi.json)|
|第二阶段需求与实现|[Project 2 材料索引](docs/project2/README.md)|
|测试结果和截图|[证据索引](docs/project2/evidence/README.md)|
|课程要求与开发提示|[需求文件](requirements/README.md)、[Prompt 索引](prompts/README.md)|
|实验报告|[Markdown 报告](docs/project2/final-report.md)、[LaTeX 与 PDF](docs/project2/report/README.md)|

## 目录结构

```text
Project1-1/
├── README.md                 # 项目入口
├── requirements/             # 课程任务书与第二阶段变更要求
├── prompts/                  # 两阶段实施 Prompt
├── source/
│   ├── app/                  # API、业务服务、规则与网页
│   ├── tests/                # 单元、集成和浏览器测试
│   ├── scripts/              # 环境、数据库与验证工具
│   └── README.md             # 安装与运行
└── docs/
    ├── README.md             # 文档导航
    ├── *.md / openapi.json   # 当前系统设计与接口说明
    ├── adr/                  # 设计决策
    ├── evidence/             # 第一阶段证据
    └── project2/             # 第二阶段设计演进、测试、过程记录与报告
        ├── evidence/         # 按验证轮次组织的日志、JUnit 和截图
        └── report/           # LaTeX 源文件与 PDF
```

本地 Python 环境位于 `.venv/`，MongoDB 数据位于 `.local/mongo/`，应用配置位于 `source/.env`。

## 快速启动

以下命令在仓库根目录运行，使用 Python 3.11 及以上版本。MongoDB 路径按本机安装位置调整。

```powershell
.\source\scripts\setup.ps1 -Python 'python'
.\source\scripts\start-local.ps1 -MongoExe 'F:\MongoDB\bin\mongod.exe'
cd source
..\.venv\Scripts\python.exe -m scripts.init_db
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动后访问[工作台](http://127.0.0.1:8000/dashboard)、[题目](http://127.0.0.1:8000/questions)、[题库](http://127.0.0.1:8000/question-banks)或[交互式 API 文档](http://127.0.0.1:8000/docs)。已有第一阶段数据的升级步骤、MongoDB 常驻启动方式和测试命令见[运行手册](source/README.md)。

## 两阶段材料

第一阶段实现账号、问卷、规则引擎与答卷统计，验收为 113 项通过，相关[测试与 AI 记录](docs/README.md#第一阶段材料)保存在 `docs/`。第二阶段形成七集合模型，首轮验收为 150 项；后续完成统一原子保存、归档分页和统计口径说明，完整回归为 167 项。各轮原始输出见[证据索引](docs/project2/evidence/README.md)。

当前完整成果位于 `main`，第一阶段版本由标签 `project1-baseline-61e2263` 保留。第二阶段曾在 `project2/question-library` 开发，现已合入主分支。实现过程见[变更记录](docs/project2/change-log.md)和[AI 使用日志](docs/project2/ai-usage-log.md)。
