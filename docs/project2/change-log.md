# 增量变更记录

基线 Commit：`61e226387140ee7ca9f985bf010769c823253a1c`。基线 Tag：`project1-baseline-61e2263`。开发分支：`project2/question-library`。用户提供的实施 Prompt 原为未跟踪文件，保留原文。

保留原四集合、认证、规则引擎、发布协议、答卷和单问卷统计。原测试、阶段性文档和证据的 SHA256 清单保存在 [protected-files.json](evidence/protected-files.json)，最终校验不变。

当前模型在原路径添加可选 source 与默认关闭的统计贡献。新增题目、题库、跨问卷统计服务，继续使用原 FastAPI、MongoDB 事务及前端，无第二套应用目录。后续实际文件变更与测试见本阶段最终报告。

## 最终原位修改清单

- `README.md`
- `docs/README.md`
- `docs/api.md`
- `docs/database-design.md`
- `docs/openapi.json`
- `docs/rule-specification.md`
- `docs/system-design.md`
- `source/README.md`
- `source/app/api/routes.py`
- `source/app/db/mongo.py`
- `source/app/main.py`
- `source/app/models/documents.py`
- `source/app/models/domain.py`
- `source/app/services/surveys.py`
- `source/app/static/app.js`
- `source/app/static/style.css`
- `source/app/templates/index.html`
- `source/scripts/build_evidence.py`
- `source/scripts/run-tests.ps1`


## 新增代码与证据

新增业务代码：`source/app/services/questions.py`、`question_banks.py`、`question_statistics.py`、`source/app/api/question_routes.py`。新增运行辅助：`source/scripts/migrate_project2.py` 与 `audit_project2.py`。新增测试位于 `source/tests/project2/`，37项，与原113项同命令运行。完整新增源文件清单见 [delivery-audit.json](evidence/delivery-audit.json)。

原规则引擎、认证、提交、单问卷统计服务及所有原测试源文件保持原样。原 `app.js` 保留原有164行，增量增加112行；换行符沿原LF规范保留，避免无意义的全文件diff。旧22个API操作保留，新增18个；现行OpenAPI共40个操作，与实际路由一致。来源和贡献授权为可选/默认关闭字段，没有重定义旧接口语义。

当前技术规范原位更新；本阶段37项测试、150项全套结果、AI日志、迁移、设计演进与独立报告位于本目录。报告权威编辑入口为用户指定的工作区 `report1/1.2.tex`，同步副本为 [report/main.tex](report/main.tex)。[7页PDF](report/1.2.pdf)经过逐页渲染检查。第一阶段1.1.tex与原PDF没有修改。

2026-10-26 开发验收结束时，本地分支为 `project2/question-library`，当时未创建提交、未推送、未创建PR。Git基线仍为61e2263；工作树差异即本轮可审查成果。报告中清楚说明远程仓库尚不包含本轮未提交改动。


## 2026-10-27 提交授权

用户明确要求“帮我提交一下”。按现有独立分支提交并推送第二阶段成果，同时保留第一阶段基线标签；不修改 main，不创建 PR。提交前检查暂存文件、历史文件保护、OpenAPI 一致性和文档链接。最终提交号由 Git 历史记录。
