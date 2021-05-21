FROM alpine:latest

WORKDIR /opt/slave-backlog-exporter

RUN apk --no-cache add postgresql-client python3 py3-pip

COPY requirements.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt

COPY app.py ./

ENV CONN_STRING='your_string_for_connect_to_postgres_slave'
ENV DISABLE_DEFAULT_METRICS="True"

CMD [ "python", "app.py" ]
