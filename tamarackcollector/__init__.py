def wrap():
    from .wrapper.db import sqlite3
    from .wrapper.driver import django

    sqlite3.wrap()
    django.wrap()


__all__ = ['TamarackMiddleware', 'wrap']
