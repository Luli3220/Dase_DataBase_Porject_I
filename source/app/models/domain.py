"""Strict network models; model_dump supplies the embedded BSON representation."""
from typing import Any, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Option(StrictModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    label: str = Field(min_length=1, max_length=300)


class Condition(StrictModel):
    operator: str = Field(max_length=30)
    operand: Any


class Target(StrictModel):
    kind: Literal["question", "end"]
    questionId: str | None = None

    @model_validator(mode="before")
    @classmethod
    def end_has_no_question(cls, value):
        if isinstance(value, dict) and value.get("kind") == "end" and "questionId" in value:
            raise ValueError("end 目标不能提供 questionId（包括 null）")
        return value


class Rule(StrictModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    priority: int = Field(ge=0, le=1000000)
    condition: Condition
    target: Target


class QuestionSource(StrictModel):
    questionId: str = Field(pattern=r"^[a-f0-9]{24}$")
    questionVersion: int = Field(ge=1)

    @field_validator('questionId', mode='before')
    @classmethod
    def bson_id(cls, value):
        from bson import ObjectId
        return str(value) if isinstance(value, ObjectId) else value


class Question(StrictModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    type: Literal["single_choice", "multiple_choice", "text", "number"]
    title: str = Field(min_length=1, max_length=500)
    required: bool = False
    options: list[Option] = Field(default_factory=list, max_length=50)
    validation: dict[str, Any] = Field(default_factory=dict)
    routingRules: list[Rule] = Field(default_factory=list, max_length=20)
    source: QuestionSource | None = None


class VersionSettings(StrictModel):
    anonymous: bool = True


class DraftInput(StrictModel):
    expectedRevision: int = Field(ge=0)
    settings: VersionSettings = Field(default_factory=VersionSettings)
    questions: list[Question] = Field(max_length=100)


class Credentials(StrictModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=10, max_length=128)


class SurveyInput(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    anonymous: bool = True
    submissionPolicy: Literal["latest_only", "multiple"] = "latest_only"
    deadlineAt: AwareDatetime | None = Field(default=None, strict=False)


class SurveyPatch(StrictModel):
    statisticsContribution: bool | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    deadlineAt: AwareDatetime | None = Field(default=None, strict=False)
    submissionPolicy: Literal["latest_only", "multiple"] | None = None


class SurveySaveInput(StrictModel):
    metadata: SurveyPatch
    draft: DraftInput


class PublishInput(StrictModel):
    expectedRevision: int = Field(ge=0)


class Answer(StrictModel):
    questionId: str = Field(min_length=1, max_length=64)
    value: Any


class SubmissionInput(StrictModel):
    surveyVersion: int = Field(ge=1)
    requestId: str = Field(min_length=36, max_length=36)
    answers: list[Answer] = Field(max_length=100)


class QuestionContent(StrictModel):
    type: Literal['single_choice', 'multiple_choice', 'text', 'number']
    title: str = Field(min_length=1, max_length=500)
    required: bool = False
    options: list[Option] = Field(default_factory=list, max_length=50)
    validation: dict[str, Any] = Field(default_factory=dict)


class QuestionCreate(StrictModel):
    content: QuestionContent


class QuestionVersionInput(QuestionCreate):
    expectedCurrentVersion: int = Field(ge=1)
    parentVersion: int = Field(ge=1)


class QuestionRestore(StrictModel):
    expectedCurrentVersion: int = Field(ge=1)
    version: int = Field(ge=1)


class QuestionFork(StrictModel):
    version: int = Field(ge=1)


class QuestionSharing(StrictModel):
    usernames: list[str] = Field(max_length=100)
    expectedRevision: int = Field(ge=0)


class QuestionArchive(StrictModel):
    archived: bool
    expectedRevision: int = Field(ge=0)


class BankInput(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=2000)


class BankPatch(BankInput):
    expectedRevision: int = Field(ge=0)


class BankMember(StrictModel):
    questionId: str = Field(pattern=r'^[a-f0-9]{24}$')
    pinnedVersion: int | None = Field(default=None, ge=1)
    expectedRevision: int = Field(ge=0)


class QuestionImport(StrictModel):
    questionId: str = Field(pattern=r'^[a-f0-9]{24}$')
    questionVersion: int = Field(ge=1)
    expectedRevision: int = Field(ge=0)
    replaceLocalId: str | None = Field(default=None, max_length=64)


def serialize(value):
    from bson import ObjectId
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {k: serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(v) for v in value]
    return value
