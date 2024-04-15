"""Functionality for the logout button."""

from browser import document, window  # type: ignore # pylint: disable=import-error


def logout(_):
    """Clear cookie and redirect to login page."""
    document.cookie = "agatha-auth=; Path=/"
    temp_anchor = document.createElement("a")
    current_path = window.location.href.split("/")[-1]
    temp_anchor.href = window.location.href.split(current_path)[0]
    temp_anchor.click()


def bind_logout_event():
    """Bind clear cookie event to logout button click."""
    document["logout-btn"].bind("click", logout)
