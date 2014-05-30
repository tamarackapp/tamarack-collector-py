import threading

from datetime import datetime

from . import worker


SEC_TO_USEC = 1000 * 1000


def request_duration(request):
    interval = request._tamarack_end - request._tamarack_start
    return int(interval.total_seconds() * SEC_TO_USEC)


class RequestData(threading.local):
    def __init__(self):
        self.queries = []
        self.view_name = None
        self.in_request = False
        self.request_start = None

    def mark_request_start(self, view_name):
        assert not self.in_request

        self.in_request = True
        self.view_name = view_name
        self.request_start = datetime.utcnow()

    def mark_request_end(self, exception):
        assert self.in_request

        interval = datetime.utcnow() - self.request_start
        interval_usec = int(interval.total_seconds() * SEC_TO_USEC)

        query_time = sum(q['total_time'] for q in self.queries)
        other_time = interval_usec - query_time

        data = {
            'timestamp': self.request_start,
            'error_count': 1 if exception else 0,
            'request_count': 1,
            'endpoint': self.view_name,
            'queries': self.queries,
            'sensor_data': {
                'other': other_time,
                'sql': query_time,
            }
        }

        worker.shared_queue.put_nowait(data)

    def log_sql(self, sql, interval):
        self.queries.append({
            'query': sql,
            'total_time': int(interval.total_seconds() * SEC_TO_USEC),
        })


current_request = RequestData()
