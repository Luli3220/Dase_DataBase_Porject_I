"""Exact-version cross-survey aggregation with survey-level consent and path semantics."""
from app.core.errors import require
from app.db.mongo import oid, transaction, now
from app.services.questions import QuestionService

# Half-open age-oriented bins cover the complete safe numeric range with open tails.
BOUNDS = [0, 18, 30, 45, 60, 121]
MIN_SHARED_SAMPLE = 3


class QuestionStatisticsService:
    def __init__(self, db):
        self.db, self.questions = db, QuestionService(db)

    def usage(self, question_id, user_id, version=None, offset=0, limit=20):
        def operation(session):
            q = self.questions.accessible(question_id, user_id, session)
            if version is not None:
                self.questions.version(q['_id'], version, session)
            source = {'source.questionId': q['_id']}
            if version is not None: source['source.questionVersion'] = version
            pipeline = [{'$match': {'questions': {'$elemMatch': source}}},
                {'$lookup': {'from': 'surveys', 'localField': 'surveyId', 'foreignField': '_id', 'as': 'survey'}},
                {'$unwind': '$survey'}, {'$match': {'$or': [{'survey.ownerId': oid(user_id)},
                    {'survey.status': 'published', '$and': [{'$or': [{'survey.deadlineAt': None}, {'survey.deadlineAt': {'$gt': now()}}]}],
                     '$expr': {'$eq': ['$version', '$survey.publishedVersion']}}]}},
                {'$sort': {'createdAt': -1, '_id': -1}}, {'$facet': {'total': [{'$count': 'n'}], 'items': [{'$skip': offset}, {'$limit': limit},
                    {'$project': {'_id': 0, 'surveyId': 1, 'surveyVersion': '$version', 'title': '$survey.title', 'state': 1,
                        'status': {'$cond': [{'$eq': ['$version', '$survey.draftVersion']}, 'draft',
                            {'$cond': [{'$eq': ['$version', '$survey.publishedVersion']}, 'published', 'historical']}]},
                        'sources': {'$map': {'input': {'$filter': {'input': '$questions', 'as': 'q',
                            'cond': {'$eq': ['$$q.source.questionId', q['_id']]}}}, 'as': 'q', 'in': '$$q.source'}}}}]}}]
            rows = list(self.db.survey_versions.aggregate(pipeline, session=session))[0]
            return {'items': rows['items'], 'total': rows['total'][0]['n'] if rows['total'] else 0,
                    'offset': offset, 'limit': limit, 'visibility': 'own versions and currently public surveys; private usage omitted'}
        return transaction(self.db, operation)

    def pipeline(self, surveys, question_id, version, mode):
        ids = [s['_id'] for s in surveys]
        latest = [s['_id'] for s in surveys if s['submissionPolicy'] == 'latest_only']
        pipeline = [{'$match': {'surveyId': {'$in': ids}}}]
        if mode == 'current_effective':
            # Crucially, deduplicate over ALL survey versions before filtering source/version.
            pipeline += [{'$sort': {'submittedAt': -1, '_id': -1}}, {'$group': {'_id': {'$cond': [
                {'$in': ['$surveyId', latest]}, {'survey': '$surveyId', 'respondent': '$respondentId'}, {'record': '$_id'}]},
                'record': {'$first': '$$ROOT'}}}, {'$replaceRoot': {'newRoot': '$record'}}]
        pipeline += [{'$lookup': {'from': 'survey_versions', 'let': {'sid': '$surveyId', 'sv': '$surveyVersion'}, 'pipeline': [
            {'$match': {'state': 'sealed', 'questions': {'$elemMatch': {'source.questionId': question_id, 'source.questionVersion': version}},
                '$expr': {'$and': [{'$eq': ['$surveyId', '$$sid']}, {'$eq': ['$version', '$$sv']}]}}},
            {'$project': {'questions': {'$filter': {'input': '$questions', 'as': 'q', 'cond': {'$and': [
                {'$eq': ['$$q.source.questionId', question_id]}, {'$eq': ['$$q.source.questionVersion', version]}]}}}}}], 'as': 'sv'}},
            {'$unwind': '$sv'}, {'$unwind': '$sv.questions'},
            {'$set': {'answer': {'$filter': {'input': '$answers', 'as': 'a', 'cond': {'$eq': ['$$a.questionId', '$sv.questions.id']}}}}},
            {'$set': {'answered': {'$gt': [{'$size': '$answer'}, 0]}, 'value': {'$arrayElemAt': ['$answer.value', 0]}}}]
        return pipeline

    def statistics(self, question_id, user_id, version, scope='mine', mode='current_effective'):
        require(scope in ('mine', 'consented_shared') and mode in ('current_effective', 'historical_raw'), '统计范围或口径非法')
        def operation(session):
            q = self.questions.accessible(question_id, user_id, session)
            v = self.questions.version(q['_id'], version, session)
            uid = oid(user_id)
            query = {'ownerId': uid} if scope == 'mine' else {'$or': [{'ownerId': uid}, {'statisticsContribution': True}]}
            surveys = list(self.db.surveys.find(query, {'ownerId': 1, 'submissionPolicy': 1}, session=session))
            base = self.pipeline(surveys, q['_id'], version, mode)
            # Per external survey suppression prevents tiny groups becoming visible through totals.
            sizes = list(self.db.submissions.aggregate(base + [{'$group': {'_id': '$surveyId', 'n': {'$sum': {'$cond': ['$answered', 1, 0]}}}}], session=session))
            counts = {x['_id']: x['n'] for x in sizes}
            suppressed = sum(s['_id'] in counts and s['ownerId'] != uid and counts[s['_id']] < MIN_SHARED_SAMPLE for s in surveys)
            allowed = [s for s in surveys if s['ownerId'] == uid or counts.get(s['_id'], 0) >= MIN_SHARED_SAMPLE]
            pipeline = self.pipeline(allowed, q['_id'], version, mode)
            facet = {'summary': [{'$group': {'_id': None, 'submissionCount': {'$sum': 1},
                       'answeredCount': {'$sum': {'$cond': ['$answered', 1, 0]}},
                       'mean': {'$avg': '$value'}}}],
                     'surveys': [{'$group': {'_id': '$surveyId'}}, {'$count': 'n'}]}
            kind = v['content']['type']
            if kind in ('single_choice', 'multiple_choice'):
                facet['options'] = [{'$match': {'answered': True}}] + ([{'$unwind': '$value'}] if kind == 'multiple_choice' else []) + [
                    {'$group': {'_id': '$value', 'n': {'$sum': 1}}}]
            if kind == 'number':
                facet['distribution'] = [{'$match': {'answered': True}}, {'$group': {'_id': {'$switch': {
                    'branches': [{'case': {'$lt': ['$value', bound]}, 'then': i} for i, bound in enumerate(BOUNDS)], 'default': len(BOUNDS)}}, 'n': {'$sum': 1}}}]
            rows = list(self.db.submissions.aggregate(pipeline + [{'$facet': facet}], session=session))[0]
            summary = rows['summary'][0] if rows['summary'] else {'submissionCount': 0, 'answeredCount': 0, 'mean': None}
            result = {'questionId': str(q['_id']), 'questionVersion': version, 'scope': scope, 'mode': mode, 'type': kind,
                'surveyCount': rows['surveys'][0]['n'] if rows['surveys'] else 0,
                'submissionCount': summary['submissionCount'], 'answeredCount': summary['answeredCount'],
                'countUnit': 'submission (not unique people across surveys)',
                'exclusions': {'unconsented': 'other private survey data excluded by default',
                               'suppressedSurveyCount': suppressed, 'minimumSharedSample': MIN_SHARED_SAMPLE,
                               'differentVersions': 'only exact source version included; no title-based merge'}}
            if kind in ('single_choice', 'multiple_choice'):
                frequencies = {r['_id']: r['n'] for r in rows['options']}
                result['options'] = [{**o, 'count': frequencies.get(o['id'], 0)} for o in v['content']['options']]
            if kind == 'number':
                frequencies = {r['_id']: r['n'] for r in rows['distribution']}
                edges = [None, *BOUNDS, None]
                result['mean'] = summary['mean']
                result['distribution'] = [{'lower': edges[i], 'upper': edges[i+1], 'count': frequencies.get(i, 0)} for i in range(len(edges)-1)]
                result['interval'] = '[lower, upper), null means unbounded; denominator=answeredCount'
            # No raw values, user IDs, usernames or external survey IDs, even for text.
            return result
        return transaction(self.db, operation)
