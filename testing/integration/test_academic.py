"""Student progress, semester submission, and cancellation integration tests."""

from datetime import datetime

from sqlmodel import Session, select

from app.models import CourseHistory, PlanItem, SemesterPlan


def test_progress_view_access(student_client, db_engine, accounts, courses):
    with Session(db_engine) as session:
        session.add_all(
            [
                CourseHistory(
                    course_code=courses.completed.course_code,
                    student_id=accounts.student.id,
                    semester_taken="Semester 1",
                    credits_earned=3,
                ),
                CourseHistory(
                    course_code=courses.planned[1].course_code,
                    student_id=accounts.other_student.id,
                    semester_taken="Semester 2",
                    credits_earned=3,
                ),
            ]
        )
        session.commit()

    response = student_client.get("/app/progress")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.template.name == "progress.html"
    assert response.context["user"].id == accounts.student.id
    progress = response.context["progress"]
    assert progress["completed_credits"] == 3
    assert progress["target_credits"] == 90
    assert progress["remaining_credits"] == 87
    assert progress["completed_courses"] == [
        {
            "code": courses.completed.course_code,
            "name": courses.completed.course_name,
            "credits": 3,
            "semester": "Semester 1",
        }
    ]
    assert "Your academic overview" in response.text
    assert courses.completed.course_name in response.text
    assert courses.planned[1].course_code not in response.text


def test_semester_plan_submission(student_client, db_engine, accounts, courses):
    course_codes = [course.course_code for course in courses.planned]
    before_submission = datetime.now().astimezone().date()

    response = student_client.post(
        "/app/plan-semester",
        data={
            "student_id": "816000001",
            "semester": "Semester 1",
            "student_notes": "Please review these courses.",
            # Despite its form name, advisor_id takes a username, not a DB ID.
            "advisor_id": accounts.admin.username,
            "course_codes": course_codes,
        },
    )

    assert response.status_code == 303
    assert response.headers["location"] == "https://testserver/app/plan-semester"
    with Session(db_engine) as session:
        plan = session.exec(select(SemesterPlan)).one()
        assert plan.student_id == accounts.student.id
        assert plan.advisor_id == accounts.admin.id
        assert plan.submitted_student_id == "816000001"
        assert plan.semester == "Semester 1"
        assert plan.student_notes == "Please review these courses."
        assert plan.status == "submitted"
        # Match the app's local date, including a request crossing midnight.
        assert (
            before_submission
            <= plan.submission_date
            <= datetime.now().astimezone().date()
        )
        items = session.exec(
            select(PlanItem)
            .where(PlanItem.plan_id == plan.plan_id)
            .order_by(PlanItem.course_order)
        ).all()
        assert [item.course_code for item in items] == course_codes
        assert [item.course_order for item in items] == [1, 2]


def test_semester_plan_cancellation(student_client, db_engine, submitted_plan):
    response = student_client.post(f"/app/plan-semester/{submitted_plan}/cancel")

    assert response.status_code == 303
    assert response.headers["location"] == "https://testserver/app/plan-semester"
    with Session(db_engine) as session:
        plan = session.get(SemesterPlan, submitted_plan)
        assert plan is not None
        assert plan.status == "cancelled"
        items = session.exec(
            select(PlanItem).where(PlanItem.plan_id == submitted_plan)
        ).all()
        assert len(items) == 2
