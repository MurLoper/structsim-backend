"""
模型基类 - 提供通用的 Mixin 功能
"""
from typing import Set, Dict, Any, Optional


class ToDictMixin:
    """
    自动生成 to_dict 方法的 Mixin

    子类可通过类属性自定义行为：
    - _exclude_fields: 要排除的字段集合（如敏感字段 password_hash）
    - _include_fields: 仅包含的字段集合（优先级高于 exclude）

    Usage:
        class User(db.Model, ToDictMixin):
            _exclude_fields = {'password_hash'}
            ...
    """

    _exclude_fields: Set[str] = set()
    _include_fields: Optional[Set[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        将模型实例转换为字典
        自动从表列生成，支持排除/包含字段配置
        """
        result = {}
        for column in self.__table__.columns:
            name = column.name

            # 如果指定了 include_fields，只包含这些字段
            if self._include_fields is not None:
                if name not in self._include_fields:
                    continue
            # 否则检查 exclude_fields
            elif name in self._exclude_fields:
                continue

            result[name] = getattr(self, name)

        return result

    def to_dict_with(self, *extra_fields: str, **extra_values) -> Dict[str, Any]:
        """
        生成字典并添加额外字段

        Args:
            *extra_fields: 从模型属性中额外添加的字段名
            **extra_values: 直接添加的键值对

        Usage:
            user.to_dict_with('computed_field', role_name='Admin')
        """
        result = self.to_dict()

        for field in extra_fields:
            if hasattr(self, field):
                result[field] = getattr(self, field)

        result.update(extra_values)
        return result
