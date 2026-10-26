"""Persisted domain models with an explicit, lossless BSON mapping."""
from typing import Literal
from bson import ObjectId
from pydantic import ConfigDict, Field, AwareDatetime
from app.models.domain import StrictModel, Question, VersionSettings, Answer, QuestionContent


class Document(StrictModel):
    model_config = ConfigDict(extra='forbid', strict=True, arbitrary_types_allowed=True, populate_by_name=True)
    id: ObjectId = Field(alias='_id',default_factory=ObjectId)
    schemaVersion: Literal[1] = 1

    def to_bson(self):
        result=self.model_dump(by_alias=True)
        if hasattr(self,'questions'):
            result['questions']=questions_to_bson([q.model_dump(exclude_none=True) for q in self.questions])
        return result


class UserDocument(Document):
    username: str
    passwordHash: str
    createdAt: AwareDatetime
    sessionVersion: int = Field(default=1,ge=1)


class SurveyDocument(Document):
    statisticsContribution: bool = False
    ownerId: ObjectId
    publicId: str
    title: str
    description: str
    status: Literal['draft','published','closed']
    publishedVersion: int | None
    draftVersion: int | None
    submissionPolicy: Literal['latest_only','multiple']
    deadlineAt: AwareDatetime | None
    createdAt: AwareDatetime
    updatedAt: AwareDatetime
    writeRevision: int = Field(ge=0)
    hasSubmissions: bool


class VersionDocument(Document):
    surveyId: ObjectId
    version: int = Field(ge=1)
    state: Literal['draft','sealed']
    revision: int = Field(ge=0)
    settings: VersionSettings
    questions: list[Question] = Field(max_length=100)
    createdAt: AwareDatetime
    sealedAt: AwareDatetime | None


class SubmissionDocument(Document):
    surveyId: ObjectId
    surveyVersion: int = Field(ge=1)
    respondentId: ObjectId
    anonymousAtSubmission: bool
    requestId: str
    payloadDigest: str
    submittedAt: AwareDatetime
    answers: list[Answer] = Field(max_length=100)


def questions_to_bson(questions):
    from copy import deepcopy
    result = deepcopy(questions)
    for question in result:
        if question.get('source'):
            question['source']['questionId'] = ObjectId(question['source']['questionId'])
    return result


class QuestionDefinitionDocument(Document):
    ownerId: ObjectId
    currentVersion: int = Field(ge=1)
    visibility: Literal['private', 'shared'] = 'private'
    sharedWith: list[ObjectId] = Field(default_factory=list, max_length=100)
    forkedFrom: dict | None = None
    archived: bool = False
    revision: int = Field(default=0, ge=0)
    createdAt: AwareDatetime
    updatedAt: AwareDatetime


class QuestionVersionDocument(Document):
    questionId: ObjectId
    version: int = Field(ge=1)
    parentVersion: int | None = None
    changeType: Literal['create', 'update', 'restore']
    restoredFromVersion: int | None = None
    content: QuestionContent
    createdBy: ObjectId
    createdAt: AwareDatetime


class QuestionBankDocument(Document):
    ownerId: ObjectId
    name: str
    description: str
    items: list[dict] = Field(default_factory=list, max_length=200)
    revision: int = Field(default=0, ge=0)
    createdAt: AwareDatetime
    updatedAt: AwareDatetime
