import threading

from collections import defaultdict, deque
from datetime import datetime

from . import worker


SEC_TO_USEC = 1000 * 1000


class TimeCounter:
    __slots__ = ('start_time', 'total_usec')

    def __init__(self):
        self.start_time = None
        self.total_usec = 0

    def start(self):
        self.start_time = datetime.utcnow()

    def stop(self):
        end_time = datetime.utcnow()

        interval = end_time - self.start_time
        interval_usec = int(interval.total_seconds() * SEC_TO_USEC)

        self.total_usec += interval_usec
        self.start_time = None

class KeyedTimeCounter:
    def __init__(self):
        self.counter_stack = deque()
        self.counters = defaultdict(TimeCounter)

    def start(self, key):
        if self.counter_stack:
            self.counter_stack[-1].stop()

        counter = self.counters[key]
        counter.start()

        self.counter_stack.append(counter)

    def stop(self, key):
        counter = self.counter_stack.pop()
        counter.stop()

        assert counter == self.counters[key]

        if self.counter_stack:
            self.counter_stack[-1].start()

    def increment(self, key, value):
        self.counters[key].total_usec += int(value * SEC_TO_USEC)

    def as_dict(self):
        return dict((k, v.total_usec) for k, v in self.counters.items())

    def all_stopped(self):
        return (not self.counter_stack and
                all(not t.start_time for t in self.counters.values()))


class RequestData(threading.local):
    def __init__(self):
        self.reset()

    def reset(self):
        self.queries = None
        self.view_name = None
        self.in_request = False
        self.request_start = None
        self.time_counters = None

    def mark_request_start(self, view_name):
        assert not self.in_request

        self.queries = None
        self.in_request = True
        self.view_name = view_name
        self.request_start = datetime.utcnow()
        self.time_counters = KeyedTimeCounter()

    def mark_request_end(self, exception):
        interval = datetime.utcnow() - self.request_start
        interval_usec = int(interval.total_seconds() * SEC_TO_USEC)

        assert self.in_request
        assert self.time_counters.all_stopped()

        sensor_data = self.time_counters.as_dict()
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

        self.reset()

    def log_sql(self, sql, interval):
        if self.queries:
            self.queries.append({
                'query': sql,
                'total_time': int(interval.total_seconds() * SEC_TO_USEC),
            })

    def start_time_counter(self, counter_name):
        if self.time_counters:
            self.time_counters.start(counter_name)

    def stop_time_counter(self, counter_name):
        if self.time_counters:
            self.time_counters.stop(counter_name)


current_request = RequestData()
