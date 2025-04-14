from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from loguru import logger
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
import calendar
import asyncpg
import datetime

from task_planner.application.models import Base, Task
from task_planner.configs.config import Config
from task_planner.application.exceptions import TaskNotFoundError


class DBWorker:
    def __init__(self, config: Config):
        self.config = config
        self.engine = None
        self.session = None
        self.url = f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.db_name}"

    async def create_database(self):
        conn = await asyncpg.connect(user=self.config.db.user,
                                     password=self.config.db.password,
                                     host=self.config.db.host,
                                     port=self.config.db.port)
        try:
            await conn.execute(f"CREATE DATABASE {self.config.db.db_name}")
            logger.info(f'DB {self.config.db.db_name} create')
        except asyncpg.exceptions.DuplicateDatabaseError:
            print(f'DB {self.config.db.db_name} already exists')
        finally:
            await conn.close()

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def init(self):
        await self.create_database()
        try:
            url = self.url
            self.engine = create_async_engine(url=url, echo=True)
            self.session = sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)()
            logger.info('DB connection created')
            await self.create_tables()
            logger.info('Tables created')
            logger.info('----- DB worker initialized -----')
        except Exception as e:
            logger.error(f'Failed to init DB: {e.__class__.__name__}: {e}')

    async def get_tasks(self,
                        name: str | None = None,
                        task_id: int | None = None,
                        from_date: datetime.datetime | None = None,
                        to_date: datetime.datetime | None = None,
                        comment: str | None = None,
                        done: bool | None = None,
                        for_calendar: bool = False) -> list[Task]:
        query = select(Task)
        if task_id:
            query = query.where(Task.id == task_id)
        if done is not None:
            query = query.where(Task.done == done)
        if name:
            query = query.where(Task.name == name)
        if comment:
            query = query.where(Task.comment == comment)
        if from_date:
            query = query.where(Task.deadline >= from_date)
        if to_date:
            query = query.where(Task.deadline <= to_date)
        async with self.session as session:
            result = await session.execute(query)
            tasks = result.scalars().all()
        if not tasks and not for_calendar:
            raise TaskNotFoundError(reason=f'Task {task_id} not found')
        return tasks

    async def add_task(self, name: str, deadline: datetime, comment: str):
        new_task = Task(name=name, deadline=deadline, comment=comment)
        self.session.add(new_task)
        await self.session.commit()

    async def generate_calendar(self, year: int, month: int) -> dict[str, Task]:
        last_day = calendar.monthrange(year, month)[1]
        from_date = datetime.datetime(year=year, month=month, day=1)
        to_date=datetime.datetime(year=year, month=month, day=last_day)
        last_day = calendar.monthrange(year, month)[1]
        days = {f"{year}-{month:02d}-{day:02d}": [] for day in range(1, last_day + 1)}
        tasks_for_month = await self.get_tasks(from_date=from_date, to_date=to_date, for_calendar=True)

        for task in tasks_for_month:
            date = task.deadline.strftime("%Y-%m-%d")
            days[date].append(task)

        return days

    async def update_task(self,
                          name: str,
                          deadline: datetime.datetime,
                          new_deadline: datetime.datetime | None = None,
                          comment: str | None = None,
                          done: bool | None = None):
        async with self.session.begin():
            result = await self.session.execute(select(Task).where(Task.name == name, Task.deadline == deadline))
            task = result.scalar_one_or_none()
            if task:
                task.deadline = new_deadline if new_deadline else task.deadline
                task.done = eval(done) if done is not None else task.done
                task.comment = comment if comment else task.comment
                await self.session.commit()
                logger.info(f'Task {name} updated successfully.')
                return task
            else:
                logger.error(f'Task {name} for update not found')
                raise TaskNotFoundError(reason="Task not found")

    async def delete_task(self, name: str, deadline: datetime.datetime):
        async with self.session.begin():
            result = await self.session.execute(select(Task).where(Task.name == name, Task.deadline == deadline))
            task = result.scalars().first()

            if task:
                await self.session.delete(task)
                await self.session.commit()
                logger.info(f"Задача {name} удалена.")
            else:
                logger.error(f'Task {name} for update not found')
                raise TaskNotFoundError(reason="Task not found")

    async def delete_done_tasks(self):
        async with self.session.begin():
            try:
                done_tasks = await self.session.execute(select(Task).where(Task.done == True))
                tasks_to_delete = done_tasks.scalars().all()
                for task in tasks_to_delete:
                    await self.session.delete(task)
                await self.session.commit()
                logger.info(f"Все выполненные задачи удалены")
            except Exception as e:
                logger.error(f'Failed to delete tasks: {e.__class__.__name__}, {e}')
                raise e

    async def close(self):
        if self.session:
            await self.session.close()

