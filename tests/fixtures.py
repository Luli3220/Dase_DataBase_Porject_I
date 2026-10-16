def fixture_questions():
    def rule(rid, priority, op, operand, target):
        return {"id": rid, "priority": priority, "condition": {"operator": op, "operand": operand}, "target": {"kind": "question", "questionId": target} if target else {"kind": "end"}}
    return [
        {"id": "q1", "type": "single_choice", "title": "是否有编程经验？", "required": True,
         "options": [{"id": "yes", "label": "有"}, {"id": "no", "label": "没有"}], "validation": {}, "routingRules": [rule("r1", 10, "eq", "no", "q3")]},
        {"id": "q2", "type": "multiple_choice", "title": "熟悉哪些语言？", "required": True,
         "options": [{"id": x, "label": x} for x in ("python", "java", "cpp")], "validation": {"minSelections": 1, "maxSelections": 3},
         "routingRules": [rule("r2", 10, "contains_all", ["python", "java"], "q4"), rule("r3", 20, "contains_any", ["cpp"], None)]},
        {"id": "q3", "type": "number", "title": "每周学习几小时？", "required": True, "options": [], "validation": {"min": 0, "max": 80, "integerOnly": False},
         "routingRules": [rule("r4", 10, "gte", 10, "q4"), rule("r5", 20, "lt", 10, None)]},
        {"id": "q4", "type": "text", "title": "课程建议？", "required": False, "options": [], "validation": {"minLength": 0, "maxLength": 500}, "routingRules": []}]


def answers(**values):
    return [{"questionId": k, "value": v} for k, v in values.items()]
