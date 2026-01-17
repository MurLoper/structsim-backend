"""
配置关联关系管理模块
"""
from .routes import config_relations_bp
from .service import ConfigRelationsService

__all__ = ['config_relations_bp', 'ConfigRelationsService']

