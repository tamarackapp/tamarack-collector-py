import json
import requests
import time

from collections import Counter
from multiprocessing import Process, Queue
from queue import Empty

shared_queue = None


def datetime_by_minute(dt):
    return dt.replace(second=0, microsecond=0).isoformat() + 'Z'


def process_jobs(url, app_id, queue):
    while True:
        time.sleep(60)
        by_minute = {}

        while True:
            try:
                i = queue.get_nowait()
            except Empty:
                break

            minute = datetime_by_minute(i['timestamp'])
            endpoint = i['endpoint']

            if (minute, endpoint) not in by_minute:
                by_minute[(minute, endpoint)] = {
                    'sensor_data': Counter(),
                    'timestamp': minute,
                    'endpoint': endpoint,
                }

            sensor_data = by_minute[(minute, endpoint)]['sensor_data']
            sensor_data['request_count'] += i['request_count']
            sensor_data['error_count'] += i['error_count']
            sensor_data['total_time'] += i['total_time']

        if not by_minute:
            continue

        data = {
            'app_name': app_id,
            'by_minute': list(by_minute.values()),
        }

        requests.post(url, data=json.dumps(data))


def start_worker(url, app_id):
    q = Queue()
    p = Process(target=process_jobs, args=(url, app_id, q, ))
    p.start()

    global shared_queue

    shared_queue = q
