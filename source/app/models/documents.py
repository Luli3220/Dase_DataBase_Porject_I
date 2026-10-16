"""Persisted domain models with an explicit, lossless BSON mapping."""
from typing import Literal
from bson import ObjectId
from pydantic import ConfigDict, Field, AwareDatetime
from app.models.domain import StrictModel, Question, VersionSettings, Answer


class Document(StrictModel):
    model_config = ConfigDict(extra='forbid', strict=True, arbitrary_types_allowed=True, populate_by_name=True)
    id: ObjectId = Field(alias='_id',default_factory=ObjectId)
    schemaVersion: Literal[1] = 1

    def to_bson(self):
        result=self.model_dump(by_alias=True)
        if hasattr(self,'questions'):
            result['questions']=[q.model_dump(exclude_none=True) for q in self.questions]
        return result


class UserDocument(Document):
    username: str
    passwordHash: str
    createdAt: AwareDatetime
    sessionVersion: int = Field(default=1,ge=1)


class SurveyDocument(Document):
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
