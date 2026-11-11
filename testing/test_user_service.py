"""Academic-details validation tests from the unit testing plan."""

from unittest.mock import Mock

import pytest

from app.repositories.user import UserRepository
from app.services.user_service import UserService


@pytest.fixture
def repository():
    return Mock(spec=UserRepository)


@pytest.fixture
def academic_details():
    """Valid baseline so each test isolates one invalid field."""
    return {
        "user_id": 1,
        "degree_name": "BSc Computer Science",
        "degree_level": "Level 3",
        "target_credits": "90",
        "required_core_courses": "15",
        "required_foundation_courses": "3",
        "required_elective_courses": "6",
    }


def test_update_academic_details_invalid_level(repository, academic_details):
    service = UserService(repository)
    academic_details["degree_level"] = "Level 5"

    with pytest.raises(ValueError) as error:
        service.update_academic_details(**academic_details)

    assert str(error.value) == "Please select a valid degree level."
    repository.update_academic_details.assert_not_called()


def test_update_academic_details_invalid_type(repository, academic_details):
    service = UserService(repository)
    academic_details["target_credits"] = "Ninety"

    with pytest.raises(ValueError) as error:
        service.update_academic_details(**academic_details)

    assert str(error.value) == "Course and credit requirements must be whole numbers."
    repository.update_academic_details.assert_not_called()


def test_update_academic_details_negative_credits(repository, academic_details):
    service = UserService(repository)
    academic_details["target_credits"] = -10

    with pytest.raises(ValueError) as error:
        service.update_academic_details(**academic_details)

    assert str(error.value) == "Target credits must be greater than zero."
    repository.update_academic_details.assert_not_called()
