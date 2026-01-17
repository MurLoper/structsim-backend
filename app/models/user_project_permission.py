"""
用户项目权限关联表
"""
from datetime import datetime
from app import db


class UserProjectPermission(db.Model):
    """用户项目权限表"""
    __tablename__ = 'user_project_permissions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, comment='项目ID')
    can_view = db.Column(db.SmallInteger, default=1, comment='是否可查看')
    can_submit = db.Column(db.SmallInteger, default=1, comment='是否可提交')
    can_manage = db.Column(db.SmallInteger, default=0, comment='是否可管理')
    valid = db.Column(db.SmallInteger, default=1, comment='1=有效,0=禁用')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'project_id', name='uk_user_project'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'projectId': self.project_id,
            'canView': self.can_view,
            'canSubmit': self.can_submit,
            'canManage': self.can_manage,
            'valid': self.valid,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }

