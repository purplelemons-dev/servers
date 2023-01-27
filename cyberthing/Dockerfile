# syntax=docker/dockerfile:1

FROM python:3.11.1-slim-bullseye

RUN mkdir /app
WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD [ "python", "bot.py" ]
