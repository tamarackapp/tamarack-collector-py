import os

from django.conf import settings
from django.core.urlresolvers import resolve

from tamarackcollector.worker import start_worker
from tamarackcollector.request import current_request

_url = os.path.join(settings.TAMARACK_URL, 'receiver-api/v1/request-data')


class TamarackMiddleware:
    def __init__(self):
        start_worker(_url, settings.TAMARACK_APP_ID)

    def process_request(self, request):
        view = resolve(request.path)[0]
        view_name = view.__module__ + '.' + view.__name__

        current_request.mark_request_start(view_name)

    def process_response(self, request, response):
        current_request.mark_request_end(None)

        return response

    def process_exception(self, request, exception):
        current_request.mark_request_end(exception)
