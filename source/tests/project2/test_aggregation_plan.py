"""Bounded real-Mongo query audit; this is not a production load/capacity benchmark."""
import json
import os
from pathlib import Path
from uuid import uuid4
from bson import ObjectId
from bson.codec_options import CodecOptions
from app.db.mongo import now
from app.models.documents import SubmissionDocument
from app.services.questions import QuestionService
from app.services.surveys import SurveyService
from app.services.question_statistics import QuestionStatisticsService
from tests.project2.test_library import content


def test_populated_source_index_and_server_aggregation(db):
    stamp = now()
    uid = db.users.insert_one({'username': 'query_audit', 'passwordHash': 'synthetic', 'createdAt': stamp, 'schemaVersion': 1}).inserted_id
    question = QuestionService(db).create(uid, content())['definition']['_id']
    surveys = SurveyService(db)
    survey = surveys.create(uid, {'title': '聚合审计', 'submissionPolicy': 'multiple'})
    draft = surveys.import_question(survey['_id'], uid, question, 1, 0)
    surveys.publish(survey['_id'], uid, 1)
    local = draft['questions'][0]['id']
    # Seed validated persisted documents for query volume, without 1000 HTTP requests.
    rows = [SubmissionDocument(surveyId=survey['_id'], surveyVersion=1, respondentId=uid,
        anonymousAtSubmission=True, requestId=str(uuid4()), payloadDigest='synthetic-query-audit', submittedAt=stamp,
        answers=[{'questionId': local, 'value': value}]).to_bson() for value in range(1000)]
    db.submissions.insert_many(rows)
    result = QuestionStatisticsService(db).statistics(question, uid, 1)
    assert result['answeredCount'] == 1000 and result['mean'] == 499.5
    assert sum(r['count'] for r in result['distribution']) == 1000
    query = {'questions': {'$elemMatch': {'source.questionId': question, 'source.questionVersion': 1}}}
    explained = db.command('explain', {'find': 'survey_versions', 'filter': query}, verbosity='executionStats',
        codec_options=CodecOptions(unicode_decode_error_handler='replace'))
    assert 'IXSCAN' in str(explained['queryPlanner'])
    assert explained['executionStats']['nReturned'] == 1
    assert explained['executionStats']['totalDocsExamined'] == 1
    evidence = os.getenv('TEST_EVIDENCE_DIR')
    if evidence:
        destination = Path(evidence).parent / 'aggregation-audit.json'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps({'seededSubmissions': 1000, 'result': result,
            'executionStats': explained['executionStats'], 'queryPlanner': explained['queryPlanner'],
            'limitation': 'single-node synthetic 1000-record query audit, not a capacity benchmark'}, default=str, ensure_ascii=False, indent=2), encoding='utf-8')
