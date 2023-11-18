FROM python:3.7-alpine

WORKDIR /forecasts

RUN apk update && apk add build-base openldap-dev python3-dev mariadb-dev mariadb-client

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY app app
COPY migrations migrations
COPY main.py config.py boot.sh ./
RUN chmod +x boot.sh

EXPOSE 5001

ENTRYPOINT ["./boot.sh"]
