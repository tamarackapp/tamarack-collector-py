import json
import os
import requests

from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import resolve

def request_duration(request):
    return int((request._tamarack_end - request._tamarack_start).total_seconds() * 1000)


def dispatch_request_timings(request, exception):
    data = {
        'app_name': settings.TAMARACK_APP_ID,
        'data': [
            {
                'timestamp': request._tamarack_start.isoformat() + 'Z',
                'errors': 1 if exception else 0,
                'requests': 1,
                'total_time': request_duration(request)
            }
        ],
        'endpoints': [
            {
                'timestamp': request._tamarack_start.isoformat() + 'Z',
                'errors': 1 if exception else 0,
                'requests': 1,
                'total_time': request_duration(request),
                'endpoint': request._tamarack_endpoint_name,
            }
        ],
    }

    url = os.path.join(settings.TAMARACK_URL, 'receiver-api/v1/request-data')

    resp = requests.post(url, data=json.dumps(data))


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
