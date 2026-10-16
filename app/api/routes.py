from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Request, Response, Query
from app.models.domain import Credentials, SurveyInput, SurveyPatch, DraftInput, PublishInput, SubmissionInput, serialize
from app.core.security import current_user, csrf_user, set_session, session_data, COOKIE
from app.services.auth import AuthService
from app.services.surveys import SurveyService
from app.services.submissions import SubmissionService
from app.services.statistics import StatisticsService
from app.db.mongo import oid
from app.rules.engine import validate_question_config

router = APIRouter(prefix="/api")
User = Annotated[dict, Depends(current_user)]
Writer = Annotated[dict, Depends(csrf_user)]
Mode = Literal["current_effective", "historical_raw"]


def db(request): return request.app.state.db
def svc(request): return SurveyService(db(request))
def profile(user): return {"id": str(user["_id"]), "username": user["username"], "createdAt": serialize(user["createdAt"])}


@router.post("/auth/register", status_code=201)
def register(body: Credentials, request: Request, response: Response):
    user = AuthService(db(request)).register(body.username, body.password)
    return {"user": profile(user), "csrfToken": set_session(request, response, user)}


@router.post("/auth/login")
def login(body: Credentials, request: Request, response: Response):
    user = AuthService(db(request)).login(body.username, body.password)
    return {"user": profile(user), "csrfToken": set_session(request, response, user)}


@router.post("/auth/logout")
def logout(request: Request, response: Response, user: Writer):
    db(request).users.update_one({"_id": user["_id"]}, {"$inc": {"sessionVersion": 1}})
    response.delete_cookie(COOKIE, path="/", secure=request.app.state.settings.cookie_secure, httponly=True, samesite="lax")
    return {"ok": True}


@router.get("/me")
def me(request: Request, user: User):
    return {"user": profile(user), "csrfToken": session_data(request)["csrf"]}


@router.get("/me/submissions")
def mine(request: Request, user: User, surveyId: str | None = None, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    query = {"respondentId": user["_id"]}
    if surveyId: query["surveyId"] = oid(surveyId)
    rows = db(request).submissions.find(query, {"surveyId": 1, "surveyVersion": 1, "submittedAt": 1}).sort([("submittedAt", -1), ("_id", -1)]).skip(offset).limit(limit)
    return serialize({"items": list(rows), "total": db(request).submissions.count_documents(query)})


@router.post("/surveys", status_code=201)
def create(body: SurveyInput, request: Request, user: Writer):
    return serialize(svc(request).create(user["_id"], body.model_dump()))


@router.get("/surveys")
def surveys(request: Request, user: User, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    q = {"ownerId": user["_id"]}
    return serialize({"items": list(db(request).surveys.find(q).sort([("createdAt", -1), ("_id", -1)]).skip(offset).limit(limit)), "total": db(request).surveys.count_documents(q)})


@router.get("/surveys/{survey_id}")
def survey(survey_id: str, request: Request, user: User): return serialize(svc(request).owned(survey_id, user["_id"]))


@router.patch("/surveys/{survey_id}")
def patch(survey_id: str, body: SurveyPatch, request: Request, user: Writer):
    return serialize(svc(request).patch(survey_id, user["_id"], body.model_dump(exclude_unset=True)))


@router.get("/surveys/{survey_id}/versions")
def versions(survey_id: str, request: Request, user: User):
    s = svc(request).owned(survey_id, user["_id"])
    return serialize({"publishedVersion": s["publishedVersion"], "draftVersion": s["draftVersion"], "items": list(db(request).survey_versions.find({"surveyId": s["_id"]}).sort("version", -1))})


@router.get("/surveys/{survey_id}/draft")
def draft(survey_id: str, request: Request, user: User): return serialize(svc(request).draft(survey_id, user["_id"]))


@router.put("/surveys/{survey_id}/draft")
def edit(survey_id: str, body: DraftInput, request: Request, user: Writer): return serialize(svc(request).edit(survey_id, user["_id"], body.model_dump(exclude_none=True)))


@router.post("/surveys/{survey_id}/draft-from-published")
def derive(survey_id: str, request: Request, user: Writer): return serialize(svc(request).derive(survey_id, user["_id"]))


@router.post("/surveys/{survey_id}/publish")
def publish(survey_id: str, body: PublishInput, request: Request, user: Writer):
    result = svc(request).publish(survey_id, user["_id"], body.expectedRevision)
    return serialize({**result, "publicUrl": request.app.state.settings.base_url.rstrip("/") + "/survey/" + result["publicId"]})


@router.post("/surveys/{survey_id}/close")
def close(survey_id: str, request: Request, user: Writer): return serialize(svc(request).close(survey_id, user["_id"]))


@router.get("/surveys/{survey_id}/preview")
def preview(survey_id: str, request: Request, user: User):
    version = svc(request).draft(survey_id, user["_id"])
    validate_question_config(version["questions"])
    s = svc(request).owned(survey_id, user["_id"])
    return {"title": s["title"], "description": s["description"], "surveyVersion": version["version"], "settings": version["settings"], "questions": version["questions"]}


@router.get("/public/surveys/{public_id}")
def public(public_id: str, request: Request, user: User):
    s, v = svc(request).public(public_id)
    return serialize({"publicId": s["publicId"], "title": s["title"], "description": s["description"], "deadlineAt": s["deadlineAt"],
        "surveyVersion": v["version"], "settings": v["settings"], "questions": v["questions"], "submissionPolicy": s["submissionPolicy"]})


@router.post("/public/surveys/{public_id}/submissions", status_code=201)
def submit(public_id: str, body: SubmissionInput, request: Request, user: Writer):
    return SubmissionService(db(request)).submit(public_id, user["_id"], body.model_dump())


@router.get("/surveys/{survey_id}/submissions")
def submissions(survey_id: str, request: Request, user: User, version: int | None = Query(None, ge=1), mode: Mode = "historical_raw", offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    return serialize(SubmissionService(db(request)).list_owner(survey_id, user["_id"], version, mode, offset, limit))


@router.get("/surveys/{survey_id}/statistics")
def statistics(survey_id: str, request: Request, user: User, version: int | None = Query(None, ge=1), mode: Mode = "current_effective", offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    return serialize(StatisticsService(db(request)).statistics(survey_id, user["_id"], version, mode, offset=offset, limit=limit))


@router.get("/surveys/{survey_id}/questions/{question_id}/statistics")
def question_statistics(survey_id: str, question_id: str, request: Request, user: User, version: int | None = Query(None, ge=1), mode: Mode = "current_effective", offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    return serialize(StatisticsService(db(request)).statistics(survey_id, user["_id"], version, mode, question_id, offset, limit))
