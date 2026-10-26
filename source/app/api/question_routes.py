"""Library routes share the existing authentication, CSRF and error boundary."""
from typing import Literal
from fastapi import APIRouter, Request, Query
from app.api.routes import User, Writer, Mode, db
from app.models.domain import (QuestionCreate, QuestionVersionInput, QuestionRestore, QuestionFork,
    QuestionSharing, QuestionArchive, BankInput, BankPatch, BankMember, QuestionImport, serialize)
from app.services.questions import QuestionService
from app.services.question_banks import QuestionBankService
from app.services.question_statistics import QuestionStatisticsService
from app.services.surveys import SurveyService

router = APIRouter(prefix='/api')


@router.post('/questions', status_code=201)
def create(body: QuestionCreate, request: Request, user: Writer):
    return serialize(QuestionService(db(request)).create(user['_id'], body.content.model_dump()))


@router.get('/questions')
def listing(request: Request, user: User, search: str = Query('', max_length=200),
            scope: Literal['accessible', 'mine', 'shared'] = 'accessible', offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    return serialize(QuestionService(db(request)).list(user['_id'], search, offset, limit, scope))


@router.get('/questions/{question_id}')
def detail(question_id: str, request: Request, user: User):
    return serialize(QuestionService(db(request)).detail(question_id, user['_id']))


@router.get('/questions/{question_id}/versions')
def history(question_id: str, request: Request, user: User, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    return serialize(QuestionService(db(request)).history(question_id, user['_id'], offset, limit))


@router.post('/questions/{question_id}/versions', status_code=201)
def append(question_id: str, body: QuestionVersionInput, request: Request, user: Writer):
    return serialize(QuestionService(db(request)).append(question_id, user['_id'], body.expectedCurrentVersion, body.parentVersion, body.content.model_dump()))


@router.post('/questions/{question_id}/restore', status_code=201)
def restore(question_id: str, body: QuestionRestore, request: Request, user: Writer):
    return serialize(QuestionService(db(request)).append(question_id, user['_id'], body.expectedCurrentVersion, body.version, restore=True))


@router.post('/questions/{question_id}/fork', status_code=201)
def fork(question_id: str, body: QuestionFork, request: Request, user: Writer):
    return serialize(QuestionService(db(request)).fork(question_id, user['_id'], body.version))


@router.patch('/questions/{question_id}/sharing')
def sharing(question_id: str, body: QuestionSharing, request: Request, user: Writer):
    return serialize(QuestionService(db(request)).sharing(question_id, user['_id'], body.usernames, body.expectedRevision))


@router.patch('/questions/{question_id}/archive')
def archive(question_id: str, body: QuestionArchive, request: Request, user: Writer):
    return QuestionService(db(request)).archive(question_id, user['_id'], body.archived, body.expectedRevision)


@router.get('/questions/{question_id}/usage')
def usage(question_id: str, request: Request, user: User, version: int | None = Query(None, ge=1), offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    return serialize(QuestionStatisticsService(db(request)).usage(question_id, user['_id'], version, offset, limit))


@router.get('/questions/{question_id}/statistics')
def statistics(question_id: str, request: Request, user: User, version: int = Query(..., ge=1),
               scope: Literal['mine', 'consented_shared'] = 'mine', mode: Mode = 'current_effective'):
    return serialize(QuestionStatisticsService(db(request)).statistics(question_id, user['_id'], version, scope, mode))


@router.post('/question-banks', status_code=201)
def bank_create(body: BankInput, request: Request, user: Writer):
    return serialize(QuestionBankService(db(request)).create(user['_id'], body.name, body.description))


@router.get('/question-banks')
def bank_list(request: Request, user: User, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    return serialize(QuestionBankService(db(request)).list(user['_id'], offset, limit))


@router.get('/question-banks/{bank_id}')
def bank_detail(bank_id: str, request: Request, user: User):
    return serialize(QuestionBankService(db(request)).detail(bank_id, user['_id']))


@router.patch('/question-banks/{bank_id}')
def bank_patch(bank_id: str, body: BankPatch, request: Request, user: Writer):
    return serialize(QuestionBankService(db(request)).patch(bank_id, user['_id'], body.expectedRevision, body.name, body.description))


@router.put('/question-banks/{bank_id}/items')
def bank_member(bank_id: str, body: BankMember, request: Request, user: Writer):
    return serialize(QuestionBankService(db(request)).member(bank_id, user['_id'], body.expectedRevision, body.questionId, body.pinnedVersion))


@router.delete('/question-banks/{bank_id}/items/{question_id}')
def bank_remove(bank_id: str, question_id: str, request: Request, user: Writer, expectedRevision: int = Query(..., ge=0)):
    return serialize(QuestionBankService(db(request)).member(bank_id, user['_id'], expectedRevision, question_id, remove=True))


@router.post('/surveys/{survey_id}/draft/import-question')
def import_question(survey_id: str, body: QuestionImport, request: Request, user: Writer):
    return serialize(SurveyService(db(request)).import_question(survey_id, user['_id'], body.questionId,
        body.questionVersion, body.expectedRevision, body.replaceLocalId))
