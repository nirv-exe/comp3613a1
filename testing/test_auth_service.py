"""Authentication test from the unit testing plan."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.repositories.user import UserRepository
from app.services.auth_service import AuthService
from app.utilities.security import encrypt_password


def test_authenticate_user_invalid_password():
    repository = Mock(spec=UserRepository)
    repository.get_by_username.return_value = SimpleNamespace(
        id=1,
        username="valid_user",
        password=encrypt_password("correctpass"),
        role="student",
    )
    service = AuthService(repository)

    with patch("app.services.auth_service.create_access_token") as create_token:
        result = service.authenticate_user(
            username="valid_user", password="wrongpass"
        )

    assert result is None
    repository.get_by_username.assert_called_once_with("valid_user")
    create_token.assert_not_called()
