"""Test module data_persistence."""

import inspect
import itertools
from collections.abc import Iterable
from random import choice, randint, sample

import pytest
from faker import Faker
from more_itertools import one
from sqlalchemy import create_engine
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session

from agatha.backend.data_persistence import models
from agatha.backend.data_persistence.crud import DataAccessObject

DAO = DataAccessObject()
fake = Faker()


@pytest.fixture(scope="session")
def engine():
    """Create SQLAlchemy engine connected to in memory database."""
    return create_engine("sqlite://", connect_args={"check_same_thread": False})


@pytest.fixture(scope="session")
def tables(engine):
    """Creates tables in sqlalchemy database and drops all after execution."""
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)


@pytest.fixture
def dbsession(engine, tables):
    """Get a database session, that is rolled back after each test.

    Args:
        engine: fixture to define the database the connection is created with.
        tables: fixture to define the created tables.
    """
    connection = engine.connect()
    # start transaction to rollback any changes
    transaction = connection.begin()

    session = Session(autocommit=False, autoflush=False, bind=connection)
    yield session

    session.close()
    transaction.rollback()
    connection.close()


def assert_db_obj_equality(expected, result):
    """Compare two database model objects for equality."""
    for attr, value in expected.__dict__.items():
        if attr.startswith("_"):
            continue
        if isinstance(value, models.Base):
            continue  # don't need to check, as for scalar relationships ids are checked
        if isinstance(value, Iterable):
            for expected_val, result_val in zip(value, getattr(result, attr)):
                if isinstance(expected_val, models.Base):
                    assert_db_obj_equality(expected_val, result_val)
                    continue
                assert expected_val == result_val
            continue
        assert value == getattr(result, attr, None)


def random_delivery_model(ids):
    """Get a random delivery model."""
    config = {
        "id": next(ids),
        "name": fake.name(),
        "description": fake.paragraph(nb_sentences=2),
    }
    object_ = models.DeliveryModel(**config)
    return config, object_


def random_incentive_type(ids):
    """Get a random incentive type."""
    config = {
        "id": next(ids),
        "name": fake.name(),
        "description": fake.paragraph(nb_sentences=2),
    }
    object_ = models.IncentiveType(**config)
    return config, object_


def random_factor(ids, delivery_models, incentive_types):
    """Get a random factor."""
    config = {"id": next(ids), "name": fake.name()}
    if choice(("delivery_model", "incentive_type")) == "delivery_model":  # nosec
        config["delivery_model"] = choice(delivery_models)  # nosec
    else:
        config["incentive_type"] = choice(incentive_types)  # nosec
    object_ = models.Factor(**config)
    return config, object_


def random_employee_model(revolori_ids, delivery_models, incentive_types):
    """Get a random employee model."""
    config = {
        "revolori_id": next(revolori_ids),
        "delivery_model": choice(delivery_models),  # nosec
        "incentive_type": choice(incentive_types),  # nosec
    }
    object_ = models.EmployeeModel(**config)
    return config, object_


def random_employee_incentive(revolori_ids, incentive_types):
    """Get a random employee-incentive."""
    config = {
        "revolori_id": choice(revolori_ids),  # nosec
        "incentive_type": choice(incentive_types),  # nosec
        "date_time": fake.unix_time(),
    }
    object_ = models.EmployeeIncentive(**config)
    return config, object_


def random_answer_type(ids):
    """Get a random answer type."""
    config = {
        "id": next(ids),
        "short_name": fake.name(),
        "description": fake.paragraph(nb_sentences=2),
        "most_positive": randint(1, 10),  # nosec
        "most_negative": randint(1, 10),  # nosec
    }
    object_ = models.AnswerType(**config)
    return config, object_


def random_question(ids, factors, answer_types):
    """Get a random question."""
    config = {
        "id": next(ids),
        "question": fake.sentence(),
        "weight": randint(1, 100),  # nosec
        "factor": choice(factors),  # nosec
        "answer_type": choice(answer_types),  # nosec
    }
    object_ = models.Question(**config)
    return config, object_


def random_survey(ids):
    """Get a random survey."""
    config = {
        "id": next(ids),
        "name": fake.name(),
        "description": fake.paragraph(nb_sentences=2),
    }
    object_ = models.Survey(**config)
    return config, object_


def random_question_answer(identifiers):
    """Get a random question-answer."""
    revolori_id, question = next(identifiers)  # nosec
    while not question.surveys:
        revolori_id, question = next(identifiers)  # nosec
    survey = choice(question.surveys)  # nosec
    config = {
        "revolori_id": revolori_id,
        "answer": fake.sentence(),
        "question": question,
        "survey": survey,
    }
    object_ = models.QuestionAnswer(**config)
    return config, object_


def random_list_of_model(min_sample, max_sample, object_generator, **kwargs):
    """Create list of random database model configs and objects.

    Args:
        min_sample: minimum number of objects to be created
        max_sample: maximum number of objects to be created
        creator: function that creates a random config and object

    Returns:
        list with two elements: list of configs and list of objects
    """
    num = randint(min_sample, max_sample)  # nosec
    if "ids" in inspect.signature(object_generator).parameters:
        kwargs["ids"] = iter(range(1, num + 1))
    return list(zip(*(object_generator(**kwargs) for _ in range(1, num + 1))))


@pytest.fixture
def random_revolori_ids():
    """Create list of random revolori ids.

    The number of created revolori ids needs to be greater than the
    number of generated employee models.
    Number is fixed to 20.
    """
    return [fake.email() for _ in range(20)]


@pytest.fixture
def random_delivery_models():
    """Fixture for random delivery models.

    Returns:
        list with two elements: list of configs and list of objects
    """
    return random_list_of_model(5, 20, random_delivery_model)


@pytest.fixture
def random_incentive_types():
    """Fixture for random incentive types.

    Returns:
        list with two elements: list of configs and list of objects
    """
    return random_list_of_model(5, 20, random_incentive_type)


@pytest.fixture
def random_factors(random_delivery_models, random_incentive_types):
    """Fixture for random factors.

    Returns:
        list with two elements: list of configs and list of objects
    """
    return random_list_of_model(
        3,
        5,
        random_factor,
        delivery_models=list(random_delivery_models[1]),
        incentive_types=list(random_incentive_types[1]),
    )


@pytest.fixture
def random_employee_models(
    random_revolori_ids, random_delivery_models, random_incentive_types
):
    """Fixture for random employee models.

    Returns:
        list with two elements: list of configs and list of objects
    """
    return random_list_of_model(
        5,
        20,
        random_employee_model,
        revolori_ids=iter(random_revolori_ids),
        delivery_models=list(random_delivery_models[1]),
        incentive_types=list(random_incentive_types[1]),
    )


@pytest.fixture
def random_employee_incentives(random_revolori_ids, random_incentive_types):
    """Fixture for random employee-incentives.

    Returns:
        list with two elements: list of configs and list of objects
    """
    return random_list_of_model(
        5,
        20,
        random_employee_incentive,
        revolori_ids=random_revolori_ids,
        incentive_types=list(random_incentive_types[1]),
    )


@pytest.fixture
def random_answer_types():
    """Fixture for random answer types.

    Returns:
        list with two elements: list of configs and list of objects
    """
    return random_list_of_model(3, 5, random_answer_type)


@pytest.fixture
def random_questions(random_answer_types, random_factors):
    """Fixture for random questions.

    Returns:
        list with two elements: list of configs and list of objects
    """
    return random_list_of_model(
        50,
        100,
        random_question,
        answer_types=random_answer_types[1],
        factors=random_factors[1],
    )


@pytest.fixture
def random_surveys(random_questions, random_employee_models):
    """Fixture for random surveys.

    Returns:
        list with two elements: list of configs and list of objects
    """
    configs, objects = random_list_of_model(
        10,
        20,
        random_survey,
    )
    for survey in objects:
        survey.questions = sample(random_questions[1], randint(5, 20))  # nosec
    return configs, objects


@pytest.fixture
def random_question_answers(random_revolori_ids, random_surveys, random_questions):
    """Fixture for random question-answers.

    Returns:
        list with two elements: list of configs and list of objects
    """
    return random_list_of_model(
        30,
        80,
        random_question_answer,
        identifiers=iter(itertools.product(random_revolori_ids, random_questions[1])),
    )


@pytest.fixture
def populated_db(
    dbsession,
    random_revolori_ids,
    random_factors,
    random_surveys,
    random_questions,
    random_answer_types,
    random_employee_incentives,
    random_employee_models,
    random_incentive_types,
    random_delivery_models,
    random_question_answers,
):
    """Fixture to populate entire database with random data.

    Returns:
        tuple of db session and dict with all objects saved to the database
    """
    objects = {
        "question_answers": random_question_answers[1],
        "factors": random_factors[1],
        "surveys": random_surveys[1],
        "questions": random_questions[1],
        "answer_types": random_answer_types[1],
        "employee_incentives": random_employee_incentives[1],
        "employee_models": random_employee_models[1],
        "incentive_types": random_incentive_types[1],
        "delivery_models": random_delivery_models[1],
    }
    for obj_list in objects.values():
        for obj in obj_list:
            DAO.create_or_update_object_in_db(dbsession, obj)
    objects["revolori_ids"] = random_revolori_ids
    return dbsession, objects


def model_tester(db, random_models, creator, use_ids=False):
    """Use creator function to save random models to db and test if expected values where saved.

    Args:
        db: database session
        random_models: check random_list_of_model returns
        creator: function that creates the object in the database and returns it
        use_ids: Switches to insert by id instead of object. Defaults to False.
    """
    config_list, object_list = random_models

    for config, expected in zip(config_list, object_list):

        if use_ids:
            config_modified = {}
            for key, value in config.items():
                if isinstance(value, models.Base):
                    config_modified[f"{key}_id"] = value.id
                else:
                    config_modified[key] = value
            config = config_modified

        if "id" in config:
            del config["id"]

        created = creator(db, **config)

        assert_db_obj_equality(expected=expected, result=created)


def model_tester_obj_ids(db, random_models, creator_obj, creator_ids):
    """Split random object lists in two halfs, test one half with insert by object, the other with insert by id.

    Args:
        db: database session
        random_models: check random_list_of_model returns
        creator_objs: function that creates the object in the database and returns it (by objects)
        creator_ids: function that creates the object in the database and returns it (by ids)
    """
    config_list, object_list = random_models

    config_list_objs = config_list[: len(config_list) // 2]
    config_list_ids = config_list[len(config_list) // 2 :]

    object_list_objs = object_list[: len(object_list) // 2]
    object_list_ids = object_list[len(object_list) // 2 :]

    model_tester(db, (config_list_objs, object_list_objs), creator_obj)
    model_tester(db, (config_list_ids, object_list_ids), creator_ids, True)


def test_add_delivery_models(dbsession, random_delivery_models):
    """Test adding delivery models to the database."""
    model_tester(dbsession, random_delivery_models, DAO.create_delivery_model)


def test_add_incentive_types(dbsession, random_incentive_types):
    """Test adding incentive types to the database."""
    model_tester(dbsession, random_incentive_types, DAO.create_incentive_type)


def test_add_factors(dbsession, random_factors):
    model_tester(dbsession, random_factors, DAO.create_factor_by_objects)


def test_add_employee_models(dbsession, random_employee_models):
    """Test adding employee models to the database."""
    model_tester_obj_ids(
        dbsession,
        random_employee_models,
        DAO.create_employee_model_by_objects,
        DAO.create_employee_model_by_ids,
    )


def test_employee_incentives(dbsession, random_employee_incentives):
    """Test adding employee-incentives to the database."""
    model_tester_obj_ids(
        dbsession,
        random_employee_incentives,
        DAO.create_employee_incentive_by_object,
        DAO.create_employee_incentive_by_id,
    )


def test_answer_types(dbsession, random_answer_types):
    """Test adding answer types to the database."""
    model_tester(dbsession, random_answer_types, DAO.create_answer_type)


def test_questions(dbsession, random_questions):
    """Test adding questions to the database."""
    model_tester_obj_ids(
        dbsession,
        random_questions,
        DAO.create_question_by_objects,
        DAO.create_question_by_ids,
    )


def test_surveys(dbsession, random_surveys):
    """Test adding surveys to the database."""
    model_tester(dbsession, random_surveys, DAO.create_survey)


def test_question_answers(dbsession, random_question_answers):
    """Test adding question_answers to the database."""
    model_tester(
        dbsession, random_question_answers, DAO.create_question_answer_by_q_id, True
    )


def test_get_all_surveys(dbsession, random_surveys):
    """Test retrieving all surveys from the database."""
    for expected, received in zip(random_surveys[1], DAO.get_all_surveys(dbsession)):
        assert_db_obj_equality(expected, received)


def test_questions_for_survey(populated_db):
    """Test DAO functionality of adding questions directly to surveys and retrieving them over relations."""
    db, objects = populated_db
    survey = choice(objects["surveys"])  # nosec
    answer_type = choice(objects["answer_types"])  # nosec
    factor = choice(objects["factors"])  # nosec

    # Test survey id not existing
    assert (
        DAO.create_question_for_survey_by_ids(
            db,
            fake.paragraph(nb_sentences=2),
            randint(1, 100),  # nosec
            factor,
            300000,
            answer_type.id,
        )
        is None
    )

    q_01_expected = DAO.create_question_for_survey(
        db,
        fake.paragraph(nb_sentences=2),
        randint(1, 100),  # nosec
        factor,
        survey,
        answer_type,
    )
    q_02_expected = DAO.create_question_for_survey_by_ids(
        db,
        fake.paragraph(nb_sentences=2),
        randint(1, 100),  # nosec
        factor.id,
        survey.id,
        answer_type.id,
    )
    revolori_id = "test:revolori:id"

    DAO.create_question_answer_by_q_id(
        db, survey.id, q_01_expected.id, revolori_id, fake.sentence()
    )
    DAO.create_question_answer_by_q_id(
        db, survey.id, q_02_expected.id, revolori_id, fake.sentence()
    )

    questions_received = DAO.get_answered_questions_by_revolori_id(db, revolori_id)
    surveys_received = DAO.get_answered_surveys_by_revolori_id(db, revolori_id)

    q_ids = [q.q_id for q in questions_received]
    s_ids = [s.id for s in surveys_received]

    assert q_01_expected.id in q_ids
    assert q_02_expected.id in q_ids
    assert len(q_ids) == 2
    assert survey.id in s_ids
    assert len(s_ids) == 1

    # test survey id that does not existing
    assert DAO.get_survey_questions_by_id(db, 300000) == []

    questions_received = DAO.get_survey_questions_by_id(db, survey.id)

    q_ids = [q.id for q in questions_received]

    assert q_01_expected.id in q_ids
    assert q_02_expected.id in q_ids


def test_dao_session():
    """Test DAO session creation."""
    session_01 = one(DAO())
    session_02 = one(DAO())

    session_01.info["test01"] = "tested"
    session_02.info["test02"] = "tested"

    assert session_01.info == {"test01": "tested"}
    assert session_02.info == {"test02": "tested"}

    test_obj = models.AnswerType(
        short_name="test",
        description="used to test",
        most_positive=5,
        most_negative=1,
    )

    DAO.create_or_update_object_in_db(session_01, test_obj)

    with pytest.raises(InvalidRequestError):
        DAO.refresh_object(session_02, test_obj)

    # clean up database
    session_01.delete(test_obj)
    session_01.commit()
