"""Tests for agatha metadata."""

from agatha import __version__


def test_version():
    """Test for agatha version."""
    assert __version__ == "0.1.0"
