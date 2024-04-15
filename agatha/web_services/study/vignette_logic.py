"""API to create and process the vignette based study evaluation."""
from dataclasses import dataclass
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from agatha.backend.data_persistence import study_models
from agatha.backend.data_persistence.study_crud import StudyDataAccessObject
from agatha.backend.incentive_mechanism import incentive
from agatha.backend.study.vignette_generator import generate_vignettes
from agatha.util import singleton


class StudyException(Exception):
    """Base class for all exceptions related to the Study module."""


class StudyAlreadyParticipated(StudyException):
    """User has already participated in study."""


@dataclass
class VignetteAnswerBuildPlan:
    """Necessary information to create a QuestionAnswer in the given context."""

    vignette_id: int
    question_id: int
    answer: str


@singleton
class UserStudyService:
    """Study App API to start and process user studys."""

    def __init__(self):
        """Init UserStudyService with DataAccessObject."""
        self.dao = StudyDataAccessObject()

    def _guard_study_access(self, db: Session, uuid: str):
        """Guard if study hasn't been filled out and employee can take study.

        Raises:
            StudyAlreadyParticipated: user already participated in the study.
        """
        answered_questions = self.dao.get_answered_questions_by_uuid(db, uuid)
        if len(answered_questions) > 0:
            raise StudyAlreadyParticipated()

    def start_study(
        self,
        survey_db: Session,
        study_db: Session,
        uuid: str,
    ) -> Tuple[Dict[str, str], List[study_models.Question]]:
        """Start given study for given user.

        Raises:
            StudyAlreadyParticipated: user already participated in the study.

        Returns:
            List of vignettes
            and questions for user to answer
        """
        self._guard_study_access(study_db, uuid)

        employee_model = incentive.get_employee_incentive(uuid, survey_db)
        delivery_model, incentive_type = (
            (employee_model.delivery_model.name, employee_model.incentive_type.name)
            if employee_model
            else (None, None)
        )
        vignettes = generate_vignettes(
            study_db,
            delivery_model=delivery_model,
            incentive=incentive_type,
        )
        questions = self.dao.get_study_questions(study_db)

        return vignettes, questions

    def submit_study(
        self,
        db: Session,
        uuid: str,
        answers: List[VignetteAnswerBuildPlan],
    ):
        """Submit the given study.

        Args:
            answerers: Answers provided by user.

        Raises:
            StudyAlreadyParticipated: user already participated in the study.
        """
        self._guard_study_access(db, uuid)

        for answer in answers:
            self.dao.add_question_answer_by_uuid(
                db,
                vignette_id=answer.vignette_id,
                question_id=answer.question_id,
                uuid=uuid,
                answer=answer.answer,
            )
