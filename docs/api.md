# API 说明（2.0.0）

本机地址为 `http://127.0.0.1:8000`，运行时可访问 `/docs`。完整定义见 [openapi.json](openapi.json)，下面按业务流程说明常用字段和行为。

## 请求约定

字段使用 camelCase，ObjectId 以字符串传递，时间使用带时区的 ISO8601，数据库保存 UTC。注册或登录后通过 Cookie 维持会话；修改状态的请求携带 X-CSRF-Token，可从认证响应或 `GET /api/me` 获取。服务端同时检查 Origin、请求字段和资源权限。

以下表格中的“所有者”指对应问卷或题库所有者；“题目可见”指题目所有者或被共享用户。所有写接口均使用 CSRF 校验，登录与注册按认证流程处理。

## 账号

|方法与路径|权限|输入与返回|
|---|---|---|
|POST /api/auth/register|公开|{username,password} → 201 {user:{id,username,createdAt},csrfToken}，同时登录|
|POST /api/auth/login|公开|{username,password} → 200 {user,csrfToken}|
|POST /api/auth/logout|登录|{ok:true}，撤销该账号已有会话|
|GET /api/me|登录|{user,csrfToken}|
|GET /api/me/submissions|登录|surveyId 可选，offset=0，limit=50（1..100）→ 本人提交摘要 {items,total}|

用户名为 3–40 位并归一化，密码为 10–128 字符。会话 Cookie 为 `survey_session`，设置 HttpOnly、SameSite=Lax，默认 28,800 秒；生产配置启用 Secure 和 HTTPS。

## 问卷管理与草稿

|方法与路径|权限|输入与返回|
|---|---|---|
|POST /api/surveys|登录|title、description、anonymous、submissionPolicy、deadlineAt → 201 元信息，同时创建 V1 草稿|
|GET /api/surveys|登录|offset=0，limit=50（1..100）→ 本人列表 {items,total}|
|GET /api/surveys/{surveyId}|所有者|问卷元信息|
|PATCH /api/surveys/{surveyId}|所有者|title、description、deadlineAt、submissionPolicy、statisticsContribution → 元信息|
|POST /api/surveys/{surveyId}/save|所有者|{metadata,draft} → {survey,draft}，原子保存|
|GET /api/surveys/{surveyId}/versions|所有者|{publishedVersion,draftVersion,items}，包含完整版本列表|
|GET /api/surveys/{surveyId}/draft|所有者|草稿及 revision；无草稿返回 409|
|PUT /api/surveys/{surveyId}/draft|所有者|{expectedRevision,settings,questions} → revision+1 的草稿|
|POST /api/surveys/{surveyId}/draft-from-published|所有者|从当前发布版派生草稿；已有时返回现存草稿|
|POST /api/surveys/{surveyId}/publish|所有者|{expectedRevision} → 元信息及 publicUrl|
|POST /api/surveys/{surveyId}/close|所有者|关闭问卷，重复调用保持关闭状态|
|GET /api/surveys/{surveyId}/preview|所有者|验证并返回草稿预览|
|POST /api/surveys/{surveyId}/draft/import-question|所有者|{questionId,questionVersion,expectedRevision,replaceLocalId?} → 更新后的草稿|

匿名设置在版本的 settings 中保存；重复填写策略是问卷级属性，在首份成功答卷后固定。deadlineAt 显式 null 表示清空；title、description、submissionPolicy 和 statisticsContribution 传 null 时返回校验错误。关闭后可继续查看管理信息和统计，新答卷与重新发布按关闭状态处理。

### 联合保存示例

先创建问卷，得到 draftVersion=1、revision=0。下面通过统一接口保存元信息和题目：

```json
{
  "metadata": {"title": "学习体验", "description": "请按实际填写", "deadlineAt": null},
  "draft": {
    "expectedRevision": 0,
    "settings": {"anonymous": true},
    "questions": [{
      "id": "age", "type": "number", "title": "年龄", "required": true,
      "options": [], "validation": {"min": 0, "max": 120, "integerOnly": true},
      "routingRules": []
    }]
  }
}
```

metadata 使用 SurveyPatch，可为空对象；draft 使用 DraftInput。元信息、草稿和来源检查中的权限锁在同一事务内提交，成功返回 survey 和 revision=1 的 draft。修订冲突、来源不一致或策略锁等失败会整体回滚。

`/save` 用于一起保存元信息和当前可编辑草稿；单独修改时，分别使用 PATCH 元信息或 PUT draft。草稿冻结或不存在时，`/save` 返回 409，元信息可通过 PATCH 编辑。

发布时提交 `{"expectedRevision":1}`，将内容冻结为 sealed 并切换公开指针。冻结后中断可沿用相同 revision 重试；继续编辑则派生新草稿。来源题核心内容按固定版本校验，局部修改可解除 source 或显式导入其他版本。导入生成局部 ID；replaceLocalId 指定替换实例时保留该 ID、清空其出边并重新验证整卷。四题示例见 [fixtures.py](../source/tests/fixtures.py)。

## 填写与提交

|方法与路径|权限|输入与返回|
|---|---|---|
|GET /api/public/surveys/{publicId}|登录|当前发布版本的填写内容|
|POST /api/public/surveys/{publicId}/submissions|登录|{surveyVersion,requestId,answers} → 201 {id,replayed,surveyVersion}|

公开内容包含 publicId、title、description、deadlineAt、surveyVersion、settings、questions 和 submissionPolicy。

```json
{
  "surveyVersion": 1,
  "requestId": "24958374-a820-4250-bd20-d711ab87e420",
  "answers": [{"questionId": "age", "value": 20}]
}
```

成功返回 `{"id":"<submissionObjectId>","replayed":false,"surveyVersion":1}`。同一逻辑请求重试沿用原 UUID 和内容，返回同一 id 与 replayed=true；新一轮填写使用新 UUID。幂等键按问卷和填写者区分，摘要包含版本及按 questionId 排序的原始答案 JSON，空白或多选排列变化也可能触发内容冲突。

已成功请求在关闭或切版后重试仍可取得原记录；新请求按当前状态与版本校验。旧表单提交返回 `SURVEY_VERSION_CHANGED` 时，客户端重新获取公开问卷。服务器重算填写路径并保存规范化的有效答案，身份与提交时间由服务端确定。

## 问卷统计与答卷列表

|方法与路径|权限|输入与返回|
|---|---|---|
|GET /api/surveys/{surveyId}/submissions|所有者|version、mode、offset、limit → 分页答卷|
|GET /api/surveys/{surveyId}/statistics|所有者|同上 → 全卷统计|
|GET /api/surveys/{surveyId}/questions/{questionId}/statistics|所有者|同上 → 单道局部题目的统计|

version 省略时使用 publishedVersion。统计 mode 默认 `current_effective`，答卷列表默认 `historical_raw`。latest_only 先跨问卷版本选每人最新提交再筛目标版本，multiple 保留每份；不存在或未发布版本返回 404，非法 mode 返回 422。

```json
{
  "version": 1, "mode": "current_effective", "submissionPolicy": "latest_only",
  "rawSubmissionCount": 2, "effectiveSubmissionCount": 1, "selectedSubmissionCount": 1,
  "questions": [{
    "questionId": "age", "title": "年龄", "type": "number", "answeredCount": 1,
    "values": [20], "offset": 0, "limit": 50, "mean": 20.0
  }]
}
```

选择题返回 `options:[{id,label,count}]`；多选频数之和可能大于实际回答次数。文本和数字 values 分页，offset 默认 0，limit 默认 50、范围 1..100；均值及回答数基于全部选中答卷，空数字样本 mean=null。

答卷列表返回 `{version,mode,total,offset,limit,items}`。每条匿名记录包含 id、surveyVersion、anonymous、answers、submittedAt；实名记录补充 respondentId 和 respondentUsername。用户名在同一快照中批量查询，账号缺失时为 null，页面回退显示原 ID。身份展示使用提交时的 anonymousAtSubmission，因此后续版本的匿名设置不会改变历史记录。

## 题目与版本

|方法与路径|权限|输入与返回|
|---|---|---|
|POST /api/questions|登录|{content:{type,title,required,options,validation}} → 201 {definition,version}|
|GET /api/questions|登录|search、scope、activeOnly、offset、limit → {items,total,offset,limit}|
|GET /api/questions/{id}|题目可见|定义、current、ownerUsername、canEdit；所有者还可查看 sharedUsernames|
|GET /api/questions/{id}/versions|题目可见|offset、limit=50（1..100）→ 历史分页|
|POST /api/questions/{id}/versions|题目所有者|{expectedCurrentVersion,parentVersion,content} → 201 新版本|
|POST /api/questions/{id}/restore|题目所有者|{expectedCurrentVersion,version} → 201 恢复版本|
|POST /api/questions/{id}/fork|题目可见|{version} → 201 独立题目 {definition,version}|
|PATCH /api/questions/{id}/sharing|题目所有者|{usernames,expectedRevision} → {ok,revision}|
|PATCH /api/questions/{id}/archive|题目所有者|{archived,expectedRevision} → {ok,revision}|
|GET /api/questions/{id}/usage|题目可见|version 可选，offset、limit=20（1..100）→ 使用关系分页|
|GET /api/questions/{id}/statistics|题目可见|version 必填，scope、mode → 精确版本的跨问卷统计|

题目列表 search 最多 200 字符，按字面量匹配当前版本标题；scope 为 accessible（默认）、mine 或 shared，offset 默认 0，limit 默认 20、范围 1..100。activeOnly 默认 false；true 时在搜索、排序、分页和 total 之前过滤归档题。题目选择器使用 true，管理页使用默认列表。

共享用户名最多 100 个，需为已注册账号，空数组撤销共享。私有资源对未共享用户返回 404，共享用户修改原题返回 403。版本、共享与归档的期望值过期时返回 409。

## 题库

|方法与路径|权限|输入与返回|
|---|---|---|
|POST /api/question-banks|登录|{name,description?} → 201 题库|
|GET /api/question-banks|登录|offset、limit=20（1..100）→ 本人题库分页|
|GET /api/question-banks/{id}|所有者|题库及成员，包含 available、resolvedVersion、content|
|PATCH /api/question-banks/{id}|所有者|{name,description?,expectedRevision} → 题库|
|PUT /api/question-banks/{id}/items|所有者|{questionId,pinnedVersion?,expectedRevision} → 题库|
|DELETE /api/question-banks/{id}/items/{questionId}|所有者|query expectedRevision → 题库|

每个题库最多 200 成员。同一题目按身份 upsert，pinnedVersion 指定固定版本，null 或省略表示选题时解析最新版。不可用成员仅返回引用和 available=false；移除成员保留题目及历史版本。

## 跨问卷统计口径

查询按精确题目版本执行。scope 默认 mine，仅包含本人问卷；consented_shared 加入显式贡献的问卷。mode 为 current_effective（默认）或 historical_raw。每份外部问卷在当前口径下至少 3 次实际回答后参与聚合。

|返回字段|含义|
|---|---|
|questionId、questionVersion、type|目标身份、版本与题型|
|scope、mode|查询范围和答卷口径|
|surveyCount|授权及抑制后，有本次所选提交的去重问卷数|
|submissionCount|包含目标题实例的所选提交次数|
|answeredCount|实际存在的目标题答案次数|
|countUnit|按提交计次，跨问卷的同一填写者分别计入|
|exclusions|权限、样本阈值和其他版本的处理说明|
|options|选择题的 {id,label,count}|
|mean、distribution、interval|数字均值、{lower,upper,count} 和区间约定|

无提交的使用问卷不计 surveyCount；旧版答卷全部被新版替代时，在有效口径下也不计。保留答卷跳过目标题时，仍可计入 surveyCount/submissionCount，answeredCount 为零。同一问卷多次提交按 surveyId 只计一次。usage.total 是可见问卷版本引用条数，可能包含同一问卷多个版本，与 surveyCount 分别展示。

跨问卷响应按表中字段返回聚合结果，文本题只返回计数。原始答卷和填写者身份由单问卷管理接口按权限展示。数字分桶、匿名和授权细节见[数据库设计](database-design.md#统计口径)。

## 状态与错误

`GET /health` 返回 `{status:"ok"}`，数据库不可用时返回 503。业务错误统一为：

```json
{"error":{"code":"VALIDATION_ERROR","message":"数字超出范围","details":{"questionId":"age","field":"answers.age"}}}
```

|HTTP 状态|常见代码|
|---|---|
|401|UNAUTHENTICATED、INVALID_CREDENTIALS、SESSION_EXPIRED|
|403|FORBIDDEN、CSRF_FAILED|
|404|NOT_FOUND|
|409|USERNAME_EXISTS、DRAFT_CONFLICT、NO_DRAFT、NO_PUBLISHED_VERSION、PUBLISH_CONFLICT、PUBLISH_INCONSISTENT、IDEMPOTENCY_CONFLICT、SURVEY_VERSION_CHANGED、POLICY_LOCKED、SURVEY_CLOSED、SURVEY_EXPIRED、VERSION_CONFLICT、BANK_CONFLICT、SOURCE_MISMATCH、QUESTION_ARCHIVED|
|413|PAYLOAD_TOO_LARGE，2 MiB 请求上限|
|422|VALIDATION_ERROR、INVALID_ROUTING_RULE|
|503|DATABASE_UNAVAILABLE|

details 提供字段或题目位置。未知 URL 和不支持的方法沿用 FastAPI 标准 detail 响应。前端对登录失效、版本冲突、关闭和过期分别提供相应提示。
