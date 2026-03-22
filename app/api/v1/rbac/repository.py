"""
RBAC 数据访问层。
"""
import time
from typing import Generic, List, Optional, Type, TypeVar

from app.extensions import db
from app.models.auth import Menu, Permission, Role, User

T = TypeVar("T")


class BaseRepository(Generic[T]):
    model_class: Type[T] | None = None

    def __init__(self):
        self.session = db.session

    def find_by_id(self, item_id: int) -> Optional[T]:
        return self.session.get(self.model_class, item_id)

    def find_by_id_valid(self, item_id: int) -> Optional[T]:
        return self.session.query(self.model_class).filter_by(id=item_id, valid=1).first()

    def find_all_valid(self, order_by: str = "sort") -> List[T]:
        query = self.session.query(self.model_class).filter_by(valid=1)
        if hasattr(self.model_class, order_by):
            query = query.order_by(getattr(self.model_class, order_by).asc())
        return query.all()

    def create(self, data: dict) -> T:
        now = int(time.time())
        data.setdefault("valid", 1)
        data.setdefault("created_at", now)
        data.setdefault("updated_at", now)
        instance = self.model_class(**data)
        self.session.add(instance)
        self.session.commit()
        return instance

    def update(self, item_id: int, data: dict) -> Optional[T]:
        instance = self.find_by_id(item_id)
        if not instance:
            return None
        data["updated_at"] = int(time.time())
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        self.session.commit()
        return instance

    def soft_delete(self, item_id: int) -> bool:
        instance = self.find_by_id(item_id)
        if not instance:
            return False
        if hasattr(instance, "valid"):
            instance.valid = 0
        if hasattr(instance, "updated_at"):
            instance.updated_at = int(time.time())
        self.session.commit()
        return True


class UserRepository(BaseRepository[User]):
    model_class = User

    def find_all_valid(self, order_by: str = "domain_account") -> List[User]:
        query = self.session.query(self.model_class).filter_by(valid=1)
        if hasattr(self.model_class, order_by):
            query = query.order_by(getattr(self.model_class, order_by).asc())
        return query.all()

    def find_by_email(self, email: str) -> Optional[User]:
        return self.session.query(self.model_class).filter_by(email=email, valid=1).first()

    def find_by_domain_account(self, domain_account: str) -> Optional[User]:
        return (
            self.session.query(self.model_class)
            .filter_by(domain_account=domain_account, valid=1)
            .first()
        )

    def find_by_lc_user_id(self, lc_user_id: str) -> Optional[User]:
        return (
            self.session.query(self.model_class)
            .filter_by(lc_user_id=lc_user_id, valid=1)
            .first()
        )

    def update_by_domain_account(self, domain_account: str, data: dict) -> Optional[User]:
        instance = (
            self.session.query(self.model_class)
            .filter_by(domain_account=domain_account, valid=1)
            .first()
        )
        if not instance:
            return None
        data["updated_at"] = int(time.time())
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        self.session.commit()
        return instance

    def soft_delete_by_domain_account(self, domain_account: str) -> bool:
        instance = (
            self.session.query(self.model_class)
            .filter_by(domain_account=domain_account, valid=1)
            .first()
        )
        if not instance:
            return False
        instance.valid = 0
        instance.updated_at = int(time.time())
        self.session.commit()
        return True


class RoleRepository(BaseRepository[Role]):
    model_class = Role

    def find_by_ids(self, ids: List[int]) -> List[Role]:
        if not ids:
            return []
        return self.session.query(self.model_class).filter(self.model_class.id.in_(ids)).all()

    def find_by_code(self, code: str) -> Optional[Role]:
        return self.session.query(self.model_class).filter_by(code=code, valid=1).first()


class PermissionRepository(BaseRepository[Permission]):
    model_class = Permission

    def find_by_ids(self, ids: List[int]) -> List[Permission]:
        if not ids:
            return []
        return self.session.query(self.model_class).filter(self.model_class.id.in_(ids)).all()

    def find_by_code(self, code: str) -> Optional[Permission]:
        return self.session.query(self.model_class).filter_by(code=code, valid=1).first()


class MenuRepository(BaseRepository[Menu]):
    model_class = Menu

    def find_all_valid(self, order_by: str = "sort") -> List[Menu]:
        query = self.session.query(self.model_class).filter_by(valid=1)
        if hasattr(self.model_class, order_by):
            query = query.order_by(
                getattr(self.model_class, order_by).asc(),
                self.model_class.id.asc(),
            )
        return query.all()

    def find_by_parent_id(self, parent_id: int) -> List[Menu]:
        return (
            self.session.query(self.model_class)
            .filter_by(parent_id=parent_id, valid=1)
            .order_by(self.model_class.sort.asc(), self.model_class.id.asc())
            .all()
        )


user_repository = UserRepository()
role_repository = RoleRepository()
permission_repository = PermissionRepository()
menu_repository = MenuRepository()
