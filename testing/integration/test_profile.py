"""Profile form parsing, service validation, and persisted academic details."""

from sqlmodel import Session

from app.models import User


def test_profile_update_integration(student_client, db_engine, accounts):
    response = student_client.post(
        "/app/profile",
        data={
            "degree_name": "  BSc Software Engineering  ",
            "degree_level": "Level 3",
            "target_credits": "96",
            "required_core_courses": "18",
            "required_foundation_courses": "6",
            "required_elective_courses": "9",
        },
    )

    assert response.status_code == 303
    assert response.headers["location"] == "https://testserver/app/profile"
    # A fresh session checks committed data rather than a cached fixture object.
    with Session(db_engine) as session:
        student = session.get(User, accounts.student.id)
        assert student is not None
        assert student.degree_name == "BSc Software Engineering"
        assert student.degree_level == "Level 3"
        assert student.target_credits == 96
        assert student.required_core_courses == 18
        assert student.required_foundation_courses == 6
        assert student.required_elective_courses == 9
        assert student.username == accounts.student.username
        assert student.role == "student"
        assert session.get(User, accounts.admin.id).target_credits == 120

    profile = student_client.get("/app/profile")
    assert profile.status_code == 200
    assert profile.template.name == "profile.html"
    assert "BSc Software Engineering" in profile.text
