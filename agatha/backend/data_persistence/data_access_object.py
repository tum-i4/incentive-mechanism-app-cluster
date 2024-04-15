"""Provides a parent class for data access objects."""

from agatha.backend.data_persistence.database import Database


class AbstractDataAccessObject:
    """Class for basic interaction with sqlalchmey database."""

    def __init__(self, database_url: str, sqlalchemy_declarative_base_class):
        """Init database and session."""
        self.database = Database(database_url)
        sqlalchemy_declarative_base_class.metadata.create_all(bind=self.database.engine)

    def __call__(self):
        """Callable class to enable dependency injection by FastAPI."""
        session = self.database.SessionLocal()
        try:
            yield session
        finally:
            session.close()
