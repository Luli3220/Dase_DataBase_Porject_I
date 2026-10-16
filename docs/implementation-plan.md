# 实施计划与阶段验收

依据：project1.pdf（11页，已逐页提取阅读）、00/01/02/03 开发规格。保留原始规格；新建独立应用，没有既有代码或 Git 仓库需要迁移。

|阶段|依赖|交付与验收|状态|
|---|---|---|---|
|A 数据库与核心|Python 3.11、真实 MongoDB|四集合 BSON/schema/index、版本 CAS/恢复、纯规则测试、真实数据库测试|已完成，72 passed，phase-a.xml|
|B API 与网页|A 测试通过|认证/CSRF、管理/填写/预览/统计页面、HTTP 链路|已完成，17 API passed，22个真实HTTP请求检查通过|
|C 测试与交付|B 主链路通过|权限/并发/版本/匿名/统计回归、浏览器、全套文档|已完成，最终102通过/0失败/0跳过；全部文档和真实证据已交付|

环境初查：db conda 环境为 Python 3.10.21，缺 FastAPI，conda 启动器报错；base Python 3.11.5 可用，因此采用项目内 .venv（Python 3.11）满足规格并保留 db 原环境。为加快起步曾借用system-site-packages，最终已关闭并按requirements-lock安装完全隔离依赖。MongoDB 8.3.11 已安装；Docker CLI 存在但 daemon 未运行。采用独立本地 Mongo 端口 27018，数据目录在项目 .local 下，不触碰既有数据库。

目录：app/{core,db,models,rules,services,static,templates}；scripts；tests/{unit,integration,web}；docs/evidence。启动入口 python -m uvicorn app.main:app。详细执行结果随阶段更新。
