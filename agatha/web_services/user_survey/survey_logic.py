"""
API to create and process User Surveys.

Classes:
    SurveyException
        InvalidSurveyId
        SurveyAlreadyAnswered
    AnswerBuildPlan
    UserSurveyService
"""

from dataclasses import dataclass
from typing import List

from sqlalchemy.orm import Session

from agatha.backend.data_persistence.crud import DataAccessObject
from agatha.backend.data_persistence.models import Question, Survey
from agatha.util import singleton


class SurveyException(Exception):
    """Base class for all exceptions related to the Survey module."""


class InvalidSurveyId(SurveyException):
    """Passed invalid SurveyID."""


class SurveyAlreadyAnswered(SurveyException):
    """Survey has already been answered."""


@dataclass
class AnswerBuildPlan:
    """Necessary information to create a QuestionAnswer in the given context."""

    question_id: int
    answer: str


@singleton
class UserSurveyService:
    """Survey App API to start and process user surveys."""

    def __init__(self):
        """Init UserSurveyService with DataAccessObject."""
        self.dao = DataAccessObject()

    def _guard_survey_access(
        self, db: Session, survey_id: int, revolori_id: str
    ) -> Survey:
        """Guard if survey exists, hasn't been filled out and employee can take survey.

        Raises:
            InvalidSurveyId: Provided SurveyID is invalid.
            SurveyAlreadyAnswered: Survey was already answered by employee.
        """
        # Guard if survey exists
        if (survey := self.dao.get_survey_by_id(db, survey_id)) is None:
            raise InvalidSurveyId()

        # Guard if survey has been filled out
        answered_surveys = self.dao.get_answered_surveys_by_revolori_id(db, revolori_id)
        if survey_id in (survey.id for survey in answered_surveys):
            raise SurveyAlreadyAnswered()

        return survey

    def start_survey(
        self,
        db: Session,
        survey_id: int,
        revolori_id: str,
    ) -> List[Question]:
        """Start given survey for given user.

        Raises:
            InvalidSurveyId: Provided SurveyID is invalid.
            SurveyAlreadyAnswered: Survey was already answered by employee.

        Returns:
            List[Question]: List of questions for employee to answer
        """
        survey = self._guard_survey_access(db, survey_id, revolori_id)

        return survey.questions

    def submit_survey(
        self,
        db: Session,
        survey_id: int,
        revolori_id: str,
        answers: List[AnswerBuildPlan],
    ):
        """Submit the given survey.

        Args:
            answerers (List[Question]): Answers provided by employee.

        Raises:
            InvalidSurveyId: Provided SurveyID is invalid.
            SurveyAlreadyAnswered: Survey was already answered by employee.
        """
        self._guard_survey_access(db, survey_id, revolori_id)

        for answer in answers:
            self.dao.create_question_answer_by_q_id(
                db,
                survey_id=survey_id,
                question_id=answer.question_id,
                revolori_id=revolori_id,
                answer=answer.answer,
            )
