class VerboseException(Exception):
    def __init__(self, reason: str):
        super().__init__()
        self._reason = reason

    @property
    def reason(self):
        return self._reason

    def __str__(self):
        return f'{self.__class__.__name__}: {self._reason}'


class TaskNotFoundError(VerboseException):
    pass


class InvalidDateFormatError(VerboseException):
    pass


class NotFullDataError(VerboseException):
    pass