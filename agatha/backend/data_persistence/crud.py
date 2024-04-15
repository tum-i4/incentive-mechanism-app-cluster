"""Provides CRUD data access to the SQLAlchemy database for the main app cluster."""

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from agatha.backend.data_persistence import models
from agatha.backend.data_persistence.data_access_object import AbstractDataAccessObject
from agatha.util import singleton


@singleton
class DataAccessObject(AbstractDataAccessObject):
    """Singleton class to interact with database."""

    SQLALCHEMY_DATABASE_URL = "sqlite:///./agatha.db"

    def __init__(self):
        """Initialize the database in parent class."""
        super().__init__(self.SQLALCHEMY_DATABASE_URL, models.Base)

    def get_survey_by_id(self, db: Session, survey_id: int) -> Optional[models.Survey]:
        """Get Survey from database by id.

        Args:
            db: an open database session
            survey_id: id of the survey to be retrieved

        Returns:
            Optional[models.Survey]: returns survey object or None if not in the database
        """
        return db.get(models.Survey, survey_id)

    def get_all_surveys(self, db: Session) -> List[models.Survey]:
        """Get all surveys in database.

        Args:
            db: an open database session

        Returns:
            List[models.Survey]: returns a list of surveys, empty, if none are in the database
        """
        return db.query(models.Survey).all()

    def get_survey_questions_by_id(
        self, db: Session, survey_id: int, include_answers: bool = False
    ) -> List[models.Question]:
        """Get all questions of a survey by it's id.

        Args:
            db: an open database session
            survey_id: id of the survey to be retrieved
            include_answers: whether to include answers in the query

        Returns:
            List[models.Question]: returns a list of question objects, empty, if none are connected to the survey, or survey does not exist
        """
        query = (
            db.query(models.Question)
            .join(models.survey_question)
            .filter(models.survey_question.c.s_id == survey_id)
        )
        if include_answers:
            query = query.options(joinedload(models.Question.answer_type))

        return query.all()

    def get_answered_surveys_by_revolori_id(
        self, db: Session, revolori_id: str
    ) -> List[models.Survey]:
        """Get all Surveys, where at least one question has been answered by specified user.

        Args:
            db: an open database session
            revolori_id: id of the user

        Returns:
            List[models.Survey]: returns a list of survey objects, empty, if none exist
        """
        return (
            db.query(models.Survey)
            .join(models.QuestionAnswer, models.Question)
            .filter(models.QuestionAnswer.revolori_id == revolori_id)
            .all()
        )

    def get_answered_questions_by_revolori_id(
        self, db: Session, revolori_id: str
    ) -> List[models.QuestionAnswer]:
        """Get all answered questions of one user.

        Args:
            db: an open database session
            revolori_id: id of the user

        Returns:
            List[models.QuestionAnswer]: returns list of question-answer objects, empty, if none exist
        """
        return (
            db.query(models.QuestionAnswer)
            .filter(models.QuestionAnswer.revolori_id == revolori_id)
            .all()
        )

    def get_all_employee_models(self, db: Session) -> List[models.EmployeeModel]:
        """Get all employees with their configured model in the database.

        Args:
            db: an open database session

        Returns:
            List[models.EmployeeModel]: a list of all employee models
        """
        return db.query(models.EmployeeModel).all()

    def get_all_incentive_types(self, db: Session) -> List[models.IncentiveType]:
        """Get all incentive types with their configured model in the database.

        Args:
            db: an open database session

        Returns:
            List[models.IncentiveType]: a list of all incentive types
        """
        return db.query(models.IncentiveType).all()

    def get_all_delivery_models(self, db: Session) -> List[models.DeliveryModel]:
        """Get all delivery models with their configured model in the database.

        Args:
            db: an open database session

        Returns:
            List[models.DeliveryModel]: a list of all delivery models
        """
        return db.query(models.DeliveryModel).all()

    def get_employee_model_by_revolori_id(
        self, db: Session, revolori_id: str
    ) -> Optional[models.EmployeeModel]:
        """Get EmployeeModel for an employee with the given revolori_id.

        Args:
            db: an open database session
            revolori_id: id for an employee from Revolori SSO
        """
        return db.get(models.EmployeeModel, revolori_id)

    def get_delivery_model_by_id(
        self, db: Session, d_id: int
    ) -> Optional[models.DeliveryModel]:
        """Get DeliveryModel with the given id.

        Args:
            db: an open database session
            d_id: id of the queried delivery model

        Returns:
            the delivery model with the given id
        """
        return db.get(models.DeliveryModel, d_id)

    def get_incentive_type_by_id(
        self, db: Session, i_id: int
    ) -> Optional[models.IncentiveType]:
        """Get IncentiveType with the given id.

        Args:
            db: an open database session
            i_id: id of the queried incentive type

        Returns:
            the incentive type with the given id
        """
        return db.get(models.IncentiveType, i_id)

    def get_admin_by_email(self, db: Session, email: str) -> Optional[models.Admin]:
        """Get Admin with the given email.

        Args:
            db: an open database session
            email: email to be queried

        Returns:
            admin with the given email, otherwise None
        """
        return db.query(models.Admin).filter(models.Admin.email == email).one_or_none()

    def refresh_object(self, db: Session, obj: models.Base) -> models.Base:
        """Update a python object with values from the database.

        Connects the object to the given session and retrieves all info from the database to update.

        Args:
            db: an open database session
            obj: any object from a subclass of Base

        Returns:
            models.Base: returns the same object with updated values
        """
        db.refresh(obj)
        return obj

    def create_or_update_object_in_db(self, db: Session, obj: models.Base):
        """Create or update object in database.

        If some arguments are not specified, that can be auto filled, the object will be returned updated.
        Example: id's are often left to auto-generation

        Args:
            db: an open database session
            obj: any object from a subclass of Base

        Returns:
            models.Base: returns the same object updated with the values written to the database.
        """
        db.add(obj)
        db.commit()
        db.refresh(obj)

    def create_question_answer_by_q_id(
        self,
        db: Session,
        survey_id: int,
        question_id: int,
        revolori_id: str,
        answer: str,
    ) -> models.QuestionAnswer:
        """Save a answer to a specific question to the database.

        Args:
            db: an open database session
            survey_id: id of the survey, the answer was given to
            question_id: id of the question that was answered
            revolori_id: id of the user answering
            answer: the answer

        Returns:
            models.QuestionAnswer: returns the created object
        """
        question_answer = models.QuestionAnswer(
            s_id=survey_id, q_id=question_id, revolori_id=revolori_id, answer=answer
        )
        self.create_or_update_object_in_db(db, question_answer)
        return question_answer

    def create_survey(self, db: Session, name: str, description: str) -> models.Survey:
        """Save new survey to the database.

        Args:
            db: an open database session
            name: name of the survey
            description: description of the survey

        Returns:
            models.Survey: returns the created object
        """
        survey = models.Survey(name=name, description=description)
        self.create_or_update_object_in_db(db, survey)
        return survey

    def create_question_for_survey(
        self,
        db: Session,
        question: str,
        weight: int,
        factor: models.Factor,
        survey: models.Survey,
        answer_type: models.AnswerType,
    ) -> models.Question:
        """Add new question to a specific survey.

        Args:
            db: an open database session
            question: the question
            weight: weight of the question
            factor: factor of the question
            survey: the survey model it should be added to
            answer_type: answer type object

        Returns:
            Optional[models.Question]: returns created question object
        """
        db_question = models.Question(
            question=question, weight=weight, factor=factor, answer_type=answer_type
        )
        survey.questions.append(db_question)
        self.create_or_update_object_in_db(db, db_question)
        return db_question

    def create_question_for_survey_by_ids(
        self,
        db: Session,
        question: str,
        weight: int,
        factor_id: int,
        survey_id: int,
        answer_type_id: int,
    ) -> Optional[models.Question]:
        """Add new question to a specific survey.

        Args:
            db: an open database session
            question: the question
            weight: weight of the question
            factor_id: id of the factor related with the question
            survey: the survey model it should be added to
            answer_type: answer type object

        Returns:
            models.Question: returns created question object or none, if survey does not exist
        """
        if survey := db.get(models.Survey, survey_id):
            db_question = models.Question(
                question=question, weight=weight, f_id=factor_id, a_id=answer_type_id
            )
            db_question.surveys.append(survey)
            self.create_or_update_object_in_db(db, db_question)
            return db_question
        return None

    def create_question_by_ids(
        self,
        db: Session,
        question: str,
        weight: int,
        factor_id: int,
        answer_type_id: int,
    ) -> models.Question:
        """Create single question with answer-type id.

        Args:
            db: an open database session
            question: the question
            weight: weight of the question
            factor_id: id of the factor related with the question
            answer_type_id: id of answer-type

        Returns:
            models.Question: returns created question object
        """
        db_question = models.Question(
            question=question, weight=weight, f_id=factor_id, a_id=answer_type_id
        )
        self.create_or_update_object_in_db(db, db_question)
        return db_question

    def create_question_by_objects(
        self,
        db: Session,
        question: str,
        weight: int,
        factor: models.Factor,
        answer_type: models.AnswerType,
    ) -> models.Question:
        """Create single question with answer-type object.

        Args:
            db: an open database session
            question: the question
            weight: weight of the question
            factor: factor of the question
            answer_type: answer-type object

        Returns:
            models.Base: returns created question object
        """
        db_question = models.Question(
            question=question, weight=weight, factor=factor, answer_type=answer_type
        )
        self.create_or_update_object_in_db(db, db_question)
        return db_question

    def add_question_to_survey(
        self, db: Session, question: models.Question, survey: models.Survey
    ) -> models.Survey:
        """Add existing question to existing survey.

        Args:
            db: an open database session
            question: question object
            survey: survey object

        Returns:
            models.Survey: returns updated survey object
        """
        survey.questions.append(question)
        self.create_or_update_object_in_db(db, survey)
        return survey

    def update_employee_model_by_ids(
        self,
        db: Session,
        revolori_id: str,
        delivery_model_id: int,
        incentive_type_id: int,
    ):
        """Update delivery model and incentive type for an employee.

        Args:
            db: an open database session
            revolori_id: id of employee from Revolori SSO
            delivery_model_id: id of the updated delivery model
            incentive_model_id: id of the updated incentive type
        """
        if employee_model := self.get_employee_model_by_revolori_id(db, revolori_id):
            employee_model.d_id = delivery_model_id
            employee_model.i_id = incentive_type_id
            db.commit()

    def update_delivery_model_by_id(
        self,
        db: Session,
        d_id: int,
        name: str,
        description: Optional[str],
    ):
        """Update delivery model details.

        Args:
            d_id: id of the delivery model to be updated
            name: the updated name for the model
            description: the updated description for the model
        """
        if delivery_model := self.get_delivery_model_by_id(db, d_id):
            delivery_model.name = name
            delivery_model.description = description
            db.commit()

    def update_incentive_type_by_id(
        self,
        db: Session,
        i_id: int,
        name: str,
        description: Optional[str],
    ):
        """Update incentive type details.

        Args:
            d_id: id of the delivery model to be updated
            name: the updated name for the model
            description: the updated description for the model
        """
        if incentive_type := self.get_incentive_type_by_id(db, i_id):
            incentive_type.name = name
            incentive_type.description = description
            db.commit()

    def create_answer_type(
        self,
        db: Session,
        short_name: str,
        description: Optional[str],
        most_positive: int,
        most_negative: int,
    ) -> models.AnswerType:
        """Save new answer-type to database.

        Args:
            db: an open database session
            short_name: short name for answer-type
            description: description of answer-type
            most_positive: most positive answer among all possibilities
            most_negative: most negative answer among all possibilities

        Returns:
            models.AnswerType: returns created object
        """
        answer_type = models.AnswerType(
            short_name=short_name,
            description=description,
            most_positive=most_positive,
            most_negative=most_negative,
        )
        self.create_or_update_object_in_db(db, answer_type)
        return answer_type

    def create_factor_by_objects(
        self,
        db: Session,
        name: str,
        delivery_model: models.DeliveryModel = None,
        incentive_type: models.IncentiveType = None,
    ) -> models.Factor:
        """Save new factor to database.

        Args:
            db: an open database session
            name: factor name
            delivery_model: related delivery model
            incentive_type: related incentive model

        Returns:
            models.Factor: returns the created object
        """
        factor = models.Factor(
            name=name, delivery_model=delivery_model, incentive_type=incentive_type
        )
        self.create_or_update_object_in_db(db, factor)
        return factor

    def create_delivery_model(
        self, db: Session, name: str, description: Optional[str]
    ) -> models.DeliveryModel:
        """Save new delivery-model to database.

        Args:
            db: an open database session
            name: name of delivery-model
            description: description of delivery-model

        Returns:
            models.DeliveryModel: returns created object
        """
        delivery_model = models.DeliveryModel(name=name, description=description)
        self.create_or_update_object_in_db(db, delivery_model)
        return delivery_model

    def create_employee_model_by_ids(
        self,
        db: Session,
        revolori_id: str,
        delivery_model_id: int,
        incentive_type_id: int,
    ) -> models.EmployeeModel:
        """Save new employee-model to database with reference ids.

        Args:
            db: an open database session
            revolori_id: id of user (employee)
            delivery_model: delivery-model id
            incentive_type: incentive-type id

        Returns:
            models.EmployeeModel: returns created object
        """
        employee_model = models.EmployeeModel(
            revolori_id=revolori_id,
            d_id=delivery_model_id,
            i_id=incentive_type_id,
        )
        self.create_or_update_object_in_db(db, employee_model)
        return employee_model

    def create_employee_model_by_objects(
        self,
        db: Session,
        revolori_id: str,
        delivery_model: models.DeliveryModel,
        incentive_type: models.IncentiveType,
    ) -> models.EmployeeModel:
        """Save new employee-model to database with reference objects.

        Args:
            db: an open database session
            revolori_id: id of user (employee)
            delivery_model: delivery-model object
            incentive_type: incentive-type object

        Returns:
            models.EmployeeModel: returns created object
        """
        employee_model = models.EmployeeModel(
            revolori_id=revolori_id,
            delivery_model=delivery_model,
            incentive_type=incentive_type,
        )
        self.create_or_update_object_in_db(db, employee_model)
        return employee_model

    def create_incentive_type(
        self, db: Session, name: str, description: Optional[str]
    ) -> models.IncentiveType:
        """Save new incentive-type to database.

        Args:
            db: an open database session
            name: name of the incentive-type
            description: description of the incentive-type

        Returns:
            models.IncentiveType: returns created object
        """
        incentive_type = models.IncentiveType(name=name, description=description)
        self.create_or_update_object_in_db(db, incentive_type)
        return incentive_type

    def create_employee_incentive_by_id(
        self,
        db: Session,
        revolori_id: str,
        date_time: int,
        incentive_type_id: int,
    ) -> models.EmployeeIncentive:
        """Save new employee-incentive to database with reference id.

        Args:
            db: an open database session
            revolori_id: id of the user (employee)
            date_time: timestamp
            incentive_type: incentive-type id

        Returns:
            models.EmployeeIncentive: returns created object
        """
        employee_incentive = models.EmployeeIncentive(
            revolori_id=revolori_id, date_time=date_time, i_id=incentive_type_id
        )
        self.create_or_update_object_in_db(db, employee_incentive)
        return employee_incentive

    def create_employee_incentive_by_object(
        self,
        db: Session,
        revolori_id: str,
        date_time: int,
        incentive_type: models.IncentiveType,
    ) -> models.EmployeeIncentive:
        """Save new employee-incentive to database with reference object.

        Args:
            db: an open database session
            revolori_id: id of the user (employee)
            date_time: timestamp
            incentive_type: incentive-type object

        Returns:
            models.EmployeeIncentive: returns created object
        """
        employee_incentive = models.EmployeeIncentive(
            revolori_id=revolori_id, date_time=date_time, incentive_type=incentive_type
        )
        self.create_or_update_object_in_db(db, employee_incentive)
        return employee_incentive

    def create_question_answer_by_objects(
        self,
        db: Session,
        revolori_id: str,
        survey: models.Survey,
        question: models.Question,
        answer: str,
    ) -> models.QuestionAnswer:
        """Save new question_answer to database with reference object.

        Args:
            db: an open database session
            revolori_id: id of the user (employee)
            survey: the survey that the answered question belongs to
            question: the question being answered
            answer: the content of the answer

        Returns:
            models.QuestionAnswer: returns created object
        """
        question_answer = models.QuestionAnswer(
            revolori_id=revolori_id,
            survey=survey,
            question=question,
            answer=answer,
        )
        self.create_or_update_object_in_db(db, question_answer)
        return question_answer

    def create_admin(self, db: Session, email: str) -> models.Admin:
        """Save new admin with email and password.

        Args:
            db: an open database session
            email: email of the new admin

        Returns:
            models.Admin: created admin
        """
        admin = models.Admin(email=email)
        self.create_or_update_object_in_db(db, admin)
        return admin
