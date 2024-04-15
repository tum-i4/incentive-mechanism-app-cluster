"""Tests for the agatha.util.config module."""

import os
from unittest import mock

from pytest import fixture

from agatha.util.config import Config


@fixture(autouse=True)
def singleton_reset():
    """Reset the singleton Config before each test."""
    if getattr(type(Config()), "_singleton", None) is not None:
        setattr(type(Config()), "_singleton", None)


def test_env_overwrite_default():
    """Test if environment-variable overwrites defaults."""
    before = Config.conf["development_mode"]
    with mock.patch.dict(os.environ, {"AGATHA_DEVELOPMENT_MODE": str(not before)}):
        Config()
        after = Config.conf["development_mode"]
    assert before != after


def test_cli_overwrite_default():
    """Test if cli-arguments overwrite defaults."""
    before = Config.conf["development_mode"]
    Config(development_mode=(not before))
    after = Config.conf["development_mode"]
    assert before != after


def test_cli_overwrite_all():
    """Test if cli-arguments overwrite defaults and env-variables."""
    before = Config.conf["development_mode"]
    with mock.patch.dict(os.environ, {"AGATHA_DEVELOPMENT_MODE": str(not before)}):
        Config(development_mode=str(before).upper())
        after = Config.conf["development_mode"]
        assert after == str(before).upper()
