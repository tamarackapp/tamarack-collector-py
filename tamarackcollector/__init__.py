def wrap():
    from .wrapper.db import sqlite3

    sqlite3.wrap()


__all__ = ['TamarackMiddleware', 'wrap']
