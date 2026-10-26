# 第二阶段 AI 使用日志（真实记录）

日期：2026-10-26，Asia/Shanghai。工具：Codex、read_thread、PowerShell/Python、PyMongo、pytest、httpx/TestClient、Playwright/Chromium、LaTeX、PDF 文本提取与页面渲染。未使用多智能体委派，没有发送邮件、聊天消息或推送远程代码。

实际用户指令：按 [Project2_Implementation_Prompt.md](../../prompts/Project2_Implementation_Prompt.md) 高标准完成第二阶段，承接已有代码，按 report1/1.1.tex 类似格式编辑 report1/1.2.tex；叙事顺序为需求分析、原数据库关系和架构回顾、实现。读取了用户指定的第一阶段聊天、课程PDF、变更PDF、原报告PDF和原TeX。采用 PDF 技能读取及版式核验，以用户指定报告为写作样式参照。原第一阶段 AI 日志未修改。

Agent 产物：在原 models、mongo、surveys、routes、main、app.js、样式、模板和脚本增量改动；新增 questions/question_banks/question_statistics 服务、question_routes、迁移脚本、新测试、当前技术文档补充与本目录材料。所有模型和权限规则以用户提供 Prompt 为依据；七集合、固定引用＋快照、追加式恢复和保守跨用户授权均来自该契约，不能冒称为本轮用户已手工审查的代码。

用户已经确定的自主取舍：保留第一阶段结构、题目稳定身份、独立内容版本、问卷内快照、局部路由、先回归后演进，以及报告脉络。Agent 进一步落实：题库成员upsert与CAS、归档、导入时定义文档写锁、跨用户每份问卷3个实际回答阈值、固定数字分桶、仅贡献匿名聚合、来源一致性校验、显式解除关联、服务拆分。**尚无证据表明用户逐行审查或手工修改本阶段代码；报告不编造人工操作。**

发现与修正：

1. 原启动脚本经后台宿主启动的 Mongo 不能稳定连接。保留现有数据目录，使用受托管前台 mongod 进程，真实基线113 passed。未删除锁文件或数据。
2. 新数据层测试将Python微秒时间与Mongo毫秒时间比较，出现1 failed/1 passed。改为比较迁移前后已持久化文档；stage-b-first保留原失败，重跑2 passed。该问题在测试比较方式，不是旧数据被迁移修改。
3. 本机Mongo explain.serverInfo返回非UTF8主机名，导致索引诊断InvalidBSON。只对explain命令显式使用替换解码，业务读取继续严格；stage-e-first保留失败。第一次仅配置Database未生效，之后对command显式传入codec_options才修正；最终阶段6 passed。
4. 全套首次运行因新增test_browser/test_boundaries与旧测试同名而产生2个收集错误。给新增project2目录增加__init__.py，原测试未改。full-first保留原错误；后续全套通过。
5. 实现审查补上预览接口source的ObjectId序列化，避免新增来源导致旧预览JSON失败；测试验证真实预览200。发现题库固定旧版可能不在首批100条历史中，选题器保留固定版本选项；未把这项静态审查虚称为先前失败用例。
6. 检查原测试脚本和证据构建脚本默认写第一阶段路径，改为project2/evidence，避免后续执行覆盖历史。保护清单校验在最终审计执行。

测试、性能查询审计及迁移均真实运行。1000份合成答卷用于查询计划和聚合正确性，不代表生产容量。最终数量以 [独立报告](test-report.md) 和 [full.xml](evidence/full.xml) 为准。公开网站部署、Docker运行、其他浏览器、数据库恢复及高可用故障切换未验证。

排版与最终审计：依照用户提供1.1.tex的双栏格式生成1.2.tex，先修正内置编译器缺失等宽字体的回退，随后本机XeLaTeX成功输出7页PDF；逐页渲染查看、修正版本图交叉标签和末页栏位，无Overfull或缺字。原1.1.tex未修改。当前OpenAPI40操作（原22全部保留）、28份历史文件不变、本地链接无断链；服务已在127.0.0.1:8000真实启动并HTTP验证。


2026-10-27：用户明确授权“okay，帮我提交一下”。本轮检查待交付文件及凭据模式，提交并推送现有第二阶段分支，保留原基线标签。没有重新运行业务测试；150 passed/43.57s引用的是上一轮完整实测，并在提交前重新执行交付审计。
