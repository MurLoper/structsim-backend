"""
Redis 客户端连接模块
提供 Redis 连接池和基础操作
"""
import json
import redis
from typing import Optional, Any, Union
from flask import current_app


class RedisClient:
    """Redis 客户端封装"""

    _instance: Optional['RedisClient'] = None
    _pool: Optional[redis.ConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_app(self, app):
        """初始化 Redis 连接池"""
        self._pool = redis.ConnectionPool(
            host=app.config.get('REDIS_HOST', 'localhost'),
            port=app.config.get('REDIS_PORT', 6379),
            db=app.config.get('REDIS_DB', 0),
            password=app.config.get('REDIS_PASSWORD'),
            decode_responses=True,
            max_connections=20
        )
        self._prefix = app.config.get('REDIS_KEY_PREFIX', 'structsim:')
        self._default_ttl = app.config.get('REDIS_DEFAULT_TTL', 3600)

    @property
    def client(self) -> redis.Redis:
        """获取 Redis 客户端"""
        if self._pool is None:
            raise RuntimeError("Redis 未初始化，请先调用 init_app")
        return redis.Redis(connection_pool=self._pool)

    def _key(self, key: str) -> str:
        """添加 key 前缀"""
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Optional[str]:
        """获取字符串值"""
        try:
            return self.client.get(self._key(key))
        except redis.RedisError as e:
            current_app.logger.error(f"Redis GET 错误: {e}")
            return None

    def set(self, key: str, value: str, ttl: int = None) -> bool:
        """设置字符串值"""
        try:
            ttl = ttl or self._default_ttl
            return self.client.setex(self._key(key), ttl, value)
        except redis.RedisError as e:
            current_app.logger.error(f"Redis SET 错误: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除 key"""
        try:
            return self.client.delete(self._key(key)) > 0
        except redis.RedisError as e:
            current_app.logger.error(f"Redis DELETE 错误: {e}")
            return False

    def exists(self, key: str) -> bool:
        """检查 key 是否存在"""
        try:
            return self.client.exists(self._key(key)) > 0
        except redis.RedisError as e:
            current_app.logger.error(f"Redis EXISTS 错误: {e}")
            return False


# 单例实例
redis_client = RedisClient()
