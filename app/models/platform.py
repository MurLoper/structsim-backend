"""
平台内容与行为分析相关模型。
"""
from datetime import datetime

from app import db
from app.models.base import ToDictMixin


def _now_ts() -> int:
    return int(datetime.utcnow().timestamp())


class PlatformSetting(db.Model, ToDictMixin):
    __tablename__ = "platform_settings"

    key = db.Column(db.String(64), primary_key=True)
    value_json = db.Column(db.JSON, nullable=False, comment="配置值(JSON)")
    description = db.Column(db.String(255), comment="配置说明")
    updated_by = db.Column(db.String(32), comment="最后更新人域账号")
    created_at = db.Column(db.Integer, default=_now_ts)
    updated_at = db.Column(db.Integer, default=_now_ts, onupdate=_now_ts)


class Announcement(db.Model, ToDictMixin):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(120), nullable=False, comment="公告标题")
    content = db.Column(db.Text, nullable=False, comment="公告正文")
    level = db.Column(db.String(16), default="info", comment="公告等级")
    is_active = db.Column(db.SmallInteger, default=1, comment="1=启用,0=停用")
    dismissible = db.Column(db.SmallInteger, default=1, comment="1=可关闭,0=不可关闭")
    sort = db.Column(db.Integer, default=100, comment="排序值")
    start_at = db.Column(db.Integer, comment="生效开始时间戳")
    end_at = db.Column(db.Integer, comment="生效结束时间戳")
    link_text = db.Column(db.String(60), comment="链接文案")
    link_url = db.Column(db.String(255), comment="链接地址")
    created_by = db.Column(db.String(32), comment="创建人域账号")
    updated_by = db.Column(db.String(32), comment="最后更新人域账号")
    created_at = db.Column(db.Integer, default=_now_ts)
    updated_at = db.Column(db.Integer, default=_now_ts, onupdate=_now_ts)

    def to_public_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "level": self.level or "info",
            "is_active": self.is_active == 1,
            "dismissible": self.dismissible == 1,
            "sort": self.sort,
            "start_at": self.start_at,
            "end_at": self.end_at,
            "link_text": self.link_text,
            "link_url": self.link_url,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class PrivacyPolicyAcceptance(db.Model, ToDictMixin):
    __tablename__ = "privacy_policy_acceptances"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    domain_account = db.Column(db.String(32), nullable=False, index=True, comment="用户域账号")
    policy_version = db.Column(db.String(32), nullable=False, comment="已同意版本")
    accepted_at = db.Column(db.Integer, default=_now_ts, comment="同意时间")
    accepted_ip = db.Column(db.String(64), comment="同意时 IP")
    created_at = db.Column(db.Integer, default=_now_ts)
    updated_at = db.Column(db.Integer, default=_now_ts, onupdate=_now_ts)


class TrackingEvent(db.Model, ToDictMixin):
    __tablename__ = "tracking_events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_name = db.Column(db.String(64), nullable=False, index=True, comment="事件名")
    event_type = db.Column(db.String(32), nullable=False, index=True, comment="事件类型")
    page_path = db.Column(db.String(255), index=True, comment="页面路径")
    page_key = db.Column(db.String(64), index=True, comment="页面唯一标识")
    feature_key = db.Column(db.String(64), index=True, comment="功能唯一标识")
    module_key = db.Column(db.String(64), index=True, comment="模块唯一标识")
    result = db.Column(db.String(32), index=True, comment="结果标识")
    target = db.Column(db.String(120), comment="事件目标")
    session_id = db.Column(db.String(64), index=True, comment="会话标识")
    domain_account = db.Column(db.String(32), index=True, comment="用户域账号")
    metadata_json = db.Column(db.JSON, comment="事件元数据")
    duration_ms = db.Column(db.Integer, comment="耗时(毫秒)")
    created_at = db.Column(db.Integer, default=_now_ts, index=True)
