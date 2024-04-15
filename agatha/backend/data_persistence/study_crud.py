"""Provides CRUD data access to the SQLAlchemy database for the user study."""

from collections import defaultdict
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from agatha.backend.data_persistence import study_models
from agatha.backend.data_persistence.data_access_object import AbstractDataAccessObject
from agatha.util import singleton


@singleton
class StudyDataAccessObject(AbstractDataAccessObject):
    """Singleton class to interact with study-database."""

    SQLALCHEMY_DATABASE_URL = "sqlite:///./agatha_study.db"

    def __init__(self):
        """Init database in parent class."""
        super().__init__(self.SQLALCHEMY_DATABASE_URL, study_models.StudyBase)

    def create_or_update_object_in_db(self, db: Session, obj: study_models.StudyBase):
        """Create or update object in database.

        If some arguments are not specified, that can be auto filled, the object will be returned updated.
        Example: id's are often left to auto-generation

        Args:
            db: an open database session
            obj: any object from a subclass of Base

        Returns:
            study_models.Base: returns the same object updated with the values written to the database.
        """
        db.add(obj)
        db.commit()
        db.refresh(obj)

    def create_user_by_uuid(
        self, db: Session, uuid: str, email: Optional[str] = None
    ) -> study_models.User:
        """Create user in database.

        Args:
            db: an open database session
            uuid: a unique identifier for the user
            email: optional - the email address of the user

        Returns:
            study_models.User: returns the user object created in the database.
        """
        user = study_models.User(uuid=uuid, email=email)
        self.create_or_update_object_in_db(db, user)
        return user

    def add_question_answer_by_uuid(
        self,
        db: Session,
        vignette_id: str,
        question_id: int,
        uuid: str,
        answer: str,
    ):
        """Store new question answer in database by uuid."""
        study_result = db.query(study_models.StudyResult).get(uuid)
        if not study_result:
            study_result = study_models.StudyResult(u_id=uuid)
        study_result.question_answers.append(
            study_models.QuestionAnswer(
                vignette_id=vignette_id,
                q_id=question_id,
                answer=answer,
            )
        )
        self.create_or_update_object_in_db(db, study_result)
        return study_result

    def add_feedback_by_uuid(
        self,
        db: Session,
        uuid: str,
        feedback01: Optional[str],
        feedback02: Optional[str],
        feedback03: Optional[str],
    ):
        """Store new question answer in database by uuid."""
        study_result = db.query(study_models.StudyResult).get(uuid)
        if not study_result:
            study_result = study_models.StudyResult(u_id=uuid)
        study_result.feedback01 = feedback01
        study_result.feedback02 = feedback02
        study_result.feedback03 = feedback03
        self.create_or_update_object_in_db(db, study_result)
        return study_result

    def create_study(
        self,
        db: Session,
        vignette_template: str,
        name: str,
        description: Optional[str] = None,
    ) -> study_models.Study:
        """Create study in database.

        Args:
            db: an open database session
            vignette_template: the template for the vignette
            name: optional name of study
            description: optional description of study

        Returns:
            study_models.Study: returns the study object created in the database.
        """
        study = study_models.Study(
            name=name,
            description=description,
            vignette_template=vignette_template,
        )
        self.create_or_update_object_in_db(db, study)
        return study

    def add_vignette_factor(
        self, db: Session, factor: str, levels: Dict[str, str]
    ) -> List[study_models.VignetteVariable]:
        """Create vignette variable in database.

        Args:
            db: an open database session
            factor: name of factor
            levels: dict containing all levels of the factor mapped to the text
        """
        vignette_variables: List[study_models.VignetteVariable] = []
        for level, text in levels.items():
            vignette_variable = study_models.VignetteVariable(
                factor=factor, level=level, text=text
            )
            self.create_or_update_object_in_db(db, vignette_variable)
            vignette_variables.append(vignette_variable)
        return vignette_variables

    def add_vignette_text_by_factor_and_level(
        self, db: Session, factor: str, level: str, text: str
    ) -> study_models.VignetteVariable:
        """Create vignette variable in database.

        Args:
            db: an open database session
            factor: the factor of the vignette variable
            level: the level of the vignette variable
            text: the text of the vignette variable

        Returns:
            study_models.VignetteVariable: returns the vignette variable object created in the database.
        """
        vignette_variable = study_models.VignetteVariable(
            factor=factor, level=level, text=text
        )
        self.create_or_update_object_in_db(db, vignette_variable)
        return vignette_variable

    def create_answer_type(
        self,
        db: Session,
        short_name: str,
        description: Optional[str],
        most_positive: int,
        most_negative: int,
    ) -> study_models.AnswerType:
        """Save new answer type to database.

        Args:
            db: an open database session
            short_name: short name for answer-type
            description: description of answer-type
            most_positive: most positive answer among all possibilities
            most_negative: most negative answer among all possibilities

        Returns:
            study_models.AnswerType: returns created object
        """
        answer_type = study_models.AnswerType(
            short_name=short_name,
            description=description,
            most_positive=most_positive,
            most_negative=most_negative,
        )
        self.create_or_update_object_in_db(db, answer_type)
        return answer_type

    def create_question_by_id(
        self,
        db: Session,
        question: str,
        answer_type_id: int,
    ) -> study_models.Question:
        """Create single question with answer type id.

        Args:
            db: an open database session
            question: the question
            answer_type_id: id of answer type

        Returns:
            study_models.Question: returns created question object
        """
        db_question = study_models.Question(question=question, a_id=answer_type_id)
        self.create_or_update_object_in_db(db, db_question)
        return db_question

    def create_question_by_object(
        self,
        db: Session,
        question: str,
        answer_type: study_models.AnswerType,
    ) -> study_models.Question:
        """Create single question with answer type id.

        Args:
            db: an open database session
            question: the question
            answer_type: answer type object

        Returns:
            study_models.Question: returns created question object
        """
        db_question = study_models.Question(question=question, answer_type=answer_type)
        self.create_or_update_object_in_db(db, db_question)
        return db_question

    def add_demographics_to_user(
        self, db: Session, uuid: str, demographics: dict
    ) -> Optional[study_models.User]:
        """Add demographics to user in database.

        Args:
            db: an open database session
            uuid: a unique identifier for the user
            demographics: a dictionary of demographics for the user

        Returns:
            study_models.User: returns the user object with newly created demographics.
        """
        if user := self.get_user_by_uuid(db, uuid):
            demographics["u_id"] = user.uuid
            user.demographics = study_models.Demographics(**demographics)
            self.create_or_update_object_in_db(db, user)
            return user
        return None

    def add_other_personal_data_to_user(
        self, db: Session, uuid: str, personal_data: dict
    ) -> Optional[study_models.User]:
        """Add other personal data to user in database.

        Args:
            db: an open database session
            uuid: a unique identifier for the user
            personal_data: a dictionary of personal data for the user

        Returns:
            study_models.User: returns the user object with newly created personal data objects.
        """
        if user := self.get_user_by_uuid(db, uuid):
            for key, value in personal_data.items():
                user.personal_data.append(
                    study_models.OtherPersonalData(
                        u_id=user.uuid, description=key, data=value
                    )
                )
            self.create_or_update_object_in_db(db, user)
            return user
        return None

    def get_user_by_uuid(self, db: Session, uuid: str) -> Optional[study_models.User]:
        """Get user by uuid.

        Args:
            db: an open database session
            uuid: a unique identifier for the user

        Returns:
            study_models.User: returns the user object from the database.
        """
        return (
            db.query(study_models.User)
            .filter(study_models.User.uuid == uuid)
            .one_or_none()
        )

    def get_vignette_template_by_id(self, db: Session, study_id: int) -> Optional[str]:
        """Get vignette template by study id."""
        if study := db.query(study_models.Study).get(study_id):
            return study.vignette_template
        return None

    def get_study_by_id(
        self, db: Session, study_id: int
    ) -> Optional[study_models.Study]:
        """Get study by id."""
        return db.query(study_models.Study).get(study_id)

    def get_factors(self, db: Session) -> Dict[str, Dict[str, str]]:
        """Get all vignette variables mapped with factor and level."""
        variables = db.query(study_models.VignetteVariable).all()

        factors: Dict[str, Dict[str, str]] = defaultdict(dict)

        for var in variables:
            factors[var.factor][var.level] = var.text
        return factors

    def get_answered_questions_by_uuid(
        self, db: Session, uuid: str
    ) -> List[study_models.QuestionAnswer]:
        """Get all answered questions of user from database."""
        return (
            db.query(study_models.QuestionAnswer)
            .join(study_models.StudyResult)
            .filter(study_models.StudyResult.u_id == uuid)
            .all()
        )

    def get_study_questions(self, db: Session) -> List[study_models.Question]:
        """Get questions from database."""
        return db.query(study_models.Question).all()
