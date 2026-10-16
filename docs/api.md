# API 规范（1.0.0）

本机基础地址http://127.0.0.1:8000；运行时/docs为交互文档，/openapi.json为机器规范，交付快照docs/openapi.json。JSON camelCase，ID字符串，时间带Z或时区，数据库UTC。未知字段拒绝。改变状态的已登录请求必须Cookie+X-CSRF-Token；注册/登录返回csrfToken，GET /api/me可读取。拒绝浏览器显式外域Origin。

|方法/路径|权限|输入/返回|
|---|---|---|
|POST /api/auth/register|公开|{username,password}→201 {user:{id,username,createdAt},csrfToken}，同时登录|
|POST /api/auth/login|公开|同上→200，建立Cookie|
|POST /api/auth/logout|登录+CSRF|→{ok:true}，撤销账号全部旧会话|
|GET /api/me|登录|{user,csrfToken}|
|GET /api/me/submissions|登录|surveyId可选,offset,limit→本人摘要{items,total}|
|POST /api/surveys|登录+CSRF|标题/说明/匿名/策略/截止→201元数据，同时创建V1|
|GET /api/surveys|登录|offset=0,limit=50(1..100)→本人{items,total}|
|GET /api/surveys/{surveyId}|所有者|问卷元数据|
|PATCH /api/surveys/{surveyId}|所有者+CSRF|title/description/deadlineAt/submissionPolicy→元数据|
|GET /api/surveys/{surveyId}/versions|所有者|{publishedVersion,draftVersion,items:完整版本列表}|
|GET /api/surveys/{surveyId}/draft|所有者|草稿含revision，无草稿409|
|PUT /api/surveys/{surveyId}/draft|所有者+CSRF|{expectedRevision,settings:{anonymous},questions}→revision+1草稿|
|POST /api/surveys/{surveyId}/draft-from-published|所有者+CSRF|下一草稿；已有则返回该草稿|
|POST /api/surveys/{surveyId}/publish|所有者+CSRF|{expectedRevision}→元数据+publicUrl，支持中断恢复|
|POST /api/surveys/{surveyId}/close|所有者+CSRF|关闭，幂等，不可重开|
|GET /api/surveys/{surveyId}/preview|所有者|验证并返回草稿，不写答卷|
|GET /api/public/surveys/{publicId}|登录|当前发布内容，无管理字段|
|POST /api/public/surveys/{publicId}/submissions|登录+CSRF|版本/UUID/答案→201 {id,replayed,surveyVersion}|
|GET /api/surveys/{surveyId}/submissions|所有者|version,mode,offset,limit→脱敏列表{version,mode,total,offset,limit,items}|
|GET /api/surveys/{surveyId}/statistics|所有者|version,mode,offset,limit→全卷统计|
|GET /api/surveys/{surveyId}/questions/{questionId}/statistics|所有者|同参数→单题统计（结构与全卷中的题相同）|
|GET /health|公开|{status:ok}，数据库不可用503|

匿名属于版本settings，不能在问卷PATCH设置。submissionPolicy为全卷属性，首份成功提交后锁定。deadlineAt显式null清空；title/description/policy不接受null。日期必须含时区。关闭后仍可查管理/统计，不接收新答卷、不重新发布。

## 创建、编辑与发布示例

POST /api/surveys：

```json
{"title":"学习体验","description":"请按实际填写","anonymous":true,"submissionPolicy":"latest_only","deadlineAt":null}
```

返回publishedVersion:null,draftVersion:1,status:draft。PUT draft：

```json
{"expectedRevision":0,"settings":{"anonymous":true},"questions":[
 {"id":"age","type":"number","title":"年龄","required":true,"options":[],"validation":{"min":0,"max":120,"integerOnly":true},"routingRules":[]}
]}
```

保存后revision=1；publish传`{"expectedRevision":1}`。发布后sealed不可编辑，先派生新草稿。冻结中断后同revision再publish完成指针切换，公开端不读取半发布版。完整四题跳转数据在tests/fixtures.py。

## 提交、幂等与版本

```json
{"surveyVersion":1,"requestId":"24958374-a820-4250-bd20-d711ab87e420","answers":[{"questionId":"age","value":20}]}
```

201为`{"id":"<submissionObjectId>","replayed":false,"surveyVersion":1}`。相同逻辑请求重试沿用UUID和内容，返回同id及replayed:true；新填写新UUID。摘要包含版本及按questionId排序的原始答案JSON，因此空白/多选排列等改变也可能409，应重发相同body。作用域survey+respondent，认证身份由服务器写入，伪造respondentId等额外字段422。

已有成功请求在关闭/切版后重试仍返回原记录（不产生新记录）；新requestId按当前状态版本验证。旧表单版本不等于公开指针时409 SURVEY_VERSION_CHANGED，不能偷偷转换答案。

公开DTO为publicId/title/description/deadlineAt/surveyVersion/settings/questions/submissionPolicy，不含ownerId、draftVersion或历史答卷。后台独立重算路径，拒绝重复题ID、无效路径答案、非法选项/类型/范围；仅保存规范化的有效答案。

## 统计、匿名与分页

version省略明确采用publishedVersion。统计mode默认current_effective；答卷列表默认historical_raw。不存在/未发布版本404；非法mode422。latest_only在全卷跨版本选每人最新记录后才筛版本，multiple保留每份；不跨版本合并题目统计。

```json
{"version":1,"mode":"current_effective","submissionPolicy":"latest_only",
 "rawSubmissionCount":2,"effectiveSubmissionCount":1,"selectedSubmissionCount":1,
 "questions":[{"questionId":"age","title":"年龄","type":"number","answeredCount":1,"values":[20],"offset":0,"limit":50,"mean":20.0}]}
```

选择题返回options:[{id,label,count}]；多选计数和可超过回答人数。文本/数字values分页（offset默认0，limit默认50，1..100），均值和人数始终基于全部选中答卷，无数字mean:null。答卷列表独立分页。匿名记录只含id/surveyVersion/anonymous/answers/submittedAt；实名额外respondentId，不返回用户名、requestId、摘要或内部文档。

## 会话和错误

Cookie survey_session：HttpOnly、SameSite=Lax、max-age28800，生产Secure。密码10..128字符，用户名3..40位并归一化。错误统一：

```json
{"error":{"code":"VALIDATION_ERROR","message":"数字超出范围","details":{"questionId":"age","field":"answers.age"}}}
```

|状态|含义|
|---|---|
|400|常规业务输入统一422，不使用400|
|401|UNAUTHENTICATED / INVALID_CREDENTIALS / SESSION_EXPIRED|
|403|FORBIDDEN / CSRF_FAILED|
|404|NOT_FOUND：问卷/题目/版本不存在或尚未公开|
|409|USERNAME_EXISTS、DRAFT_CONFLICT、NO_DRAFT、NO_PUBLISHED_VERSION、PUBLISH_CONFLICT、PUBLISH_INCONSISTENT、IDEMPOTENCY_CONFLICT、SURVEY_VERSION_CHANGED、POLICY_LOCKED、SURVEY_CLOSED、SURVEY_EXPIRED|
|413|PAYLOAD_TOO_LARGE（2MiB，包括流式请求）|
|422|VALIDATION_ERROR / INVALID_ROUTING_RULE，字段/JSON/规则/路径错误|
|503|DATABASE_UNAVAILABLE，不泄露数据库异常|

未知URL/不支持方法使用FastAPI标准detail；上述业务异常使用error结构。错误不回显密码或无效原始输入。网页401跳登录，旧版409提示刷新，关闭/过期显示禁止信息。
