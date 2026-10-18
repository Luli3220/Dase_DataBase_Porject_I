# AI使用说明与证据索引

本说明对应正式实验报告第6章“AI使用与设计演进”，按“工具—Prompt—产物—设计取舍/修改—验证”组织。开发实施与功能修正的记录为2026-10-16；本次索引核对日期为2026-10-18。当前正式叙述、原始Prompt和执行证据分开保存，避免重复复制大量聊天或把计划当作结果。

## 1. 先看这些入口

|入口|内容及边界|
|---|---|
|[正式实验报告](report/DataBase_Project_1.pdf)第6–7页|作者关于需求分析、候选方案比较、AI实施、问题与修正的说明|
|[ChatGPT分享记录](https://chatgpt.com/share/6ad37dad-75c4-83ec-b5d6-765759cca816)|作者提供的前期设计讨论入口；PDF中已有同一地址。本次网页工具未能读取全文，不转述未核验的具体轮次/原句|
|[原始Prompt目录](../prompts/README.md)|总控及A/B/C分阶段规格的完整原文，不以本说明摘要替代原文|
|[源码](../source/app/) / [测试](../source/tests/)|Agent实际生成并在后续修改的实现|
|[测试总索引](evidence/README.md)|阶段72/17、初次102、目录整理102、用户名修正113及失败记录|
|[首次逐轮实施日志](https://github.com/Luli3220/Dase_DataBase_Porject_I/blob/744a4d298e4e0ae779c8bee421aba6d7ae6f7ff3/docs/ai-usage-log.md)|本说明整理前的完整历史版本，固定commit可回溯，不复制成另一份并行现行日志|

ChatGPT分享页与Coding Agent的实施记录不是同一个证据入口：前者用于前期讨论，后者以仓库Prompt、Git提交、代码与测试日志核验；不默认分享页包含全部工具执行过程。

## 2. 使用了哪些工具，作者与AI分别做什么

**工具。** 前期设计讨论使用ChatGPT（作者提供分享链接）；实现阶段使用Codex Coding Agent，通过PowerShell查看材料、编辑代码、执行Python/pytest/httpx/真实MongoDB及Playwright/Chromium。报告核对使用PDF文本提取及逐页渲染。没有采用现成问卷系统或关系数据库，不编造未记录的模型版本、对话轮数或人工操作。

**作者的工作。** 按正式报告第6章，作者的工作重点是结合课程要求比较数据组织方案、确定业务语义和验收标准，并提出后续修正要求。当前可核对的设计输入包括四集合结构、内容版本与Schema版本分离、已发布版本保留、匿名不等于免登录、历史答卷保留以及跨版本latest_only口径。后续“非匿名答卷应显示注册用户名、历史匿名仍受保护”的要求也是作者在会话中明确提出的。

**AI的工作。** Agent读取已确定的课程材料和规格，完成Schema/索引、数据访问、规则解释器、服务/API、认证、网页、测试与技术文档；实际执行命令、发现或复核边界问题，再按要求修改并回归。Agent对实现方式的选择（如副本集事务、CAS、响应白名单）在设计文档中说明理由。

**修改如何归属。** “作者提出设计取舍或修改要求”不等于“作者亲手改写了代码”。本记录中，具体代码修改和自动化验证由Agent完成；未声称作者手工修改/逐行审查过代码。早期候选方案比较按作者报告说明，并通过分享链接提供来源；没有成功读取的早期对话不伪造为逐字记录。

## 3. 实际Prompt—产物—修改索引

下表标明原文文件或准确短引；摘要不是虚构的完整对话。

|编号/输入来源|实际任务/Prompt|得到的实现|修改或约束落实|验证入口|
|---|---|---|---|---|
|P0：用户首轮要求 + [总控原文](../prompts/00-总控Prompt.md)|准确短引：“请直接创建真实可运行的代码，不要只输出方案或伪代码”；要求A→B→C逐阶段执行测试|可运行项目、实施顺序、分层结构|业务数据仅MongoDB；每阶段先验收再继续|阶段日志及[实施计划历史](archive/implementation-plan.md)|
|P1：[数据库与规则原文](../prompts/01-数据库与规则引擎.md)|四集合、BSON、版本指针/冻结、匿名、重复、声明式跳转、固定fixture|[Schema/索引](../source/app/db/mongo.py)、[文档模型](../source/app/models/documents.py)、[规则引擎](../source/app/rules/engine.py)、[问卷服务](../source/app/services/surveys.py)|事务处理跨集合写；revision CAS；先冻结后切指针；路径复核和幂等唯一索引|[Phase A](evidence/phase-a.txt)：72通过|
|P2：[API与网页原文](../prompts/02-后端API与网页.md)|注册登录、ownership、公开填写、可视化编辑/预览、版本/统计界面|[认证](../source/app/services/auth.py)、[API](../source/app/api/routes.py)、[网页](../source/app/static/app.js)|签名Cookie/CSRF、明确匿名DTO、日期输入解析、分支答案清除、重试沿用UUID|[API阶段](evidence/phase-b-api.txt)：17通过；[HTTP](evidence/final-http.json)：22项PASS|
|P3：[测试与验收原文](../prompts/03-测试文档与验收.md)|真实Mongo、权限/版本/并发/匿名/统计/边界、步骤与输入输出、文档和AI日志|[unit/integration/web测试](../source/tests/)、[用例](test-cases.md)、[报告](test-report.md)|增加极大整数、退出撤销、分块请求、统计snapshot；保留真实错误和未验证项|[首次完整](evidence/final.txt)：102通过|
|P4：用户目录整理要求|准确短引：“prompt可以放一个目录，然后source可以放一个目录……做好索引”|requirements/prompts/source/docs及各README|修正脚本工作目录、证据与打包根路径；保留Mongo数据及原材料|[目录迁移](evidence/restructure/README.md)：102通过|
|P5：用户名修正要求|准确短引：“为非匿名答卷增加respondentUsername字段，数据来自users.username”；要求批量、历史匿名、最小修改|[owner_submission/list_owner](../source/app/services/submissions.py)、网页身份显示、[新增测试](../source/tests/integration/test_respondent_usernames.py)|当前页去重ID的一次users.find；仅非匿名输出用户名；缺失为null保留ID；架构/规则/统计不改|[新增11项及完整113项](evidence/respondent-username/README.md)|
|P6：用户最终报告核对要求|本次输入摘要：按原始PDF检查完成报告、解释docs内容、明确AI使用并加入分享索引|[逐项核对](requirements-traceability.md)、本文、文档/证据总索引、4份历史文档归档|正式PDF原样收录；修正最新113/历史102定位；不改业务代码、不改写历史执行结果|2026-10-18逐页阅读与测试收集113项；不是功能测试重跑|

## 4. 方案取舍与AI实现问题分别记录

**设计取舍。** 报告比较了“配置与版本集中在问卷文档”“版本独立文档”“题目/选项进一步拆分”等方案，最终采用四集合。这里的候选方案A是讨论中的备选设计，不代表系统曾实际按该方案运行或已经发生历史数据损坏。跨版本先去重再筛版本、匿名身份内外分离，同样属于业务语义与设计约束的明确过程，不能把它们虚构成已发生的线上事故。

**实际实施问题及修正。**

|问题/发现方式|实际修改|证据/限制|
|---|---|---|
|conda启动器异常，db为Python3.10.21且缺依赖；系统包继承出现无关依赖冲突|改用3.11.5独立venv，关闭系统包继承、锁定版本|pip check通过；没有修改原conda环境|
|沙箱pip网络异常、Docker daemon未运行，后台Mongo进程曾无法持续连接|使用批准的依赖安装执行与常驻本机mongod/rs0|真实Mongo测试；Docker只验证配置，不声称容器运行|
|审查发现严格日期模型可能拒绝ISO字符串|仅对AwareDatetime输入允许必要解析，仍拒绝无时区时间|API日期测试|
|审查发现极大整数在math.isfinite前可能转换溢出|先检查安全范围，再判断有限值；加入10**1000测试|静态审查发现的风险，不虚称曾触发失败测试|
|视觉检查发现选择题答卷显示内部选项ID|按原问卷版本映射选项标签|真实浏览器与截图；历史答案仍保存稳定ID|
|作者发现非匿名答卷显示内部用户ID|批量补用户名，前端优先显示；匿名快照控制DTO|新增11项，完整113项通过|
|用户名修正首次测试时Mongo未启动|复用原数据目录启动rs0，不修改功能代码即重跑|[首次4通过/7准备错误](evidence/respondent-username/initial-no-mongo.txt)与[随后11通过](evidence/respondent-username/targeted.txt)均保留|

## 5. 实际验证与代码版本

|版本/阶段|实际结果|证据|
|---|---|---|
|首次交付[80ac7d3](https://github.com/Luli3220/Dase_DataBase_Porject_I/commit/80ac7d327ed8f133e657a62e688827c6901fba60)|最终102项通过；阶段A72、阶段B17；独立HTTP22项PASS|[证据索引](evidence/README.md)|
|目录整理[795c8b8](https://github.com/Luli3220/Dase_DataBase_Porject_I/commit/795c8b8c9a34ecf4275aa295325a201f3e1014de)|102项通过，31.82秒|[restructure](evidence/restructure/README.md)|
|功能修正[744a4d2](https://github.com/Luli3220/Dase_DataBase_Porject_I/commit/744a4d298e4e0ae779c8bee421aba6d7ae6f7ff3)|新增11项通过；完整113项通过，37.82秒|[full.txt](evidence/respondent-username/full.txt)、[full.xml](evidence/respondent-username/full.xml)|

113项为72单元、39真实数据库/API/并发、2浏览器实例；不同阶段数量不能相加为一个“总测试数”。22项HTTP检查独立于pytest。2026-10-18核对了原始XML及当前测试收集的113项，没有重新运行功能测试，也没有把旧记录的日期更新为今天。

## 6. 结论与未验证范围

AI承担了主要代码实现、自动化执行和部分问题修复；作者负责提出课程目标、设计/验收约束和具体修正要求。判断依据是可追踪的规格、代码修改、真实测试结果以及作者提供的报告/讨论入口，不能仅依据AI自述“已完成”。

未验证项仍包括Docker容器构建/运行、公网HTTPS部署、容量压测、多节点故障转移和其他浏览器引擎；本次分享页自动读取也未成功。以上限制与已通过的本机功能测试分开说明，避免夸大实现或人工参与。
