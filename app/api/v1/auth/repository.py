"""
认证模块数据访问层。
"""
from typing import List, Optional

from app.extensions import db
from app.models.auth import Permission, Role, User


class AuthRepository:
    """认证相关数据访问"""

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        return User.query.filter_by(email=email, valid=1).first()

    @staticmethod
    def get_user_by_domain_account(domain_account: str) -> Optional[User]:
        return User.query.filter_by(domain_account=domain_account, valid=1).first()

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_lc_user_id(lc_user_id: str) -> Optional[User]:
        return User.query.filter_by(lc_user_id=lc_user_id, valid=1).first()

    @staticmethod
    def get_all_valid_users() -> List[User]:
        return User.query.filter_by(valid=1).order_by(User.domain_account.asc()).all()

    @staticmethod
    def get_role_by_code(code: str) -> Optional[Role]:
        return Role.query.filter_by(code=code, valid=1).first()

    @staticmethod
    def get_permissions_by_codes(codes: List[str]) -> List[Permission]:
        if not codes:
            return []
        return Permission.query.filter(Permission.code.in_(codes), Permission.valid == 1).all()

    @staticmethod
    def create_role(role_data: dict) -> Role:
        role = Role(**role_data)
        db.session.add(role)
        db.session.commit()
        return role

    @staticmethod
    def update_last_login(user: User, timestamp: int) -> None:
        user.last_login_at = timestamp
        db.session.commit()

    @staticmethod
    def upsert_user_by_domain_account(domain_account: str, user_data: dict) -> User:
        user = User.query.filter_by(domain_account=domain_account).first()
        if user:
            for key, value in user_data.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            db.session.commit()
            return user

        user = User(**user_data)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def create_user(user_data: dict) -> User:
        user = User(**user_data)
        db.session.add(user)
        db.session.commit()
        return user


auth_repository = AuthRepository()
