"""Admin role enforcement and advisor review persistence."""

import pytest
from sqlmodel import Session, select

from app.models import PlanItem, SemesterPlan


@pytest.mark.parametrize(
    ("path", "template", "context_key"),
    [
        ("/admin/requests", "admin.html", "requests"),
        ("/admin/dashboard", "admin-dashboard.html", "dashboard"),
    ],
)
@pytest.mark.parametrize("role", ["admin", "student"])
def test_admin_role_authorization(
    login, accounts, submitted_plan, path, template, context_key, role
):
    client = login(getattr(accounts, role))

    response = client.get(path)

    assert response.headers["content-type"].startswith("text/html")
    if role == "admin":
        assert response.status_code == 200
        assert response.template.name == template
        assert response.context["user"].id == accounts.admin.id
        assert context_key in response.context
        assert accounts.student.username in response.text
        assert "816000001" in response.text
    else:
        # The application's existing exception handler uses HTTP 200 here.
        # Check denial and absence of protected data, as agreed in the test plan.
        assert response.template.name == "401.html"
        assert "Unauthorized" in response.text
        assert "requests" not in response.context
        assert "dashboard" not in response.context
        assert "user" not in response.context
        assert accounts.student.username not in response.text
        assert "816000001" not in response.text


@pytest.mark.parametrize(
    ("decision", "feedback"),
    [
        ("approved", "  Your course selection is approved.  "),
        ("rejected", "  Please revise your course selection.  "),
    ],
)
def test_admin_plan_review_action(
    admin_client, db_engine, accounts, submitted_plan, decision, feedback
):
    response = admin_client.post(
        f"/admin/requests/{submitted_plan}/review",
        data={"decision": decision, "advisor_feedback": feedback},
    )

    assert response.status_code == 303
    assert response.headers["location"] == "https://testserver/admin/requests"
    with Session(db_engine) as session:
        plan = session.get(SemesterPlan, submitted_plan)
        assert plan is not None
        assert plan.status == decision
        assert plan.advisor_feedback == feedback.strip()
        assert plan.advisor_id == accounts.admin.id
        assert plan.student_id == accounts.student.id
        items = session.exec(
            select(PlanItem).where(PlanItem.plan_id == submitted_plan)
        ).all()
        assert len(items) == 2
