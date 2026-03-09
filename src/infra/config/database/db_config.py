import logging
import os
from typing import Any
from dotenv import load_dotenv
from google.cloud.sql.connector import Connector
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from .db_base import Base
from src.infra.settings.settings import settings

load_dotenv()


class DBConnectionHandler:
    """
    Class to manage database connections using SQLAlchemy.
    """

    def __init__(self) -> None:
        self.db_instance = settings.DB_INSTANCE_NAME
        self.db_user = settings.DB_USER
        self.db_password = settings.DB_PASSWORD
        self.db_name = settings.DB_NAME

        self.__connector = None

        self.__engine = create_engine(
            "postgresql+pg8000://",
            creator=self.get_connection,
        )

        self.session = None

        self.log = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )

    def get_connection(self) -> Any:
        """
        Create and return a database connection.
        """
        if self.__connector is None:
            self.__connector = Connector()

        conn = self.__connector.connect(
            instance_connection_string=self.db_instance,
            driver="pg8000",
            user=self.db_user,
            password=self.db_password,
            db=self.db_name,
        )
        self.log.info("Database connection established.")
        return conn

    def get_engine(self) -> Engine:
        """
        Return the SQLAlchemy engine instance.
        """
        self.log.info("Retrieving database engine.")
        return self.__engine

    def __enter__(self) -> "DBConnectionHandler":
        """
        Open a database session.
        """
        session_make = sessionmaker(bind=self.__engine)
        self.session = session_make()
        self.log.info("Database session opened.")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Close the database session.
        """
        self.log.info("Closing database session.")
        if self.session is not None:
            self.session.close()

    def create_tables(self) -> None:
        """
        Create all tables in the database.
        """
        Base.metadata.create_all(bind=self.__engine)
        self.log.info("Database tables created.")