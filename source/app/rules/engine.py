"""Pure data-driven static validation and forward-only path execution."""
import math
from pydantic import ValidationError
from app.models.domain import Question
from app.core.errors import DomainError, require

MISSING = object()
OPERATORS = {"single_choice": {"eq"}, "multiple_choice": {"contains_any", "contains_all"},
             "number": {"eq", "gt", "gte", "lt", "lte"}, "text": set()}
KEYS = {"single_choice": set(), "multiple_choice": {"minSelections", "maxSelections"},
        "text": {"minLength", "maxLength"}, "number": {"min", "max", "integerOnly"}}


def numeric(value):
    # BSON integers are signed 64-bit. Keep integers exactly representable in JS too.
    return type(value) in (int, float) and abs(value) <= 9007199254740991 and math.isfinite(value)


def validate_question_config(questions, allow_empty=False):
    try:
        qs = [Question.model_validate(q).model_dump(exclude_none=True) for q in questions]
    except ValidationError as exc:
        raise DomainError("VALIDATION_ERROR", "题目结构错误", fields=[{"field": ".".join(map(str, e["loc"])), "message": e["msg"]} for e in exc.errors()])
    require((allow_empty or len(qs) > 0) and len(qs) <= 100, "问卷须包含 1..100 题")
    ids = [q["id"] for q in qs]
    require(len(set(ids)) == len(ids), "题目 ID 重复")
    for index, q in enumerate(qs):
        detail = {"questionId": q["id"], "field": f"questions.{q['id']}"}
        def check(ok, message, rule=False):
            require(ok, message, "INVALID_ROUTING_RULE" if rule else "VALIDATION_ERROR", **detail)
        check(bool(q["title"].strip()), "题目标题不能为空")
        options = [o["id"] for o in q["options"]]
        check(len(options) == len(set(options)) and all(o["label"].strip() for o in q["options"]), "选项重复或标签为空")
        check(bool(options) if q["type"] in ("single_choice", "multiple_choice") else not options, "选项与题型不匹配")
        v = q["validation"]
        check(set(v) <= KEYS[q["type"]], "校验参数不适用于当前题型")
        if q["type"] in ("text", "multiple_choice"):
            lo_key, hi_key, cap = ("minLength", "maxLength", 10000) if q["type"] == "text" else ("minSelections", "maxSelections", len(options))
            lo, hi = v.get(lo_key, 0), v.get(hi_key, cap)
            check(type(lo) is int and type(hi) is int and 0 <= lo <= hi <= cap, "上下限非法或矛盾")
            if q["type"] == "multiple_choice" and q["required"]:
                check(hi >= 1, "必答多选至少允许选择一项")
        if q["type"] == "number":
            check(all(numeric(v[k]) for k in ("min", "max") if k in v), "数字边界必须为有限安全数值")
            check(type(v.get("integerOnly", False)) is bool, "integerOnly 必须为布尔")
            check(v.get("min", -math.inf) <= v.get("max", math.inf), "数字上下限矛盾")
            if v.get("integerOnly") and "min" in v and "max" in v:
                check(math.ceil(v["min"]) <= math.floor(v["max"]), "整数范围内没有可用值")
        priorities, rule_ids = set(), set()
        for r in q["routingRules"]:
            check(r["priority"] not in priorities and r["id"] not in rule_ids, "规则 ID 或优先级重复", True)
            priorities.add(r["priority"]); rule_ids.add(r["id"])
            op, operand = r["condition"]["operator"], r["condition"]["operand"]
            check(op in OPERATORS[q["type"]], "运算符不适用于题型", True)
            if q["type"] == "single_choice":
                check(type(operand) is str and operand in options, "规则选项不存在", True)
            elif q["type"] == "multiple_choice":
                check(type(operand) is list and len(operand) > 0 and all(type(x) is str and x in options for x in operand) and len(operand) == len(set(operand)), "规则操作数须为非空唯一选项数组", True)
            elif q["type"] == "number":
                check(numeric(operand), "规则操作数须为有限数值", True)
            t = r["target"]
            if t["kind"] == "end":
                check("questionId" not in t, "结束目标不能含题目 ID", True)
            else:
                check(t.get("questionId") in ids and ids.index(t["questionId"]) > index, "跳转目标须存在且位于当前题之后", True)
    return qs


def validate_answer(q, value=MISSING):
    t, v = q["type"], q.get("validation", {})
    empty = value is MISSING or value is None or (t == "text" and type(value) is str and not value.strip()) or (t == "multiple_choice" and type(value) is list and not value)
    def check(ok, message):
        require(ok, message, questionId=q["id"], field=f"answers.{q['id']}")
    if empty:
        check(not q.get("required", False), "有效路径上的必答题未回答")
        return MISSING
    options = [o["id"] for o in q.get("options", [])]
    if t == "single_choice":
        check(type(value) is str and value in options, "请选择有效选项")
    elif t == "multiple_choice":
        check(type(value) is list and all(type(x) is str and x in options for x in value), "请选择有效选项数组")
        check(len(value) == len(set(value)), "选项不能重复")
        check(v.get("minSelections", 0) <= len(value) <= v.get("maxSelections", len(options)), "选择数量超出范围")
        value = [x for x in options if x in value]
    elif t == "text":
        check(type(value) is str, "文本答案须为字符串")
        value = value.strip()
        check(v.get("minLength", 0) <= len(value) <= v.get("maxLength", 10000), "文本长度超出范围")
    elif t == "number":
        check(numeric(value), "数字答案须为有限 JSON 数值，不能是布尔或字符串")
        check(v.get("min", -math.inf) <= value <= v.get("max", math.inf), "数字超出范围")
        check(not v.get("integerOnly", False) or value % 1 == 0, "数字必须为整数")
    return value


def evaluate_condition(condition, value):
    if value is MISSING:
        return False
    op, rhs = condition["operator"], condition["operand"]
    if op == "contains_any": return bool(set(value) & set(rhs))
    if op == "contains_all": return set(rhs) <= set(value)
    if op == "eq": return value == rhs
    if op == "gt": return value > rhs
    if op == "gte": return value >= rhs
    if op == "lt": return value < rhs
    if op == "lte": return value <= rhs
    raise DomainError("INVALID_ROUTING_RULE", "未知运算符")


def next_question(questions, index, value):
    for rule in sorted(questions[index].get("routingRules", []), key=lambda r: r["priority"]):
        if evaluate_condition(rule["condition"], value):
            target = rule["target"]
            return len(questions) if target["kind"] == "end" else next(i for i, q in enumerate(questions) if q["id"] == target["questionId"])
    return index + 1


def trace_path_and_validate_submission(questions, answers):
    require(len(answers) <= 100, "答案数量超限")
    supplied = {}
    known = {q["id"] for q in questions}
    for a in answers:
        qid = a["questionId"]
        require(qid in known and qid not in supplied, "未知或重复题目 ID", questionId=qid)
        supplied[qid] = a["value"]
    index, path, normalized = 0, [], []
    while index < len(questions):
        q = questions[index]
        require(q["id"] not in path, "无效循环", "INVALID_ROUTING_RULE")
        path.append(q["id"])
        value = validate_answer(q, supplied.get(q["id"], MISSING))
        if value is not MISSING:
            normalized.append({"questionId": q["id"], "value": value})
        index = next_question(questions, index, value)
    require(set(supplied) <= set(path), "不能提交被跳过的题目答案", field="answers")
    return normalized, path
