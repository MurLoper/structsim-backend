"""
配置数据缓存服务
提供配置数据的 Redis 缓存读写操作
"""
import json
from typing import Optional, List, Any, TypeVar, Callable
from flask import current_app
from .redis_client import redis_client

T = TypeVar('T')


class CacheKeys:
    """缓存 Key 定义"""
    # 配置数据
    PROJECTS = "config:projects"
    SIM_TYPES = "config:sim_types"
    FOLD_TYPES = "config:fold_types"
    PARAM_DEFS = "config:param_defs"
    OUTPUT_DEFS = "config:output_defs"
    CONDITION_DEFS = "config:condition_defs"
    SOLVERS = "config:solvers"
    STATUS_DEFS = "config:status_defs"
    PARAM_TPL_SETS = "config:param_tpl_sets"
    COND_OUT_SETS = "config:cond_out_sets"

    # 工况配置
    CONDITIONS_ALL = "conditions:all"

    @staticmethod
    def condition(condition_id: int) -> str:
        return f"condition:{condition_id}"

    @staticmethod
    def condition_by_fold_sim(fold_type_id: int, sim_type_id: int) -> str:
        return f"condition:fold:{fold_type_id}:sim:{sim_type_id}"

    @staticmethod
    def conditions_by_fold(fold_type_id: int) -> str:
        return f"conditions:fold:{fold_type_id}"

    # 关联数据
    FOLD_TYPE_SIM_TYPE_RELS = "config:fold_type_sim_type_rels"


class ConfigCache:
    """配置数据缓存服务"""

    # 缓存 TTL 配置（秒）
    TTL_CONFIG = 3600      # 基础配置 1小时
    TTL_CONDITIONS = 3600  # 工况配置 1小时
    TTL_LIST = 1800        # 列表数据 30分钟

    @staticmethod
    def _serialize(data: Any) -> str:
        """序列化数据为 JSON"""
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def _deserialize(data: Optional[str]) -> Optional[Any]:
        """反序列化 JSON 数据"""
        if data is None:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    @classmethod
    def get_or_set(
        cls,
        key: str,
        fetch_fn: Callable[[], T],
        ttl: int = None
    ) -> T:
        """
        获取缓存，如果不存在则从数据库获取并缓存

        Args:
            key: 缓存 key
            fetch_fn: 获取数据的函数
            ttl: 缓存过期时间（秒）
        """
        # 尝试从缓存获取
        cached = redis_client.get(key)
        if cached is not None:
            result = cls._deserialize(cached)
            if result is not None:
                return result

        # 从数据库获取
        data = fetch_fn()

        # 写入缓存
        if data is not None:
            ttl = ttl or cls.TTL_CONFIG
            redis_client.set(key, cls._serialize(data), ttl)

        return data

    @classmethod
    def set(cls, key: str, data: Any, ttl: int = None) -> bool:
        """直接设置缓存"""
        ttl = ttl or cls.TTL_CONFIG
        return redis_client.set(key, cls._serialize(data), ttl)

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """直接获取缓存"""
        cached = redis_client.get(key)
        return cls._deserialize(cached)

    @classmethod
    def delete(cls, key: str) -> bool:
        """删除缓存"""
        return redis_client.delete(key)

    @classmethod
    def invalidate_condition(cls, condition_id: int = None,
                             fold_type_id: int = None,
                             sim_type_id: int = None):
        """
        失效工况相关缓存

        Args:
            condition_id: 工况ID
            fold_type_id: 姿态ID
            sim_type_id: 仿真类型ID
        """
        # 失效列表缓存
        cls.delete(CacheKeys.CONDITIONS_ALL)

        # 失效单个工况缓存
        if condition_id:
            cls.delete(CacheKeys.condition(condition_id))

        # 失效姿态+仿真类型组合缓存
        if fold_type_id and sim_type_id:
            cls.delete(CacheKeys.condition_by_fold_sim(fold_type_id, sim_type_id))

        # 失效姿态下所有工况缓存
        if fold_type_id:
            cls.delete(CacheKeys.conditions_by_fold(fold_type_id))

    @classmethod
    def invalidate_config(cls, config_type: str = None):
        """
        失效配置缓存

        Args:
            config_type: 配置类型，如 'projects', 'sim_types' 等
                        如果为 None，则失效所有配置缓存
        """
        if config_type:
            key = getattr(CacheKeys, config_type.upper(), None)
            if key:
                cls.delete(key)
        else:
            # 失效所有配置缓存
            for attr in dir(CacheKeys):
                if attr.isupper() and not attr.startswith('_'):
                    cls.delete(getattr(CacheKeys, attr))
