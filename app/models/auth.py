"""
权限菜单模型 - 用户、角色、权限、菜单
按照 requirement_and_design.md 规范设计
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.base import ToDictMixin


class User(db.Model, ToDictMixin):
    """用户表"""
    __tablename__ = 'users'
    _exclude_fields = {'password_hash'}  # 排除敏感字段
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    email = db.Column(db.String(120), unique=True, nullable=False, comment='邮箱')
    password_hash = db.Column(db.String(256), comment='密码哈希')
    name = db.Column(db.String(100), comment='姓名')
    avatar = db.Column(db.String(255), comment='头像URL')
    phone = db.Column(db.String(20), comment='手机号')
    department = db.Column(db.String(100), comment='部门')
    
    # 角色ID列表
    role_ids = db.Column(db.JSON, comment='角色ID列表')
    
    # 状态
    valid = db.Column(db.SmallInteger, default=1, comment='1=有效,0=禁用')
    
    # 用户偏好
    preferences = db.Column(db.JSON, comment='用户偏好设置 {lang, theme, ...}')
    
    # 最近使用（用于置顶）
    recent_project_ids = db.Column(db.JSON, comment='最近使用的项目ID')
    recent_sim_type_ids = db.Column(db.JSON, comment='最近使用的仿真类型ID')
    
    # 时间戳
    last_login_at = db.Column(db.Integer, comment='最后登录时间')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

    def to_public_dict(self):
        """公开信息（用于参与人选择等）"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'avatar': self.avatar,
            'department': self.department
        }

    def set_password(self, password: str):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """验证密码"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)


class Role(db.Model, ToDictMixin):
    """角色表"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='角色名称')
    code = db.Column(db.String(30), unique=True, comment='角色编码')
    description = db.Column(db.String(200), comment='角色描述')
    
    # 权限ID列表
    permission_ids = db.Column(db.JSON, comment='权限ID列表')
    
    # 状态
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))


class Permission(db.Model, ToDictMixin):
    """权限表"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='权限名称')
    code = db.Column(db.String(50), unique=True, comment='权限编码')
    type = db.Column(db.String(20), comment='类型: PAGE/ACTION/DATA')
    resource = db.Column(db.String(100), comment='资源标识')
    description = db.Column(db.String(200), comment='权限描述')
    
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)
    
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))


class Menu(db.Model, ToDictMixin):
    """菜单表"""
    __tablename__ = 'menus'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parent_id = db.Column(db.Integer, default=0, comment='父菜单ID，0为顶级')
    name = db.Column(db.String(50), nullable=False, comment='菜单名称')
    title_i18n_key = db.Column(db.String(100), comment='国际化标题key')
    icon = db.Column(db.String(50), comment='图标名称')
    path = db.Column(db.String(200), comment='路由路径')
    component = db.Column(db.String(200), comment='前端组件路径')

    # 菜单类型: MENU=菜单, BUTTON=按钮
    menu_type = db.Column(db.String(20), default='MENU', comment='菜单类型')
    # 是否隐藏菜单（不在侧边栏显示，但路由可访问）
    hidden = db.Column(db.SmallInteger, default=0, comment='是否隐藏')

    # 关联权限
    permission_code = db.Column(db.String(50), comment='所需权限编码')

    # 状态
    valid = db.Column(db.SmallInteger, default=1)
    sort = db.Column(db.Integer, default=100)

    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))

