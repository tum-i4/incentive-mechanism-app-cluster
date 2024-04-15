"""Study app router."""

import logging
import random
from contextlib import contextmanager

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette import status

from agatha.backend.data_persistence.crud import DataAccessObject
from agatha.backend.data_persistence.study_crud import StudyDataAccessObject
from agatha.util import logger
from agatha.util.consts import BASE_DIR
from agatha.web_services.study.vignette_logic import (
    StudyAlreadyParticipated,
    UserStudyService,
    VignetteAnswerBuildPlan,
)
from agatha.web_services.temp_user_management.user_management_logic import (
    TemporaryUserManagement,
)
from agatha.web_services.user_survey.app import survey_exceptions_handled
from agatha.web_services.user_survey.survey_logic import (
    AnswerBuildPlan,
    UserSurveyService,
)

URL_PREFIX = "/study"
SURVEY_ID = 3

templates = Jinja2Templates(directory=BASE_DIR / "web_services/templates")

router = APIRouter(prefix=URL_PREFIX, tags=["study_app_app"])
study_database = StudyDataAccessObject()
database = DataAccessObject()
user_management = TemporaryUserManagement()
user_study_service = UserStudyService()
user_survey_service = UserSurveyService()

logger.setup_logger()
log = logging.getLogger(__name__)


@contextmanager
def study_exceptions_handled():
    """Reraise study exception thrown inside the context with corresponding HTTPExceptions."""
    try:
        yield
    except StudyAlreadyParticipated as exc:
        raise HTTPException(403, "User has already participated in the study") from exc


@router.get("/new")
def new_study_participant(db: Session = Depends(study_database)):
    """Create a new user and redirect to study."""
    new_user = user_management.create_new_user(db)
    return RedirectResponse(f"{URL_PREFIX}/{new_user.uuid}")


@router.get("/{user_uuid}")
def user_study(user_uuid: str):
    """User study entry point."""
    return RedirectResponse(f"{URL_PREFIX}/1/{user_uuid}")


@router.get("/1/{user_uuid}", name="Get user study form")
def personal_data_form(request: Request, user_uuid: str):
    """Render demographic data form."""
    questions = [
        {
            "name": "age",
            "type": "input",
            "input_type": "number",
            "max": 200,
            "min": 1,
            "required": True,
        },
        {
            "name": "gender",
            "type": "radio",
            "options": ["male", "female", "other", "prefer not to say"],
            "required": True,
        },
        {
            "name": "zip code",
            "type": "input",
            "input_type": "number",
            "min": 0,
            "required": True,
        },
        {
            "name": "country",
            "type": "input",
            "input_type": "text",
            "max": 60,
            "min": 3,
            "required": True,
        },
        {
            "name": "education",
            "type": "select",
            "options": [
                "Less than a high school diploma",
                "High school diploma or equivalent degree",
                "No degree",
                "Bachelor's degree",
                "Master's degree",
            ],
            "required": True,
        },
        {
            "name": "employment status",
            "type": "select",
            "options": [
                "Unemployed",
                "Worker",
                "Employee",
                "Self-employed / contractor",
                "Student",
            ],
            "required": True,
        },
        {
            "name": "average monthly income",
            "type": "input",
            "input_type": "number",
            "min": 0,
            "required": True,
        },
    ]
    return templates.TemplateResponse(
        "study/form.html",
        {
            "request": request,
            "service_name": "study",
            "questions": questions,
            "prefix": f"{URL_PREFIX}/1",
            "user_uuid": user_uuid,
        },
    )


@router.post("/1/{user_uuid}", name="Post user demographic data")
async def submit_form(
    user_uuid: str,
    age: int = Form(),
    gender: str = Form(),
    zip_code: int = Form(),
    country: str = Form(),
    education: str = Form(),
    employment_status: str = Form(),
    average_monthly_income: str = Form(),
    session: Session = Depends(study_database),
):
    """Post user form submission."""
    study_database.add_demographics_to_user(
        session,
        user_uuid,
        {
            "age": age,
            "gender": gender,
            "education": education,
            "zip_code": zip_code,
            "country": country,
            "employment_status": employment_status,
            "avg_current_income": average_monthly_income,
        },
    )
    return RedirectResponse(
        f"{URL_PREFIX}/2/{user_uuid}", status_code=status.HTTP_302_FOUND
    )


@router.get("/1/gadget/{gadget_id}")
def get_gadget(request: Request):
    """Render individual gadget templated in agatha layout."""
    choices = [
        {"type": "incorrect", "name": "incorrect1.jpg"},
        {"type": "incorrect", "name": "incorrect2.jpg"},
        {"type": "incorrect", "name": "incorrect3.jpg"},
        {"type": "correct", "name": "correct.jpg"},
    ]
    random.shuffle(choices)
    return templates.TemplateResponse(
        "gadgets/test_gadget.html",
        {
            "request": request,
            "choices": choices,
        },
    )


@router.get("/2/{user_uuid}")
def get_survey(request: Request, user_uuid: str, db: Session = Depends(database)):
    """Retrieve user survey."""
    with survey_exceptions_handled():
        questions = user_survey_service.start_survey(db, SURVEY_ID, user_uuid)

    return templates.TemplateResponse(
        "user_survey/survey.html",
        {
            "request": request,
            "service_name": "user survey",
            "questions": questions,
            "render_response": True,
        },
    )


@router.post("/2/{user_uuid}")
async def submit_survey(
    request: Request, user_uuid: str, db: Session = Depends(database)
):
    """Intermediate page between survey completion and vignette."""
    user_data = await request.json()
    log.debug("user submission: %s", user_data)
    answers = [AnswerBuildPlan(**kwargs) for kwargs in user_data]
    with survey_exceptions_handled():
        user_survey_service.submit_survey(
            db=db, survey_id=SURVEY_ID, revolori_id=user_uuid, answers=answers
        )
    return templates.TemplateResponse(
        "study/inter.html",
        {
            "request": request,
            "service_name": "study",
            "vignette_url": f"{URL_PREFIX}/3/{user_uuid}",
        },
    )


@router.get("/3/{user_uuid}")
def vignettes(
    request: Request,
    user_uuid: str,
    study_db: Session = Depends(study_database),
    survey_db: Session = Depends(database),
):
    """Render vignette study."""
    with study_exceptions_handled():
        vignette_dict, questions = user_study_service.start_study(
            survey_db, study_db, user_uuid
        )
    return templates.TemplateResponse(
        "study/study.html",
        {
            "request": request,
            "service_name": "user study",
            "questions": questions,
            "vignettes": vignette_dict,
        },
    )


@router.post("/3/{user_uuid}", status_code=201)
async def post_vignettes_data(
    request: Request, user_uuid: str, db: Session = Depends(study_database)
):
    """Save the given study answers to the database."""
    user_data = await request.json()
    log.debug("user submission: %s", user_data)
    answers = [VignetteAnswerBuildPlan(**kwargs) for kwargs in user_data]
    with study_exceptions_handled():
        user_study_service.submit_study(db=db, uuid=user_uuid, answers=answers)
