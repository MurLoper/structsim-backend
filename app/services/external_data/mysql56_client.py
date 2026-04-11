from __future__ import annotations

from contextlib import contextmanager
from queue import Empty, Full, LifoQueue
from typing import Any, Dict, Iterable, List

import pymysql
from flask import current_app
from pymysql.cursors import DictCursor


class ExternalMySQL56Client:
    """外部 MySQL 5.6 只读客户端。"""

    def __init__(self) -> None:
        self._connection_kwargs_cache: Dict[str, Any] | None = None
        self._pools: Dict[str, LifoQueue] = {}

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
        conn = self._acquire_connection(database)
        try:
            yield conn
        except Exception:
            self._close_connection(conn)
            raise
        finally:
            if getattr(conn, 'open', False):
                self._release_connection(database, conn)

    def _pool_size(self) -> int:
        return int(current_app.config.get('EXTERNAL_MYSQL_POOL_SIZE', 0) or 0)

    def _pool_for(self, database: str) -> LifoQueue:
        if database not in self._pools:
            self._pools[database] = LifoQueue(maxsize=self._pool_size())
        return self._pools[database]

    def _new_connection(self, database: str):
        return pymysql.connect(database=database, **self.connection_kwargs)

    def _acquire_connection(self, database: str):
        if self._pool_size() <= 0:
            return self._new_connection(database)

        pool = self._pool_for(database)
        try:
            conn = pool.get_nowait()
        except Empty:
            return self._new_connection(database)

        try:
            conn.ping(reconnect=True)
            return conn
        except Exception:
            self._close_connection(conn)
            return self._new_connection(database)

    def _release_connection(self, database: str, conn) -> None:
        if self._pool_size() <= 0:
            self._close_connection(conn)
            return
        try:
            self._pool_for(database).put_nowait(conn)
        except Full:
            self._close_connection(conn)

    @staticmethod
    def _close_connection(conn) -> None:
        try:
            conn.close()
        except Exception:
            pass

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
