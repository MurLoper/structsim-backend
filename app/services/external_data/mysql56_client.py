from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterable, List

import pymysql
from flask import current_app
from pymysql.cursors import DictCursor


class ExternalMySQL56Client:
    """外部 MySQL 5.6 只读客户端。"""

    def __init__(self) -> None:
        self._connection_kwargs_cache: Dict[str, Any] | None = None

    def _build_connection_kwargs(self) -> Dict[str, Any]:
        app = current_app
        return {
            'host': app.config['EXTERNAL_MYSQL_HOST'],
            'port': int(app.config['EXTERNAL_MYSQL_PORT']),
            'user': app.config['EXTERNAL_MYSQL_USER'],
            'password': app.config['EXTERNAL_MYSQL_PASSWORD'],
            'charset': app.config.get('EXTERNAL_MYSQL_CHARSET', 'utf8mb4'),
            'cursorclass': DictCursor,
            'connect_timeout': float(app.config.get('EXTERNAL_MYSQL_CONNECT_TIMEOUT', 10)),
            'read_timeout': float(app.config.get('EXTERNAL_MYSQL_READ_TIMEOUT', 20)),
            'write_timeout': float(app.config.get('EXTERNAL_MYSQL_WRITE_TIMEOUT', 20)),
            'autocommit': True,
        }

    @property
    def connection_kwargs(self) -> Dict[str, Any]:
        if self._connection_kwargs_cache is None:
            self._connection_kwargs_cache = self._build_connection_kwargs()
        return self._connection_kwargs_cache

    @contextmanager
    def connection(self, database: str):
        conn = pymysql.connect(database=database, **self.connection_kwargs)
        try:
            yield conn
        finally:
            conn.close()

    def fetch_all(self, database: str, sql: str, params: Iterable[Any] | None = None) -> List[Dict[str, Any]]:
        with self.connection(database) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                return list(cursor.fetchall() or [])

    def fetch_one(self, database: str, sql: str, params: Iterable[Any] | None = None) -> Dict[str, Any] | None:
        with self.connection(database) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchone()


external_mysql56_client = ExternalMySQL56Client()
