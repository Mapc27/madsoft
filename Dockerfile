FROM python:3.8

RUN pip install poetry==1.8.3
RUN poetry config virtualenvs.create false
ENV PYTHONUNBUFFERED 1

WORKDIR /app/

COPY pyproject.toml .
COPY poetry.lock .
RUN poetry config installer.max-workers 10
RUN poetry install --no-root

COPY ./app .

ENTRYPOINT ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
