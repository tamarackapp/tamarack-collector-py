from .dbapi2 import wrap_connection_callable


def wrap():
    import sqlite3

    wrap_connection_callable(sqlite3, 'connect')

    wrap_connection_callable(sqlite3.dbapi2, 'connect')
