from datetime import datetime

from task_planner.application.exceptions import InvalidDateFormatError, NotFullDataError


async def get_deadline(year: str | int | None, month: str | int | None, day: str | int | None):
    data = (year, month, day)
    if all(not i for i in data):
        return None
    elif any(not i for i in data):
        raise NotFullDataError(reason=f'One or more date components are missing')
    try:
        deadline = datetime(year=int(year), month=int(month), day=int(day))
        return deadline
    except ValueError:
        raise InvalidDateFormatError(reason=f'Wrong date format {year}-{month}-{day}')







