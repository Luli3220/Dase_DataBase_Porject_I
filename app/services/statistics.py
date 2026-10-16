from app.core.errors import require
from app.services.submissions import SubmissionService
from app.db.mongo import transaction


class StatisticsService(SubmissionService):
    def statistics(self, survey_id, user_id, version=None, mode="current_effective", question_id=None, offset=0, limit=50):
        return transaction(self.db, lambda session: self._statistics(survey_id, user_id, version, mode, question_id, offset, limit, session))

    def _statistics(self, survey_id, user_id, version, mode, question_id, offset, limit, session):
        s = self.surveys.owned(survey_id, user_id, session)
        version = version if version is not None else s["publishedVersion"]
        v, pipeline = self.selected(s, version, mode, session)
        qs = [q for q in v["questions"] if question_id is None or q["id"] == question_id]
        require(bool(qs), "题目不存在", "NOT_FOUND", 404)
        # Aggregate values in Mongo; bounded text/numeric samples use slice + pagination.
        aggregate = list(self.db.submissions.aggregate(pipeline + [{"$unwind": "$answers"}, {"$group": {"_id": "$answers.questionId", "n": {"$sum": 1}, "avg": {"$avg": "$answers.value"}}}], session=session))
        counts = {r["_id"]: r for r in aggregate}
        results = []
        for q in qs:
            qid, t = q["id"], q["type"]
            stat = {"questionId": qid, "title": q["title"], "type": t, "answeredCount": counts.get(qid, {}).get("n", 0)}
            match = pipeline + [{"$unwind": "$answers"}, {"$match": {"answers.questionId": qid}}]
            if t in ("single_choice", "multiple_choice"):
                stages = match + ([{"$unwind": "$answers.value"}] if t == "multiple_choice" else [])
                opts = {r["_id"]: r["n"] for r in self.db.submissions.aggregate(stages + [{"$group": {"_id": "$answers.value", "n": {"$sum": 1}}}], session=session)}
                stat["options"] = [{**o, "count": opts.get(o["id"], 0)} for o in q["options"]]
            else:
                stat["values"] = [r["answers"]["value"] for r in self.db.submissions.aggregate(match + [{"$skip": offset}, {"$limit": limit}, {"$project": {"answers.value": 1}}], session=session)]
                stat.update(offset=offset, limit=limit)
                if t == "number": stat["mean"] = counts.get(qid, {}).get("avg")
            results.append(stat)
        raw_count = self.db.submissions.count_documents({"surveyId": s["_id"], "surveyVersion": version}, session=session)
        _, effective = self.selected(s, version, "current_effective", session)
        count = lambda p: next(iter(self.db.submissions.aggregate(p + [{"$count": "n"}], session=session)) , {"n": 0})["n"]
        return {"version": version, "mode": mode, "submissionPolicy": s["submissionPolicy"], "rawSubmissionCount": raw_count,
                "effectiveSubmissionCount": count(effective), "selectedSubmissionCount": count(pipeline), "questions": results}
