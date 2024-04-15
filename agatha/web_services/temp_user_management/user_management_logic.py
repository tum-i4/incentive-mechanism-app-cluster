"""Logic module for user study user management."""

from uuid import uuid4

from sqlalchemy.orm import Session

from agatha.backend.data_persistence.study_crud import StudyDataAccessObject
from agatha.backend.data_persistence.study_models import User
from agatha.util import singleton


@singleton
class TemporaryUserManagement:
    """Temporary User Management logic layer service."""

    def __init__(self):
        """Init self."""
        self.dao = StudyDataAccessObject()

    def create_new_user(self, session: Session) -> User:
        """Create a new user.

        Generates a random new UUID, saves it to the database and returns the
        UUID.
        """
        new_user_uuid = uuid4()
        return self.dao.create_user_by_uuid(session, new_user_uuid.hex)
