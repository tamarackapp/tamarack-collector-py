import os

from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import resolve

from .worker import start_worker

_url = os.path.join(settings.TAMARACK_URL, 'receiver-api/v1/request-data')
shared_queue = start_worker(_url, settings.TAMARACK_APP_ID)


def request_duration(request):
    interval = request._tamarack_end - request._tamarack_start
    return int(interval.total_seconds() * 1000)


def dispatch_request_timings(request, exception):
    data = {
        'timestamp': request._tamarack_start,
        'errors': 1 if exception else 0,
        'requests': 1,
        'total_time': request_duration(request),
        'endpoint': request._tamarack_endpoint_name,
    }

    shared_queue.put_nowait(data)


class TamarackMiddleware:
    def process_request(self, request):
        request._tamarack_start = datetime.utcnow()

        view = resolve(request.path)[0]
        view_name = view.__module__ + '.' + view.__name__

        request._tamarack_endpoint_name = view_name

    def process_response(self, request, response):
        request._tamarack_end = datetime.utcnow()

        dispatch_request_timings(request, None)

        return response

    def process_exception(self, request, exception):
        request._tamarack_end = datetime.utcnow()

        dispatch_request_timings(request, exception)
