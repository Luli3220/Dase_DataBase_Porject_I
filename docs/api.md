# API 规范（2.0.0）

本机基础地址为http://127.0.0.1:8000，运行时可通过/docs查看交互文档，接口定义见[openapi.json](openapi.json)。

请求和响应采用camelCase字段名，ObjectId以字符串表示，时间使用带时区的ISO8601格式，数据库统一保存UTC。注册或登录后，客户端通过Cookie维持会话；修改状态的请求还需携带X-CSRF-Token。令牌由认证响应或GET /api/me获取，服务端同时校验请求Origin及输入字段。

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
|PATCH /api/surveys/{surveyId}|所有者+CSRF|title/description/deadlineAt/submissionPolicy/statisticsContribution→元数据|
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

保存后revision为1，发布请求传`{"expectedRevision":1}`。发布将版本冻结为sealed，后续修改通过派生新草稿完成。若冻结后发生中断，使用相同revision重试publish即可继续切换公开指针。完整四题示例见[tests/fixtures.py](../source/tests/fixtures.py)。

## 提交、幂等与版本

```json
{"surveyVersion":1,"requestId":"24958374-a820-4250-bd20-d711ab87e420","answers":[{"questionId":"age","value":20}]}
```

201为`{"id":"<submissionObjectId>","replayed":false,"surveyVersion":1}`。相同逻辑请求重试沿用UUID和内容，返回同id及replayed:true；新填写新UUID。摘要包含版本及按questionId排序的原始答案JSON，因此空白/多选排列等改变也可能409，应重发相同body。作用域survey+respondent，认证身份由服务器写入，伪造respondentId等额外字段422。

问卷关闭或切版后，已成功请求的重试仍返回原记录。新的requestId按当前状态与版本校验，旧表单版本与公开版本不一致时返回409 SURVEY_VERSION_CHANGED，页面提示重新获取问卷。

公开DTO为publicId/title/description/deadlineAt/surveyVersion/settings/questions/submissionPolicy，不含ownerId、draftVersion或历史答卷。后台独立重算路径，拒绝重复题ID、无效路径答案、非法选项/类型/范围；仅保存规范化的有效答案。

## 统计、匿名与分页

version省略明确采用publishedVersion。统计mode默认current_effective；答卷列表默认historical_raw。不存在/未发布版本404；非法mode422。latest_only在全卷跨版本选每人最新记录后才筛版本，multiple保留每份；不跨版本合并题目统计。

```json
{"version":1,"mode":"current_effective","submissionPolicy":"latest_only",
 "rawSubmissionCount":2,"effectiveSubmissionCount":1,"selectedSubmissionCount":1,
 "questions":[{"questionId":"age","title":"年龄","type":"number","answeredCount":1,"values":[20],"offset":0,"limit":50,"mean":20.0}]}
```

选择题返回options:[{id,label,count}]，多选题各选项次数之和可能大于回答人数。文本和数字values分页展示，offset默认0，limit默认50、范围1..100；均值和回答数按全部选中答卷计算，数字为空时mean为null。

答卷列表独立分页。匿名记录包含id、surveyVersion、anonymous、answers和submittedAt，非匿名记录增加respondentId和respondentUsername；幂等键和摘要由服务端内部使用。

`GET /api/surveys/{surveyId}/submissions`的非匿名身份示例：

```json
{"id":"<submissionObjectId>","surveyVersion":2,"anonymous":false,"respondentId":"<userObjectId>","respondentUsername":"reader_actual","answers":[],"submittedAt":"2026-10-16T00:00:00Z"}
```

respondentUsername来自users.username，服务端在同一snapshot事务中批量查询当前页的非匿名用户。全匿名页和空页直接返回列表。若关联账号缺失，respondentUsername为null，网页回退显示原respondentId。

身份可见性只取决于每份答卷的anonymousAtSubmission；即使公开版本已改为非匿名，旧匿名记录也不返回两个身份字段；后续改为匿名也不反向修改已有非匿名承诺。统计接口依旧不包含账号身份。

## 会话和错误

Cookie survey_session：HttpOnly、SameSite=Lax、max-age28800，生产Secure。密码10..128字符，用户名3..40位并归一化。错误统一：

```json
{"error":{"code":"VALIDATION_ERROR","message":"数字超出范围","details":{"questionId":"age","field":"answers.age"}}}
```

|状态|含义|
|---|---|
|401|UNAUTHENTICATED / INVALID_CREDENTIALS / SESSION_EXPIRED|
|403|FORBIDDEN / CSRF_FAILED|
|404|NOT_FOUND：问卷/题目/版本不存在或尚未公开|
|409|USERNAME_EXISTS、DRAFT_CONFLICT、NO_DRAFT、NO_PUBLISHED_VERSION、PUBLISH_CONFLICT、PUBLISH_INCONSISTENT、IDEMPOTENCY_CONFLICT、SURVEY_VERSION_CHANGED、POLICY_LOCKED、SURVEY_CLOSED、SURVEY_EXPIRED|
|413|PAYLOAD_TOO_LARGE（2MiB，包括流式请求）|
|422|VALIDATION_ERROR / INVALID_ROUTING_RULE，字段/JSON/规则/路径错误|
|503|DATABASE_UNAVAILABLE，不泄露数据库异常|

未知URL/不支持方法使用FastAPI标准detail；上述业务异常使用error结构。错误不回显密码或无效原始输入。网页401跳登录，旧版409提示刷新，关闭/过期显示禁止信息。


## 第二阶段新增接口

以下均要求登录，写入同时要求 CSRF。身份只取 Cookie；请求模型禁止多余字段。题目私有资源对未共享用户返回404，已共享用户尝试修改原题返回403。版本/草稿/题库 CAS 冲突409；非法配置422。可选 source 对旧请求兼容，返回字段为增量扩展。

|方法 / 路径|请求与返回|
|---|---|
|POST /api/questions|{content:{type,title,required,options,validation}} →201 {definition,version}|
|GET /api/questions|search≤200（字面量匹配）、scope=accessible/mine/shared、offset≥0、limit=20(1..100) → {items,total,offset,limit}|
|GET /api/questions/{id}|基本信息、current、ownerUsername、canEdit；只有所有者看到sharedUsernames|
|GET /api/questions/{id}/versions|offset / limit=50(1..100) →历史 {items,total,offset,limit}|
|POST /api/questions/{id}/versions|{expectedCurrentVersion,parentVersion,content} →201新版本|
|POST /api/questions/{id}/restore|{expectedCurrentVersion,version} →201追加恢复版本|
|POST /api/questions/{id}/fork|{version} →201 {definition,version}，独立身份|
|PATCH /api/questions/{id}/sharing|{usernames:[已注册用户名]≤100,expectedRevision} →{ok,revision}；空数组撤销|
|PATCH /api/questions/{id}/archive|{archived:bool,expectedRevision} →{ok,revision}|
|GET /api/questions/{id}/usage|version可选、offset / limit=20(1..100) →{items,total,visibility,...}，仅授权可见使用关系|
|GET /api/questions/{id}/statistics|version必填，scope=mine/consented_shared，mode=current_effective/historical_raw →精确版本计数、分布与排除说明|
|POST /api/question-banks|{name,description?} →201题库|
|GET /api/question-banks|offset / limit=20(1..100) →本人题库分页|
|GET /api/question-banks/{id}|成员含available；不可用成员不返回内容；可用成员含resolvedVersion/content|
|PATCH /api/question-banks/{id}|{name,description?,expectedRevision} →题库|
|PUT /api/question-banks/{id}/items|{questionId,pinnedVersion?:int或null,expectedRevision} →题库；同题upsert，固定/最新可切换|
|DELETE /api/question-banks/{id}/items/{questionId}|query expectedRevision必填 →题库，原题与历史不删除|
|POST /api/surveys/{id}/draft/import-question|{questionId,questionVersion,expectedRevision,replaceLocalId?:string或null} →revision+1的草稿；首次导入生成新ID，替换保留ID并清空出边|

题库最多200成员。未固定版本的题库成员只在选题时解析最新；import-question始终提交明确版本。旧 PUT draft 仍可提交没有source的本地题；带source的核心内容必须与库中固定版本一致。删除source是明确解除关联。原 PATCH survey 新增 statisticsContribution（bool，默认false），仅所有者可改，null非法。其余旧接口请求与行为继续保留。

跨问卷统计返回 questionId、questionVersion、type、scope、mode、surveyCount、submissionCount、answeredCount、countUnit、exclusions；选择题增加options[{id,label,count}]；数字题增加mean、distribution[{lower,upper,count}]与interval。文本不返回原文。所有跨问卷结果均不包含respondentId、用户名、原始答卷和外部问卷标识。数字分桶及小样本规则见[数据库设计](database-design.md)。
