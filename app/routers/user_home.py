from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, IsUserLoggedIn, get_current_user, is_admin
from app.repositories.academic import AcademicRepository
from app.services.academic_service import AcademicService
from . import router, templates


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db:SessionDep
):
    progress = AcademicService(AcademicRepository(db)).get_degree_progress(user.id)
    return templates.TemplateResponse(
        request=request, 
        name="app.html",
        context={
            "user": user,
            "progress": progress,
        }
    )