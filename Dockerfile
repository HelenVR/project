FROM python:3.11-slim
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ARG APP_DIR=/usr/task_planner
ENV PATH $APP_DIR:$PATH
WORKDIR $APP_DIR
COPY . ./

ENV VIRTUAL_ENV "${APP_DIR}/venv"
RUN python3.11 -m venv $VIRTUAL_ENV
ENV PATH "$VIRTUAL_ENV/bin:$PATH"

RUN pip3.11 install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-root --only main

RUN apt-get update && \
    apt-get install -y curl \
    traceroute \
    mc \
    tcpdump \
    telnet \
    dnsutils \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean autoclean && apt-get autoremove --yes && rm -rf /var/lib/{apt,dpkg,cache,log}

ENV APP_PORT=5200
EXPOSE ${APP_PORT}
CMD ["python", "-m", "task_planner/main.py"]