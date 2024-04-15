"""Routes for the user survey."""
import logging
from contextlib import contextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from agatha.backend.data_persistence.crud import DataAccessObject
from agatha.util import logger
from agatha.util.consts import BASE_DIR
from agatha.web_services.user_survey.survey_logic import (
    AnswerBuildPlan,
    InvalidSurveyId,
    SurveyAlreadyAnswered,
    UserSurveyService,
)

app = FastAPI(tags=["user_survey_app"])
templates = Jinja2Templates(directory=BASE_DIR / "web_services/templates")

logger.setup_logger()
log = logging.getLogger(__name__)

database = DataAccessObject()
user_survey_service = UserSurveyService()


@contextmanager
def survey_exceptions_handled():
    """Reraise survey exception thrown inside the context with corresponding HTTPExceptions."""
    try:
        yield
    except InvalidSurveyId as exc:
        raise HTTPException(404, "Invalid Survey ID") from exc
    except SurveyAlreadyAnswered as exc:
        raise HTTPException(403, "User has already answered the survey") from exc


@app.get("/{survey_id}/{revolori_id}", response_class=HTMLResponse)
def get_survey(
    request: Request, survey_id: int, revolori_id: str, db: Session = Depends(database)
):
    """Retrieve survey with id={survey_id}."""
    with survey_exceptions_handled():
        questions = user_survey_service.start_survey(db, survey_id, revolori_id)

    return templates.TemplateResponse(
        "user_survey/survey.html",
        {
            "request": request,
            "service_name": "user survey",
            "questions": questions,
            "render_response": False,
        },
    )


@app.post("/{survey_id}/{revolori_id}", status_code=201)
async def post_survey_data(
    request: Request, survey_id: int, revolori_id: str, db: Session = Depends(database)
):
    """Save the given survey answers to the database."""
    user_data = await request.json()
    log.debug("user submission: %s", user_data)
    answers = [AnswerBuildPlan(**kwargs) for kwargs in user_data]
    with survey_exceptions_handled():
        user_survey_service.submit_survey(
            db=db, survey_id=survey_id, revolori_id=revolori_id, answers=answers
        )
