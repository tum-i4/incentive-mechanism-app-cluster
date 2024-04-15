"""Provides initialization functionality for sqlalchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Database:
    """Class to init and hold info for database access."""

    def __init__(self, database_url: str):
        """Init sqlalchmey engine and create a session factory."""
        self.engine = create_engine(
            database_url, connect_args={"check_same_thread": False}
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
