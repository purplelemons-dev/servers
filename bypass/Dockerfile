# syntax=docker/dockerfile:1

FROM python:3.11.1-slim-bullseye

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "server.py"]
