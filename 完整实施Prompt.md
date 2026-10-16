# MongoDB 问卷系统（第一阶段）——Coding Agent 完整实施 Prompt

本文件整合总控、数据库与规则引擎、后端与网页、测试与交付四部分，可作为单一输入交给 Coding Agent。**课程原始 PDF `project1.pdf` 是原始约束**，本规格记录项目讨论中补充的行为定义。

# 交给 Coding Agent 的总控 Prompt：基于 MongoDB 的问卷系统（第一阶段）

你是一名具备 MongoDB 文档建模、Python/FastAPI、Web 开发、测试与技术文档能力的资深工程师。请基于本仓库、课程原始文件 `project1.pdf`（如可访问）以及同目录的三份阶段规格，**直接完成第一阶段可运行的在线问卷系统**；不要只产出方案、伪代码或漂亮的页面。以下是已由项目负责人确定的产品与设计约束，不得擅自改变。

## 0. 先读材料和检查项目

1. 检查当前仓库文件、技术栈、既有实现、依赖、Git 状态、可用的 MongoDB/Docker 环境；优先保护已有代码和数据，不做破坏性清空，不强制重置仓库。
2. 阅读 `01-数据库与规则引擎.md`、`02-后端API与网页.md`、`03-测试文档与验收.md`。如有课程原始 PDF，以原始要求为硬约束；本系列文档补充了其未定义的业务语义。
3. 创建 `docs/implementation-plan.md`：按阶段列任务、依赖、验收项、当前状态。必要时创建 `docs/adr/` 记录重要设计取舍。
4. 简要说明要采用的目录结构与启动方式后开始实际实现；除遇到无法安全推进的外部阻塞外，不在每一步都等待确认。

## 1. 项目背景和评分重点

实现简化版问卷系统：用户注册/登录、创建与管理问卷、公开 URL 分享、登录后填写、题目校验、条件跳转、保存每次提交、按题统计。课程明确规定 MongoDB，禁止关系数据库和现成问卷系统框架。前端可以简洁。阶段一完成后，阶段二会在原有代码上增加未知需求，禁止推倒重做；因此重视松耦合、版本兼容、测试与文档。

评分为 MongoDB 设计 35、后端逻辑 25、测试 10、文档 15、AI 使用说明 15；阶段一成绩占总成绩 30%，阶段二 70%。请将数据库设计原理、业务逻辑可验证性和真实开发记录视作正式交付物。

## 2. 不得偏离的架构

- Python 3.11+、FastAPI、PyMongo（或在说明理由后选同等 MongoDB 驱动）；服务端渲染 HTML 模板或简单静态网页 + 原生 JavaScript；pytest；MongoDB（建议 Docker Compose 提供可复现服务）。
- 仅 MongoDB 保存业务数据，禁止 SQLite、PostgreSQL 等关系数据库。
- 四个核心集合：`users` / `surveys` / `survey_versions` / `submissions`；版本内嵌 `questions`、`options`、`validation`、`routingRules`；提交内嵌 `answers`。
- 四种内部题型 `single_choice` / `multiple_choice` / `text` / `number`；按题型分别校验。禁止把某份问卷的 ID、选项、跳转路径硬编码进服务逻辑。
- 用户必须登录才能提交。匿名只意味着创建者看不到用户身份；系统需内部识别提交者。所有者 API 不能泄露匿名记录的 `respondentId`（包括嵌套内容、导出、调试响应等）。
- `surveys.publishedVersion` 明确指向对外服务的版本，`surveys.draftVersion` 是草稿指针。已发布版本不可编辑，历史答卷引用当时版本。
- 每次成功提交保存新记录。`latest_only`：整份问卷内每个用户仅最后一次计入当前有效统计；`multiple`：每次都计入。历史原始记录不删除。重复请求使用幂等键避免意外重复计数。
- 单选、多选、数字条件跳转：有序规则、第一条匹配优先、否则进入数组下一题；初始版本不允许跳回前面或自身。路径上必答题必须回答；被跳过的题不能混入有效提交。
- `schemaVersion` 代表数据库文档格式，`version`/`surveyVersion` 代表问卷内容版本，二者不可混用。

## 3. 按阶段实施，不得跳过验收

### Phase A：数据库与规则引擎
执行 `01-数据库与规则引擎.md`：确定并实现 BSON 字段、索引、基础集合校验，用户/问卷/版本/提交的数据访问逻辑；实现版本发布指针、不可变已发布版本、问卷配置校验、答案校验、声明式跳转、提交路径校验。编写针对每个规则的单元测试。完成后输出目录、设计要点及测试结果，再进行下一阶段。

### Phase B：后端 API 与网页
执行 `02-后端API与网页.md`：可登录、创建草稿、添加四类题、配置规则、预览、发布、分享 URL、按路径填写与提交、创建者查看问卷/统计；提供清晰错误提示和权限保护。保证服务端复核全部数据。完成后实际执行主要操作链路验证。

### Phase C：测试与交付
执行 `03-测试文档与验收.md`：真实 MongoDB 集成测试、接口/权限/匿名/版本/并发/统计/边界测试；运行环境启动说明、测试用例输入输出、结果、数据库结构和索引说明、API 文档、关键逻辑、项目报告、真实 AI 使用过程说明。发现问题要修复并回归。

## 4. 工作和汇报规则

- 每阶段完成后都要运行相关测试，说明使用的命令、通过/失败数量、环境限制；无法运行时明确标注“未验证”，不要伪造。
- 保留 `README.md`、`.env.example`、`docker-compose.yml`（若环境许可）、依赖清单、初始化脚本、测试脚本、`docs/`；不得提交明文密码、真实 token 或 `.env`。
- 所有设计取舍写明“为什么这样做、为什么不采用另一方案、风险/限制、对第二阶段的影响”。
- 严格记录 AI 使用日志：实际提示词或引用、生成/修改的代码、发现的错误、人工审查或修改；不能虚构人类的操作。
- 优先完成 P0 功能及六大必测项，避免用可选 UI、美化、复杂通用规则语言等推迟核心功能。
- 不要声称已经部署/测试除非有可复现的实际证据；不自动推送外部仓库、不删除现有业务数据。

## 5. 完成标准

必须能通过一套最小演示流程：注册 A 与 B → A 登录并创建四类题及跳转规则的问卷 → 发布得到 `/survey/<publicId>` → B 登录按不同路径提交 → 再次提交（符合 `latest_only` / `multiple`）→ A 查看匿名统计和原始答卷（看不到 B 身份）→ A 从已发布问卷派生新草稿并发布 V2 → V1 答卷依然可以按原版本解释 → 全套测试和文档可复现。

请开始执行，从仓库现状与 Phase A 入手。


---

# Phase A Prompt：MongoDB 数据库、版本管理和规则引擎

> 将本文件交给 Coding Agent 执行。目标：完成可运行、可测试的数据库和业务核心，不只输出设计图。所有在本文描述的“验收”应以实际代码和测试为依据。

## A0. 范围与技术约束

- 按课程任务实现 MongoDB 问卷系统第一阶段，**禁止关系数据库和现成问卷系统**。
- 核心集合限于 `users`、`surveys`、`survey_versions`、`submissions`；只有经具体业务理由论证后才能增加辅助集合，不要把题目、选项、规则机械拆成独立集合。
- 首选 Python 3.11+、FastAPI、PyMongo、Pydantic、pytest、MongoDB。持久化业务数据（用户、问卷、版本、答卷）全部写入 MongoDB；开发日志和测试文档可在文件系统保存。
- 本文档中的 JSON 例子仅展示网络接口/概念结构：MongoDB 实际使用 BSON ObjectId 和 UTC Date，API 对外使用字符串 ID 和 ISO 8601 时间；用统一序列化函数转换，切勿混用字符串与 ObjectId 导致关联失败。
- 所有用户权限和服务端校验不可由前端替代。

## A1. 建立文档模型（需有实际 Pydantic 模型 + BSON 映射）

### Collection 1: `users`

字段：
- `_id: ObjectId`：用户稳定 ID；
- `username: str`：必填，合理长度，归一化规则明确，唯一；
- `passwordHash: str`：Argon2id 等适当的不可逆密码哈希，禁止明文与自制哈希；
- `createdAt: UTC datetime`；
- `schemaVersion: int`，当前为 1。

唯一索引：`username`。不要以可变用户名替代 `_id` 进行引用。

### Collection 2: `surveys`

字段：
- `_id: ObjectId`；`ownerId: ObjectId`，关联 `users`；
- `publicId: str`：不可预测的 URL-safe 随机值（可使用 `secrets`），唯一，用于 `/survey/<publicId>`；
- `title: str`、`description: str`；
- `status: 'draft'|'published'|'closed'`；
- `publishedVersion: int|null`：当前对填写者开放的版本，草稿期间为空；
- `draftVersion: int|null`：当前正在编辑的版本；
- `submissionPolicy: 'latest_only'|'multiple'`：**全问卷级策略**，默认 `latest_only`，一旦已有成功提交则禁止改变（以免跨版本去重语义不稳定）。
- `deadlineAt: UTC datetime|null`、`createdAt`、`updatedAt`、`schemaVersion: 1`。

设计说明：之前讨论时暂把 `submissionPolicy` 放在版本 `settings` 下；本实施规格把它移动到 `surveys`，因为 `latest_only` 按**整份问卷跨版本**去重，策略必须有统一的权威来源。此项是有明确理由的细化，不是遗漏。

建议索引：`publicId` 唯一；`(ownerId, createdAt desc)`；根据实际查询添加索引，说明权衡。

### Collection 3: `survey_versions`

字段：
- `_id: ObjectId`、`surveyId: ObjectId`；
- `version: int`：同一问卷中的业务版本号，从 1 起；
- `schemaVersion: int`：文档结构格式，当前 1，与 `version` 完全不同；
- `state: 'draft'|'sealed'`：`draft` 可修改，`sealed` 不可修改；
- `revision: int`：草稿并发编辑时的乐观锁，编辑时条件更新并递增；
- `settings: {anonymous: bool}`：问卷该版本是否对**创建者**隐藏填写者账号身份；
- `questions: Question[]`：嵌入完整题目配置；
- `createdAt: UTC datetime`、`sealedAt: UTC datetime|null`。

唯一索引 `(surveyId, version)`。每份答卷引用这对稳定标识。`questions` 保持有界；约定课程项目中限制最多题数、选项数、规则数和文本长度，防止无限增长及 BSON 16MiB 上限问题。

#### Question（版本内嵌）

```json
{
  "id": "q1",
  "type": "single_choice",
  "title": "你是否有编程经验？",
  "required": true,
  "options": [
    {"id": "yes", "label": "有"},
    {"id": "no", "label": "没有"}
  ],
  "validation": {},
  "routingRules": []
}
```

- 四种内部类型：`single_choice`、`multiple_choice`、`text`、`number`。
- 题目顺序唯一来源为 `questions` 的**数组顺序**，不另存 `order`；规则以稳定的 `question.id` 引用目标，绝不以题号作引用。
- 选择题必须有非空 `options`，每个选项具有唯一、稳定的 `id` 和显示用 `label`；文本/数字题不得包含选择项（或规范化为空字段，不应出现语义模糊数据）。
- 同一问卷内跨版本保留相同 `question.id` 仅当题目语义延续；语义已根本改变，应创建新题 ID。选项 ID 同理，不能把老 ID 偷换成新含义。
- `required` 表示**该题被有效路径访问时**是否必答，而非整份问卷无条件必答。
- 可省略不适用的 `options`；`validation` 可为空对象、`routingRules` 默认为空数组。

#### Validation 定义

| 类型 | `value` | `validation` 支持 | 处理规则 |
|---|---|---|---|
| `single_choice` | 单个 option ID 字符串 | `{}` | 必须属于题目选项 |
| `multiple_choice` | option ID 字符串数组 | `minSelections`、`maxSelections` | 无重复、全是合法选项、满足上下限 |
| `text` | 字符串 | `minLength`、`maxLength` | 去首尾空白后按 Unicode 码点数判断并保存规范化文本 |
| `number` | JSON number | `min`、`max`、`integerOnly` | 禁止 `bool`、NaN、无穷、数字字符串，按范围/整数要求判断 |

- 可选题：未提供答案、`null`、空文本、空多选需要统一规范成“未回答”，不写入最终 `answers`；必答题此时失败。对单选/数字，空字符串是非法类型而不是数字 0。
- 非必答多选：没选合法；一旦选择，则必须满足 `minSelections/maxSelections`。所有约束参数也必须在问卷**发布前**通过合法性检查。
- 多选规定 `0 <= minSelections <= maxSelections <= options_count`，必答时有效选择数最少 1；若业务要求“必须选2个”，两者均设 2。
- 文本 `0 <= minLength <= maxLength`。数字 `min <= max`（如均存在），`integerOnly` 布尔。
- 手机号等标识符推荐文本字段；课程 PDF 中的“手机号必须为整数”是示例，若按数字题实现应能通过原例，但在设计说明中解释为何真实手机号应按文本处理（前导 0、国际区号）。
- 校验严格区分 `MISSING` 与有效 `0`、`false`（数字禁止布尔）。

#### RoutingRule（版本中嵌入 question.routingRules）

```json
{
  "id": "rule_1",
  "priority": 10,
  "condition": {
    "operator": "eq",
    "operand": "no"
  },
  "target": {
    "kind": "question",
    "questionId": "q3"
  }
}
```

- `target.kind: 'question'|'end'`；`kind='end'` 时不允许 `questionId`，`question` 时必须引用存在的目标。
- `priority` 正整数或非负整数均可，但必须统一；同题不可重复。**数字越小越先**，命中第一条即终止查找；未命中默认按数组进入下一题。最后一题默认结束。
- 允许运算符及参数：
  - 单选：`eq` + 一个合法 option ID；
  - 多选：`contains_any`、`contains_all` + 非空、无重复的合法 option ID 数组。`contains_any` 是交集非空；`contains_all` 是规则参数集合为用户选择集合的子集；
  - 数字：`eq`、`gt`、`gte`、`lt`、`lte` + 有限数值；
  - 文本：第一阶段无条件跳转运算符，不允许把任意代码/正则/表达式直接执行。
- 未回答的可选题不触发其条件规则，直接进入下一题。
- 第一阶段强制所有 `question` 类型目标的数组索引严格大于当前题索引，禁止自跳、回跳和环；`end` 允许提前结束。
- 运算符白名单 + 数据驱动解释器，不使用 `eval` / `exec` / 执行用户脚本；任何题目不可硬编码跳转。

### Collection 4: `submissions`

字段：
- `_id: ObjectId`、`surveyId: ObjectId`、`surveyVersion: int`；
- `respondentId: ObjectId`：服务器认证身份写入，绝不信任客户端提供；
- `anonymousAtSubmission: bool`：从当前提交时所用不可变版本复制，历史匿名承诺不可因后续设置变更被解除；
- `requestId: str`：客户端为一次**逻辑提交**生成 UUID，网络重试沿用同一值（幂等）；新的真正提交生成新值；
- `answers: [{questionId: str, value: str|list[str]|number}]`：仅保存经过完整校验的有效路径答案；未回答的可选题不存答案；
- `submittedAt: UTC datetime`：由服务端生成；`schemaVersion: 1`。

建立 `(surveyId, respondentId, requestId)` 唯一索引，避免一次 HTTP 重试产生两次答卷。冲突时相同 requestId+相同请求内容返回原记录；相同 requestId 但内容不同返回 409，而不是静默接受不同答案（可用规范化输入比较或存 `payloadDigest`）。

不使用 `(surveyId, respondentId)` 唯一索引，因为用户可以重复提交且历史必须保存。

建议 `(surveyId, surveyVersion, respondentId, submittedAt desc)` 及按实际聚合需要的辅助索引。最新记录排序至少 `(submittedAt desc, _id desc)`：提供确定性次序，并在文档说明服务器生成时间与同时间戳并发的限制；如强需提交顺序线性化另行设计。

## A2. 匿名和重复提交：必须遵循的语义

1. 所有填写者必须登录，包括匿名问卷。
2. `respondentId` 存在数据库内部，用于重复提交、本人查询、审计；创建者查看匿名问卷的逐条答卷、统计、导出、错误日志响应时，均不能得到账号标识、用户名、邮箱或可直接关联到账号的隐含映射。不要仅依赖前端隐藏字段。
3. 创建者是否可见身份，以**答卷发生时** `anonymousAtSubmission` 为准；不能因为 V2 改成实名，就公开 V1 原匿名答卷身份。对于匿名问卷自由文本，明确说明只能隐藏账号身份，无法担保回答内容绝对不可识别。
4. 每次成功提交追加一份独立记录；绝对不以 update/replace 覆盖此前的成功提交。
5. `latest_only`（默认）：对同一 `surveyId` 的各 `respondentId`，按 `(submittedAt, _id)` 选择最新的**整份问卷**提交记录。旧记录保留。注意去重在跨版本全体提交中进行，再根据所选版本过滤，以免旧版旧提交被误算当前有效记录。
6. `multiple`：每份成功提交都参与当前有效统计。
7. 统计接口必须显式提供统计口径：`current_effective` / `historical_raw`。前者按整份问卷的 `submissionPolicy` 选择有效记录，再按目标版本计算；后者展示指定版本的**原始提交**，不得默认为“当前唯一人数”。
8. 版本统计默认要求 `version` 参数，或由服务端明确采用 `publishedVersion`；跨版本合并单题均值/计数默认**不做**，避免相同题号不同语义。

## A3. 问卷生命周期、编辑和发布

- 新建问卷：`surveys.status='draft'`, `publishedVersion=null`, `draftVersion=1`，创建一份 V1 `survey_versions.state='draft'`。创建过程应具备可恢复/幂等逻辑；不得留下无法使用的半成品而不报告。
- 编辑草稿：只能修改 `draftVersion` 指向且 `state='draft'` 的文档；使用 `revision` 乐观锁（条件更新 + 增加版本号），失配返回 409 并提示刷新。
- 发布：先对整个版本进行**静态校验**；通过后原子性地在 `survey_versions` 单文档上把 `state` 从 `draft` 置为 `sealed`（同时设 `sealedAt`），从此不得改变 `questions/settings`；再对 `surveys` 执行条件更新，设 `publishedVersion=该版本`、`draftVersion=null`、`status='published'`。不要指望普通两个 collection 的写入天然具备事务原子性。
- **权威性**：对外填写始终以 `surveys.publishedVersion` 为准，并要求指向已 sealed 的版本。若 sealed 成功但指针提交失败，必须可检测、可重试/恢复，不允许“半发布版本”被对外误用。允许根据实际 Mongo 部署选择多文档事务；若默认 Docker standalone 不支持事务，用上述“先冻结后切指针 + CAS + 恢复”方案。
- 从已发布版本创建新草稿：复制版本中的题目与设置生成 V2（或下一个唯一版本号），修改只作用于草稿；V1 对外继续有效。确保新版本号分配并发安全（唯一复合索引、条件更新和冲突重试），不得通过未经保护的 `count()+1` 分配。
- 问卷可关闭、设置截止时间。只读列表仍可访问；`closed` 或超过 `deadlineAt` 不再接受提交。修改截止时间和问卷状态需创建者权限。
- 用户携带提交开始时看到的 `surveyVersion`；提交时如果不同于当前发布版本，返回明确 `409 SURVEY_VERSION_CHANGED` 并要求重新获取问卷，不要按当前版本悄悄解释旧答案。
- `anonymous` 的不同版本不会追溯性改变历史答卷隐私性；`submissionPolicy` 在首份成功提交后锁定。

## A4. 两层校验 + 路径执行器

### 静态配置校验（发布前必须完全通过）

- 题型、题目 ID、选项 ID、规则 ID、优先级的唯一性与值域；title 和 options 合法；
- `required` 类型正确，`validation` 按题型合法，边界不矛盾；
- 规则运算符适用于题型，`operand` 类型与选项/数值范围合法；
- 目标题目存在、向后、且不是自己；无冲突优先级；`end` 不带题目 ID；
- 问卷至少一题；明确并实施长度/题目数上限。

### 动态答案校验（在服务端完成）

- 客户端不得决定 `respondentId` / `anonymousAtSubmission` / `submittedAt`；不能直接提交任意题目 ID、重复题目 ID、无效选项 ID、错误类型；
- 从 `questions[0]` 出发，按当前题 `type` 规范化并校验，检查规则，命中第一条则跳转，否则走下一题，直至 `end` 或数组结束；
- 仅要求**有效路径上的必答题**回答；跳过的必答题无需回答；
- 非必答题无答案时直接按顺序前进（不执行其条件规则）；
- 不在本次路径的额外答案一律拒绝，不悄悄入库；可选题空答案规范化为不存；
- 最终持久化的是服务器重算并通过校验的 `answers`，不是不可信原始请求体。

建议独立实现 `validate_question_config`、`validate_answer`、`evaluate_condition`、`next_question`、`trace_path_and_validate_submission`，不要把所有规则写在 HTTP 路由中。统一领域错误码：`VALIDATION_ERROR`、`INVALID_ROUTING_RULE`、`SURVEY_CLOSED`、`SURVEY_EXPIRED`、`SURVEY_VERSION_CHANGED`、`DRAFT_CONFLICT`、`FORBIDDEN` 等；结构化错误应包含可定位的 question ID 和字段路径。

## A5. 设计验证用的固定样例（必须实现为测试 fixture）

- Q1 单选（必答）：“是否有编程经验？” yes/no；选 no 直接跳 Q3，否则 Q2。
- Q2 多选（必答）：“熟悉哪些语言？” python/java/cpp；至少 1 项、至多 3 项；`priority=10` 选择同时包含 python、java 跳 Q4；`priority=20` 包含 cpp 则 `end`；否则 Q3。
- Q3 数字（必答）：“每周学习几小时？” `min=0,max=80,integerOnly=false`；`gte 10` 跳 Q4，否则 `end`。
- Q4 文本（非必答）：“课程建议？” 长度 `0..500`；默认 `end`。

注意：Q2 两条规则同时命中时第一条优先，跳到 Q4。Q1=no 跳过 Q2 后，Q2 的必答限制不生效。

## A6. 数据库初始化与验收

编写 `scripts/init_db.py`（或等价脚本），可重复运行创建索引和必要的 Mongo `$jsonSchema` 基础校验器。初始化不得清除数据库；若需要演示数据使用显式 `scripts/seed_demo.py`，仅在受控的开发/测试数据库运行。至少有：

1. 唯一 username/publicId/(surveyId,version)/(surveyId,respondentId,requestId) 索引生效。
2. 草稿版本可编辑但 sealed 版本不可编辑；发表后指针解析准确。
3. 使用真实 MongoDB 插入/读取嵌套题目和答卷，BSON ObjectId、UTC Date 完全一致。
4. 静态校验拒绝非法规则和目标；路径引擎正确处理优先级、跳题、提前结束、非必答和额外答案。
5. 匿名、版本引用、重复提交策略有稳定数据访问接口。
6. 相关单元测试（不依赖数据库）+ 最少一组真正使用 MongoDB 的集成测试可运行。

### Phase A 交付文件

- 领域模型和 Schema 映射、Mongo repository/索引初始化、校验器、规则引擎、版本服务、提交/统计所需数据操作；
- `docs/database-design.md`（字段及 BSON 类型、四集合关系、索引、嵌入 vs 引用、设计取舍、版本与隐私策略、面向阶段二的扩展说明）；
- `docs/rule-specification.md`（题型、规则语法、优先级、默认路径、错误码、算法）；
- 真实执行的测试命令和结果记录；尚未通过的测试清楚标出，不能声称完成。


---

# Phase B Prompt：FastAPI 后端接口和可用网页

> 前提：Phase A 的四集合模型、问卷版本机制、校验器和路由引擎已实现且测试通过。此阶段必须交付可以使用浏览器演示的完整业务链路，而不只是 API 文档或静态页面。

## B0. 技术方案与基本原则

- 后端：FastAPI + PyMongo，推荐以同步 `def` 路由封装同步数据库驱动，避免在异步事件循环中直接执行阻塞 Mongo 查询。
- 前端：Jinja2 模板（可选）+ HTML/CSS + 少量原生 JavaScript；不使用整套现成问卷系统框架。移动端基本可用，界面无需重型视觉设计。
- 数据模型、规则解释器、提交校验、统计逻辑放在独立 service/repository 层，不与模板或 HTTP 路由耦合。
- 严格保持 Phase A 的单一字段定义和业务语义，不另外在前端发明第二种规则表示法。
- 提供 `.env.example` 配置 Mongo URI、数据库名、SESSION_SECRET、ENVIRONMENT、APP_BASE_URL 等，真实密钥/用户密码/Token 不入库。

## B1. 身份认证和访问权限（P0）

实现用户注册、登录、登出、获取当前用户资料。密码必须安全哈希存储，登录验证禁止明文比较。建议采用经签名且带过期时间的 HttpOnly、SameSite Cookie 登录会话；生产环境要求 Secure。所有改变状态的 Cookie 会话请求应有 CSRF 防护，并使用合适的鉴权失败响应；浏览器页面对退出、过期登录有明确反馈。

访问控制：

1. 创建、管理、发布、关闭问卷以及查看其答卷/统计，只允许 `survey.ownerId == 当前用户ID`。
2. 其他已登录用户通过公开链接可以填写已发布且尚未关闭/到期的问卷，**但不能访问创建者的管理 API**。
3. “登录后只能看到自己创建的问卷”作用于个人管理列表；不应阻止填写者使用收到的分享 URL 访问其他人问卷。
4. 所有填写请求的 `respondentId` 必须由会话确定，不能通过请求 JSON 伪造。
5. 匿名问卷的创建者答卷详情与统计接口，必须在后端过滤身份字段；可以显示答卷内容，但不能显示 `respondentId`、用户名或可通过其推断账号的内部键。历史匿名答卷也要遵守提交当时的匿名约定。
6. 防止 IDOR：不能仅因知道数据库 ID 或 publicId 就获得管理权限；不要向未授权用户返回敏感记录细节。
7. 前端渲染文本必须转义以避免 XSS；验证长度、避免 Mongo 查询操作符注入（不能将用户提供的任意字典直接当作 Mongo filter）；统一异常处理，禁止泄露堆栈/密码哈希。

## B2. 完整 API（可合理微调路径，但必须写明最终规范）

### 认证

- `POST /api/auth/register`：用户名密码注册；重复用户名返回冲突；
- `POST /api/auth/login`：验证并建立会话；
- `POST /api/auth/logout`：清理会话；
- `GET /api/me`：查看自己的非敏感资料。

### 创建者管理问卷

- `POST /api/surveys`：创建标题、说明、`anonymous`、`submissionPolicy` 初始问卷和 V1 草稿；
- `GET /api/surveys`：仅列当前账号创建的问卷，按时间倒序；
- `GET /api/surveys/{surveyId}`：本人问卷基础信息及状态；
- `PATCH /api/surveys/{surveyId}`：更新允许编辑的标题/说明/截止时间等元信息，校验所有权；
- `GET /api/surveys/{surveyId}/versions`：版本列表、草稿与发布指针；
- `GET /api/surveys/{surveyId}/draft`：取得草稿（含 `revision`）；
- `PUT /api/surveys/{surveyId}/draft`：整体或结构化更新当前草稿题目、选项、校验、跳转；含 `expectedRevision`，冲突返回 409；
- `POST /api/surveys/{surveyId}/draft-from-published`：在没有草稿时复制已发布版本创建下一草稿；
- `POST /api/surveys/{surveyId}/publish`：静态校验通过后发布指定草稿；更新指针并返回公开 URL；
- `POST /api/surveys/{surveyId}/close`：关闭问卷；若实现重新开放，需作为显式状态转移并覆盖测试。

### 填写者公开链接（需要登录才可获取有效填写内容）

- `GET /api/public/surveys/{publicId}`：读取当前 `publishedVersion` 问卷的公共内容（题目、选项、校验/跳转所需的安全配置），不泄露创建者管理字段/历史答卷/用户身份；
- `POST /api/public/surveys/{publicId}/submissions`：请求包含 `surveyVersion`、`requestId`、`answers: [{questionId,value}]`；后端认证、状态截止/版本检查、校验有效路径、严格控制重复题目 ID、幂等写入 Mongo，返回新提交 ID 或幂等重试的同一 ID；
- `GET /api/me/submissions?surveyId=...`（建议）：填写者只查看自己的提交列表/摘要，不可查询他人账号。

### 创建者统计与答卷

- `GET /api/surveys/{surveyId}/submissions?version=1&mode=historical_raw`：仅创建者，返回按匿名/非匿名策略脱敏的答卷列表，分页；
- `GET /api/surveys/{surveyId}/statistics?version=1&mode=current_effective`：该版本题目逐项统计和提交数，必须声明口径；
- `GET /api/surveys/{surveyId}/questions/{questionId}/statistics?version=1&mode=current_effective`：单题统计；
- `mode` 允许 `current_effective` 或 `historical_raw`，`version` 未指定时明确按已发布版本处理；非法/不存在版本返回规范错误。

推荐统一错误结构：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请选择至少两项",
    "details": {
      "questionId": "q2",
      "field": "answers.q2"
    }
  }
}
```

明确 `400/401/403/404/409/422` 的使用边界。具体错误文本可调整，但应保证稳定的错误码供前端使用。提供 FastAPI OpenAPI 文档以及 `docs/api.md`，给出主要请求/响应样例、身份要求、字段解释、常见错误。

## B3. Web 页面与具体交互（全部 P0）

### 1. 注册与登录

- `/register`、`/login`：有输入框、表单校验、错误提示、跳转；
- 未登录访问填写页时，提示登录，并在登录后返回原公开问卷链接；
- 页面可看到当前登录身份和退出入口。

### 2. 我的问卷（创建者工作台）

- `/dashboard`：只显示当前用户的问卷，至少包含标题、状态、创建时间、截止时间、当前发布版本、分享链接/复制链接、编辑、统计、关闭入口；
- 明确区分 `draft` / `published` / `closed`；不能将“已有新草稿”误当成“对外已经更新”。

### 3. 创建/编辑问卷

提供可用的表单编辑器（不要求拖拽）：

- 问卷标题、说明、匿名开关、重复填写策略（已有提交后锁定）、截止时间；
- 添加四类题型，修改题目标题与必答，增删选择题选项，控制选项/题目顺序；
- 多选 `minSelections,maxSelections`；文本 `minLength,maxLength`；数字 `min,max,integerOnly`；
- 可为单选/多选/数字题添加跳转规则：选择运算符、设置操作数、选择目标题目/结束、设置规则优先级；
- 编辑器显示规则配置错误（目标无效、逆向跳转、重复优先级等），禁止发布非法草稿；
- **预览模式**：用当前草稿进行 UI 演示，但不产生正式 Submission；
- 发布按钮展示服务端静态校验结果，发布成功后显示公开 URL；
- 如果问卷已有发布版，必须先从发布版派生新草稿再编辑，原版不允许直接覆盖；显示草稿/发布的版本差别。

前端可以依据题型动态显示字段，但所有校验与跳转仍须由后端解释器最终复核。避免让用户手工编辑原始 JSON 作为主要交互（调试工具可以有 JSON 视图）。

### 4. 填写页面

- `/survey/{publicId}`：需要登录；读取当前已发布版本；显示问卷标题、说明、题目和必答标识；
- 按一题一屏或清晰的逐题步骤交互；上一题返回修改时，根据新答案**重新计算路径**，不再有效的答案从草稿中删除；
- 单选 radio、多选 checkbox、文本 textarea、数字 input；依据规则跳转、即时显示合法范围与错误；
- 提交时显示确认/成功反馈；一次逻辑提交使用同一 `requestId` 重试，不允许点击两次意外生成两次答卷；用户主动新一轮填写才生成新 requestId；
- 后端 `SURVEY_VERSION_CHANGED` 时，友好提示“问卷已更新，需要刷新重填”，不能悄悄转版；
- 对关闭、过期问卷显示可理解的禁止提交提示。

### 5. 统计界面

- `/surveys/{surveyId}/statistics`：仅所有者可访问；选择查看版本和统计口径；
- 单选：每选项被选人数、当前题实际回答总数；
- 多选：每选项被选择次数，支持一人多项，不能将选项计数之和误认为答题人数；
- 文本：逐条查看非空回答，分页/限制长度；
- 数字：实际回答人数和均值；无有效数字回答返回 `null` 或明确“暂无数据”，绝不除零；
- 支持“全部题目统计”和“单题统计”；为匿名提交记录隐藏账号身份；
- 明确区分：原始提交数、按 `latest_only` 去重后的有效提交数、每道题的实际回答数；跳题造成分母不同属正常现象。

## B4. API 与数据库一致性要求

1. 创建者操作都先检查 ownership；`publicId` 只提供填写入口，不提供管理权限。
2. 上传的 `surveyVersion` 不是当前 `publishedVersion` 时返回 409，避免新旧题目配置错配。
3. 发布版本不可变；如果新草稿与公开版并存，填写者只看到公开版。
4. 截止时间统一使用 UTC 存储和服务器判定，前端按本地时区展示。避免使用浏览器时间作为权威。
5. 提交去重依据 Mongo 唯一索引，而不是仅前端禁用按钮；原子处理重复 `requestId`。
6. `latest_only` 的有效答卷选择跨同一 survey 的全部版本完成，然后再按需要的 version 过滤；历史原始统计按 version 独立查询。
7. 不能仅过滤 `respondentId` 字段名：应采用明确的对外响应 DTO，从源头控制匿名问卷能返回哪些字段。
8. 任何已发布版本的匿名标志由历史版本/提交快照决定，不根据当前最新版本反向解除匿名。
9. 错误响应、URL 和数据字段应在代码、前端与 `docs/api.md` 保持一致。

## B5. 推荐目录结构（可适度调整）

```text
project/
  app/
    main.py
    core/             # 配置、鉴权、错误
    db/               # MongoDB 连接、索引、repositories
    models/           # Pydantic 请求/响应/领域类型
    services/         # users, surveys, versions, submissions, statistics
    rules/            # validators, conditions, path_executor
    api/              # auth, surveys, public, statistics
    templates/        # 页面模板
    static/           # CSS / JavaScript
  scripts/
    init_db.py
    seed_demo.py       # 可选，仅开发数据
  tests/
  docs/
  .env.example
  docker-compose.yml   # 如部署环境可用
  pyproject.toml       # 或 requirements.txt
  README.md
```

请使核心规则服务在不运行 Web 服务器时也可直接单元测试；不要将业务逻辑全塞进 `main.py`。

## B6. 手动演示验收（必须在真实服务上走通）

1. 创建账号 A、B；A 登录。
2. A 创建问卷，含四类题及多选/数字跳转规则，设置匿名及 `latest_only`，发布 V1。
3. 从 Dashboard 获得 `/survey/<publicId>`；B 登录，通过链接按 Q1=no → Q3 的路径完成提交；回到新一轮填写改为 Q1=yes → Q2 另一条路径再次提交。
4. A 在统计页看到两个历史提交，但 `current_effective` 下 B 只计入最新提交；A 看不到 B 的登录身份（匿名问卷）。
5. A 创建 V2 草稿，修改题目、发布；已保存的 V1 答卷继续能按 V1 解释；在 V2 发布前打开 V1 的填写页尝试提交时，得到 409 版本变化错误。
6. A 关闭问卷后，B 不能再提交，但旧答卷仍可查看统计。
7. 对重复点击提交、非法选项 ID、跳题绕过必答、无权查看他人问卷等情形返回正确错误。

### Phase B 交付文件与报告

- 可运行的 FastAPI 服务、前端文件、API 定义、配置样例；
- `README.md`：安装依赖、Mongo 启动、初始化、启动后端、测试、演示账号的生成方式（不提供固定真实密码）；
- `docs/api.md`：请求响应、错误语义、权限、版本行为；
- 演示每一步的实际运行记录（文字、命令、必要截图，不能虚构）；
- 明确尚未完成之处及原因，全部 P0 项通过才能视为本阶段完成。


---

# Phase C Prompt：测试、回归、文档、AI 使用过程与第一阶段交付

> 前提：Phase A（数据库与规则引擎）和 Phase B（后端 API、Web）已经有可运行代码。本阶段不仅“写测试”，还要**真实执行测试并修复失败**，保存可复核的输入/输出/结果。

## C0. 课程要求及质量目标

课程作业至少要求：创建问卷、添加题目、跳转逻辑、校验、提交问卷、统计的测试；且每项要有测试步骤、输入、输出、结果。提交可运行代码、MongoDB schema/配置、系统说明、数据库设计、API 文档、关键逻辑、AI 使用日志和完整项目报告。项目评分：MongoDB 35、后端 25、测试 10、文档 15、AI 15；第二阶段还要在第一阶段基础上修改，禁止推倒重做。

目标：创建**需求-接口-测试-证据**的可追踪矩阵，所有关键业务特性都有至少一项真实执行的测试证据；让第二阶段新增需求时可以重跑回归测试。

## C1. 测试环境与命令

- 测试环境要隔离：`survey_test` 或独立 MongoDB 实例；不能清空用户开发/正式数据库。
- MongoDB 专有行为（唯一索引、BSON、聚合、读写竞态、集合校验）必须使用**真实 MongoDB** 测试，不得只用 mongomock 并声称数据库集成通过。
- 规则函数可独立执行纯单元测试；API 测试使用 FastAPI TestClient / httpx；浏览器端交互可选择 Playwright 或详尽的手工步骤，视环境而定。
- 推荐命令需按实际项目实现，示例：`pytest -q`、`pytest tests/unit -q`、`pytest tests/integration -q`、`python scripts/init_db.py`。如无法启动 Mongo/Docker，记录阻塞、实际尝试命令和未验证项，不能凭空写“全部通过”。
- 测试时间、Git commit（若可用）、Python/Mongo 版本、实际命令与结果需要记录。

## C2. 单元测试：每个细节可验证

### 问卷配置与题型校验

1. 单选：合法选项成功、未知选项失败、字符串外类型失败、必答未回答失败。
2. 多选：0 项非必答允许，必答无答案失败；合法数量成功；少于 min / 多于 max 失败；重复选项 ID 失败；包含未知选项失败；`minSelections > maxSelections` 发布失败。
3. 文本：空白字符串、前后空白修剪、最大/最小长度边界、Unicode 长度、非字符串输入。
4. 数字：下限、上限、边界等于、负值、分数和 `integerOnly`；拒绝数字字符串、`bool`、NaN/Infinity。
5. 规则：`eq` / `contains_any` / `contains_all` / `gt,gte,lt,lte` 的正例和反例；同条件命中多条优先级选择；无命中顺序前进；`target=end` 提前结束；非法运算符类型或 operand、重复优先级、不存在目标、自跳/回跳发布失败。
6. 有效路径：跳过的必答题不要求回答；路径上的必答题缺失失败；额外提供被跳过的题目答案失败；可选题无回答时不触发规则；最后一题自动结束。
7. 已发布 `sealed` 版本不能被编辑；草稿冲突检测返回稳定错误码。

### 固定问卷 fixture（必须一致）

- Q1：单选 yes/no，必答；no 跳 Q3，否则 Q2。
- Q2：多选 python/java/cpp，必答，1..3；同时包含 python & java → Q4（priority=10），包含 cpp → END（priority=20），未命中 → Q3。
- Q3：数字 0..80，必答；>=10 → Q4，否则 END。
- Q4：文本 0..500，可选；默认 END。

| ID | 输入/情况 | 预期 |
|---|---|---|
| R01 | Q1=no，Q3=8 | Q1→Q3→END，成功 |
| R02 | Q1=no，Q3=12，Q4 未填写 | Q1→Q3→Q4→END，成功（Q4 可选） |
| R03 | Q1=yes，Q2=[python,java] | Q1→Q2→Q4→END，成功 |
| R04 | Q1=yes，Q2=[cpp] | Q1→Q2→END，成功 |
| R05 | Q1=yes，Q2=[python,java,cpp] | 同时命中两规则，按 priority=10 去 Q4 |
| R06 | Q1=no，Q3 缺失 | 拒绝（有效路径必答缺失） |
| R07 | Q1=yes，Q2=[python,python] | 拒绝（重复选项） |
| R08 | Q1=yes，Q2=[cpp]，额外携带 Q3 | 拒绝（无效路径答案） |
| R09 | Q1=no，Q3=-1 | 拒绝（小于下限） |
| R10 | Q1=no，Q3="12" | 拒绝（类型错误） |
| R11 | Q2 规则目标 Q99 不存在 | 拒绝发布 |
| R12 | Q3 规则跳到 Q1 | 拒绝发布 |
| R13 | Q2 两条规则同 priority | 拒绝发布 |
| R14 | 单选使用 contains_all | 拒绝发布 |
| R15 | 多选 minSelections > maxSelections | 拒绝发布 |

## C3. API + 真实 MongoDB 集成测试

### 用户与权限

- 注册成功、重复 username、错误密码、未登录、会话过期、登出；
- A 的管理列表不含 B 创建的问卷；B 即使拿到 A 的 surveyId 也不能编辑、发布、关闭、查看统计；
- 已登录 B 可以通过 A 的公开链接填写（这是正常权限路径）；
- 认证中的用户 ID 不能被表单中的假 `respondentId` 覆盖；
- 至少测试 401/403/404/409/422 的典型错误码与响应体。

### 版本与发布

- 创建问卷自动生成 V1 草稿；发布前执行全量静态规则校验；
- 发布后 `publishedVersion` 解析到正确 sealed 文档；
- 发布后继续编辑必须基于新草稿 V2，V1 数据内容和既有答案不变化；
- 存在 V2 草稿时公开链接仍呈现 V1；V2 发布后公开链接转 V2；
- V1 填写请求在 V2 发布后提交返回 409，不把答案写到 V2；
- 版本号同一问卷不重复，并发创建草稿、草稿 revision 冲突、发布指针更新至少各有边界测试；
- 发布过程若出现跨集合中断应能检测并重试/恢复，不得把未成为权威版本的记录公开。

### 答卷、幂等、匿名、重复填写

- 每次新的成功提交追加记录，无覆盖；同一逻辑请求使用相同 requestId 重试仅产生一个文档；相同 requestId + 不同答案拒绝；
- `latest_only`：U1 在同一 survey 下先提交 V1、后提交 V2，则全问卷的当前有效统计只含 U1 的 V2 提交；V1 的 `historical_raw` 仍保留旧提交，V1 的 `current_effective` 不应错误计入 U1 的旧记录；
- `multiple`：同用户多份提交均被统计；`submissionPolicy` 首次提交后不可修改；
- 匿名创建者通过提交列表、单题/整份统计均无法获得 `respondentId`、username；系统内部仍可对同一账号去重；更改问卷版本匿名设置不得泄露历史匿名身份；
- 关闭和过期问卷拒绝提交；同一问卷多用户同时成功提交互不覆盖；重复/并发请求不会让一次逻辑提交重复计数。

### 统计正确性

- 单选：每项人数/次数（依统计口径）与实际答题总数；
- 多选：每个选项计数，一人选多项时选项之和可能大于答题人数；
- 文本：非空回答逐条展示，支持分页；
- 数字：仅有效数字计算平均，边界与空结果正确；
- 跳过 Q2 的答卷不计入 Q2 的“回答人数”；
- 单题统计与整问卷对应题统计完全一致；
- 跨版本相同题号不同含义时不直接混合统计；
- 原始提交数、当前有效数、单题实际回答数语义明确。

### MongoDB 基础验证

- username/publicId/(surveyId,version)/(surveyId,respondentId,requestId) 唯一索引在真实 Mongo 生效；
- 集合 JSON Schema 基本校验能够拒绝至少一个错误结构；
- 日期以 BSON UTC 时间、Mongo 引用 ID 类型一致，聚合排序与筛选得到真实预期；
- 数据库初始化可重复执行、不会误删真实数据。

## C4. Web 浏览器端验收

至少完成可复现手工步骤或真实浏览器自动化：

1. 注册登录 → 创建问卷 → 添加四类型题目 → 编辑选项和校验 → 可视化设置跳转 → 预览 → 发布 → 复制问卷链接。
2. 第二账号登录，在填写页面根据回答变化正确跳转，填写非法内容看到明确信息，完成提交看到成功反馈。
3. 回到前题改变选项，先前分支的答案不会误提交；点击提交重试不会复制同一份逻辑答卷。
4. 创建者统计页面有版本、口径选择，且匿名问卷看不到提交者身份。
5. 创建新草稿并发布 V2，V1 历史仍可统计；关闭/过期状态提示正确。
6. 在小尺寸屏幕上基本可用，表单有标签、按钮可键盘访问、错误信息可辨识。

若没有浏览器自动化依赖或浏览器环境，提供真实的手工操作证据与待补自动化范围，不得伪造截图。

## C5. 文档清单（全部必须与最终代码一致）

- `README.md`：系统目标、主要功能、技术栈、依赖、配置、安装与启动、演示流程、如何执行测试、当前限制；
- `docs/system-design.md`：架构/模块职责、端到端数据流、身份与匿名语义、访问控制；
- `docs/database-design.md`：四集合 BSON Schema、字段说明、示例文档、索引、集合关系图、嵌入 vs 引用取舍、Schema 版本、问卷发布指针、历史答卷的正确解释；
- `docs/rule-specification.md`：四种题型、校验规则、运算符、优先级、目标、默认路径、静态/动态校验、错误条件；
- `docs/api.md`：全部关键 API 的路径/方法、请求响应、状态码、认证、版本语义；
- `docs/test-cases.md`：编号、目标、前提、步骤、输入、预期输出、实际输出、PASS/FAIL/SKIP、证据路径；
- `docs/test-report.md`：真实执行环境、执行命令、时间、通过/失败/跳过统计、发现的问题与修复、未验证范围；
- `docs/requirements-traceability.md`：课程需求 → 集合/字段 → 业务方法 → API/页面 → 测试 ID 的追踪表；
- `docs/ai-usage-log.md`：真实使用的工具、实际 Prompt（或原文文件引用）、产生的代码/建议、发现的问题、修改与验证。不捏造人工操作；
- `docs/project-report.md`：项目目标、系统设计、MongoDB 设计、跳转/校验、AI 使用过程、测试结果、遇到问题及解决方案；明确为什么如此设计及第二阶段扩展思路。

可使用 Mermaid 图表示集合关系或逻辑流程，但要与代码一致。凡无法确证的结果标注“未验证”。不要将本任务中的预期测试输出冒充实际执行结果。

## C6. 完成判定与最终汇报格式

只有在以下条件均达成时可宣称第一阶段完成：

- 核心注册/登录、创建/管理、发布链接、四类题、设置约束、数据驱动跳转、多人/重复/匿名提交、单题和整问卷统计均可运行；
- 至少课程规定六类测试有可复现步骤和真实结果，关键边界测试通过；
- 全部业务数据在 MongoDB，索引和权限/匿名有证据；
- 已发布版本不可变、历史答卷可按其版本解释；
- `README.md` 可让新环境重新启动系统；文档和实际代码一致；AI 使用过程真实。

Coding Agent 最终回复请按如下结构给出：

1. **已实现功能**（按六大模块列）；
2. **关键文件/目录**（可直接定位）；
3. **运行命令与本地访问地址**（仅写实际已验证的地址）；
4. **测试结果**（具体命令、PASS/FAIL/SKIP 数与原因）；
5. **设计决策与非目标**（含关系数据库对比、版本语义、隐私限制）；
6. **尚未完成/环境限制**（不可隐瞒）；
7. **第二阶段扩展入口**（新增题型、运算符、统计与版本兼容分别在哪里改）。

最后检查并清理意外生成的密钥/调试数据，提交完整文档和可运行代码；不得自动推送外部仓库，也不得清空非测试数据库。
