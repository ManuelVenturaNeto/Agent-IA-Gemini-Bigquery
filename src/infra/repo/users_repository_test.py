import logging
import pytest
from src.infra.repo.users_repository import UsersRepository


# @pytest.mark.skip(reason="Sensitive test")
def test_get_user_by_id():
    repo = UsersRepository()
    user = repo.get_user_by_id(1)

    assert user is not None
    assert user.id == 1


# @pytest.mark.skip(reason="Sensitive test")
def test_get_user_by_email():
    repo = UsersRepository()
    user = repo.get_user_by_email("user050@empresa.com")

    assert user is not None
    assert user.email == "user050@empresa.com"
