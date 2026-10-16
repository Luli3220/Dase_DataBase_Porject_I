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
