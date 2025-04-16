import datetime
import csv
import os.path
from loguru import logger
from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi import Request

from ..workers.db_worker import DBWorker
from ..application.exceptions import (
    TaskNotFoundError,
    InvalidDateFormatError,
    NotFullDataError,
)
from ..application.utils import get_deadline
from ..application.benchmarking import measure_time

router = APIRouter(responses={404: {"description": "Not found"}}, tags=["tasks"])


@router.get("/", response_class=HTMLResponse, name="read_root")
async def read_root(request: Request):
    return request.app.state.templates.TemplateResponse(
        "menu.html", {"request": request}
    )


@router.get("/search_task", response_class=HTMLResponse)
async def search_task_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "search_task.html", {"request": request}
    )


@router.get("/add_task_page", response_class=HTMLResponse)
async def add_task_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "add_task.html", {"request": request}
    )


@router.post("/add_task", response_class=HTMLResponse)
@measure_time
async def add_task(
    request: Request,
    name: str = Form(...),
    year: int = Form(...),
    month: int = Form(...),
    day: int = Form(...),
    comment: str = Form(...),
):
    db_worker: DBWorker = request.app.state.db_worker
    name = name.capitalize()
    try:
        deadline = await get_deadline(year=year, month=month, day=day)
        if deadline < datetime.datetime.now():
            error_message = f"Введите другое значение для времени выполнения задачи"
            return request.app.state.templates.TemplateResponse(
                "add_task.html",
                {"request": request, "error_message": error_message},
                status_code=422,
            )
        tasks = await db_worker.get_tasks(name=name, from_date=deadline, to_date=deadline)
        if tasks:
            error_message = f"Задача с таким названием и сроком выполнения уже существует id {tasks[0].id}"
            return request.app.state.templates.TemplateResponse(
                "add_task.html", {"request": request, "error_message": error_message},
                status_code=422,
            )
    except (NotFullDataError, InvalidDateFormatError) as e:
        logger.error(e.reason)
        error_message = f"Вы ввели неправильное время: {year}-{month}-{day}"
        return request.app.state.templates.TemplateResponse(
            "search_task.html",
            {"request": request, "error_message": error_message},
            status_code=422,
        )
    except Exception as e:
        if e.__class__ != TaskNotFoundError:
            logger.error(f"Failed to check task: {e.__class__.__name__}, {e}")
            error_message = f"Ошибка приложения: {e}"
            return request.app.state.templates.TemplateResponse(
                "add_task.html",
                {"request": request, "error_message": error_message},
                status_code=404,
            )
    try:
        await db_worker.add_task(name=name, comment=comment, deadline=deadline)
        message = "Задача добавлена"
        return request.app.state.templates.TemplateResponse(
            "add_task.html", {"request": request, "message": message}
        )
    except Exception as e:
        error_message = f"Не удалось сохранить задачу"
        logger.error(error_message + f" {e.__class__.__name__}, {e}")
        return request.app.state.templates.TemplateResponse(
            "add_task.html",
            {"request": request, "error_message": error_message},
            status_code=500,
        )


@router.get("/show_task/{task_id}", response_class=HTMLResponse)
async def show_task(request: Request, task_id: int):
    db_worker: DBWorker = request.app.state.db_worker
    try:
        task = await db_worker.get_tasks(task_id=task_id)
        return request.app.state.templates.TemplateResponse(
            "show_task.html", {"request": request, "task": task[0]}
        )
    except TaskNotFoundError:
        logger.error(f"Task {task_id} not found")
        error_message = f"Не удалось найти задачу {task_id}."
        return request.app.state.templates.TemplateResponse(
            "show_tasks.html",
            {"request": request, "error_message": error_message},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e.__class__.__name__}, {e}")
        error_message = f"Не удалось найти задачу {e.__class__.__name__}, {e}."
        return request.app.state.templates.TemplateResponse(
            "show_tasks.html",
            {"request": request, "error_message": error_message},
            status_code=500,
        )


@router.post("/search_task", response_class=HTMLResponse)
@measure_time
async def search_task(
    request: Request,
    name: str | None = Form(None),
    comment: str | None = Form(None),
    start_year: str | None = Form(None),
    start_month: str | None = Form(None),
    start_day: str | None = Form(None),
    end_year: str | None = Form(None),
    end_month: str | None = Form(None),
    end_day: str | None = Form(None),
    done: str | None = Form(None),
):
    db_worker: DBWorker = request.app.state.db_worker
    if name:
        name = name.capitalize()
    if done:
        done = done == "True"
    try:
        from_date = await get_deadline(start_year, start_month, start_day)
    except (NotFullDataError, InvalidDateFormatError) as e:
        logger.error(e.reason)
        error_message = f"Вы ввели неправильное начальное время поиска: {start_year}-{start_month}-{start_day}"
        return request.app.state.templates.TemplateResponse(
            "search_task.html",
            {"request": request, "error_message": error_message},
            status_code=422,
        )

    try:
        to_date = await get_deadline(end_year, end_month, end_day)
    except (NotFullDataError, InvalidDateFormatError) as e:
        logger.error(e)
        error_message = f"Вы ввели неправильное начальное время поиска: {end_year}-{end_month}-{end_day}"
        return request.app.state.templates.TemplateResponse(
            "search_task.html",
            {"request": request, "error_message": error_message},
            status_code=422,
        )
    try:
        tasks = await db_worker.get_tasks(
            name=name, from_date=from_date, to_date=to_date, comment=comment, done=done
        )
        return request.app.state.templates.TemplateResponse(
            "show_tasks.html", {"request": request, "tasks": tasks}
        )
    except TaskNotFoundError:
        logger.error("Tasks not found")
        error_message = f"Задачи по данным фильтрам не найдены"
        return request.app.state.templates.TemplateResponse(
            "search_task.html",
            {"request": request, "error_message": error_message},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"Failed to get tasks: {e.__class__.__name__}, {e}")
        error_message = f"Не удалось получить задачи: {e}"
        return request.app.state.templates.TemplateResponse(
            "search_task.html",
            {"request": request, "error_message": error_message},
            status_code=500,
        )


@router.get("/download", response_class=HTMLResponse, name="download")
async def download(request: Request):
    db_worker: DBWorker = request.app.state.db_worker
    try:
        tasks = await db_worker.get_tasks()
    except TaskNotFoundError:
        error_message = "Не найдено задач для скачивания"
        return request.app.state.templates.TemplateResponse(
            "download.html",
            {"request": request, "error_message": error_message},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"Failed to get tasks to download: {e.__class__.__name__}, {e}")
        error_message = f"Ошибка при поиске задач - {e.__class__.__name__}, {e}"
        return request.app.state.templates.TemplateResponse(
            "download.html",
            {"request": request, "error_message": error_message},
            status_code=500,
        )
    csv_file = f'tasks_{datetime.datetime.now().strftime("%Y_%m_%d")}.csv'

    with open(csv_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "id",
                "Название",
                "Выполнить до",
                "Комментарий",
                "Уведомление",
                "Выполнено",
            ]
        )
        for task in tasks:
            writer.writerow(
                [
                    task.id,
                    task.name,
                    task.deadline.strftime("%Y-%m-%d"),
                    task.comment,
                    "Да" if task.done else "Нет",
                ]
            )
        response = FileResponse(
            path=csv_file,
            media_type="text/csv",
            filename=os.path.basename(csv_file)
        )
        response.headers["Content-Disposition"] = f"attachment; filename={os.path.basename(csv_file)}"

        return response


@router.get("/update_task", response_class=HTMLResponse)
async def update_task(request: Request):
    return request.app.state.templates.TemplateResponse(
        "update_task.html", {"request": request}
    )


@router.post("/update_task", response_class=HTMLResponse)
@measure_time
async def update_task(
    request: Request,
    name: str = Form(None),
    comment: str | None = Form(None),
    year: str | None = Form(None),
    month: str | None = Form(None),
    day: str | None = Form(None),
    new_year: str | None = Form(None),
    new_month: str | None = Form(None),
    new_day: str | None = Form(None),
    done: str | None = Form(None),
):
    db_worker: DBWorker = request.app.state.db_worker
    name = name.capitalize()
    try:
        deadline = await get_deadline(year=year, month=month, day=day)
        new_deadline = await get_deadline(year=new_year, month=new_month, day=new_day)
        if new_deadline and new_deadline < datetime.datetime.now():
            error_message = f"Введите другое значение для времени выполнения задачи"
            return request.app.state.templates.TemplateResponse(
                "add_task.html",
                {"request": request, "error_message": error_message},
                status_code=422,
            )
    except (NotFullDataError, InvalidDateFormatError) as e:
        logger.error(e)
        error_message = f"Вы ввели неправильное время {year}-{month}-{day} {new_year}-{new_month}-{new_day}"
        return request.app.state.templates.TemplateResponse(
            "update_task.html",
            {"request": request, "error_message": error_message},
            status_code=422,
        )
    try:
        task = await db_worker.update_task(
            name=name,
            deadline=deadline,
            new_deadline=new_deadline,
            comment=comment,
            done=done,
        )
        return request.app.state.templates.TemplateResponse(
            "show_task.html",
            {"request": request, "task": task, "message": "Задача обновлена"},
        )
    except TaskNotFoundError:
        logger.error(f"Task with name {name} wasn't found")
        error_message = f"Задача с названием {name} не найдена"
        return request.app.state.templates.TemplateResponse(
            "update_task.html",
            {"request": request, "error_message": error_message},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"Failed to get tasks: {e.__class__.__name__}, {e}")
        error_message = f"Не удалось получить задачи: {e}"
        return request.app.state.templates.TemplateResponse(
            "search_task.html",
            {"request": request, "error_message": error_message},
            status_code=500,
        )


@router.get("/delete_task")
async def delete_task(request: Request):
    return request.app.state.templates.TemplateResponse(
        "delete_task.html", {"request": request}
    )


@router.post("/delete_task")
@measure_time
async def delete_task(
    request: Request,
    name: str | None = Form(None),
    year: str | None = Form(None),
    month: str | None = Form(None),
    day: str | None = Form(None),
    done: str | None = Form(None),
):
    db_worker: DBWorker = request.app.state.db_worker
    if done and eval(done):
        try:
            await db_worker.delete_done_tasks()
            return request.app.state.templates.TemplateResponse(
                "delete_task.html", {"request": request, "message": "Задачи удалены"}
            )
        except Exception as e:
            logger.error(f"Failed to delete done tasks: {e.__class__.__name__}, {e}")
            error_message = f"Не удалось удалить задачи: {e}."
            return request.app.state.templates.TemplateResponse(
                "delete_task.html",
                {"request": request, "error_message": error_message},
                status_code=500,
            )
    if not name or any(not i for i in (month, year, day)):
        logger.error(f"Wrong request format")
        error_message = f"Чтобы удалить задачу введите её название и срок выполнения."
        return request.app.state.templates.TemplateResponse(
            "delete_task.html",
            {"request": request, "error_message": error_message},
            status_code=422,
        )
    try:
        deadline = await get_deadline(year=year, month=month, day=day)
    except (NotFullDataError, InvalidDateFormatError) as e:
        logger.error(e)
        error_message = (
            f"Вы ввели неправильное время выполнения задачи: {year}-{month}-{day}"
        )
        return request.app.state.templates.TemplateResponse(
            "delete_task.html",
            {"request": request, "error_message": error_message},
            status_code=422,
        )
    name = name.capitalize()
    try:
        await db_worker.delete_task(name=name, deadline=deadline)
        return request.app.state.templates.TemplateResponse(
            "delete_task.html",
            {
                "request": request,
                "message": f"Задача удалена",
            },
        )
    except TaskNotFoundError:
        logger.error(f"Task {name} not found")
        error_message = f"Задача {name} с датой выполнения до {deadline.strftime('%Y-%m-%d')} не найдена"
        return request.app.state.templates.TemplateResponse(
            "delete_task.html",
            {"request": request, "error_message": error_message},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"Failed to delete tasks: {e.__class__.__name__}, {e}")
        error_message = f"Не удалось удалить задачу: {e}"
        return request.app.state.templates.TemplateResponse(
            "delete_task.html",
            {"request": request, "error_message": error_message},
            status_code=500,
        )


@router.get("/show_tasks/{date}")
async def show_tasks(request: Request, date: str):
    db_worker = request.app.state.db_worker
    date = datetime.datetime.strptime(date, "%Y-%m-%d")
    tasks = await db_worker.get_tasks(from_date=date, to_date=date)
    return request.app.state.templates.TemplateResponse(
        "show_tasks.html", {"request": request, "tasks": tasks}
    )


@router.get("/get_all_tasks")
async def get_all_tasks(request: Request):
    db_worker: DBWorker = request.app.state.db_worker
    try:
        all_tasks = await db_worker.get_tasks()
        return request.app.state.templates.TemplateResponse(
            "show_tasks.html", {"request": request, "tasks": all_tasks}
        )
    except TaskNotFoundError:
        logger.error(f"No tasks found")
        error_message = f"Список задач пуст"
        return request.app.state.templates.TemplateResponse(
            "show_tasks.html", {"request": request, "error_message": error_message},
            status_code=404
        )

