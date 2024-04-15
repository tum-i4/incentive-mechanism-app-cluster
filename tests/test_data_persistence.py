"""Test module data_persistence."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from agatha.backend.data_persistence import models
from agatha.backend.data_persistence.crud import DataAccessObject

DAO = DataAccessObject()


# inspired by https://gist.github.com/kissgyorgy/e2365f25a213de44b9a2
@pytest.fixture(scope="session")
def engine():
    """Create SQLAlchemy engine with test-path."""
    # create in memory database
    return create_engine("sqlite://", connect_args={"check_same_thread": False})


@pytest.fixture(scope="session")
def tables(engine):
    """Creates tables in sqlalchemy database and drops all after execution."""
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)


@pytest.fixture
def dbsession(engine, tables):
    """Returns an sqlalchemy session, and after the test tears down everything properly."""
    connection = engine.connect()
    # begin the nested transaction
    transaction = connection.begin()
    # use the connection with the already started transaction

    session = Session(autocommit=False, autoflush=False, bind=connection)

    yield session

    session.close()
    # roll back the broader transaction
    transaction.rollback()
    # put back the connection to the connection pool
    connection.close()


@pytest.fixture
def example_survey():
    """Get example survey for the database."""
    return models.Survey(
        id=1,
        name="measure of reciprocity",
        description="Survey used to gauge the reciprocal, trust and lending behavior of individuals",
        questions=[
            models.Question(
                question="I usually lend my belongings to other people (books, CDs etc)",
                weight=50,
                factor=models.Factor(
                    name="reciprocity",
                    delivery_model=models.DeliveryModel(
                        name="gift before",
                        description="Unconditional delivery of calculated incentive prior to data sharing requests",
                    ),
                ),
                answer_type=models.AnswerType(
                    short_name="likert 5 scale",
                    description="Scale of 5 units that ranges between the choices 'Strongly disagree' to 'Strongly agree'",
                    most_positive=5,
                    most_negative=1,
                ),
            ),
            models.Question(
                question="In general, one can trust people",
                weight=50,
                factor=models.Factor(
                    name="autonomy",
                    incentive_type=models.IncentiveType(
                        name="gift cards",
                        description="Gift card worth x euros, redeemable at some place y",
                    ),
                ),
                answer_type=models.AnswerType(
                    short_name="likert 7 scale",
                    description="scale of 7 units that ranges between the choices 'Very untrue of me' to 'Very true of me'",
                    most_positive=1,
                    most_negative=7,
                ),
            ),
        ],
    )


def survey_equality(survey_expected: models.Survey, survey_given: models.Survey):
    """Assert equality for two models.Survey objects."""
    assert survey_expected.description == survey_given.description
    assert survey_expected.name == survey_given.name

    for q1, q2 in zip(survey_expected.questions, survey_given.questions):
        assert q1.question == q2.question
        assert q1.weight == q2.weight
        assert q1.factor.name == q2.factor.name
        assert q1.answer_type.short_name == q2.answer_type.short_name
        assert q1.answer_type.description == q2.answer_type.description


def test_adding_to_database(dbsession, example_survey):
    """Test if adding a survey and requesting it, returns the same survey."""
    DAO.create_or_update_object_in_db(dbsession, example_survey)

    survey_saved = DAO.get_survey_by_id(dbsession, 1)

    survey_equality(example_survey, survey_saved)


def test_dao_api(dbsession, example_survey):
    """Test the DataAccessObject by using it's function to fill the database."""
    d_model_01 = DAO.create_delivery_model(
        db=dbsession,
        name="gift before",
        description="Unconditional delivery of calculated incentive prior to data sharing requests",
    )
    i_type_01 = DAO.create_incentive_type(
        db=dbsession,
        name="gift cards",
        description="Gift card worth x euros, redeemable at some place y",
    )
    factor_01 = DAO.create_factor_by_objects(
        db=dbsession,
        name="reciprocity",
        delivery_model=d_model_01,
    )
    factor_02 = DAO.create_factor_by_objects(
        db=dbsession,
        name="autonomy",
        incentive_type=i_type_01,
    )
    ans_type_01 = DAO.create_answer_type(
        db=dbsession,
        short_name="likert 5 scale",
        description="Scale of 5 units that ranges between the choices 'Strongly disagree' to 'Strongly agree'",
        most_positive=5,
        most_negative=1,
    )
    ans_type_02 = DAO.create_answer_type(
        db=dbsession,
        short_name="likert 7 scale",
        description="scale of 7 units that ranges between the choices 'Very untrue of me' to 'Very true of me'",
        most_positive=1,
        most_negative=7,
    )
    question_01 = DAO.create_question_by_objects(
        db=dbsession,
        question="I usually lend my belongings to other people (books, CDs etc)",
        weight=50,
        factor=factor_01,
        answer_type=ans_type_01,
    )
    question_02 = DAO.create_question_by_objects(
        db=dbsession,
        question="In general, one can trust people",
        weight=50,
        factor=factor_02,
        answer_type=ans_type_02,
    )
    survey_saved = DAO.create_survey(
        db=dbsession,
        name="measure of reciprocity",
        description="Survey used to gauge the reciprocal, trust and lending behavior of individuals",
    )
    assert survey_saved is not None

    DAO.add_question_to_survey(dbsession, question_01, survey_saved)
    DAO.add_question_to_survey(dbsession, question_02, survey_saved)

    survey_equality(example_survey, survey_saved)
