import logging
from typing import Optional
from sqlalchemy.orm import Session
from src.infra.config.database.db_config import DBConnectionHandler
from src.infra.repo.models.users import User


class UsersRepository:
    """
    Repository for User queries.
    """

    def __init__(self) -> None:
        self.log = logging.getLogger(self.__class__.__name__)
        self.db_handler = DBConnectionHandler()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Return a single user by ID, or None if not found.
        """
        with self.db_handler as db:
            session: Session = db.session
            user = session.query(User).filter(User.id == user_id).first()
            self.log.info(f"get_user_by_id({user_id}) -> {user}")
            return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Return a single user by email, or None if not found.
        """
        with self.db_handler as db:
            session: Session = db.session
            user = session.query(User).filter(User.email == email).first()
            self.log.info(f"get_user_by_email({email}) -> {user}")
            return user
