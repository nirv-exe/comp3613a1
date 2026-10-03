from fastapi import Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.academic import AcademicRepository
from app.services.academic_service import AcademicService

from . import router, templates


@router.get("/app/progress", response_class=HTMLResponse, name="progress_view")
async def progress_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    repo = AcademicRepository(db)
    service = AcademicService(repo)
    progress = service.get_degree_progress(user.id)
    
    return templates.TemplateResponse(
        request=request,
        name="progress.html",
        context={"user": user, "progress": progress},
    )
