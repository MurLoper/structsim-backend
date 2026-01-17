"""
认证模块 - 数据访问层
职责：封装所有数据库操作，提供数据访问接口
禁止：业务逻辑、HTTP相关代码
"""
from typing import Optional, List
from app.models.auth import User
from app.extensions import db


class AuthRepository:
    """认证相关数据访问"""
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return User.query.filter_by(email=email, valid=1).first()
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_all_valid_users() -> List[User]:
        """获取所有有效用户"""
        return User.query.filter_by(valid=1).all()
    
    @staticmethod
    def update_last_login(user: User, timestamp: int) -> None:
        """更新用户最后登录时间"""
        user.last_login_at = timestamp
        db.session.commit()
    
    @staticmethod
    def create_user(user_data: dict) -> User:
        """创建新用户"""
        user = User(**user_data)
        db.session.add(user)
        db.session.commit()
        return user


# 单例实例
auth_repository = AuthRepository()

