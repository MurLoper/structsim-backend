"""
序列化工具 - 统一的命名转换和数据序列化
实现 snake_case ↔ camelCase 自动转换
"""
from typing import Any, Dict, List, Union
import re


def to_camel_case(snake_str: str) -> str:
    """
    将snake_case转换为camelCase
    
    Examples:
        >>> to_camel_case('user_name')
        'userName'
        >>> to_camel_case('created_at')
        'createdAt'
        >>> to_camel_case('id')
        'id'
    """
    if not snake_str or '_' not in snake_str:
        return snake_str
    
    components = snake_str.split('_')
    # 第一个组件保持小写，其余组件首字母大写
    return components[0] + ''.join(x.title() for x in components[1:])


def to_snake_case(camel_str: str) -> str:
    """
    将camelCase转换为snake_case
    
    Examples:
        >>> to_snake_case('userName')
        'user_name'
        >>> to_snake_case('createdAt')
        'created_at'
        >>> to_snake_case('id')
        'id'
    """
    # 在大写字母前插入下划线，然后转小写
    snake = re.sub('([A-Z])', r'_\1', camel_str).lower()
    # 移除开头的下划线（如果有）
    return snake.lstrip('_')


def dict_keys_to_camel(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    递归转换字典的key为camelCase
    
    Args:
        data: 可以是字典、列表或其他类型
        
    Returns:
        转换后的数据，保持原有结构
        
    Examples:
        >>> dict_keys_to_camel({'user_name': 'test', 'created_at': 123})
        {'userName': 'test', 'createdAt': 123}
        
        >>> dict_keys_to_camel([{'user_id': 1}, {'user_id': 2}])
        [{'userId': 1}, {'userId': 2}]
    """
    if isinstance(data, dict):
        return {
            to_camel_case(k): dict_keys_to_camel(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [dict_keys_to_camel(item) for item in data]
    else:
        return data


def dict_keys_to_snake(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    递归转换字典的key为snake_case
    
    Args:
        data: 可以是字典、列表或其他类型
        
    Returns:
        转换后的数据，保持原有结构
        
    Examples:
        >>> dict_keys_to_snake({'userName': 'test', 'createdAt': 123})
        {'user_name': 'test', 'created_at': 123}
        
        >>> dict_keys_to_snake([{'userId': 1}, {'userId': 2}])
        [{'user_id': 1}, {'user_id': 2}]
    """
    if isinstance(data, dict):
        return {
            to_snake_case(k): dict_keys_to_snake(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [dict_keys_to_snake(item) for item in data]
    else:
        return data


class ModelSerializer:
    """
    模型序列化器基类
    提供统一的序列化方法
    """
    
    @staticmethod
    def to_dict(model_instance, camel_case: bool = True) -> Dict:
        """
        将模型实例转换为字典
        
        Args:
            model_instance: SQLAlchemy模型实例
            camel_case: 是否转换为camelCase，默认True
            
        Returns:
            字典格式的数据
        """
        if hasattr(model_instance, 'to_dict'):
            data = model_instance.to_dict()
        else:
            # 如果模型没有to_dict方法，使用默认转换
            data = {
                c.name: getattr(model_instance, c.name)
                for c in model_instance.__table__.columns
            }
        
        if camel_case:
            return dict_keys_to_camel(data)
        return data
    
    @staticmethod
    def to_dict_list(model_instances: List, camel_case: bool = True) -> List[Dict]:
        """
        将模型实例列表转换为字典列表
        
        Args:
            model_instances: SQLAlchemy模型实例列表
            camel_case: 是否转换为camelCase，默认True
            
        Returns:
            字典列表
        """
        return [
            ModelSerializer.to_dict(instance, camel_case)
            for instance in model_instances
        ]


# 便捷函数
def serialize_model(model_instance, camel_case: bool = True) -> Dict:
    """序列化单个模型实例"""
    return ModelSerializer.to_dict(model_instance, camel_case)


def serialize_models(model_instances: List, camel_case: bool = True) -> List[Dict]:
    """序列化模型实例列表"""
    return ModelSerializer.to_dict_list(model_instances, camel_case)

