from datetime import datetime

from tamarackcollector.request import current_request


class WrappingCursor(object):
    def __init__(self, underlying_cursor):
        self._cursor = underlying_cursor
        self._in_query = False

    def callproc(self, procname, *args, **kwargs):
        op = lambda c: c.callproc(procname, *args, **kwargs)
        return self.__call_wrapped(procname, op)

    def execute(self, operation, *args, **kwargs):
        op = lambda c: c.execute(operation, *args, **kwargs)
        return self.__call_wrapped(operation, op)

    def executemany(self, operation, *args, **kwargs):
        op = lambda c: c.executemany(operation, *args, **kwargs)
        return self.__call_wrapped(operation, op)

    def __call_wrapped(self, sql, op):
        if self._in_query:
            return op(self._cursor)

        self._in_query = True
        start_time = datetime.utcnow()
        try:
            return op(self._cursor)
        finally:
            end_time = datetime.utcnow()

            duration = end_time - start_time

            current_request.log_sql(sql, duration)
            self._in_query = False

    def __getattribute__(self, name):
        try:
            return super(WrappingCursor, self).__getattribute__(name)
        except AttributeError:
            pass

        try:
            cursor = super(WrappingCursor, self).__getattribute__('_cursor')
        except AttributeError:
            cursor = None

        if cursor:
            return getattr(cursor, name)


class ConnectionProxy(object):
    def __init__(self, connection, cursor_class):
        self._connection = connection
        self._cursor_class = cursor_class

    def cursor(self, *args, **kwargs):
        return self._cursor_class(self._connection.cursor(*args, **kwargs))

    def __getattribute__(self, name):
        try:
            return super(ConnectionProxy, self).__getattribute__(name)
        except AttributeError:
            pass

        hasconnection = True
        try:
            super(ConnectionProxy, self).__getattribute__('_connection')
        except AttributeError:
            hasconnection = False

        if hasconnection:
            return getattr(self._connection, name)

    # def __setattr__(self, name, value):
    #     if hasattr(self._connection, name):
    #         return setattr(self._connection, name, value)

    #     return super(ConnectionProxy, self).__setattr__(name, value)

    # def __delattr__(self, name):
    #     if hasattr(self._connection, name):
    #         return delattr(self._connection, name)

    #     return super(ConnectionProxy, self).__delattr__(name)


def wrap_connection_callable(module, name,
                             cursor_class=WrappingCursor,
                             proxy_class=ConnectionProxy):
    old_callable = getattr(module, name)

    if getattr(old_callable, '_tamarack_wrapped', False):
        return

    def new_callable(*args, **kwargs):
        return proxy_class(old_callable(*args, **kwargs), cursor_class)

    new_callable._tamarack_wrapped = True
    setattr(module, name, new_callable)
