"""Incentive selection logic."""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from agatha.backend.data_persistence import models
from agatha.backend.data_persistence.crud import DataAccessObject

log = logging.getLogger(__name__)
database = DataAccessObject()


@dataclass
class Score:
    """Dataclass to record weighted sum and accumulate possible min & max."""

    weighted_sum: int = 0
    minimum: int = 0
    maximum: int = 0


def get_incentive_types(session: Session) -> List[models.IncentiveType]:
    """Retrieve all available incentives."""
    incentive_types = database.get_all_incentive_types(session)
    return incentive_types


def calculate_score(
    answer_type: models.AnswerType, answer: str
) -> Tuple[int, int, int]:
    """Calculate the score of an answer, taking forward/reverse answer type into account.

    Args:
        answer_type: type of the answer
        answer: the answer to be converted to a score

    Returns:
        a tuple with converted score, possible min & possible max value of this answer type
    """
    if answer_type.most_negative is None or answer_type.most_positive is None:
        log.error("Broken answer type with id %s", answer_type.id)
        raise ValueError("Broken answer type")

    min_score = min(answer_type.most_negative, answer_type.most_positive)
    max_score = max(answer_type.most_negative, answer_type.most_positive)
    try:
        trivial_answer = int(answer)
        return (
            abs(trivial_answer - answer_type.most_negative) + min_score,
            min_score,
            max_score,
        )
    except ValueError as err:
        if answer_type.most_negative == 0 and answer_type.most_positive == 0:
            # answer type with most_xxx values set to 0 are meant to be skipped
            log.debug("Skipped free text answer")
            return 0, 0, 0
        raise err


def normalize_and_select(score_dict: Dict[int, Score]) -> int:
    """Normalize a score group with min-max normalization, then select the one with \
    the highest score.

    Args:
        score_dict: a dict with delivery model id or incentive type id as key, and
        its corresponding Score data class

    Returns:
        the id with the highest score
    """
    selected: Tuple[int, float] = (0, -1)  # (id,  normalized score)
    for config_id, score in score_dict.items():
        normalized = 0.0
        if (score_range := score.maximum - score.minimum) > 0:
            normalized = (score.weighted_sum - score.minimum) / score_range
        if normalized > selected[1]:
            selected = (config_id, normalized)
    return selected[0]


def calculate_delivery_and_incentive(
    answers: List[models.QuestionAnswer],
) -> Optional[Dict[str, int]]:
    """Calculate the delivery model and incentive type based on user survey result.

    Args:
        answers: answers given by a user for a survey.

    Returns:
        a dict containing selected delivery model and incentive type.
    """
    delivery_scores: Dict[int, Score] = defaultdict(Score)
    incentive_scores: Dict[int, Score] = defaultdict(Score)

    for answer in answers:
        question = answer.question
        if answer.answer is not None and question.weight is not None:
            score, min_value, max_value = calculate_score(
                question.answer_type, answer.answer
            )
        else:
            log.error("Empty answer field")
            continue
        if question.factor.d_id is not None:
            score_record = delivery_scores[question.factor.d_id]
        if question.factor.i_id is not None:
            score_record = incentive_scores[question.factor.i_id]
        score_record.weighted_sum += question.weight * score
        score_record.minimum += question.weight * min_value
        score_record.maximum += question.weight * max_value

    if len(delivery_scores) == 0 or len(incentive_scores) == 0:
        log.error(
            "Cannot calculate complete configuration because there's no quantifiable "
            "answer for at least one configuration category"
        )
        return None

    config = {
        "delivery_model": normalize_and_select(delivery_scores),
        "incentive_type": normalize_and_select(incentive_scores),
    }
    return config


def get_employee_incentive(
    revolori_id: str, session: Session
) -> Optional[models.EmployeeModel]:
    """Retrieve intentive type for a specific employee.

    Args:
        revolori_id: employee id from Revolori SSO.

    Returns:
        EmployeeModel if exists, otherwise None.
    """
    if employee_model := database.get_employee_model_by_revolori_id(
        session, revolori_id
    ):
        return employee_model

    answers = database.get_answered_questions_by_revolori_id(session, revolori_id)
    if len(answers) == 0:
        log.info("Employee %s has not completed user survey yet", revolori_id)
        return None

    log.info("Calculating configuration for employee %s", revolori_id)
    if configuration := calculate_delivery_and_incentive(answers):
        employee_model = database.create_employee_model_by_ids(
            session,
            revolori_id=revolori_id,
            delivery_model_id=configuration["delivery_model"],
            incentive_type_id=configuration["incentive_type"],
        )
        return employee_model
    return None
