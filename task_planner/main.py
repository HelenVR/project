import os

import uvicorn
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sys
from loguru import logger

from task_planner.configs.config import load_config
from task_planner.handlers import tasks_handler, calendar_handler, api_handler
from task_planner.workers.db_worker import DBWorker
from task_planner.application.middlewares import basic_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.remove()
    debug_flag = os.getenv('DEBUG', '').lower() in ('true', '1', 'yes')
    log_level = 'DEBUG' if debug_flag else 'INFO'
    logger.add(sys.stdout, level=log_level)
    app.mount("/static", StaticFiles(directory=os.getenv("STATIC_DIR", "/task_planner/static")), name="static")
    app.state.templates = Jinja2Templates(directory=os.getenv("TEMPLATES_DIR", "/tasks_planner/task_planner/templates"))
    app.state.config = load_config()
    middleware_deps = [Depends(basic_auth(app.state.config.api.login, app.state.config.api.password))]
    for handler in (tasks_handler, calendar_handler):
        app.include_router(handler.router)
    app.include_router(api_handler.router, dependencies=middleware_deps)
    app.state.db_worker = DBWorker(app.state.config)
    await app.state.db_worker.init()
    app.state.months = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    yield
    await app.state.db_worker.close()

app = FastAPI(lifespan=lifespan)

if __name__ == '__main__':
    try:
        uvicorn.run("main:app", host=os.getenv("APP_HOST", "127.0.0.1"), port=int(os.getenv("APP_PORT", "6001")))
    except KeyboardInterrupt:
        logger.info('Application is closed')

