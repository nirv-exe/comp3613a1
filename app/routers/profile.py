from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.user import UserRepository
from app.services.user_service import UserService
from app.utilities.flash import flash
from . import router, templates


@router.get("/app/profile", response_class=HTMLResponse, name="profile_view")
async def profile_view(request: Request, user: AuthDep):
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"user": user},
    )


@router.post("/app/profile", name="profile_update")
async def profile_update(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    degree_name: str = Form(""),
    degree_level: str = Form(""),
    target_credits: str = Form(""),
    required_core_courses: str = Form(""),
    required_foundation_courses: str = Form(""),
    required_elective_courses: str = Form(""),
):
    try:
        UserService(UserRepository(db)).update_academic_details(
            user.id,
            degree_name,
            degree_level,
            target_credits,
            required_core_courses,
            required_foundation_courses,
            required_elective_courses,
        )
    except ValueError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(
            url=request.url_for("profile_view"), status_code=303
        )

    flash(request, "Academic details updated.", "success")
    return RedirectResponse(url=request.url_for("profile_view"), status_code=303)
