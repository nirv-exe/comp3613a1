"""Semester-plan validation tests from the unit testing plan."""

from unittest.mock import Mock

import pytest

from app.repositories.academic import AcademicRepository
from app.services.academic_service import AcademicService


@pytest.fixture
def repository():
    return Mock(spec=AcademicRepository)


def test_review_plan_invalid_decision(repository):
    service = AcademicService(repository)

    with pytest.raises(ValueError) as error:
        service.review_plan(
            plan_id=1,
            advisor_id=2,
            decision="pending",
            advisor_feedback="Review notes",
        )

    assert str(error.value) == "Invalid review decision."
    repository.review_semester_plan.assert_not_called()


def test_review_plan_reject_no_feedback(repository):
    service = AcademicService(repository)

    with pytest.raises(ValueError) as error:
        service.review_plan(
            plan_id=1,
            advisor_id=2,
            decision="rejected",
            advisor_feedback=" ",
        )

    assert str(error.value) == "Feedback is required when rejecting a request."
    repository.review_semester_plan.assert_not_called()


def test_create_plan_duplicate_courses(repository):
    service = AcademicService(repository)

    with pytest.raises(ValueError) as error:
        service.create_plan(
            student_id=1,
            submitted_student_id="816000001",
            semester="Semester 1",
            student_notes="Proposed courses",
            advisor_username="advisor",
            course_codes=["COMP3613", "COMP3613"],
        )

    assert str(error.value) == "A course cannot be selected more than once."
    repository.create_semester_plan.assert_not_called()


def test_create_plan_missing_student_id(repository):
    service = AcademicService(repository)

    with pytest.raises(ValueError) as error:
        service.create_plan(
            student_id=1,
            submitted_student_id=" ",
            semester="Semester 1",
            student_notes="Proposed courses",
            advisor_username="advisor",
            course_codes=["COMP3613"],
        )

    assert str(error.value) == "Please enter your student ID before submitting."
    repository.create_semester_plan.assert_not_called()
