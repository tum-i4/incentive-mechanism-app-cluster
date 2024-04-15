"""Test vignette generator."""

import random
from unittest.mock import MagicMock, patch

import pytest

from agatha.backend.study.vignette_generator import (
    Vignette,
    generate_vignette,
    generate_vignette_id,
    generate_vignettes,
    parse_vignette_id,
)


@pytest.fixture
def factors():
    """Generate factors.

    Example:
        {
            "a": {
                "a": "a.a",
                "b": "a.b",
            },
            "b": {
                "a": "b.a",
                "b": "b.b",
            },
            ...
        }

    """
    n = 5
    m = 2
    return {
        chr(i): {chr(j): f"{chr(i)}.{chr(j)}" for j in range(97, 97 + m)}
        for i in range(97, 97 + n)
    }


@pytest.fixture
def random_factor_key_choice(factors):
    """Generate random key choice.

    Example:
        {
            "a": "a",
            "b": "a",
            ...
        }

    Returns:
        Tuple of mapping from factor to one level and all factor and level values.
    """
    factor_levels = {
        factor: random.choice(list(levels))  # noqa: E501
        for factor, levels in factors.items()
    }
    return factor_levels, factors


@pytest.fixture
def vignette_id_and_factors(random_factor_key_choice):
    """Generate vignette ids with chosen factor keys and factor values.

    Example:
            "{"study_id":1,"factor_levels":{"a":"b","b":"a","c":"b","d":"a"}}"
            {"a":"a","b":"a","c":"b","d":"a"},
            {
            "a": {
                "a": "a.a",
                "b": "a.b",
            },
            "b": {
                "a": "b.a",
                "b": "b.b",
            },
            ...
        }

    Returns:
        Tuple of vignette id, factor levels and factor dict.
    """
    factor_levels, factor_dict = random_factor_key_choice
    return (generate_vignette_id(1, **factor_levels), factor_levels, factor_dict)


def test_vingette_id():
    """Test vignette id generation with static values."""
    factor_levels = {
        "A": "1",
        "B": "2",
        "C": "3",
    }
    study_id = 1
    vignette_id = '{"study_id": 1, "factor_levels": {"A": "1", "B": "2", "C": "3"}}'
    assert generate_vignette_id(study_id, **factor_levels) == vignette_id
    vignette = parse_vignette_id(vignette_id)
    assert vignette == Vignette(study_id, vignette_id, factor_levels)
    assert (
        generate_vignette_id(vignette.study_id, **vignette.factor_levels) == vignette_id
    )
    assert parse_vignette_id(
        generate_vignette_id(study_id, **factor_levels)
    ) == Vignette(study_id, vignette_id, factor_levels)


def test_random_vignette_id_to_text(vignette_id_and_factors):
    """Test vignette creation by id with randomized values."""
    vignette_id, factor_levels, factor_dict = vignette_id_and_factors

    factor_list = list(factor_dict)
    random.shuffle(factor_list)

    vignette_template = "".join([f"${{{factor}}}" for factor in factor_list])
    vignette_expected = "".join(
        [f"{factor_dict[factor][factor_levels[factor]]}" for factor in factor_list]
    )

    database = MagicMock()
    database.get_vignette_template_by_id = MagicMock(return_value=vignette_template)

    with patch("agatha.backend.study.vignette_generator.database", database):
        vignette = generate_vignette(
            None,
            Vignette(study_id=1, vignette_id=vignette_id, factor_levels=factor_levels),
            factor_dict,
        )
        assert vignette == vignette_expected


def test_vignette_id_to_text():
    """Test vignette creation by id with static values."""
    vignette_id = '{"study_id": 1, "factor_levels": {"A": "1", "B": "2", "C": "3"}}'
    factor_dict = {
        "A": {
            "1": "x",
        },
        "B": {
            "2": "y",
        },
        "C": {
            "3": "z",
        },
    }
    vignette_template = "${A}${B}${C}"
    vignette_expected = "xyz"

    database = MagicMock()
    database.get_vignette_template_by_id = MagicMock(return_value=vignette_template)

    with patch("agatha.backend.study.vignette_generator.database", database):
        vignette = generate_vignette(
            None,
            parse_vignette_id(vignette_id),
            factor_dict,
        )
        assert vignette == vignette_expected


def test_vignette_generator_preset_value():
    """Test vignette generator with static values and one preset factor."""
    factor_dict = {
        "A": {
            "1": "x",
            "2": "x",
        },
        "B": {
            "1": "y",
            "2": "y",
        },
        "C": {
            "1": "z",
            "2": "z",
        },
    }
    vignette_template = "${A}${B}${C}"
    preset_factors = {
        "A": "1",
    }
    expected_ids = [
        '{"study_id": 1, "factor_levels": {"A": "1", "B": "1", "C": "1"}}',
        '{"study_id": 1, "factor_levels": {"A": "1", "B": "1", "C": "2"}}',
        '{"study_id": 1, "factor_levels": {"A": "1", "B": "2", "C": "1"}}',
        '{"study_id": 1, "factor_levels": {"A": "1", "B": "2", "C": "2"}}',
        '{"study_id": 1, "factor_levels": {"A": null, "B": "1", "C": "1"}}',
        '{"study_id": 1, "factor_levels": {"A": null, "B": "1", "C": "2"}}',
        '{"study_id": 1, "factor_levels": {"A": null, "B": "2", "C": "1"}}',
        '{"study_id": 1, "factor_levels": {"A": null, "B": "2", "C": "2"}}',
    ]

    database = MagicMock()
    database.get_vignette_template_by_id = MagicMock(return_value=vignette_template)
    database.get_factors = MagicMock(return_value=factor_dict)

    with patch("agatha.backend.study.vignette_generator.database", database):
        vignettes = generate_vignettes(None, **preset_factors)
        assert len(vignettes) == 8
        assert set(vignettes) == set(expected_ids)


def test_vignette_generator_preset_value_none():
    """Test vignette generator with static values and one factor preset to None."""
    factor_dict = {
        "A": {
            "1": "x",
            "2": "x",
        },
        "B": {
            "1": "y",
            "2": "y",
        },
        "C": {
            "1": "z",
            "2": "z",
        },
    }
    vignette_template = "${A}${B}${C}"
    preset_factors = {
        "A": None,
    }
    expected_ids = [
        '{"study_id": 1, "factor_levels": {"A": null, "B": "1", "C": "1"}}',
        '{"study_id": 1, "factor_levels": {"A": null, "B": "1", "C": "2"}}',
        '{"study_id": 1, "factor_levels": {"A": null, "B": "2", "C": "1"}}',
        '{"study_id": 1, "factor_levels": {"A": null, "B": "2", "C": "2"}}',
    ]

    database = MagicMock()
    database.get_vignette_template_by_id = MagicMock(return_value=vignette_template)
    database.get_factors = MagicMock(return_value=factor_dict)

    with patch("agatha.backend.study.vignette_generator.database", database):
        vignettes = generate_vignettes(None, **preset_factors)
        assert len(vignettes) == 4
        assert set(vignettes) == set(expected_ids)
