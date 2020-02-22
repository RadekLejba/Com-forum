FROM python:3.8.0

WORKDIR /usr/src/forum

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install netcat-openbsd

RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/forum/requirements.txt
RUN pip install -r requirements.txt

COPY entrypoint.sh /usr/src/forum/entrypoint.sh

COPY . /usr/src/forum/

ENTRYPOINT ["/usr/src/forum/entrypoint.sh"]
