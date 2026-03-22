"""
权限与菜单模型。

用户身份以 `domain_account` 作为业务唯一标识。
数据库仍保留自增 `id` 作为内部代理键，避免一次性改动所有外键关系。
"""
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models.base import ToDictMixin


class User(db.Model, ToDictMixin):
    """用户表"""

    __tablename__ = "users"
    _exclude_fields = {"password_hash"}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False, comment="邮箱")
    domain_account = db.Column(
        db.String(32),
        unique=True,
        index=True,
        nullable=False,
        comment="域账号，作为业务唯一标识",
    )
    lc_user_id = db.Column(
        db.String(64),
        unique=True,
        index=True,
        comment="外部平台用户ID",
    )
    user_name = db.Column(db.String(100), comment="用户展示名")
    real_name = db.Column(db.String(100), comment="真实姓名")
    password_hash = db.Column(db.String(256), comment="密码哈希")
    avatar = db.Column(db.String(255), comment="头像URL")
    phone = db.Column(db.String(20), comment="手机号")
    department = db.Column(db.String(100), comment="部门")

    role_ids = db.Column(db.JSON, comment="角色ID列表")
    valid = db.Column(db.SmallInteger, default=1, comment="1=有效,0=禁用")
    preferences = db.Column(db.JSON, comment="用户偏好设置")
    recent_project_ids = db.Column(db.JSON, comment="最近使用的项目ID")
    recent_sim_type_ids = db.Column(db.JSON, comment="最近使用的仿真类型ID")
    daily_round_limit = db.Column(
        db.Integer,
        nullable=True,
        default=None,
        comment="用户日提单轮次上限，None 表示继承角色默认值",
    )

    last_login_at = db.Column(db.Integer, comment="最后登录时间")
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(
        db.Integer,
        default=lambda: int(datetime.utcnow().timestamp()),
        onupdate=lambda: int(datetime.utcnow().timestamp()),
    )

    def to_public_dict(self):
        """公开用户信息，统一以 domain_account 作为主键"""
        display_name = self.real_name or self.user_name or self.domain_account
        return {
            "id": self.domain_account,
            "domain_account": self.domain_account,
            "domainAccount": self.domain_account,
            "lc_user_id": self.lc_user_id,
            "lcUserId": self.lc_user_id,
            "user_name": self.user_name,
            "userName": self.user_name,
            "real_name": self.real_name,
            "realName": self.real_name,
            "display_name": display_name,
            "email": self.email,
            "avatar": self.avatar,
            "department": self.department,
        }

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)


class Role(db.Model, ToDictMixin):
    """角色表"""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment="角色名称")
    code = db.Column(db.String(30), unique=True, comment="角色编码")
    description = db.Column(db.String(200), comment="角色描述")
    permission_ids = db.Column(db.JSON, comment="权限ID列表")

    max_cpu_cores = db.Column(db.Integer, default=192, comment="可用CPU核数上限")
    max_batch_size = db.Column(db.Integer, default=200, comment="单次提单轮次上限")
    node_list = db.Column(db.JSON, comment="可用计算节点ID列表")
    daily_round_limit_default = db.Column(db.Integer, default=500, comment="角色默认日提单轮次上限")

    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(
        db.Integer,
        default=lambda: int(datetime.utcnow().timestamp()),
        onupdate=lambda: int(datetime.utcnow().timestamp()),
    )


class Permission(db.Model, ToDictMixin):
    """权限表"""

    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment="权限名称")
    code = db.Column(db.String(50), unique=True, comment="权限编码")
    type = db.Column(db.String(20), comment="类型: PAGE/ACTION/DATA")
    resource = db.Column(db.String(100), comment="资源标识")
    description = db.Column(db.String(200), comment="权限描述")

    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(
        db.Integer,
        default=lambda: int(datetime.utcnow().timestamp()),
        onupdate=lambda: int(datetime.utcnow().timestamp()),
    )


class Menu(db.Model, ToDictMixin):
    """菜单表"""

    __tablename__ = "menus"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parent_id = db.Column(db.Integer, default=0, comment="父菜单ID，0 为顶级")
    name = db.Column(db.String(50), nullable=False, comment="菜单名称")
    title_i18n_key = db.Column(db.String(100), comment="国际化标题 key")
    icon = db.Column(db.String(50), comment="图标名称")
    path = db.Column(db.String(200), comment="路由路径")
    component = db.Column(db.String(200), comment="前端组件路径")
    menu_type = db.Column(db.String(20), default="MENU", comment="菜单类型")
    hidden = db.Column(db.SmallInteger, default=0, comment="是否隐藏")
    permission_code = db.Column(db.String(50), comment="所需权限编码")
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(
        db.Integer,
        default=lambda: int(datetime.utcnow().timestamp()),
        onupdate=lambda: int(datetime.utcnow().timestamp()),
    )
