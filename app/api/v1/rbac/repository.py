"""
RBAC - 数据访问层
"""
import time
from typing import Optional, List, TypeVar, Generic, Type
from app.extensions import db
from app.models.auth import User, Role, Permission

T = TypeVar('T')


class BaseRepository(Generic[T]):
    model_class: Type[T] = None

    def __init__(self):
        self.session = db.session

    def find_by_id(self, id: int) -> Optional[T]:
        return self.session.get(self.model_class, id)

    def find_by_id_valid(self, id: int) -> Optional[T]:
        return self.session.query(self.model_class).filter_by(id=id, valid=1).first()

    def find_all_valid(self, order_by: str = 'sort') -> List[T]:
        query = self.session.query(self.model_class).filter_by(valid=1)
        if hasattr(self.model_class, order_by):
            query = query.order_by(getattr(self.model_class, order_by).asc())
        return query.all()

    def create(self, data: dict) -> T:
        now = int(time.time())
        data.setdefault('valid', 1)
        data.setdefault('created_at', now)
        data.setdefault('updated_at', now)
        instance = self.model_class(**data)
        self.session.add(instance)
        self.session.commit()
        return instance

    def update(self, id: int, data: dict) -> Optional[T]:
        instance = self.find_by_id(id)
        if not instance:
            return None
        data['updated_at'] = int(time.time())
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        self.session.commit()
        return instance

    def soft_delete(self, id: int) -> bool:
        instance = self.find_by_id(id)
        if not instance:
            return False
        if hasattr(instance, 'valid'):
            instance.valid = 0
        if hasattr(instance, 'updated_at'):
            instance.updated_at = int(time.time())
        self.session.commit()
        return True


class UserRepository(BaseRepository[User]):
    model_class = User

    def find_by_email(self, email: str) -> Optional[User]:
        return self.session.query(self.model_class).filter_by(email=email, valid=1).first()

    def find_by_username(self, username: str) -> Optional[User]:
        return self.session.query(self.model_class).filter_by(username=username, valid=1).first()


class RoleRepository(BaseRepository[Role]):
    model_class = Role

    def find_by_ids(self, ids: List[int]) -> List[Role]:
        if not ids:
            return []
        return self.session.query(self.model_class).filter(self.model_class.id.in_(ids)).all()


class PermissionRepository(BaseRepository[Permission]):
    model_class = Permission

    def find_by_ids(self, ids: List[int]) -> List[Permission]:
        if not ids:
            return []
        return self.session.query(self.model_class).filter(self.model_class.id.in_(ids)).all()


user_repository = UserRepository()
role_repository = RoleRepository()
permission_repository = PermissionRepository()
