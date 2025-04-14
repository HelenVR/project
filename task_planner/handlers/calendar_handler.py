import datetime
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request

from ..workers.db_worker import DBWorker

router = APIRouter(responses={404: {"description": "Not found"}}, tags=["calendar"])


@router.get("/year_calendar", response_class=HTMLResponse)
async def year_calendar(request: Request):
    year = datetime.datetime.now().year
    months = request.app.state.months
    return request.app.state.templates.TemplateResponse(
        "year_calendar.html", {"request": request, "year": year, "months": months}
    )


@router.get("/read_calendar/{year}/{month}", response_class=HTMLResponse)
async def read_calendar(request: Request, month: int = None, year: int = None):
    db_worker: DBWorker = request.app.state.db_worker
    month_name = request.app.state.months[month - 1]
    days = await db_worker.generate_calendar(year, month)
    return request.app.state.templates.TemplateResponse(
        "show_calendar.html",
        {"request": request, "days": days, "month_name": month_name, "year": year},
    )

