import re
import os
import subprocess
import datetime as d
import time
from prometheus_client.core import REGISTRY, CounterMetricFamily
from prometheus_client import start_http_server

REQUEST = 'select now()-pg_last_xact_replay_timestamp() as replication_lag;'
CONNECT_STRING = os.environ.get("CONNECT_STRING")
DISABLE_DEFAULT_METRICS = "True"

# Clearing url and selecting a slave node


def clear_unnecessary_from_string(conn_string):
    rgxMount = re.compile(
        'jdbc:|&sslmode=disable|&tcpKeepAlive=true|&targetServerType=master|&ssl=true|\d+\.\d+\.\d+\.\d+\:[0-9]{4}\,'
    )

    conn_string_other = rgxMount.sub('', conn_string)
    return conn_string_other


def clear_url(conn_string):
    jdbc_pattern = 'postgresql://(.*?):(\d*)\/(.*)\?user=(.*)\&password=(.*)'

    (j_host, j_port, j_dbname, j_username, j_password) = re.compile(
        jdbc_pattern).findall(conn_string)[0]

    clear_conn_sring = 'postgresql://' + j_host + ':' + j_port + '/' + \
        j_dbname + '?user=' + j_username + '&password=' + j_password

    return clear_conn_sring

# Executing a request


cmd = 'echo "' + REQUEST + '" | ' + 'psql "' + \
    clear_url(clear_unnecessary_from_string(CONNECT_STRING)) + '"  | awk "{print $1}"'

time_pattern = r'\d\d:\d\d:\d\d'

if DISABLE_DEFAULT_METRICS == "True":
    for coll in list(REGISTRY._collector_to_names.keys()):
        REGISTRY.unregister(coll)


def run_request(command):
    ps = subprocess.Popen(command, shell=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = ps.communicate()[0]
    output = output.decode("utf-8")
    ps.stdout.close()
    return output

# We give metrics


class CustomCollector(object):
    def __init__(self):
        pass

    def collect(self):
        time_str = re.compile(time_pattern).findall(run_request(cmd))[0]
        total_lag = d.datetime.strptime(time_str, '%H:%M:%S')
        total_minutes = int(total_lag.hour)*60 + int(total_lag.minute)*1
        value = CounterMetricFamily(
            "slave_lag", 'Postgres slave node lag metric', labels='value')
        value.add_metric(["postgres_slave_lag"], total_minutes)
        yield value


if __name__ == '__main__':
    start_http_server(9099)
    REGISTRY.register(CustomCollector())
    while True:
        time.sleep(1)
