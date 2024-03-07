FROM python:3.11
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:${PATH}"
WORKDIR /app

COPY ./pyproject.toml /app
COPY ./poetry.lock /app
COPY ./bot /app/bot
COPY ./.env /app


RUN pip install poetry
RUN poetry self update
RUN poetry install
CMD ["poetry", "run", "python", "bot/run.py"]