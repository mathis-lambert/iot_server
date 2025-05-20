FROM python:3.12-slim

RUN pip install --upgrade pip

WORKDIR /app

COPY pyproject.toml ./

RUN pip install .

COPY . .

ENTRYPOINT ["python", "src/server/main.py"]
