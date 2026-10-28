# 题目校验与跳转规则

规则引擎位于[source/app/rules/engine.py](../source/app/rules/engine.py)，负责配置检查、答案规范化、条件匹配和填写路径计算。

## 题型与答案

|题型|答案格式|校验条件|
|---|---|---|
|single_choice|选项ID字符串|选项有效、必答检查|
|multiple_choice|选项ID数组|选项有效、无重复、minSelections/maxSelections|
|text|字符串|去除首尾空白后，按Unicode码点检查minLength/maxLength|
|number|JSON数字|min/max/integerOnly，有限值，绝对值不超过2^53-1|

数字答案拒绝布尔、数字字符串及NaN/Infinity，0是有效值。手机号等标识可用文本保存前导零和国际区号；数字题也支持课程中的整数示例。

可选题的缺失、null、空白文本和空多选统一视为未回答，省略于answers；必答检查在路径访问到该题时生效。单选和数字的空字符串属于非法输入。多选一旦选择，就按数量上下限校验；必答多选至少选择一项。

## 配置检查

发布前检查题目ID、选项ID、规则ID、优先级、参数边界和跳转目标。question.id在版本内唯一，option.id与rule.id在题目内唯一。priority为0..1000000整数，同题规则优先级各不相同。

文本长度和多选数量满足0≤min≤max；文本上限10000码点，多选上限为选项数。数字边界满足min≤max，integerOnly为布尔值。题目按questions数组排序，跳转使用稳定题目ID。

## 条件与目标

|题型|运算符|含义|
|---|---|---|
|单选|eq|等于指定选项|
|多选|contains_any|包含操作数中的任一选项|
|多选|contains_all|包含操作数中的全部选项|
|数字|eq、gt、gte、lt、lte|相应数值比较|

文本题按顺序前进。选择题操作数必须引用有效选项，多选操作数为非空、无重复数组；数字操作数为有限数值。

目标为`{kind:question,questionId:...}`或`{kind:end}`。题目目标必须存在且位于当前题之后；end直接结束问卷。同题规则按priority升序匹配，第一条成立后生效；未匹配时进入数组下一题，最后一题结束。可选题未回答时同样进入下一题。

## 填写路径

服务器从首题开始，逐题规范化答案并计算下一位置，直到结束。实际路径上的必答题需要回答；未知题目、重复题目以及路径外答案会被拒绝。最终保存的是规范化后的路径答案。

对应函数为validate_question_config、validate_answer、evaluate_condition、next_question与trace_path_and_validate_submission。规则解释器按白名单处理条件。

固定样例与R01–R15见[测试用例](test-cases.md)。其中Q3的“否则结束”通过lt10/end规则表达，默认前进逻辑仍为下一题。

## 题库来源与局部路由

题库版本保存题型、标题、必答、选项和校验。routingRules 使用问卷内的局部 ID，因此由每份问卷独立配置。导入时生成局部实例，初始 routingRules=[]，再校验整份问卷。

source 记录所选题目与版本，问卷服务会检查内容是否一致。修改关联题时，可显式替换版本，或解除来源后作为本地题编辑。替换保留局部 ID 和其他题目的入边，清空本题出边；校验失败时事务回滚。库题更新后，已发布问卷及历史答卷仍按原快照解释。

## 错误与扩展

错误结构为`{error:{code,message,details}}`。配置/答案错误返回422 VALIDATION_ERROR或INVALID_ROUTING_RULE，details包含questionId及field；草稿冲突、版本变化、关闭和过期使用相应409错误码，详见[API文档](api.md)。

新增题型时，需要扩展请求模型、配置/答案校验、前端控件和统计服务；新增条件时扩展操作符白名单及匹配函数，并补充对应测试。
