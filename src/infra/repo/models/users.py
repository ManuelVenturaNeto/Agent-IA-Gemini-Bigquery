from sqlalchemy import Column, Integer, String
from src.infra.config.database.db_base import Base


class User(Base):
    """
    SQLAlchemy model for the users table.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    company_id = Column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', company_id={self.company_id})>"