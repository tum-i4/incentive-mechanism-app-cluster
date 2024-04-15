"""Specifies SQLAlchemy database model."""

from typing import List, Optional

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Association table for many to many relationship between Survey and Question
survey_question = Table(
    "survey_question",
    Base.metadata,
    Column(
        "s_id",
        ForeignKey("survey.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "q_id",
        ForeignKey("question.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)


survey_employee = Table(
    "survey_employee",
    Base.metadata,
    Column(
        "revolori_id",
        ForeignKey("employee_model.revolori_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "s_id",
        ForeignKey("survey.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)


class DeliveryModel(Base):
    """Model for table delivery_model."""

    __tablename__ = "delivery_model"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)


class IncentiveType(Base):
    """Model for table incentive_type."""

    __tablename__ = "incentive_type"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)


class EmployeeModel(Base):
    """Model for table employee_model."""

    __tablename__ = "employee_model"
    revolori_id = Column(String, primary_key=True, nullable=False)
    d_id = Column(Integer, ForeignKey("delivery_model.id", ondelete="SET NULL"))
    i_id = Column(Integer, ForeignKey("incentive_type.id", ondelete="SET NULL"))
    # Many to one (one-directional) relationship with DeliveryModel
    delivery_model: DeliveryModel = relationship("DeliveryModel")
    # Many to one (one-directional) relationship with IncentiveType
    incentive_type: IncentiveType = relationship("IncentiveType")

    surveys: List["Survey"] = relationship(
        "Survey", secondary=survey_employee, back_populates="employee_models"
    )


class EmployeeIncentive(Base):
    """Model for table employee_incentive."""

    __tablename__ = "employee_incentive"
    revolori_id = Column(
        String,
        ForeignKey("employee_model.revolori_id", ondelete="SET NULL"),
        primary_key=True,
        nullable=False,
    )
    i_id = Column(
        Integer, ForeignKey("incentive_type.id", ondelete="SET NULL"), primary_key=True
    )
    date_time = Column(Integer, primary_key=True)
    # Many to one (one-directional) relationship with IncentiveType
    incentive_type: IncentiveType = relationship("IncentiveType")


class Survey(Base):
    """Model for table survey."""

    __tablename__ = "survey"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    # Many to many (bidirectional) relationship to Question
    questions: List["Question"] = relationship(
        "Question", secondary=survey_question, back_populates="surveys"
    )
    employee_models: List[EmployeeModel] = relationship(
        "EmployeeModel", secondary=survey_employee, back_populates="surveys"
    )


class AnswerType(Base):
    """Model for table answer_type."""

    __tablename__ = "answer_type"
    id = Column(Integer, primary_key=True)
    short_name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    most_positive = Column(Integer, nullable=False)
    most_negative = Column(Integer, nullable=False)


class Factor(Base):
    """Model for question factors."""

    __tablename__ = "factor"
    __table_args__ = (CheckConstraint("(d_id IS NULL) <> (i_id IS NULL)"),)
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    d_id = Column(Integer, ForeignKey("delivery_model.id", ondelete="SET NULL"))
    i_id = Column(Integer, ForeignKey("incentive_type.id", ondelete="SET NULL"))
    # Many (factors) to one (delivery model) relationship
    delivery_model: Optional[DeliveryModel] = relationship("DeliveryModel")
    # Many (factors) to one (incentive type) relationship
    incentive_type: Optional[IncentiveType] = relationship("IncentiveType")


class Question(Base):
    """Model for table question."""

    __tablename__ = "question"
    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    weight = Column(Integer, nullable=False)
    f_id = Column(Integer, ForeignKey("factor.id", ondelete="SET NULL"))
    a_id = Column(
        Integer, ForeignKey("answer_type.id", ondelete="SET NULL"), nullable=False
    )
    # Many to one (one-directional) relationship with AnswerType
    answer_type: AnswerType = relationship("AnswerType")
    # Many (questions) to one (factor) relationship
    factor: Factor = relationship("Factor")
    # One to Many (bidirectional) relationship with QuestionAnswer
    question_answers: List["QuestionAnswer"] = relationship(
        "QuestionAnswer", back_populates="question"
    )
    # Many to many (bidirectional) relationship with Survey
    surveys: List[Survey] = relationship(
        "Survey", secondary=survey_question, back_populates="questions"
    )


class QuestionAnswer(Base):
    """Model for table question_answer."""

    __tablename__ = "question_answer"
    s_id = Column(
        Integer,
        ForeignKey("survey.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    q_id = Column(
        Integer,
        ForeignKey("question.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    revolori_id = Column(
        String,
        ForeignKey("employee_model.revolori_id", ondelete="SET NULL"),
        primary_key=True,
        nullable=False,
    )
    answer = Column(String)
    # One to one (one-directional) relationship with Survey
    survey: Survey = relationship("Survey")
    # One to one (bidirectional) relationship with Question
    question: Question = relationship("Question", back_populates="question_answers")


class Admin(Base):
    """Model for admin table."""

    __tablename__ = "admin"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
