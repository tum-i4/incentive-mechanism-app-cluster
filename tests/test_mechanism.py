"""Test module incentive_mechanism."""

from itertools import zip_longest
from typing import List, Union
from unittest.mock import Mock

from pytest import fixture
from sqlalchemy.orm import Session

from agatha.backend.data_persistence import models
from agatha.backend.incentive_mechanism.incentive import (
    Score,
    calculate_score,
    get_employee_incentive,
    normalize_and_select,
)

GIFT_MODEL = models.DeliveryModel(
    id=1,
    name="gift",
)


LOSS_MODEL = models.DeliveryModel(
    id=2,
    name="loss",
)


TRAINING_INCENTIVE = models.IncentiveType(
    id=1,
    name="training",
)


GIFT_CARD_INCENTIVE = models.IncentiveType(
    id=2,
    name="gift card",
)


IN_DB_EMPLOYEE = models.EmployeeModel(
    revolori_id="1",
    delivery_model=GIFT_MODEL,
    incentive_type=TRAINING_INCENTIVE,
)


CONFIG_OPTIONS: List[Union[models.DeliveryModel, models.IncentiveType]] = [
    GIFT_MODEL,
    LOSS_MODEL,
    TRAINING_INCENTIVE,
    GIFT_CARD_INCENTIVE,
]

ANSWER_TYPES = [
    models.AnswerType(
        id=1,
        short_name="likert-7",
        most_negative=1,
        most_positive=7,
    ),
    models.AnswerType(
        id=2,
        short_name="likert-5-reverse",
        most_negative=5,
        most_positive=1,
    ),
    models.AnswerType(
        id=3,
        short_name="likert-5",
        most_negative=1,
        most_positive=5,
    ),
    models.AnswerType(
        id=4,
        short_name="likert-7-reverse",
        most_negative=7,
        most_positive=1,
    ),
    models.AnswerType(
        id=5,
        short_name="free_text",
        most_negative=0,
        most_positive=0,
    ),
]


@fixture
def factors() -> List[models.Factor]:
    """All available factors."""
    all_factors = []
    for i, opt in zip_longest(range(1, 6), CONFIG_OPTIONS, fillvalue=GIFT_MODEL):
        all_factors.append(
            models.Factor(
                id=i if isinstance(i, int) else 0,
                name=f"{opt.name} factor",
                d_id=opt.id if isinstance(opt, models.DeliveryModel) else None,
                i_id=opt.id if isinstance(opt, models.IncentiveType) else None,
            )
        )
    return all_factors


@fixture
def question_answers(factors) -> List[models.QuestionAnswer]:
    """Example question answers."""
    answer_values = [6, 2, 4, 3, "icecream"]
    weights = [30, 70, 60, 40, 0]
    answers = []
    for answer_type, factor, answer_value, weight in zip(
        ANSWER_TYPES, factors, answer_values, weights
    ):
        answers.append(
            models.QuestionAnswer(
                s_id=0,
                revolori_id="2",
                answer=str(answer_value),
                question=models.Question(
                    weight=weight,
                    factor=factor,
                    answer_type=answer_type,
                ),
            )
        )
    return answers


@fixture
def mock_employee_in_db_dao() -> Mock:
    """Mock DAO when queried EmployeeModel is already in database."""
    mock = Mock(spec=Session)
    mock.get = Mock(return_value=IN_DB_EMPLOYEE)
    return mock


@fixture
def mock_no_data_dao() -> Mock:
    """Mock DAO when no model and no survey results available."""
    mock = Mock(spec=Session)
    mock.get = Mock(return_value=None)
    mock.query.return_value.filter.return_value.all.return_value = []
    return mock


@fixture
def mock_calculable_employee_dao(question_answers) -> Mock:
    """Mock DAO when the configuration of an employee can be calculated."""
    mock = Mock(spec=Session)
    mock.get = Mock(return_value=None)
    mock.query.return_value.filter.return_value.all.return_value = question_answers
    return mock


def test_employee_in_db(mock_employee_in_db_dao):
    """Test when the employee model already in database."""
    fetched = get_employee_incentive("1", mock_employee_in_db_dao)
    mock_employee_in_db_dao.get.assert_called_once_with(models.EmployeeModel, "1")
    assert fetched == IN_DB_EMPLOYEE


def test_employee_no_data(mock_no_data_dao):
    """Test when no model and no survey results available."""
    fetched = get_employee_incentive("2", mock_no_data_dao)
    mock_no_data_dao.get.assert_called_once_with(models.EmployeeModel, "2")
    mock_no_data_dao.query.assert_called_once_with(models.QuestionAnswer)
    assert fetched is None


def test_calculable_employees(mock_calculable_employee_dao):
    """Test when configuration of an employee can be calculated."""
    fetched = get_employee_incentive("2", mock_calculable_employee_dao)
    mock_calculable_employee_dao.get.assert_called_once_with(models.EmployeeModel, "2")
    mock_calculable_employee_dao.query.assert_called_once_with(models.QuestionAnswer)
    assert fetched.revolori_id == "2"
    assert fetched.d_id == 1
    assert fetched.i_id == 1


def test_calculate_score():
    """Test calculate_score with forward, reward and free text answers."""
    likert_7, likert_5_reverse, _, _, free_text = ANSWER_TYPES
    assert calculate_score(likert_7, 5) == (5, 1, 7)
    assert calculate_score(likert_5_reverse, 2) == (4, 1, 5)
    assert calculate_score(free_text, "icecream") == (0, 0, 0)


def test_normalize_and_select():
    """Test normalize_and_select with an example\
        whose absolute max and normalized max differentiate."""
    score_a = Score(
        weighted_sum=50,
        minimum=10,
        maximum=60,
    )
    score_b = Score(weighted_sum=60, minimum=50, maximum=120)
    assert normalize_and_select({1: score_a, 2: score_b}) == 1
