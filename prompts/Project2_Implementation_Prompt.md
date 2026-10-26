# Project 2｜增量演进实施总控 Prompt

> **文件组织原则（必须遵守）：代码和持续维护的技术文档在原路径直接增量更新；Project 1 既有测试与阶段性证据保留；Project 2 新测试、测试记录、AI 使用日志单独归档；Project 2 完整报告独立新建。通过 Git 基线保留 Project 1 技术文档的历史版本。**

## 0. 工作方式与不可突破的约束

仓库：`https://github.com/Luli3220/Dase_DataBase_Porject_I`，默认分支 `main`。Project 2 需求以用户提供的《大作业一：需求变更.pdf》为准；Project 1 约束以 `requirements/project1.pdf`、`docs/`、现有测试和实际实现为准。要求完成八项需求：常用题目复用、跨用户共享、旧问卷内容不受修改影响、修改历史与恢复、多版本并存、反向查询使用问卷、题库管理、跨问卷单题统计。

你的角色是负责**需求追踪、MongoDB 建模、兼容性改造、FastAPI 后端、前端、测试及文档**的高级工程师。**目标是可运行、可复核、可提交的第二阶段成果，而非概念演示。** 请自主执行所有可完成的步骤；遇到非决定性的细节优先遵循本 Prompt 中的明确约定。发现代码与本文假设不一致时，以实际代码为事实依据，记录差异并做最小必要调整，不要凭空声称完成。

硬性约束：

1. **严禁推倒重做**：在原有代码上增量开发，保留原四集合 `users`、`surveys`、`survey_versions`、`submissions` 的职责；保留注册登录、草稿编辑/预览、问卷发布、条件跳转、答案校验、匿名机制、重复填写、幂等提交、历史版本及原统计 API 的行为与兼容性。
2. **不能删除或重写已有历史数据**，尤其不得修改已冻结的问卷版本及旧答卷。老问卷中无题库来源标识的题目仍必须正常工作。不能根据题目标题相同就自动合并身份。
3. 使用 MongoDB、FastAPI、PyMongo、Pydantic 和现有前端技术栈；不引入关系数据库、现成问卷框架，避免无必要的大型依赖和前端重构。
4. 权限在后端强制执行，客户端传入的所有者/身份字段不可被信任；延续登录、CSRF、Origin 检查、返回字段白名单、请求大小限制、事务和异常格式。
5. 保存已有接口请求/响应的兼容性。新字段尽量可选、采用增量迁移；确需改变公开接口时给出明确原因、兼容层及测试。
6. 不得只写文档或只生成代码而不验证。**先运行/记录基线，逐阶段实施并测试，最终执行全套测试**。若环境不可用，明确说明哪些命令未运行以及阻碍，不得虚构通过数或测试截图。
7. 不要把一切写成一个巨型服务。新增职责通过独立模块实现，最大限度复用已有 `rules/engine.py`、`services/surveys.py`、`services/submissions.py`、`services/statistics.py` 及 `db/mongo.py`。

### 0.1 代码、技术文档、测试记录与报告如何组织（强制规则）

原则：**同一个软件系统持续演进，当前技术文档随代码更新；但两个阶段的测试与 AI 过程可独立核验，最终报告分别提交。** 不能为了“区分 Project 2”而另建第二套 `source/` 或第二份互相矛盾的当前 API/数据库说明。

1. **业务代码——在原文件上直接改。** 在新 Git 分支中修改现有 `source/app/` 的相关文件，例如 `models/domain.py`、`models/documents.py`、`db/mongo.py`、`api/routes.py`、`services/surveys.py`、`services/statistics.py`、`static/app.js`；确有必要时，在同一 `source/app/` 下新增 `services/questions.py`、`services/question_banks.py`、`services/question_statistics.py` 等模块。必要的迁移/验证脚本加入原 `source/scripts/`。**禁止**复制一套 `source_project2/`、`app_project2/` 或另写一个替代系统。
2. **当前技术文档——直接维护原路径。** `docs/database-design.md`、`docs/system-design.md`、`docs/api.md`、`docs/openapi.json`（实际程序重新导出）、`docs/rule-specification.md`（如规则确有变动）、根目录 `README.md`、`source/README.md` 和 `docs/README.md` 应在原文件中增量更新，使之准确描述 **Project 2 完成后的整个系统（包含旧功能与新增功能）**。保留仍正确的旧内容，增加新集合/字段、接口、运行方法、兼容策略和必要的设计说明；**不要新建与这些文件职责重叠的 `docs/project2/api.md`、`docs/project2/openapi.json`、`docs/project2/system-design.md` 来维护另一套“当前规范”**。现行规范只能有一个权威版本。
3. **历史可追溯——用 Git 保存第一阶段技术文档的原貌。** 开发前记录 Project 1 最终 Commit，建议加只读基线 Tag；原技术文档可以随第二阶段更新，但第一阶段内容必须能通过 Git 基线完整恢复和比较。更新原文档时不要删除仍成立的设计原理，并在 Project 2 变更记录中注明关键差异。这是“维护当前技术文档”，不是篡改阶段性测试事实。
4. **原测试代码——保留并继续回归。** `source/tests/` 中的 Project 1 测试不删除、不跳过、不弱化断言；必要的最小兼容修改需说明原因并保留 diff。Project 2 新增测试优先放 `source/tests/project2/`（可细分 `unit/`、`integration/`、`web/`）；测试配置/fixtures 可按实际需要在原路径共同维护，保证一条命令能执行旧测试和新测试。
5. **阶段性报告、测试证据和 AI 日志——严格分开。** Project 1 已有的 `docs/test-cases.md`、`docs/test-report.md`、`docs/ai-usage-log.md`、`docs/evidence/` 及第一阶段最终报告视为历史交付，**不要覆盖、清空或把第二阶段结果混写进去**。Project 2 的 `test-cases.md`、`test-report.md`、`ai-usage-log.md` 和 `evidence/` 单独建立在 `docs/project2/` 下。原有 113 passed 是第一阶段的历史证据；Project 2 的总通过数必须来自本阶段真实运行。
6. **新增的演进过程文档——单独归档。** `docs/project2/` 还需保存 `requirements-traceability.md`、`database-evolution.md`、`migration.md`、`change-log.md` 等侧重 **Project 1 → Project 2 修改过程** 的材料。这些文档与根 `docs/` 的当前技术说明职责不同：前者解释“如何变、为什么变”，后者解释“当前系统怎样工作”。
7. **Project 2 最终报告——独立新建。** 创建 `docs/project2/final-report.md`；需要 LaTeX/PDF 时另建 `docs/project2/report/`，不得直接改写 Project 1 的报告文件。新的报告是 **完整的第二阶段项目完成报告**，包含原设计摘要、新需求、改动、兼容性、测试与 AI 使用过程，不是简单追加章节。
8. **文档与代码同步交付。** 修改接口、数据模型或规则时，务必在同一阶段更新原有的当前技术文档；生成 OpenAPI 后检验与实际 FastAPI 路由一致。阶段性证据与报告则写到 `docs/project2/`。不得让代码、现行 API 文档和 OpenAPI 描述相互矛盾。

推荐的最终组织结构（保留原仓库其他全部文件）：

```text
repo/
├── source/
│   ├── app/                            # 原代码原地增量更新 + 必要新模块
│   ├── tests/
│   │   ├── unit/                       # Project 1 原测试继续保留
│   │   ├── integration/                # Project 1 原测试继续保留
│   │   ├── web/                        # Project 1 原测试继续保留
│   │   └── project2/                   # Project 2 的新增测试
│   └── scripts/                        # 原脚本维护 + 新增迁移脚本
├── docs/
│   ├── database-design.md              # 当前完整数据库设计：原文件更新
│   ├── system-design.md                # 当前完整系统架构：原文件更新
│   ├── api.md                          # 当前完整 API：原文件更新
│   ├── openapi.json                    # 当前程序导出：原文件更新
│   ├── rule-specification.md           # 当前规则规范：按需更新
│   ├── test-cases.md                   # Project 1 测试用例：历史保留
│   ├── test-report.md                  # Project 1 测试结果：历史保留
│   ├── ai-usage-log.md                 # Project 1 AI 使用日志：历史保留
│   ├── evidence/                       # Project 1 原始测试证据：历史保留
│   └── project2/
│       ├── README.md                   # 第二阶段材料索引
│       ├── requirements-traceability.md
│       ├── database-evolution.md       # 设计变化与方案比较
│       ├── migration.md
│       ├── change-log.md
│       ├── test-cases.md               # Project 2 新增用例及回归清单
│       ├── test-report.md              # Project 2 独立测试结果
│       ├── ai-usage-log.md             # Project 2 独立 AI 日志
│       ├── evidence/                   # Project 2 控制台/JUnit/HTTP/截图
│       ├── final-report.md             # 第二阶段独立完整报告
│       └── report/                     # 可选：独立 LaTeX/PDF
├── prompts/
│   ├── ...                              # Project 1 Prompt 原样保留
│   └── project2/
│       └── implementation.md           # 第二阶段实施 Prompt
└── README.md                            # 当前项目入口：原文件更新
```

**禁止的反例**：另建一整套 Project 2 业务代码；同时维护两份内容不一致的“当前 API 文档”；把新测试数据覆盖第一阶段 113 passed 记录；将两阶段 AI 日志混成一份；修改 Project 1 最终报告充当 Project 2 报告；为让测试通过而跳过旧测试。**注意：更新 `docs/api.md` / `docs/openapi.json` 是允许且要求的，它们是当前技术规范；它们的 Project 1 原始版本由 Git 基线保留。**

## 1. 开始前先审计并冻结 Project 1 基线

先阅读并理解以下文件的实际内容：

- `source/app/models/domain.py`、`source/app/models/documents.py`：严格请求模型及 BSON 文档模型；
- `source/app/db/mongo.py`：`$jsonSchema`、集合初始化与索引，初始化不得清空数据；
- `source/app/rules/engine.py`：题目配置、条件跳转与答案路径验证；
- `source/app/services/surveys.py`：草稿 `revision`、发布冻结及版本指针；
- `source/app/services/submissions.py`：答卷保存、`requestId` 幂等、`latest_only` / `multiple` 策略；
- `source/app/services/statistics.py`：现有逐问卷 MongoDB 聚合；
- `source/app/api/routes.py`、`source/app/static/app.js`：现有接口与交互；
- `source/tests/`、`docs/api.md`、`docs/database-design.md`、`docs/test-report.md` 和已有 AI 日志。

记录当前基线 Git Commit、分支、原文件结构及现有测试结果。为 Project 2 创建独立开发分支（如 `project2/question-library`），建议为 Project 1 最终 Commit 加基线 Tag，以便复原原有技术文档和进行 Git diff；**实际修改在同一仓库的原 `source/app/` 文件上进行，但不要直接在第一阶段基线分支上混入未审查变更**。随着代码演进，同步更新原 `docs/` 下的当前技术说明；不要重写第一阶段测试/AI 历史或删除已有测试记录。已提交报告中 **113 passed** 仅属于 Project 1 的历史证据，不是 Project 2 的实测结果。先执行能运行的基线测试，将命令、环境、真实输出和 Commit 记录在 `docs/project2/test-report.md` 或 `docs/project2/evidence/`，不得覆盖第一阶段测试报告。

在实施之前，先在 `docs/project2/requirements-traceability.md` 产出 `需求 → 数据结构 → 后端接口 → UI → 测试用例` 追踪矩阵，并在 `docs/project2/change-log.md` 维护新增/修改文件清单。随后继续开发，不要停在方案讨论。

## 2. 数据模型：原四集合 + 三个新集合

采用**可复用题目的稳定身份 + 不可变题目版本 + 问卷内固定版本快照**的设计，默认新增 `question_definitions`、`question_versions`、`question_banks` 三个 MongoDB 集合。除非经过明确论证，不额外拆出选项、规则、答案等集合。以下字段是建议的业务契约，字段的 BSON/Pydantic 类型及必要约束须由实现统一确定并写入文档。

### 2.1 `question_definitions`：共享题目的全局身份

建议包含 `_id:ObjectId`、`ownerId:ObjectId`、`currentVersion:int`、`visibility`（默认私有）、`sharedWith:[ObjectId]`、`forkedFrom`（可选 `{questionId, questionVersion}`）、`createdAt`、`updatedAt`、`schemaVersion`。可增加 `archivedAt` / `revision`；不得把持续增长的所有历史版本嵌入此文档。

规定：同一全局 `questionId` 标识同一条题目演进族；版本内容由独立集合保存。拥有者能够管理共享范围及创建新版本；被分享者默认只有读取/使用权，不能改写原题。如果被分享者希望独立维护，应创建 **fork：新的全局 `questionId`**，并记录来源。撤销分享只阻止后续未授权访问/选题，不影响已发布问卷快照。

### 2.2 `question_versions`：不可变的具体内容

建议包含 `_id:ObjectId`、`questionId:ObjectId`、`version:int`、`parentVersion:int|null`、`changeType`（如 `create/update/restore`）、`restoredFromVersion:int|null`、`content:{type,title,required,options,validation}`、`createdBy:ObjectId`、`createdAt`、`schemaVersion`。版本号在同一 `questionId` 下单调递增并保持唯一，`(questionId,version)` 建复合唯一索引。`parentVersion` 用于准确描述从哪个旧版本派生，不能假定永远只从最新版本编辑。fork 的跨题来源存储在新定义的 `forkedFrom`，与同题历史关系区分。

题目版本**不保存问卷跳转目标 `routingRules`**：现有规则的 target 使用问卷内局部题目 ID，不能跨问卷安全复用。导入问卷时由问卷实例自己管理路由规则。`content` 要完整支持 Project 1 的单选、多选、文本、数字题及其选项/校验约束，复用现有规则校验逻辑。

已创建的题目版本不可原地编辑或删除；修改生成新版本。**恢复旧版本**采用追加一个新版本（内容复制指定旧版并记录 `restoredFromVersion`），不回写旧版，也不破坏已有引用。创建版本与推进 `currentVersion` 的操作必须具备并发控制；不要用 `count()+1` 分配版本。使用事务 + CAS/等效唯一性约束处理并发，失败显式返回冲突。

### 2.3 `question_banks`：题库和成员

建议包含 `_id:ObjectId`、`ownerId:ObjectId`、`name`、`description`、`items:[{questionId,pinnedVersion?}]`、`createdAt`、`updatedAt`、`schemaVersion`。控制成员数组上限与文档体积；同一题可加入多个题库，但同一题库不得重复添加同一全局题目。银行成员引用已有题目，不复制内容。

`pinnedVersion` 若指定，则题库选题默认展示该版本；未指定则在**选题时**解析 `currentVersion`，最终导入仍必须固定精确版本，绝不能将“总是跟随最新”写入已发布问卷。题库所有者只能管理自己的题库，添加他人题目时检查当前共享权限。删除成员不得删除题目或历史版本。

### 2.4 对原 `survey_versions.questions[]` 做最小扩展

保留现有 `id/type/title/required/options/validation/routingRules` 结构；增加可选：

```json
"source": {
  "questionId": "<全局题目 ObjectId，BSON 中使用 ObjectId>",
  "questionVersion": 2
}
```

这里 `questions[].id` 是**问卷局部实例 ID**，不同于全局 `source.questionId`。导入时为实例生成新的唯一局部 ID，并将题目版本的完整 `content` 物化到当前草稿；`routingRules` 默认空数组，由当前问卷自行配置。发布仍依赖原有不可变 `survey_versions` 快照；公开填写、提交和原有单问卷统计**不得因题库更新而实时读取/修改题目内容**。

对于带 `source` 的题目，后端必须防止局部编辑无声改变来源含义。修改 `title/type/options/validation/required` 等核心内容时，应明确执行“解除题库关联并作为本地题目编辑”或“创建新题目版本/独立 fork 后再导入”，**不能留下指向旧版本的虚假 source**；问卷自身的 `routingRules` 可独立编辑。建议一个问卷版本中同一全局题目最多出现一个实例，避免跨题统计重复计算，且必须保证局部题目 ID 全局唯一。

旧题目没有 `source` 必须完全合法。因为当前 Pydantic 模型启用 `extra='forbid'`，`$jsonSchema` 也检验问题结构，必须同步升级请求模型、BSON 模型、校验器、序列化、前端保存及数据库 validator，保证保存/读取过程中 `source` 不丢失。**不要为了增加可选字段批量改写旧的 sealed 文档或旧答卷**。若现有 `schemaVersion` 不需提升即可兼容，可继续保留；若确有必要提升，须同时支持旧格式读取并提供显式、可重复执行的迁移。

## 3. 八项需求的业务行为与边界

1. **创建与复用**：可以独立创建题目并保存为 v1；新建/编辑问卷草稿时可以从自己的或被分享的题目中搜索、预览、选择具体版本并导入。导入多个问卷保留相同全局来源 ID，但局部实例 ID 各自独立。
2. **跨用户分享**：按用户授予/撤销读取和复用权限，展示创建者与来源；未被分享的私有题目不可经 API 猜测 ID 读取。共享不授予修改、删除、查看他人答案的权限。
3. **历史稳定性**：一旦问卷版本 `sealed`，其题目内容、来源、规则不可改变；发布后库题创建新版本、撤销共享、归档等不影响旧问卷或其答卷解释。
4. **版本追踪与恢复**：可查询同题所有版本和 `parentVersion` / `restoredFromVersion`；支持从任意旧版派生新版本；恢复是追加新版本而非覆盖。
5. **多版本共存**：不同问卷可固定引用同题不同版本；题库最新版本变化不自动更新任何已导入问卷。草稿可通过显式操作将引用升级为新版本，并处理校验与路由配置。
6. **使用关系查询**：按全局题目及可选精确版本，反向查询使用它的问卷/问卷版本，区分草稿、已发布和历史版本。利用 `survey_versions.questions[].source` 查询，不默认维护无限增长的 `usedBy[]`。跨用户只展示有权限公开的问卷详情；其他私有问卷不能因为题目共享而泄露名称、所有者身份或答卷。
7. **题库管理**：支持创建、列表、查看、修改名称/说明、添加/移除成员、题库内选题和选择版本；允许一个题目属于多个题库；题库成员可指向固定版本或在选题时使用最新版本。
8. **跨问卷统计**：按 `questionId` + **精确 `questionVersion`** 关联不同问卷实例及其答案，支持回答总次数、实际回答数、单选/多选选项频数、数字均值和**年龄等数字题的分布（直方图/分桶）**。默认**不合并不同题目版本**，不因为标题相同而合并。不同版本统计含义可能变化，若未来增加跨版本合并，必须另行证明题型、选项 ID/语义、数值单位及边界兼容，不能靠版本号或标题强行聚合。

## 4. 跨问卷统计：口径、MongoDB 查询和权限（重点）

设计独立的题目级统计服务，复用现有 `SubmissionService.selected` 的语义：

- 先按 `source.questionId + source.questionVersion` 查找合法的**已发布问卷版本**及其中的**局部 `questions[].id`**；精确匹配同一个嵌入数组元素，MongoDB 查询用 `$elemMatch` 或等效方式，避免两个数组元素字段交叉误匹配。
- 再从每份问卷各自的答卷中按原有 `submissionPolicy` 选择有效答卷：`latest_only` 必须先在**整份问卷跨版本**取每位填写者最新提交，再匹配该目标问卷版本；`multiple` 则保留每次有效提交。`historical_raw` 可作为独立查询模式，不与当前有效口径混淆。
- 仅聚合实际回答目标题目的 `answers[]`，不得将被跳过/未答的题目计入回答数；多选题的各选项计数之和可大于回答人数；缺失数值不参与平均值。
- 区分 `answerCount`（题目实际回答次数）、`surveyCount`（参与统计问卷数）和可选的 `distinctRespondentCount`（跨问卷去重用户数）；**不同问卷中的回答默认分别计数**，不要误称“独立人数”。排序、筛选、分页和统计总量要有明确定义。
- 以 MongoDB 聚合管道完成主要筛选、`$unwind`、`$group`、数字分桶等计算，不允许读取全部历史答卷到 Python 内存再拼凑。为问卷/版本/时间/来源查询设计必要索引，并对典型查询执行 `explain` 或以可复现数据量比较优化前后；不要宣称未经测试的性能结论。

**跨用户权限默认保守**：题目共享只意味着允许使用，不意味着其创建者可以查看其他问卷的原始数据。建议将统计查询明确分成 `mine`（我拥有的问卷，默认可汇总）和 `consented_shared`（其他问卷所有者显式授权贡献的匿名聚合）。跨用户模式不得返回 `respondentId`、用户名、原始文本答案或完整答卷；小样本可设置合理的抑制阈值并展示统计范围/排除原因。用户撤销数据贡献授权后，新的跨用户统计查询应排除相应问卷，历史答卷本身不变。增加必要的问卷级授权标识及默认值 `false`，兼容旧问卷。不得为了“全问卷统计”绕过权限。报告应明确解释为什么“能看到使用关系”不等于“能查看他人的回答”。

统计接口返回选定题目版本、范围、参与问卷数量、有效回答数、题型相关分布、排除/不兼容原因等。数字分桶范围、分母、边界区间约定要确定，避免重复计数或遗漏边界值；测试空数据、负值/小数/极值和所有版本的过滤。

## 5. API 和前端：在原系统上增加，不改变既有主流程

按现有 `routes.py` 风格新增 REST API；下列是**必须覆盖的能力**，具体参数名可根据代码一致性统一，并在原有 `docs/api.md` 和 `docs/openapi.json` 中增量更新，形成反映 **Project 2 整个系统** 的唯一现行 API 规范；Project 1 对应文件的原貌通过基线 Git Commit/Tag 查看：

- `POST/GET /api/questions`：创建、列出自己和被分享的题目（含分页/搜索）；`GET /api/questions/{id}`：题目基本信息及有权限的版本。
- `GET /api/questions/{id}/versions`、`POST /api/questions/{id}/versions`：历史及从指定版本创建新版本，提交当前版本预期值以支持 CAS。
- `POST /api/questions/{id}/restore`：从指定历史版恢复为全新版本；`POST /api/questions/{id}/fork`：创建新的独立题目身份并保存来源。
- `PATCH /api/questions/{id}/sharing`：题目所有者维护共享用户集合；必须检验目标用户真实存在，且用户不能自行扩大权限。
- `GET /api/questions/{id}/usage`：被哪些授权可见的问卷/版本使用；`GET /api/questions/{id}/statistics?version=...&scope=...`：精确版本的跨问卷统计。
- `POST/GET /api/question-banks`、`GET/PATCH /api/question-banks/{id}`、添加/移除成员和从题库选题的端点。
- `POST /api/surveys/{surveyId}/draft/import-question`：从题库选取精确版本并原子地加入问卷草稿，必须检查用户对问卷与题目的权限、草稿状态、`expectedRevision`、题目数量限制及局部 ID 唯一性。返回新的草稿修订号；不能暗中修改已发布版本。
- 根据需要提供问卷设置共享统计贡献的受保护 API，默认不共享，禁止未经授权的跨用户聚合。

**前端尽量只扩展现有 `app.js`、样式及路由**：增加“我的题目/共享给我的题目”“题目历史/恢复/派生”“题库管理”“从题库添加题目”“题目使用情况”“跨问卷统计”入口；显示具体版本和来源，并在修改关联题的核心内容时明确提示“解除关联 / 创建新版本 / 独立派生”，不能误导用户为“原题就地修改”。保留原四题型编辑、条件跳转编辑、草稿预览和公共填写流程；移动端基本可用。所有动态内容延续安全转义，不把未授权数据注入页面。

## 6. 数据完整性、索引与无损迁移

在 `db/mongo.py` 增加新集合的 MongoDB `$jsonSchema` 与索引。至少包括：`question_definitions(ownerId,updatedAt)`、`question_versions(questionId,version)` 唯一、`question_banks(ownerId,updatedAt)`，以及支持来源反向查询的 `survey_versions.questions.source` 多键索引。请审查复合多键索引的合法性和查询方式，确保同一个 `questions[]` 元素中的来源 ID / 版本对应。根据实际查询量决定是否增加 `sharedWith` 索引，并说明读写成本。

新增/更新必须由服务端校验 ID、用户权限、来源版本存在性、题目内容一致性、版本父子关系、题库成员上限及重复引用。跨文档操作采用 MongoDB 副本集事务或可证明等价的恢复协议，正确处理并发版本创建、导入与发布冲突、共享撤销竞态、题库成员冲突。题目版本不可变不仅要靠前端禁用按钮，还必须在服务层写入路径保护，必要时加数据库约束。

初始化与迁移必须可重复执行、**不 `drop` 数据、不清空集合、不覆盖旧答卷**。旧文档 `source` 缺省时正常读取与保存；旧问卷的本地题可通过显式“保存到题库”生成新全局题目，默认**不倒填已发布历史版本的来源**。如选择额外提供历史来源映射，应采用不修改 sealed 快照的显式、可审核机制，且不得按标题自动推断等价。

在新增的 `docs/project2/migration.md` 提供备份建议、迁移执行/回滚步骤及新旧数据库读写兼容说明；既有测试数据库初始化流程必须继续可用。

## 7. 测试：新需求全覆盖 + Project 1 回归

延续仓库的 `pytest` 单元测试、MongoDB 集成测试、FastAPI HTTP 测试和 Playwright 浏览器测试组织方式；原有测试尽量原样保留，新增用例优先放在 `source/tests/project2/` 下（不同层级可分类）。至少覆盖：

1. 题目创建、合法/非法配置、四题型及原校验器复用；
2. 私有/共享读取与引用，撤销分享、非所有者篡改、不可越权查使用关系/统计；
3. 同一题目被多个问卷复用，局部实例 ID 不同而全局 `source` 相同；
4. 同一题目的 v1/v2/v3，任意历史版派生，版本血缘，fork 新身份，恢复旧版生成新版本；
5. 题库成员添加/移除、多题库引用、指定版本/最新选取、不重复入库；
6. 旧问卷发布快照在题库更新、撤销共享、归档后不变；导入后的核心内容修改不允许“假来源”；
7. 反向查询准确定位问卷/问卷版本，尤其校验 `$elemMatch` 不发生跨数组元素误匹配；
8. 跨问卷选项频数、多选、数字均值与分布，精确版本过滤，不混合不同版本，路径跳过题不计入；
9. `latest_only` 跨问卷版本的“先去重后筛版本”与 `multiple/historical_raw` 的差别，跨问卷多份提交不误报成独立人数；
10. 匿名答卷保护、统计授权范围、跨用户无原始文本/身份泄漏、默认拒绝外部数据聚合；
11. 两个请求并发创建新题目版本、并发导入草稿、失败重试，不发生重复版本和丢失更新；
12. Project 1 老文档无 `source` 的完整 CRUD/发布/提交/统计；旧接口契约与既有安全测试继续通过；
13. 真实浏览器端到端串联“用户 A 创建并分享 → 用户 B 导入 → A 更新到 v2 → 问卷 A 仍为 v1 → 恢复旧版 → 查询使用关系 → 执行跨问卷统计”。

测试必须给出输入、预期输出、实际结果、命令、环境和日志路径；把第二阶段测试记录写入 `docs/project2/test-cases.md`、`docs/project2/test-report.md`，原始证据存入 `docs/project2/evidence/`。新增测试应该含失败用例而不只是成功路径。不能直接复制 Project 1 的 113 passed 作为 Project 2 结果，且不得覆盖第一阶段的测试日志。若依赖 MongoDB 单节点副本集/Chromium，请按仓库实际脚本启动并说明环境限制。

## 8. 文档、AI 使用证据与最终报告：当前文档更新，阶段材料分离（重点）

**文件组织规则必须贯彻整个开发过程。** 业务代码和描述“当前系统状态”的技术文档继续在原位置维护；记录“第二阶段做了什么”的测试证据、AI 日志、设计演进及最终报告独立归档。两类材料通过 Git Commit 和交叉链接关联，不产生两套不一致的当前规范。

### 8.1 原位置维护的当前技术文档（就地更新）

以下文件需要在既有内容上补充 Project 2 变更，使每份文档反映当前运行中的**完整系统**：

- `docs/database-design.md`：在原四集合职责、索引、版本机制基础上，新增三个集合、`questions[].source`、共享权限、不可变题目版本、索引、数据迁移与跨问卷统计设计；必要时更新模型/关系图及 BSON 示例。说明何处继续嵌入、何处使用引用及原因。
- `docs/system-design.md`：补充题目与题库模块、导入/派生/恢复流程、与问卷服务及规则引擎的协作、使用关系和跨问卷统计；保留旧功能路径及前后端架构。
- `docs/api.md`：按原文件组织补全新旧所有接口，保留既有请求/响应和错误码的正确描述；修改处指出兼容性和新增字段。**此文件是整个 Project 2 系统的当前 API 说明**，不另建 `docs/project2/api.md`。
- `docs/openapi.json`：从 Project 2 实际运行的 FastAPI 应用重新导出，并与路由/模型一致；**此文件是当前 OpenAPI 规范**，不另建 `docs/project2/openapi.json`。Project 1 原版通过基线 Commit/Tag 保留。
- `docs/rule-specification.md`：如果复用/导入导致规则边界或校验语义变化则更新，尤其说明题库不保存依赖问卷局部 ID 的 `routingRules`。
- `README.md`、`source/README.md`、`docs/README.md`：在原文件中更新当前功能清单、启动/测试说明、数据库初始化/迁移步骤、演示流程和文档导航，清楚指向 Project 2 独立证据及报告。

**更新原则**：保留仍正确的 Project 1 技术内容，不将增量需求写成“另一套系统”；发现已失效的描述应修正，不要因为它曾是 Stage 1 文档就让当前技术说明过时。每次重大模型或 API 调整同步维护相关原文件。所有第一阶段技术文档原貌可通过 Git 基线追溯，在 `docs/project2/change-log.md` 记录影响与对照。

### 8.2 单独创建的 Project 2 过程与交付材料

所有第二阶段专属的过程记录放 `docs/project2/`：

- `README.md`：第二阶段材料索引，同时链接原位置维护的当前技术文档和 Project 1 基线版本。
- `requirements-traceability.md`：八项变更需求的 `需求 → 数据结构 → 接口 → UI → 测试 → 证据` 矩阵。
- `database-evolution.md`：**重点讲“为什么从四集合变成七集合”**，比较方案、逐项说明字段/索引/引用关系的变化及替代方案，附关键 Git diff/关联图。不要照抄一份完整的 `docs/database-design.md` 造成维护分叉。
- `migration.md`：升级前后检查、备份、Schema/索引演进、旧数据兼容和可重复执行的迁移/回滚说明。
- `change-log.md`：记录 Project 1 基线 Commit、增量修改的原代码/原技术文档、新增模块、原因、接口兼容性、关联测试/Commit。
- `test-cases.md`：Project 2 新增功能测试、边界用例及 Project 1 回归覆盖矩阵，清楚列出步骤、输入、预期、实际结果。
- `test-report.md`：Project 2 的**独立真实测试报告**，记录环境、测试命令、新增测试与旧测试回归、通过/失败/跳过数量、已知限制和证据链接。不可覆盖 `docs/test-report.md` 中第一阶段的 113 passed。
- `ai-usage-log.md`：**只记录 Project 2 的真实 AI 使用过程**，至少包括使用的工具、真实 Prompt/路径、Agent 生成或修改了哪些代码、人工审查与决策、发现问题/修正、相关测试与 Commit。可引用而不改写原 `docs/ai-usage-log.md`；不编造 AI 失误、人工操作或执行证据。
- `evidence/`：第二阶段真实 JUnit、pytest 输出、HTTP 验证、浏览器截图、数据迁移及聚合验证等。不可覆盖 `docs/evidence/` 的第一阶段记录。
- `final-report.md`：第二阶段完整独立的课程报告，详见 8.3；可附 `report/` 下独立 LaTeX/PDF。

**原阶段材料不可变范围**：Project 1 的 `docs/test-cases.md`、`docs/test-report.md`、`docs/ai-usage-log.md`、`docs/evidence/`、第一阶段最终报告和原 Prompt 保持原样。它们属于已经发生的测试和协作过程，与需要持续更新的技术规范不同。原测试代码仍可在原位置继续运行，必要修订须留下 Git diff 和说明。

### 8.3 Project 2 最终报告：完全另起，内容完整

创建 `docs/project2/final-report.md`；需要课程报告的 `.tex` / PDF 时，再另建 `docs/project2/report/`，不得覆盖第一阶段报告的源文件或 PDF。第二阶段报告必须自成一体，而不是在 Project 1 报告最后续写几节。至少包含：

1. 第二阶段项目目标、八项需求变化及不得推倒重做的约束（简述承接关系）；
2. Project 1 原模型和系统关键结构；这些结构在新需求下遇到的实际限制；
3. MongoDB 演进方案比较、七集合模型、版本血缘、稳定引用与不可变快照；
4. 在原有源码基础上的业务模块、接口与前端改动；共享、题库、恢复、导入、发布流程；
5. 旧数据保护、Schema/索引变化、权限与事务一致性、跨问卷统计口径及限制；
6. Project 1 全部原功能的回归和 Project 2 新功能真实测试结果，可复现证据及未覆盖范围；
7. 实际 AI 使用过程、自主设计取舍、问题发现与修复；
8. 总结、当前局限及可能的后续改进。

在报告中明确列出 **“保留的原有代码/模块、直接修改的原有代码/模块、新增的代码模块、新增的阶段性材料”**，并通过 Git 基线 diff 与测试证据证明不是推倒重做。引用当前完整技术说明时链接到原 `docs/` 文件；说明历史状态时引用 Project 1 Git Tag/Commit 或第一阶段原报告。报告不得把第一阶段的 113 passed 误记成第二阶段当前测试结果。

提供与实际实现一致的数据库模型图、版本图和典型 MongoDB 文档示例。证据与结论必须一一对应，不得杜撰执行结果。

## 9. 执行顺序与阶段验收门槛

**阶段 A — 基线审计**：记录并标记 Project 1 的 Git Commit/Tag、现有接口/模型、运行已有测试；建立 `docs/project2/` 和 `source/tests/project2/` 目录；形成需求追踪矩阵、变更记录和初始测试证据；保护原阶段性测试/AI 记录。后续在原路径维护当前技术文档。

**阶段 B — 数据层**：新集合、文档模型、来源字段、索引、数据库验证器、迁移/旧文档兼容；完成 MongoDB 基础集成测试。通过后进入下一阶段。

**阶段 C — 题目与题库后端**：创建、版本、恢复、fork、共享、题库成员、权限及并发控制；完成 API 和安全测试。

**阶段 D — 与问卷集成**：导入固定题目版本、保持快照、草稿 CAS、路由解耦和原问卷接口兼容；完成流程测试。

**阶段 E — 使用关系与跨问卷统计**：实现正确的反向引用、有效提交筛选、聚合分布、授权与性能验证。

**阶段 F — 前端与交付**：在原前端上增量增加必要功能，完成端到端演示及原有全部测试回归；**同步更新原 `docs/database-design.md`、`docs/system-design.md`、`docs/api.md`、`docs/openapi.json` 和各 README**，确保当前技术规范与实现一致；把 Project 2 独立测试、AI 日志、设计演进、迁移、证据和完整新报告归档到 `docs/project2/`；保留第一阶段测试/AI 原始证据。

每阶段自检：模型与 API 是否一致？索引及查询是否对应？旧数据会不会改变含义？是否存在越权和统计误算？是否有可复现的测试？发现问题及时修正，不把错误留给最后阶段。

## 10. 最终回复格式（必须真实、具体）

交付时按以下顺序汇报：

1. **完成情况矩阵**：八条需求逐条标记已完成/部分完成/未完成，附文件与测试证据；
2. **关键架构决策**：七集合字段与关联、固定引用+快照、版本血缘、匿名与跨用户统计范围；
3. **核心代码变更**：逐文件列出“原代码直接修改”与“新增模块”的路径及原因，并列出旧 API 是否受影响；确认不存在复制替代系统；
4. **迁移与兼容**：升级命令、是否实际运行、旧文档/旧答卷保护措施、可回退方式；
5. **测试结果**：实际执行命令、环境、数量、通过/失败/跳过、日志与未测试范围；日志应链接到 `docs/project2/evidence/`，并与 Project 1 历史记录区分；
6. **启动与演示步骤**：从已有 Project 1 数据启动，操作八项功能并查看正确统计；
7. **遗留问题和权衡**：未解决缺陷、可预见风险和后续优化，不夸大结果；
8. **文档与 AI 使用追踪**：确认当前技术说明与 OpenAPI 已在原 `docs/` 文件中更新；说明哪些代码由 Agent 增量修改、哪些设计经过人工确认、哪些问题被发现和修正；列出独立的 `docs/project2/ai-usage-log.md`、`docs/project2/test-report.md` 与 `docs/project2/final-report.md`，确认没有覆盖 Project 1 历史测试/AI 材料。

**完成标准**：不是“新增了题库页面”，而是八项需求在实际持久化数据、真实权限、历史版本、跨问卷统计和旧系统回归中形成闭环；Project 1 核心功能及历史记录没有退化；证据可以复现；最终设计与实施报告能够清楚解释每一项取舍。**代码与现行技术文档在原位置持续更新；Project 1 历史测试/AI 证据保留；Project 2 的测试、AI 日志与变更记录单独归档；Project 2 最终报告独立新建**，缺一不可。
