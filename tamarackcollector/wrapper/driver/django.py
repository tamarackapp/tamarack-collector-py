import os

from datetime import datetime
from functools import wraps

from django.conf import settings
from django.core.urlresolvers import resolve

from tamarackcollector.worker import start_worker
from tamarackcollector.request import current_request


class TamarackMiddleware:
    def __init__(self):
        url = os.path.join(settings.TAMARACK_URL, 'receiver-api/v1/request-data')
        start_worker(url, settings.TAMARACK_APP_ID)

    def process_request(self, request):
        view = resolve(request.path)[0]
        view_name = view.__module__ + '.' + view.__name__

        current_request.mark_request_start(view_name)

    def process_response(self, request, response):
        current_request.mark_request_end(None)

        return response

    def process_exception(self, request, exception):
        current_request.mark_request_end(exception)

class TimedView:
    def __init__(self, view):
        self.view = view

    def __call__(self, *args, **kwargs):
        start = datetime.utcnow()
        try:
            return self.view(*args, **kwargs)
        finally:
            duration = (datetime.utcnow() - start).total_seconds()
            current_request.increment_time_counter('controller', duration)

def wrap_view_factory_function(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return TimedView(f(*args, **kwargs))

    return wrapped

def wrap():
    from django.core.handlers.base import BaseHandler

    BaseHandler.make_view_atomic = wrap_view_factory_function(BaseHandler.make_view_atomic)
