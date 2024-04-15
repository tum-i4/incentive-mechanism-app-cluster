"""Tests for temporary user management in user study app."""

from unittest.mock import Mock

from pytest import fixture

from agatha.web_services.temp_user_management.user_management_logic import (
    TemporaryUserManagement,
)


@fixture
def session():
    """Mock session."""
    return Mock()


@fixture
def temporary_user_management():
    """TemporaryUserManagement."""
    return TemporaryUserManagement()


def test_create_new_user(
    temporary_user_management: TemporaryUserManagement, session: Mock
):
    """Test that create_new_user adds to the database and returns unique uuids."""
    uuid_1 = temporary_user_management.create_new_user(session)
    uuid_2 = temporary_user_management.create_new_user(session)
    assert session.add.call_count == 2
    assert uuid_1 != uuid_2
