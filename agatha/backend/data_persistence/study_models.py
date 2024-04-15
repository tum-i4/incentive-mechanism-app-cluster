"""Specifies SQLAlchemy database model."""

from typing import List

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

StudyBase = declarative_base(name="StudyBase")


class Study(StudyBase):
    """Model for table study."""

    __tablename__ = "study"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    vignette_template = Column(String)


class VignetteVariable(StudyBase):
    """Model for table vignette."""

    __tablename__ = "vignette"
    id = Column(Integer, primary_key=True)
    factor = Column(String, nullable=False)
    level = Column(String, nullable=False)
    text = Column(String, nullable=False)


class StudyResult(StudyBase):
    """Model for table study_result."""

    __tablename__ = "study_result"
    u_id = Column(
        String,
        ForeignKey("user.uuid", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    feedback01 = Column(String)
    feedback02 = Column(String)
    feedback03 = Column(String)
    question_answers: List["QuestionAnswer"] = relationship(
        "QuestionAnswer", back_populates="study_result"
    )


class AnswerType(StudyBase):
    """Model for table answer_type."""

    __tablename__ = "answer_type"
    id = Column(Integer, primary_key=True)
    short_name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    most_positive = Column(Integer, nullable=False)
    most_negative = Column(Integer, nullable=False)


class Question(StudyBase):
    """Model for table question."""

    __tablename__ = "question"
    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    a_id = Column(
        Integer, ForeignKey("answer_type.id", ondelete="SET NULL"), nullable=False
    )
    # Many to one (one-directional) relationship with AnswerType
    answer_type: AnswerType = relationship("AnswerType")


class QuestionAnswer(StudyBase):
    """Model for table question_answer."""

    __tablename__ = "question_answer"
    q_id = Column(
        Integer,
        ForeignKey("question.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    s_id = Column(
        String,
        ForeignKey("study_result.u_id", ondelete="SET NULL"),
        primary_key=True,
        nullable=False,
    )
    vignette_id = Column(String, primary_key=True, nullable=False)
    answer = Column(String)
    # One to one (bidirectional) relationship with Question
    question: Question = relationship("Question")
    study_result: StudyResult = relationship(
        "StudyResult", back_populates="question_answers"
    )


class Demographics(StudyBase):
    """Model for table demographics."""

    __tablename__ = "demographics"
    u_id = Column(
        String,
        ForeignKey("user.uuid", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    age = Column(Integer)
    gender = Column(String)
    education = Column(String)
    zip_code = Column(String)
    country = Column(String)
    employment_status = Column(String)
    avg_current_income = Column(String)


class OtherPersonalData(StudyBase):
    """Model for table personal_data."""

    __tablename__ = "personal_data"
    id = Column(Integer, primary_key=True)
    u_id = Column(
        String,
        ForeignKey("user.uuid", ondelete="CASCADE"),
        nullable=False,
    )
    description = Column(String)
    data = Column(String)


class User(StudyBase):
    """Model for table user."""

    __tablename__ = "user"
    uuid = Column(
        String,
        primary_key=True,
        nullable=False,
    )
    email = Column(String)
    demographics: Demographics = relationship("Demographics", uselist=False)
    personal_data: List[OtherPersonalData] = relationship("OtherPersonalData")
    study_result: StudyResult = relationship("StudyResult")
