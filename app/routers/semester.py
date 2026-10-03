from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.academic import AcademicRepository
from app.services.academic_service import AcademicService
from app.utilities.flash import flash

from . import router, templates


@router.get("/app/plan-semester", response_class=HTMLResponse, name="plan_semester_view")
async def plan_semester_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    new: bool = False,
):
    service = AcademicService(AcademicRepository(db))
    courses = service.get_courses()
    plans = service.get_semester_plans(user.id)
    progress = service.get_degree_progress(user.id)
    return templates.TemplateResponse(
        request=request,
        name="plan-semester.html",
        context={
            "user": user,
            "courses": courses,
            "plans": plans,
            "progress": progress,
            "show_form": new,
        },
    )


@router.get(
    "/app/plan-semester/{plan_id}",
    response_class=HTMLResponse,
    name="semester_plan_detail_view",
)
async def semester_plan_detail_view(
    request: Request,
    plan_id: int,
    user: AuthDep,
    db: SessionDep,
):
    service = AcademicService(AcademicRepository(db))
    details = service.get_semester_plan_details(user.id, plan_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Semester request not found")

    plan, items = details
    progress = service.get_degree_progress(user.id)
    return templates.TemplateResponse(
        request=request,
        name="semester-plan-detail.html",
        context={"user": user, "plan": plan, "items": items, "progress": progress},
    )


@router.post(
    "/app/plan-semester/{plan_id}/cancel",
    response_class=HTMLResponse,
    name="semester_plan_cancel",
)
async def semester_plan_cancel(
    request: Request,
    plan_id: int,
    user: AuthDep,
    db: SessionDep,
):
    service = AcademicService(AcademicRepository(db))
    if service.cancel_plan(user.id, plan_id) is None:
        raise HTTPException(
            status_code=409,
            detail="This request cannot be cancelled.",
        )

    flash(request, "Semester request cancelled.", "success")
    return RedirectResponse(
        url=request.url_for("plan_semester_view"),
        status_code=303,
    )


@router.post("/app/plan-semester", response_class=HTMLResponse, name="plan_semester_submit")
async def plan_semester_submit(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    student_id: str = Form(""),
    semester: str = Form(""),
    student_notes: str = Form(""),
    advisor_id: str = Form(""),
    course_codes: list[str] = Form([]),
):
    repo = AcademicRepository(db)
    service = AcademicService(repo)
    selected_courses = [code for code in course_codes if code]
    try:
        service.create_plan(
            user.id,
            student_id.strip(),
            semester,
            student_notes,
            advisor_id,
            selected_courses,
        )
    except ValueError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(
            url=f"{request.url_for('plan_semester_view')}?new=true",
            status_code=303,
        )
    flash(request, "Semester request submitted successfully.", "success")
    
    return RedirectResponse(url=request.url_for("plan_semester_view"), status_code=303,)


@router.get("/app/history", response_class=HTMLResponse, name="progress_history_view")
async def progress_history_view(request: Request, user: AuthDep, db: SessionDep):
    history = AcademicService(AcademicRepository(db)).get_course_history(user.id)
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={"user": user, "history": history},
    )
