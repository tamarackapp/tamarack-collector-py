import json
import requests
import time

from multiprocessing import Process, Queue
from queue import Empty


def datetime_by_minute(dt):
    return dt.replace(second=0, microsecond=0).isoformat() + 'Z'


def process_jobs(url, app_id, queue):
    while True:
        time.sleep(60)
        buckets = {}
        endpoint_buckets = {}

        while True:
            try:
                i = queue.get_nowait()
            except Empty:
                break

            minute = datetime_by_minute(i['timestamp'])
            endpoint = i['endpoint']

            if minute not in buckets:
                buckets[minute] = {
                    'requests': 0,
                    'errors': 0,
                    'total_time': 0,
                    'timestamp': minute
                }

            if (minute, endpoint) not in endpoint_buckets:
                endpoint_buckets[(minute, endpoint)] = {
                    'requests': 0,
                    'errors': 0,
                    'total_time': 0,
                    'timestamp': minute,
                    'endpoint': endpoint
                }

            bucket = buckets[minute]
            bucket['requests'] += i['requests']
            bucket['errors'] += i['errors']
            bucket['total_time'] += i['total_time']

            endpoint_bucket = endpoint_buckets[(minute, endpoint)]
            endpoint_bucket['requests'] += i['requests']
            endpoint_bucket['errors'] += i['errors']
            endpoint_bucket['total_time'] += i['total_time']

        if not buckets:
            continue

        data = {
            'app_name': app_id,
            'data': list(buckets.values()),
            'endpoints': list(endpoint_buckets.values()),
        }

        requests.post(url, data=json.dumps(data))


def start_worker(url, app_id):
    q = Queue()
    p = Process(target=process_jobs, args=(url, app_id, q, ))
    p.start()

    return q
