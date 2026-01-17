"""
分页工具
"""
from typing import TypeVar, Generic
from dataclasses import dataclass
from flask import request

T = TypeVar('T')


@dataclass
class PageParams:
    """分页参数"""
    page: int = 1
    page_size: int = 20
    
    @classmethod
    def from_request(cls) -> 'PageParams':
        """从请求参数中获取分页参数"""
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        # 限制范围
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        return cls(page=page, page_size=page_size)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size


@dataclass
class PageResult(Generic[T]):
    """分页结果"""
    items: list[T]
    total: int
    page: int
    page_size: int
    
    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1
    
    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev
        }

