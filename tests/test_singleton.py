"""Test agatha.util.Singleton."""

from unittest.mock import Mock

import pytest

from agatha.util import singleton


def test_singleton_general_behavior():
    """Test that all Singleton instances act as one."""

    @singleton
    class Test:
        """Singleton class for testing."""

        def __init__(self):
            self.variable = 0

        def inc(self):
            """Increment `variable`."""
            self.variable += 1

    instance1 = Test()
    assert instance1.variable == 0
    instance1.inc()
    assert instance1.variable == 1
    instance2 = Test()
    assert instance2.variable == 1


def test_singleton_init():
    """Test that the Singleton's init function only gets called on first instantiation."""
    mock_init = Mock()

    @singleton
    class Test:
        """Singleton class for testing."""

        def __init__(self):
            mock_init()

    Test()
    Test()
    mock_init.assert_called_once()


def test_singleton_init_with_parameters():
    """Test that the Singleton's init function gets called with the right arguments."""
    mock_init = Mock()

    @singleton
    class Test:
        """Singleton class for testing."""

        def __init__(self, test: str, value: int):
            mock_init(test, value=value)

    Test("test", value=2)

    mock_init.assert_called_once_with("test", value=2)


def test_singleton_new_with_parameters():
    """Test that the Singleton's new function gets called with the right arguments."""
    mock_new = Mock()

    @singleton
    class Test:
        """Singleton class for testing."""

        def __new__(cls, test: str, value: int):
            mock_new(test, value=value)

    Test("test", value=2)

    mock_new.assert_called_once_with("test", value=2)


def test_singleton_without_defined_init():
    """Test that Singleton works without having to define `__init__`."""

    @singleton
    class Test:
        """Singleton class for testing."""

        def __init__(self, variable):
            self.variable = variable

    instance1 = Test(0)
    instance2 = Test(10)
    assert instance2.variable == 0
    instance2.variable = 10
    assert instance1.variable == 10


def test_existing_singleton_variable_raises():
    """Test that defining a singleton class with an existing `_singleton` variable raises."""
    with pytest.raises(TypeError):

        @singleton
        class Test:  # pylint: disable-msg=unused-variable
            """Singleton class for testing."""

            _singleton = 0


def test_singleton_wrapper_transparency():
    """Test that Singleton class retains its type."""

    class Test:
        """Singleton class for testing."""

    Test_Singleton = singleton(Test)

    assert issubclass(Test_Singleton, Test)
