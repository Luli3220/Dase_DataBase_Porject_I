# 源码导航

应用由 FastAPI 提供同源网页和 JSON API，业务服务通过 PyMongo 访问 MongoDB。先看 `main.py` 的装配，再按具体功能进入路由和服务。

|目录 / 文件|职责|
|---|---|
|[main.py](main.py)|应用装配、中间件、错误处理、静态文件与页面入口|
|[api/routes.py](api/routes.py)|账号、问卷、原子保存、填写和问卷统计接口|
|[api/question_routes.py](api/question_routes.py)|题目、历史、共享、题库和跨问卷统计接口|
|[core/](core/)|配置、会话、CSRF、请求大小和业务异常|
|[models/domain.py](models/domain.py)|网络请求模型与响应序列化|
|[models/documents.py](models/documents.py)|持久化模型及 BSON 映射|
|[db/mongo.py](db/mongo.py)|MongoDB 连接、事务、验证器和索引|
|[rules/engine.py](rules/engine.py)|题目配置、答案校验、条件匹配与路径计算|
|[templates/index.html](templates/index.html)|网页入口|
|[static/app.js](static/app.js)、[style.css](static/style.css)|页面交互与样式|

## 业务服务

|文件|功能|
|---|---|
|[auth.py](services/auth.py)|用户名归一化、注册、登录与密码验证|
|[surveys.py](services/surveys.py)|问卷元信息、草稿、原子保存、发布、关闭和导入|
|[submissions.py](services/submissions.py)|路径重算、幂等提交、有效答卷筛选和答卷列表|
|[statistics.py](services/statistics.py)|单份问卷或单道局部题目的统计|
|[questions.py](services/questions.py)|题目身份、版本、恢复、fork、共享和来源校验|
|[question_banks.py](services/question_banks.py)|题库信息、成员和固定版本选择|
|[question_statistics.py](services/question_statistics.py)|使用关系与精确版本的跨问卷聚合|

保存流程、权限与统计口径见[系统设计](../../docs/system-design.md)，字段见[数据库设计](../../docs/database-design.md)，测试入口见[测试导航](../tests/README.md)。
