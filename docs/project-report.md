# 第一阶段项目完成报告

日期2026-10-16。项目目标：完成基于MongoDB的可注册、可创建发布、可登录填写、可按规则跳题并统计的在线问卷系统，并为课程第二阶段的未知需求保留现有结构与历史数据兼容。

## 完成情况

课程六大功能已实现：账号认证；问卷创建/个人管理/发布分享/截止关闭；单选、多选、文本和数字题；配置校验与声明式跳转；多人、匿名和重复填写；单题及全卷统计/回答明细。网页提供可视化表单，不要求用户手工编辑JSON，包含预览、分支返回、幂等重试、版本与口径选择，手机宽度可用。

后端为FastAPI/PyMongo，所有业务数据只持久化MongoDB。Python3.11.5隔离环境满足规格；db conda为3.10，因此未修改用户现有环境。没有替代为关系库或现成问卷系统，也没有推送到外部仓库或宣称公网部署。

## MongoDB设计与关键选择

四个集合users/surveys/survey_versions/submissions；题目、选项、校验及规则嵌入版本，答案嵌入独立答卷。不同用户/版本/无限增长的提交采用引用，ObjectId和UTC Date保持BSON类型；JSON Schema约束基础结构，Pydantic文档模型与规则层做细校验。唯一索引保护用户名、公开ID、版本、幂等键。详细字段、关系、索引成本及嵌入理由见database-design.md。

不用关系数据库一是课程明确禁止，二是一个问卷版本整体冻结/读取适合文档边界，无需把每个选项机械拆表再装配。并不声称关系数据库技术上无法实现。单节点副本集支持跨集合事务，解决新建半成品、首份提交与策略修改、切版/关闭与提交竞态；每卷共享writeRevision是明确的课程规模性能取舍。发布先冻结后切权威指针，中间中断可重试恢复，未成为公开指针的sealed版本不会被填写者误读。

schemaVersion代表文档格式；version/surveyVersion代表问卷内容。发布版不可编辑，派生下一草稿不会影响当前公开版。旧提交引用原题目/选项快照，旧表单切版后409，避免静默重解释。

## 跳转、校验、隐私与统计

白名单解释器按priority升序取首条匹配，未匹配走数组下一题，仅向后或结束；无eval/exec。单选eq、多选any/all、数字比较，静态检查目标/operand/类型/唯一性/边界，动态从首题重算路径。路径上必答缺失拒绝，被跳过题的额外答案拒绝，可选空值不落库。Unicode文本trim；数字拒绝bool/字符串/非有限/超出安全范围。

每次成功新逻辑填写追加，不覆盖历史。相同UUID和内容返回原ID，不同内容409；最新统计跨整卷选每个账号最新后才按版本筛。multiple每份有效，首次成功后策略锁定。统计明确原始数、有效数、题目回答数，数字mean无数据为null，文本/数字明细分页；单题与全卷同一实现。

匿名仍登录，内部respondentId用于去重，但创建者读取使用allowlist DTO；anonymousAtSubmission保证历史匿名不被V2实名设置解除。自由文本可能主动透露身份，不能承诺绝对匿名。Cookie签名/过期/HttpOnly/SameSite、CSRF、ownership、退出会话撤销、输入长度和输出转义共同保护边界。

## 实际测试与过程

Phase A实际72通过后进入B；Phase B17API通过，加22个真实HTTP请求检查后进入C。真实浏览器验证编辑四类题及三类跳转、预览不入库、登录返回链接、即时校验、分支旧答案清除、重复提交/统计、V2冲突、关闭和390px表单。

最终在完全隔离的精确依赖环境执行 `python -m pytest -q --junitxml=docs/evidence/final.xml`：**102 passed / 0 failed / 0 skipped，31.36秒**。包含69规则单元、31真实数据库/API/并发、2浏览器实例。pip check通过。原始输出、JUnit、逐项结果、截图和环境JSON均已交付；测试用例有输入/步骤/输出/结果，见test-cases.md。Git工作区不存在，所以不编造commit。

实际遇到并修复：conda启动器/Python版本不符；pip沙箱网络；Mongo后台进程持续性；严格日期输入；极大整数判断溢出；答卷明细选项标签；统计同响应快照及会话撤销边界。具体命令与真实结果见test-report.md。没有虚构“测试曾失败后修复”的叙事，部分问题由静态或视觉审查发现。

AI工具为本会话Codex，使用原始课程材料和四份Prompt作为输入，生成代码、执行测试、修复并写文档。用户提供需求与设计约束，AI未声称用户已人工审查。详细真实过程、错误和修改见ai-usage-log.md。

## 交付与未验证范围

交付源代码、四集合schema/索引初始化、配置样例、精确依赖、Docker替代配置、启动/测试/演示脚本、OpenAPI及中文API文档、系统/数据库/规则设计、需求追踪、测试证据、AI日志和本报告。原PDF和规格保留，敏感.env、虚拟环境和数据库数据不进入交付压缩包。脚本scripts/package_delivery.py生成delivery/Project1-complete.zip、SHA256SUMS.txt及docs/delivery-manifest.json，并逐文件核对压缩内容。

已在最终代码上重启本机127.0.0.1:8000服务，再次通过22项HTTP检查与health200；Python编译、JS/PowerShell语法、Compose配置解析和文档本地链接均检查通过。该结果不扩展为“Docker容器已运行”。

环境限制：Docker daemon不可用，Docker构建/运行未验证；本机实际Mongo8.3.11，未单独验证Mongo7/8.0；未做容量压测、公网HTTPS部署、多节点故障恢复或其他浏览器引擎测试。单节点副本集不是高可用部署。关闭不可重开、只允许向后跳、不跨版本合并统计都是已确定的第一阶段边界，未删减课程功能。

## 第二阶段保持兼容的扩展入口

新增题型：models/domain.py、models/documents.py、rules/engine.py、static/app.js控件与services/statistics.py。新增条件：白名单、静态operand校验、evaluate_condition及前端规则菜单。新增统计：StatisticsService，保持mode/version和匿名DTO。文档结构变更：schemaVersion、新迁移脚本、旧数据读取兼容，不把问卷version当迁移版本。每次需求变更补ADR、需求追踪和AI日志，执行现有102项及新增测试，禁止丢弃第一阶段重写。

## 交付目录整理

首次提交80ac7d3之后，按用户要求重组目录：requirements保存原始任务，prompts保存原文规格，source集中实现/测试/运行配置，docs保留交付文档与证据。根及各目录README提供索引；当前运行手册为source/README.md，上文原实现相对路径以source为根。原始材料和业务实现字节未变，仅调整路径、脚本定位和文档。

迁移后完整回归102项通过（31.82秒），并实际验证安装入口、Mongo初始化、服务启动和文档链接，单独保存docs/evidence/restructure。初始31.36秒的验收记录保持原样。目录映射见[目录调整记录](repository-layout.md)，当前索引见[仓库README](../README.md)。
