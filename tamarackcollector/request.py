import threading

from collections import defaultdict
from datetime import datetime

from . import worker


SEC_TO_USEC = 1000 * 1000


class TimeCounter:
    __slots__ = ('start_time', 'total_usec', 'nesting')

    def __init__(self):
        self.start_time = None
        self.total_usec = 0
        self.nesting = 0

    def start(self):
        if self.nesting == 0:
            self.start_time = datetime.utcnow()

        self.nesting += 1

    def stop(self):
        end_time = datetime.utcnow()
        self.nesting -= 1

        if self.nesting == 0:
            interval = end_time - self.start_time
            interval_usec = int(interval.total_seconds() * SEC_TO_USEC)

            self.total_usec += interval_usec


class RequestData(threading.local):
    def __init__(self):
        self.queries = []
        self.view_name = None
        self.in_request = False
        self.request_start = None
        self.time_counters = None

    def mark_request_start(self, view_name):
        assert not self.in_request

        self.in_request = True
        self.view_name = view_name
        self.request_start = datetime.utcnow()
        self.time_counters = defaultdict(TimeCounter)

    def mark_request_end(self, exception):
        assert self.in_request

        interval = datetime.utcnow() - self.request_start
        interval_usec = int(interval.total_seconds() * SEC_TO_USEC)

        sensor_data = dict((k, v.total_usec) for k, v in self.time_counters.items())
        other_time = interval_usec

        for val in sensor_data.values():
            other_time -= val

        sensor_data['other'] = other_time

        data = {
            'timestamp': self.request_start,
            'error_count': 1 if exception else 0,
            'request_count': 1,
            'endpoint': self.view_name,
            'queries': self.queries,
            'sensor_data': sensor_data,
        }

        worker.shared_queue.put_nowait(data)

    def log_sql(self, sql, interval):
        self.queries.append({
            'query': sql,
            'total_time': int(interval.total_seconds() * SEC_TO_USEC),
        })
        self.increment_time_counter('sql', interval.total_seconds())

    def start_time_counter(self, counter_name):
        self.time_counters[counter_name].start()

    def stop_time_counter(self, counter_name):
        self.time_counters[counter_name].stop()

    def increment_time_counter(self, counter, value):
        if self.time_counters is not None:
            self.time_counters[counter].total_usec += int(value * SEC_TO_USEC)


current_request = RequestData()
