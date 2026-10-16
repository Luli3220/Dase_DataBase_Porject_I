# AI使用日志（真实过程）

工具：Codex会话中的代码生成/编辑、PowerShell进程执行、pytest、真实MongoDB、httpx、Playwright/Chromium、实际截图查看。使用PDF技能读取原PDF；没有使用现成问卷框架、关系数据库或多智能体并行开发。截至首轮本地交付，没有外部推送、发消息或发布公网网站。后续GitHub提交授权见文末。日期2026-10-16（Asia/Shanghai）。

## 实际Prompt来源

用户原始指令：阅读Project1/project1.pdf和Markdown开发规格，按00-总控Prompt顺序完成“数据库Schema与核心规则引擎→后端API、身份认证和问卷网页→完整测试、修复和文档”，创建真实可运行代码，每阶段执行测试并报告，严格遵循Mongo结构、版本、匿名与重复策略，提供完整项目及启动/设计/API/测试/AI日志/完成报告。用户允许在conda db操作；检查后发现Python版本不足，记录并使用项目venv。

实际引用并执行的提示文件（原文保留在交付根目录）：00-总控Prompt.md、01-数据库与规则引擎.md、02-后端API与网页.md、03-测试文档与验收.md。完整实施Prompt.md为合并版，内容作为参考，未虚构额外人工提示轮次。原始PDF11页已完整提取阅读。总控/规格本身为项目负责人已确定的设计输入，不将其冒称AI独立原创。

## 生成、修改与验证记录

|顺序/阶段|AI执行/产物|发现的问题及真实修改|验证|
|---|---|---|---|
|1 材料与环境|读取所有规格/PDF，检查文件、Git、解释器、Mongo/Docker；生成implementation-plan|无既有代码/Git；db为3.10；Docker daemon不可用|实际命令输出，不声称可用的环境未运行|
|2 A规则|models/domain.py、rules/engine.py、固定fixture及单元测试|Q3“否则END”用lt规则表达，保持通用下一题；严格区分0/MISSING|R01–R15及类型/边界/运算符执行|
|3 A数据库|schema/index、BSON转换、surveys/submissions/statistics服务、init脚本、ADR001|事务保护首份策略/状态竞态；冻结后恢复；不采用进程内锁|72项Phase A真实通过|
|4 环境修复|项目venv安装依赖、本机mongod rs0|沙箱pip网络失败→批准网络执行；后台Mongo不持续→常驻进程|真实Mongo事务/索引/聚合测试|
|5 B API|auth/security/main/routes，严格DTO、CSRF与Cookie|ISO日期输入按AwareDatetime允许解析，不允许无时区|17项API通过；22个真实HTTP请求检查|
|6 B UI|HTML/CSS/原生JS编辑器、填写/预览/统计|使用转义/textContent；返回前题清除后续；一次逻辑提交锁定body/UUID|真实Chromium页、完整浏览器及手机测试|
|7 C边界|并发/恢复/策略/同时间排序/分页测试|审查发现极大整数有限值转换可溢出，调整判断顺序，增加10**1000回归|98项阶段回归；随后完整102项|
|8 C加固|四集合Pydantic BSON文档模型、sessionVersion、请求限制、只读snapshot统计|复制Cookie可撤销；分块请求也限制；同响应统计保持快照|新增撤销/分块两例，完整102项通过|
|9 视觉复核|查看实际statistics/mobile截图|发现答卷选项显示内部ID，按历史版本映射标签|重新跑浏览器，更新真实截图|
|10 隔离与交付|关闭system-site-packages，精确lock，README/全套docs/证据索引/打包脚本|消除继承base无关包冲突；Docker明确未运行|pip check通过；最终102 passed/0 failed/0 skipped|

阶段报告已经在会话中实际发送：A72通过后进入B；B17API与22HTTP通过后进入C；C浏览器通过后继续边界与交付。所有测试数字来自真实输出及JUnit，不是Prompt中预期值。日志不记录密码/会话密钥；演示脚本只在显式运行时生成随机账号。

## AI错误与人工参与边界

AI曾采用不适合自动化宿主的后台Mongo启动方式，实际连接失败后修正；初期为快速建立环境使用system-site-packages，导致无关包冲突提示，交付前改为完全隔离；日期严格模式、极大整数和选项显示问题由AI审查并修改。文档编写时一次同文件删除/新增组合补丁被工具原子拒绝，调整为Update操作后成功，无业务文件损失。

这些修改由AI在本会话完成。没有证据表明用户手工改过代码、人工审查测试或批准设计逐项细节，因此不写“人工已审查/人工修复”。用户实际贡献是提供原始课程文件、明确规格和高标准验收要求。人类后续可按README重跑并评审；这不冒充已发生的工作。

AI的价值：生成分层实现及测试、执行真实环境、检查匿名/版本/并发语义、形成可追踪证据。AI的限制：不能自动判断自然语言题目是否根本改变语义；没有替代真实运行证据；没有完成Docker启动、公网部署或容量证明。第二阶段应保留此日志、继续记录新提示/修改/回归，而非重写项目。

## 后续：用户授权提交GitHub

用户实际补充指令：“okay，如果确认没问题，请你提交到：https://github.com/Luli3220/Dase_DataBase_Porject_I.git”。依此检查远端refs（当时为空）、Git身份配置、依赖和原始102项测试证据；未改业务代码，因此不重复执行无变化的全部功能测试。将Project1作为仓库根目录初始化main，排除.env、.venv、.local、缓存和delivery重复压缩包；提交前扫描暂存清单与敏感内容，再常规push并核对远端提交。实际提交结果以Git历史和会话回报为准，不在提交前编造commit号。
