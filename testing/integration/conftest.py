"""Integration fixtures using real application layers and a disposable database."""

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import database
from app.models import Course, PlanItem, SemesterPlan, User
from app.utilities.security import encrypt_password


@pytest.fixture
def db_engine(monkeypatch):
    # StaticPool shares one in-memory database with TestClient's worker thread.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    # Redirect startup, request sessions, and schema recovery to the test DB.
    # The configured application database is never connected to by these tests.
    monkeypatch.setattr(database, "engine", engine)
    try:
        SQLModel.metadata.create_all(engine)
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def accounts(db_engine):
    password = "integration-test-password"
    password_hash = encrypt_password(password)
    student = User(
        username="integration_student",
        email="student@example.com",
        password=password_hash,
        role="student",
        degree_name="BSc Computer Science",
        degree_level="Level 2",
        target_credits=90,
        required_core_courses=15,
        required_foundation_courses=3,
        required_elective_courses=6,
    )
    admin = User(
        username="admin",
        email="advisor@example.com",
        password=password_hash,
        role="admin",
    )
    other_student = User(
        username="other_student",
        email="other@example.com",
        password=password_hash,
        role="student",
    )
    with Session(db_engine) as session:
        session.add_all([student, admin, other_student])
        session.commit()
        for user in (student, admin, other_student):
            session.refresh(user)
    return SimpleNamespace(
        student=student, admin=admin, other_student=other_student, password=password
    )


@pytest.fixture
def courses(db_engine):
    completed = Course(
        course_code="COMP1601",
        course_name="Computer Programming I",
        credit_amt=3,
        course_type="core",
    )
    planned = [
        Course(
            course_code="COMP3613",
            course_name="Software Engineering II",
            credit_amt=3,
            course_type="core",
        ),
        Course(
            course_code="COMP3603",
            course_name="Human Computer Interaction",
            credit_amt=3,
            course_type="elective",
        ),
    ]
    with Session(db_engine) as session:
        session.add_all([completed, *planned])
        session.commit()
        for course in (completed, *planned):
            session.refresh(course)
    return SimpleNamespace(completed=completed, planned=planned)


@pytest.fixture
def submitted_plan(db_engine, accounts, courses):
    """Seed a pending request independently of the submission route under test."""
    with Session(db_engine) as session:
        plan = SemesterPlan(
            student_id=accounts.student.id,
            advisor_id=accounts.admin.id,
            submitted_student_id="816000001",
            semester="Semester 1",
            status="submitted",
            submission_date=date(2026, 1, 15),
            student_notes="Please review my course selection.",
        )
        session.add(plan)
        session.commit()
        session.refresh(plan)
        plan_id = plan.plan_id
        session.add_all(
            [
                PlanItem(
                    plan_id=plan_id,
                    course_code=course.course_code,
                    course_order=order,
                )
                for order, course in enumerate(courses.planned, start=1)
            ]
        )
        session.commit()
    return plan_id


@pytest.fixture
def client(db_engine):
    from app.main import app

    # HTTPS also allows the real Secure cookies when ENV is production.
    # Keep redirects visible so a validation redirect cannot look like success.
    with TestClient(
        app, base_url="https://testserver", follow_redirects=False
    ) as test_client:
        yield test_client


@pytest.fixture
def login(client, accounts):
    def login_as(user):
        client.cookies.clear()
        response = client.post(
            "/login",
            data={"username": user.username, "password": accounts.password},
        )
        assert response.status_code == 303
        destination = "/admin/dashboard" if user.role == "admin" else "/app"
        assert response.headers["location"] == f"https://testserver{destination}"
        assert client.cookies.get("access_token")
        return client

    return login_as


@pytest.fixture
def student_client(login, accounts):
    return login(accounts.student)


@pytest.fixture
def admin_client(login, accounts):
    return login(accounts.admin)
