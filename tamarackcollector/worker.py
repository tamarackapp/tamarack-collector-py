import json
import requests
import time

from collections import Counter
from datetime import datetime, timedelta
from multiprocessing import Process, Queue
from queue import Empty

shared_queue = None


def datetime_by_minute(dt):
    return dt.replace(second=0, microsecond=0).isoformat() + 'Z'


def increment_counter(counter, data):
    for k, v in data.items():
        counter[k] += v


def process_jobs(url, app_id, queue):
    by_minute = {}
    last_sync = datetime.utcnow()

    while True:
        try:
            i = queue.get(block=True, timeout=30)
        except Empty:
            i = None

        if i:
            minute = datetime_by_minute(i['timestamp'])
            endpoint = i['endpoint']

            if (minute, endpoint) not in by_minute:
                by_minute[(minute, endpoint)] = {
                    'sensor_data': Counter(),
                    'timestamp': minute,
                    'endpoint': endpoint,
                    'request_count': 0,
                    'error_count': 0,
                }

            minute_data = by_minute[(minute, endpoint)]
            minute_data['request_count'] += i['request_count']
            minute_data['error_count'] += i['error_count']

            increment_counter(minute_data['sensor_data'], i['sensor_data'])

        if (datetime.utcnow() - last_sync) > timedelta(seconds=60):
            data = {
                'app_name': app_id,
                'by_minute': list(by_minute.values()),
            }

            resp = requests.post(url, data=json.dumps(data)
                                 {'Content-Type': 'application/json'})

            if resp.status_code == 200:
                by_minute = {}
                last_sync = datetime.utcnow()
            else:
                print('Could not sync tamarack data: %s' % resp)


def start_worker(url, app_id):
    q = Queue()
    p = Process(target=process_jobs, args=(url, app_id, q, ))
    p.start()

    global shared_queue

    shared_queue = q
