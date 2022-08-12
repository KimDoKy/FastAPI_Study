FROM python:3.8-slim-buster

WORKDIR /backend

ENV FASTAPICODE 1
ENV FASTAPIBUFFERED 1

RUN apt-get update \
    && apt-get -y install netcat gcc postgresql \
    && apt-get clean

RUN pip install --upgrade pip
COPY ./requirements.txt /backend/requirements.txt
RUN pip install -r requirements.txt

COPY . /backend
