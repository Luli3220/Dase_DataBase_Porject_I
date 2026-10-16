# 规则与校验规范

实现入口：`app/rules/engine.py`，纯函数，不依赖 HTTP/Mongo。`validate_question_config` 静态检查，`validate_answer` 动态规范化，`evaluate_condition` 白名单解释，`next_question` 取首条命中，`trace_path_and_validate_submission` 重算有效路径。

四题型 single_choice/multiple_choice/text/number。选择题只保存稳定选项 ID，不保存显示标签。文本 trim 后按 Unicode 码点长度检查和保存。数字只接受有限 JSON number，拒绝 bool、字符串、NaN/Infinity；绝对值上限 2^53-1 保证 BSON/浏览器一致。数字支持 min/max/integerOnly。手机号课程整数示例可用数字题；真实号码建议文本保留前导零和国际区号。

可选题缺失/null、空白文本/空数组多选统一“不回答”，不落 answers；必答题访问到时则拒绝。单选或数字的空字符串非法。0 是有效数字。多选必须无重复且合法，一旦选择须满足数量限制；未选可选题不触发条件。静态检查 0≤min≤max（多选≤选项数，文本≤10000），不支持参数拒绝，必答多选必须至少允许一项。

单选 eq；多选 contains_any（交集非空）、contains_all（operand 是答案子集）；数字 eq/gt/gte/lt/lte；文本无跳转操作。operand 严格验证选项数组/数值，priority 为0..1000000整数且同题唯一，升序首条命中生效。rule.id 同题唯一，question.id 全版本唯一，option.id 同题唯一。

目标 `{kind:question,questionId:...}` 或 `{kind:end}`；只能向数组后方跳，禁止自跳、回跳和不存在目标。未命中走数组下一题，最后一题结束，不存冗余 order。执行不使用 eval/exec/用户脚本。端到端路径从首题开始，验证路径上必答；携带任何不在有效路径的答案（即使为null）均拒绝；未知或重复题 ID 拒绝。

错误统一 `{error:{code,message,details}}`；规则错误 INVALID_ROUTING_RULE，答案/参数 VALIDATION_ERROR，details 提供 questionId/field，HTTP422。草稿版本冲突 DRAFT_CONFLICT、旧版提交 SURVEY_VERSION_CHANGED、关闭 SURVEY_CLOSED、过期 SURVEY_EXPIRED 为409。

固定 fixture 精确对应规格 R01..R15；Q3“否则 END”使用第二条 lt10/end 规则表达，保证默认语义始终是下一题，而非为 Q3 硬编码。规则配置/执行都受测试覆盖。第二阶段增加题型时在模型、静态参数、答案、运算符、前端控件、统计分派增加实现，并保持旧 schemaVersion 解释器可用。
