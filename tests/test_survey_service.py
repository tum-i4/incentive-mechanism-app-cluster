"""Module to test UserSurveyService."""

from typing import List, Tuple
from unittest.mock import Mock

import pytest
from pytest import fixture
from sqlalchemy.orm import Session

from agatha.backend.data_persistence.crud import DataAccessObject
from agatha.backend.data_persistence.models import EmployeeModel, Question, Survey
from agatha.web_services.user_survey.survey_logic import (
    AnswerBuildPlan,
    InvalidSurveyId,
    SurveyAlreadyAnswered,
    UserSurveyService,
)

DEFAULT_REVOLORI_ID: str = "default@example.com"
"""Revolori id used by fixtures."""

DEFAULT_SURVEY_ID = 0
"""Survey_id used by fixtures."""


@fixture
def base_mock_dao() -> Mock:
    """Mock DataAccessObject returning None on relevant function calls.

    Calls which return None: `get_survey_by_id`, `get_answered_surveys_by_revolori_id`,
    `delete_question_answers`, `create_question_answer_by_q_id`
    """
    mock = Mock(spec=DataAccessObject)
    mock.get_survey_by_id = Mock(return_value=None)
    mock.get_answered_surveys_by_revolori_id = Mock(return_value=None)
    mock.delete_question_answers = Mock(return_value=None)
    mock.create_question_answer_by_q_id = Mock(return_value=None)
    return mock


@fixture
def sample_survey():
    """Sample survey without any Questions and EmployeeModels."""
    return Survey(
        id=DEFAULT_SURVEY_ID,
        name="Test survey",
        description="test survey",
        questions=[],
        employee_models=[],
    )


@fixture
def sample_questions_for_sample_survey(sample_survey) -> List[Question]:
    """List of questions which are added to sample_survey."""
    questions = [
        Question(id=0, question="Sample question", weight=10, surveys=[sample_survey]),
        Question(id=1, question="Another question", weight=5, surveys=[sample_survey]),
    ]
    return questions


@fixture
def sample_survey_with_employee(
    sample_survey, sample_questions_for_sample_survey
) -> Mock:
    """Sample survey with 1 EmployeeModel and 2 Questions (sample_questions_for_sample_survey).

    Uses DEFAULT_REVOLORI_ID for EmployeeModel.
    """
    sample_survey.questions = sample_questions_for_sample_survey
    sample_survey.employee_models = [
        EmployeeModel(revolori_id=DEFAULT_REVOLORI_ID, surveys=[sample_survey])
    ]
    return sample_survey


@fixture
def mock_survey_dao(sample_survey_with_employee, base_mock_dao) -> Mock:
    """Mock dao with a single survey that is not filled out.

    For Survey specification see `sample_survey_with_employee`
    """
    mock = base_mock_dao
    mock.get_survey_by_id = Mock(return_value=sample_survey_with_employee)
    mock.get_answered_surveys_by_revolori_id = Mock(return_value=[])
    return mock


@fixture
def mock_survey_filled_out_dao(sample_survey_with_employee, mock_survey_dao) -> Mock:
    """mock_survey_dao with an answered survey."""
    mock = mock_survey_dao
    mock.get_answered_surveys_by_revolori_id = Mock(
        return_value=[sample_survey_with_employee],
    )
    return mock


@fixture
def sample_answers() -> List[AnswerBuildPlan]:
    """2 Sample questions.

    id: 0, 1
    answer: 1, 2
    """
    return [
        AnswerBuildPlan(question_id=0, answer="1"),
        AnswerBuildPlan(question_id=1, answer="2"),
    ]


def user_service_with_mock_dao(mock_dao: Mock) -> Tuple[UserSurveyService, Session]:
    """Create a UserSurveyService with self.dao mocked by the given mock and a Mock Session."""
    survey_service = UserSurveyService()
    survey_service.dao = mock_dao
    return survey_service, Mock(spec=Session)


class TestStartSurvey:
    """All tests for UserSurveyService.start_survey."""

    def test_no_survey(self, base_mock_dao: Mock):
        """Tests InvalidSurveyId getting raised when no survey is found."""
        survey_service, session = user_service_with_mock_dao(base_mock_dao)
        with pytest.raises(InvalidSurveyId):
            survey_service.start_survey(db=session, survey_id=0, revolori_id="")

    def test_survey_filled_out(self, mock_survey_filled_out_dao):
        """Tests SurveyAlreadyAnswered getting raised if the survey is already filled out."""
        survey_service, session = user_service_with_mock_dao(mock_survey_filled_out_dao)
        with pytest.raises(SurveyAlreadyAnswered):
            survey_service.start_survey(db=session, survey_id=0, revolori_id="")

    def test_survey_good_case(
        self, mock_survey_dao, sample_questions_for_sample_survey
    ):
        """Test that the questions are returned for the good case."""
        survey_service, session = user_service_with_mock_dao(mock_survey_dao)
        assert (
            survey_service.start_survey(
                session, survey_id=0, revolori_id=DEFAULT_REVOLORI_ID
            )
            == sample_questions_for_sample_survey
        )


class TestSubmitSurvey:
    """All tests for UserSurveyService.submit_survey."""

    def test_no_survey(
        self,
        base_mock_dao: Mock,
    ):
        """Tests InvalidSurveyId getting raised when no survey is found."""
        survey_service, session = user_service_with_mock_dao(base_mock_dao)
        with pytest.raises(InvalidSurveyId):
            survey_service.submit_survey(
                db=session, survey_id=0, revolori_id="", answers=[]
            )

    def test_survey_filled_out(self, mock_survey_filled_out_dao):
        """Tests SurveyAlreadyAnswered getting raised if the survey is already filled out."""
        survey_service, session = user_service_with_mock_dao(mock_survey_filled_out_dao)
        with pytest.raises(SurveyAlreadyAnswered):
            survey_service.submit_survey(
                db=session, survey_id=0, revolori_id="", answers=[]
            )

    @staticmethod
    def call_to_list(call_) -> List:
        """Return a list of all arguments given, regardless of being positional or keyword."""
        return list(call_.args) + list(call_.kwargs.values())

    def assert_create_question_call(
        self,
        mock_dao: Mock,
        sample_answers: List[AnswerBuildPlan],
        session: Session,
        survey_id: int,
        revolori_id: str,
    ):
        """Asserts all given answers were added to the mock_dao."""
        for answer in sample_answers:
            mock_dao.create_question_answer_by_q_id.assert_any_call(
                session,
                survey_id=survey_id,
                question_id=answer.question_id,
                revolori_id=revolori_id,
                answer=answer.answer,
            )

    def test_submit_answer(
        self,
        mock_survey_dao,
        sample_survey_with_employee,
        sample_answers,
    ):
        """Test successfully submitting answers for a survey."""
        survey_service, session = user_service_with_mock_dao(mock_survey_dao)
        survey_service.submit_survey(
            session,
            survey_id=DEFAULT_SURVEY_ID,
            revolori_id=DEFAULT_REVOLORI_ID,
            answers=sample_answers,
        )
        self.assert_create_question_call(
            mock_survey_dao,
            sample_answers,
            session,
            DEFAULT_SURVEY_ID,
            DEFAULT_REVOLORI_ID,
        )
