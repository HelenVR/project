from fastapi import APIRouter, Request
from fastapi.responses import ORJSONResponse, Response
from loguru import logger

from ..application.models import TasksCountResponse, TasksInfoResponse, TaskRequest, TaskInfo
from ..application.benchmarking import measure_time
from ..workers.db_worker import DBWorker
from ..application.exceptions import TaskNotFoundError


router = APIRouter(prefix="/api", responses={404: {"description": "Not found"}}, tags=["tasks"])


@router.get('/tasks_count')
@measure_time
async def get_tasks_count(request: Request):
    db_worker: DBWorker = request.app.state.db_worker
    try:
        all_tasks = await db_worker.get_tasks(for_calendar=True)
        return TasksCountResponse(tasks_count=(len(all_tasks)))
    except Exception as e:
        logger.error(f'Failed to get tasks: {e.__class__.__name__}, {e}')
        error_message = {"error": f"Ошибка приложения, не удалось получить задачи"}
        return ORJSONResponse(status_code=500, content=error_message)


@router.get('/tasks_info')
@measure_time
async def get_tasks_info(request: Request):
    db_worker: DBWorker = request.app.state.db_worker
    try:
        all_tasks = await db_worker.get_tasks(for_calendar=True)
        all_tasks = [TaskInfo.from_orm(i) for i in all_tasks]
        return TasksInfoResponse(tasks_info=all_tasks)
    except Exception as e:
        logger.error(f'Failed to get tasks: {e.__class__.__name__}, {e}')
        error_message = {"error": f"Ошибка приложения, не удалось получить задачи"}
        return ORJSONResponse(status_code=500, content=error_message)


@router.post('/task_info')
async def get_task_info(request: Request, task_request: TaskRequest):
    db_worker: DBWorker = request.app.state.db_worker
    try:
        all_tasks = await db_worker.get_tasks(name=task_request.task_name.capitalize(), done=task_request.done)
        return TasksInfoResponse(tasks_info=all_tasks)
    except TaskNotFoundError:
        return ORJSONResponse(status_code=404, content={"error": f"Task {task_request.task_name} not found"})
    except Exception as e:
        logger.error(f'Failed to get task {task_request.task_name}: {e.__class__.__name__}, {e}')
        error_message = {"error": f"Ошибка приложения, не удалось получить задачу {task_request.task_name}"}
        return ORJSONResponse(status_code=500, content=error_message)


@router.delete('/task/{task_id}')
async def delete_task(request: Request, task_id: int):
    db_worker: DBWorker = request.app.state.db_worker
    error = {"error": f"Application error, task {task_id} wasn't deleted"}
    try:
        all_tasks = await db_worker.get_tasks(task_id=task_id)
    except TaskNotFoundError:
        return ORJSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
    except Exception as e:
        logger.error(f'Failed to get task {task_id}: {e.__class__.__name__}, {e}')
        return ORJSONResponse(status_code=500, content=error)
    try:
        task = all_tasks[0]
        await db_worker.delete_task(task.name, task.deadline)
        return Response(status_code=204)
    except Exception as e:
        logger.error(f'Failed to delete task: {e.__class__.__name__}, {e}')
        return ORJSONResponse(status_code=500, content=error)

