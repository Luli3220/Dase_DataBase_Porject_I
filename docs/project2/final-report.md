# 基于 MongoDB 的在线问卷系统：版本化题目与增量演进

杨子炫，10245501483，2026年10月26日。仓库：[Luli3220/Dase_DataBase_Porject_I](https://github.com/Luli3220/Dase_DataBase_Porject_I)。本阶段实现保存在本地分支，尚未推送，远程链接提供项目入口，不表示远程已包含本次修改。

## 需求分析与原设计回顾

第二阶段的八项反馈可以归结为两条主线：题目需要独立于问卷被复用、共享和组织；题目变化后需要保留版本关系、历史解释和跨问卷统计。课程要求同时强调不得推倒重做，因此演进必须承接原结构和原功能。

第一阶段用users管理账号，surveys管理所有者、公开链接、发布/草稿指针及策略，survey_versions嵌入题目、选项、校验和跳转，submissions独立保存答卷。这个设计符合完整读取问卷、整体冻结内容、有界配置嵌入和无界答卷独立增长的访问模式。原FastAPI/PyMongo服务、纯函数规则引擎、原生JavaScript前端以及事务、CAS、幂等机制继续保留。

原局部questions[].id只在对应问卷实例中标识答案，无法证明不同问卷中的两个题是同一道题；相同标题也不等价。将所有题改为实时引用最新内容又会使旧问卷改变，破坏旧答案解释。因此需要增加独立题目生命周期，同时保留问卷作为不可变历史快照的聚合边界。

## 数据库演进及关键决策

采用七集合：原四集合加question_definitions、question_versions、question_banks。定义保存稳定questionId、ownerId、共享用户、currentVersion和revision；版本独立保存具体content、parentVersion、changeType与restoredFromVersion；题库只保存有界成员引用。版本不嵌入定义，避免历史无界增长。没有额外拆分选项/规则/答案集合，也没有维护不断增长的usedBy数组。

问卷题目新增可选source={questionId,questionVersion}。导入生成独立局部ID，并把完整内容物化进草稿；发布后仍只读原survey_versions快照。固定引用用于溯源和统计，内嵌快照用于历史解释，两者承担不同职责。新增来源字段在网络为字符串、在Mongo为ObjectId，由严格模型和BSON转换统一处理。

题目版本追加而不覆盖；版本号在同题下单调递增，但父版本可为任意历史版。恢复是复制指定旧版追加新版本，fork则创建新questionId并记录跨题来源。路由目标依赖问卷局部ID，因此库题不保存routingRules。导入默认无路由，显式替换保留局部ID和入边、清空出边，再验证整卷。关联题核心内容不能无声改写；用户可解除关联成为本地题，或显式导入新版本。

定义按ownerId/updatedAt、sharedWith建索引，题目版本(questionId,version)唯一，题库按ownerId/updatedAt，问卷来源按同一questions数组中的全局ID和精确版本建复合多键索引。使用$elemMatch绑定同一元素，防止Q/v1和R/v2误匹配为Q/v2。详细字段与模型图见唯一现行 [数据库设计](../database-design.md)，方案比较见 [演进论证](database-evolution.md)。

## 权限、事务与业务实现

题目默认私有，仅所有者或被共享者可读/使用；猜测私有ID返回404。共享不授予修改或答卷权限，独立维护通过fork。共享用户名归一化、去重并核验账号存在。题库所有者只能管理本人题库，成员上限200，成员操作upsert防重复；固定版本不会随currentVersion变化，未固定版本在选题时解析最新。

追加版本采用Mongo事务、currentVersion CAS和唯一索引；草稿保存和导入采用revision CAS。导入、fork、题库选用在事务内写题目定义revision，使撤销共享/归档与新引用操作争用同一文档；重试重新校验权限。并发请求至多一方使用同一期望值成功，失败显式409。原发布冻结和恢复协议保留，提交仍沿用原幂等、匿名快照与路径重算。

后端新增三个职责独立的服务及question_routes，沿用登录、CSRF、Origin、2MiB请求限制、字段白名单、错误结构。前端在原app.js增量加入搜索、共享、历史、恢复、fork、题库、固定版本导入、解除关联、反查和统计。没有引入问卷框架或第二套前端系统。

## 跨问卷统计与隐私

统计以稳定身份和精确题目版本关联问卷快照，再由局部ID定位答案。current_effective先按每份问卷自己的策略在全部问卷版本中选择最新答卷，再筛选目标来源版本；multiple/historical_raw保留所有选中提交，避免旧版本最新记录被错误计入。跳过题不计实际回答，提交次数与实际回答数分别展示，跨问卷多份提交不称独立人数。

MongoDB内部完成lookup/filter/group/facet。单选按选项计数，多选展开选项，数字均值与分布基于全部实际回答；负数、小数和安全极值进入完整覆盖的半开区间。年龄分桶为(-∞,0)、[0,18)、[18,30)、[30,45)、[45,60)、[60,121)、[121,+∞)。空均值为null，文本只返回计数。

mine只汇总本人问卷，consented_shared增加问卷所有者显式贡献的数据。贡献字段默认false，每份外部问卷当前口径下不足3个实际回答则整体抑制，撤销后新的查询排除。跨问卷结果不返回原始文本、账号、完整答卷或外部问卷ID。使用查询只披露自己全部版本及当前可公开访问的问卷，不暴露他人私有问卷名称或数量。共享题目和共享数据权限分别建模。

## 旧数据兼容与原位变更证明

source可选，旧题不自动绑定；statisticsContribution缺省false；schemaVersion保持1。迁移只安装验证器和索引，不修改旧内容。对原开发数据库连续两次执行migrate_project2，6用户、3问卷、6问卷版本、6答卷前后指纹一致。原阶段测试、AI日志和证据按SHA256清单核对，原测试未改。基线为61e2263，本地Tag project1-baseline-61e2263；可使用Git差异复核。

|分类|路径及处理|
|---|---|
|保留原模块|rules/engine.py；services/auth.py、submissions.py、statistics.py；core身份/错误/请求边界；原113项测试|
|直接修改原代码|models/domain.py、documents.py：可选来源及新模型；db/mongo.py：验证器与索引；services/surveys.py：事务来源校验/导入；api/routes.py：预览序列化；main.py：增量路由；app.js/style.css/index.html：增量UI|
|直接修改原脚本|run-tests.ps1、build_evidence.py：第二阶段输出路径及当前OpenAPI导出|
|新增模块|services/questions.py、question_banks.py、question_statistics.py；api/question_routes.py；scripts/migrate_project2.py|
|新增阶段材料|tests/project2/；docs/project2/的测试、AI日志、演进、迁移、报告和证据|
|当前技术规范更新|原docs/database-design.md、system-design.md、api.md、openapi.json、rule-specification.md及各README|

旧接口保持原请求兼容，source与贡献字段为增量字段；原公开填写、提交及单问卷统计不依赖题库实时读取。回退需在独立环境恢复升级前备份并检出基线，不承诺旧严格模型可编辑新source文档，不能删除新字段冒称无损降级。本轮未执行备份恢复或生产部署。

## 实测结果与问题修复

本轮基线113 passed/29.55s；增量后原功能回归113 passed/25.27s。最终同一条pytest命令执行**150项，全部通过，无失败/错误/跳过，43.57s**，包含原113项与新增37项。覆盖四题型、非法配置、权限、共享撤销、版本父链、恢复、fork、题库、快照、来源防伪、使用查询、统计、匿名、并发和双账号浏览器。证据见 [独立测试报告](test-report.md)、[full.xml](evidence/full.xml)。

真实浏览器：A共享年龄题给B，双方导入；A问卷18，B multiple问卷24/30/45；mine均值18，启用贡献后29.25。更新v2及恢复v3后旧问卷仍v1；390px无水平溢出且无JS异常。1000份合成数字答卷0..999得到均值499.5、计数1000，来源查询IXSCAN检查1键/1文档。该查询审计不代表生产容量。

实际遇到并修复了后台Mongo进程持续性、BSON毫秒时间比较、explain主机名非UTF8诊断、新旧测试文件同名收集冲突、预览source序列化和固定旧版本选题边界。首次失败日志保留，不将失败覆盖成从未发生。原代码功能错误与测试/环境问题在AI日志中分别说明。

## AI 使用、局限与后续

Agent依据用户提供需求、Prompt、原报告和聊天上下文完成代码、测试、文档与排版。用户给出七集合/固定版本/快照的实施契约与报告脉络；Agent细化CAS、共享竞态、题库upsert、小样本阈值及分桶并实际验证。没有证据表明用户已逐行审查或手工修改本阶段实现，不虚构人工工作或AI失误。真实工具、提示、产物和修复见 [AI日志](ai-usage-log.md)。

当前限制包括实时统计成本、单节点副本集、基础小样本抑制、固定年龄区间、无数据库管理员级append-only隔离。未验证Docker、公网部署、多浏览器、高可用、生产压力或回滚恢复。后续可在明确语义和权限下增加预聚合、缓存、数据贡献策略和运维权限；不能通过实时更新旧问卷来省去快照。

八项新增需求均在原系统上形成数据、API、UI和测试闭环；本阶段的价值是调整题目的聚合边界，同时保留既有问卷和答卷的历史解释能力。对应矩阵见 [需求追踪](requirements-traceability.md)，运行与演示见 [原运行手册](../../source/README.md)。
