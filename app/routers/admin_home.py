from fastapi import APIRouter, Form, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep, IsUserLoggedIn, get_current_user, is_admin
from app.repositories.academic import AcademicRepository
from app.services.academic_service import AcademicService
from app.utilities.flash import flash
from . import router, templates


@router.get("/admin/dashboard", response_class=HTMLResponse, name="admin_dashboard_view")
async def admin_dashboard_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    dashboard = AcademicService(AcademicRepository(db)).get_advisor_dashboard()
    return templates.TemplateResponse(
        request=request,
        name="admin-dashboard.html",
        context={"user": user, "dashboard": dashboard},
    )


@router.get("/admin", name="admin_home_view")
async def admin_home_view(
    request: Request,
    user: AdminDep,
):
    return RedirectResponse(
        url=request.url_for("admin_dashboard_view"),
        status_code=303,
    )


@router.get(
    "/admin/requests",
    response_class=HTMLResponse,
    name="admin_requests_view",
)
async def admin_requests_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    service = AcademicService(AcademicRepository(db))
    requests = service.get_advisor_requests()

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user": user,
            "requests": requests,
        },
    )


@router.get(
    "/admin/requests/{plan_id}",
    response_class=HTMLResponse,
    name="admin_plan_detail_view",
)
async def admin_plan_detail_view(
    request: Request,
    plan_id: int,
    user: AdminDep,
    db: SessionDep,
):
    service = AcademicService(AcademicRepository(db))
    details = service.get_advisor_plan_details(plan_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Request not found")

    plan, student, items = details
    progress = service.get_degree_progress(student.id)
    return templates.TemplateResponse(
        request=request,
        name="admin-plan-detail.html",
        context={
            "user": user,
            "plan": plan,
            "student": student,
            "items": items,
            "progress": progress,
        },
    )


@router.post(
    "/admin/requests/{plan_id}/review",
    response_class=HTMLResponse,
    name="admin_plan_review_action",
)
async def admin_plan_review_action(
    request: Request,
    plan_id: int,
    user: AdminDep,
    db: SessionDep,
    decision: str = Form(...),
    advisor_feedback: str = Form(""),
):
    service = AcademicService(AcademicRepository(db))
    try:
        result = service.review_plan(plan_id, user.id, decision, advisor_feedback)
    except ValueError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(
            url=request.url_for("admin_plan_detail_view", plan_id=plan_id),
            status_code=303,
        )
    if result is None:
        raise HTTPException(
            status_code=409,
            detail="This request has already been reviewed.",
        )

    decision_label = "approved" if decision == "approved" else "rejected"
    flash(request, f"Request REQ-{plan_id:04d} {decision_label}.", "success")
    return RedirectResponse(
        url=request.url_for("admin_requests_view"),
        status_code=303,
    )
