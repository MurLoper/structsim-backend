"""
平台内容与埋点业务层。
"""
from __future__ import annotations

import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from app.common.errors import BusinessError, NotFoundError
from app.constants import ErrorCode
from app.models.auth import User
from app.models.platform import Announcement, TrackingEvent
from .repository import platform_repository


DEFAULT_PLATFORM_SETTINGS: Dict[str, Any] = {
    "announcement_poll_interval_seconds": 60,
    "tracking_enabled": True,
    "privacy_policy_required": True,
    "privacy_policy_title": "隐私协议",
    "privacy_policy_version": "1.0.0",
    "privacy_policy_summary": "请仔细阅读并同意隐私协议后继续使用系统。",
    "privacy_policy_content": (
        "欢迎使用 StructSim AI Platform。\n\n"
        "1. 我们会记录与你使用系统相关的必要账号信息、操作日志和业务数据，用于身份认证、"
        "安全审计、问题排查与功能改进。\n"
        "2. 你的申请单、结果数据和配置信息仅用于当前业务处理与系统分析，不会超出授权范围使用。\n"
        "3. 如需停用账号、导出数据或发起隐私相关咨询，请联系系统管理员。"
    ),
}


SETTING_DESCRIPTIONS: Dict[str, str] = {
    "announcement_poll_interval_seconds": "公告轮询周期（秒）",
    "tracking_enabled": "是否启用前端埋点收集",
    "privacy_policy_required": "是否强制要求同意隐私协议",
    "privacy_policy_title": "隐私协议标题",
    "privacy_policy_version": "隐私协议版本号",
    "privacy_policy_summary": "隐私协议摘要",
    "privacy_policy_content": "隐私协议正文",
}


def _now_ts() -> int:
    return int(time.time())


class PlatformService:
    def __init__(self):
        self.repository = platform_repository

    @staticmethod
    def _normalize_domain_account(value: Any) -> str:
        return str(value or "").strip().lower()

    def _get_valid_user_or_raise(self, user_identity: Any) -> User:
        domain_account = self._normalize_domain_account(user_identity)
        if not domain_account:
            raise BusinessError(ErrorCode.TOKEN_INVALID, "无效的用户身份")

        user = User.query.filter_by(domain_account=domain_account, valid=1).first()
        if not user:
            raise BusinessError(ErrorCode.USER_NOT_FOUND, "当前用户不存在或已被禁用")
        return user

    def _get_settings(self) -> Dict[str, Any]:
        rows = self.repository.get_settings(DEFAULT_PLATFORM_SETTINGS.keys())
        data = dict(DEFAULT_PLATFORM_SETTINGS)
        for key, row in rows.items():
            data[key] = row.value_json
        return data

    @staticmethod
    def _serialize_announcement(item: Announcement) -> Dict[str, Any]:
        return item.to_public_dict()

    def _get_active_announcements(self, now_ts: Optional[int] = None) -> List[Dict[str, Any]]:
        current_ts = now_ts or _now_ts()
        result: List[Dict[str, Any]] = []
        for item in self.repository.list_announcements():
            if item.is_active != 1:
                continue
            if item.start_at and item.start_at > current_ts:
                continue
            if item.end_at and item.end_at < current_ts:
                continue
            result.append(self._serialize_announcement(item))
        return result

    def get_bootstrap(self, user_identity: Any) -> Dict[str, Any]:
        user = self._get_valid_user_or_raise(user_identity)
        settings = self._get_settings()
        acceptance = self.repository.get_latest_privacy_acceptance(
            user.domain_account,
            str(settings["privacy_policy_version"]),
        )
        return {
            "announcement_poll_interval_seconds": int(
                settings["announcement_poll_interval_seconds"] or 60
            ),
            "tracking_enabled": bool(settings["tracking_enabled"]),
            "active_announcements": self._get_active_announcements(),
            "privacy_policy": {
                "required": bool(settings["privacy_policy_required"]),
                "title": str(settings["privacy_policy_title"]),
                "version": str(settings["privacy_policy_version"]),
                "summary": str(settings["privacy_policy_summary"]),
                "accepted": acceptance is not None,
                "accepted_at": acceptance.accepted_at if acceptance else None,
            },
        }

    def get_privacy_policy(self, user_identity: Any) -> Dict[str, Any]:
        user = self._get_valid_user_or_raise(user_identity)
        settings = self._get_settings()
        version = str(settings["privacy_policy_version"])
        acceptance = self.repository.get_latest_privacy_acceptance(user.domain_account, version)
        return {
            "required": bool(settings["privacy_policy_required"]),
            "title": str(settings["privacy_policy_title"]),
            "version": version,
            "summary": str(settings["privacy_policy_summary"]),
            "content": str(settings["privacy_policy_content"]),
            "accepted": acceptance is not None,
            "accepted_at": acceptance.accepted_at if acceptance else None,
        }

    def accept_privacy_policy(
        self, user_identity: Any, accepted_ip: Optional[str], policy_version: Optional[str] = None
    ) -> Dict[str, Any]:
        user = self._get_valid_user_or_raise(user_identity)
        settings = self._get_settings()
        current_version = str(settings["privacy_policy_version"])
        target_version = str(policy_version or current_version)
        if target_version != current_version:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "当前提交的隐私协议版本不是最新版本")

        accepted_at = _now_ts()
        self.repository.save_privacy_acceptance(
            domain_account=user.domain_account,
            policy_version=target_version,
            accepted_at=accepted_at,
            accepted_ip=accepted_ip,
        )
        self.repository.commit()
        return {
            "accepted": True,
            "policy_version": target_version,
            "accepted_at": accepted_at,
        }

    def get_admin_content(self, user_identity: Any) -> Dict[str, Any]:
        self._get_valid_user_or_raise(user_identity)
        return {
            "settings": self._get_settings(),
            "announcements": [self._serialize_announcement(item) for item in self.repository.list_announcements()],
        }

    def update_settings(self, user_identity: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        user = self._get_valid_user_or_raise(user_identity)
        next_settings = self._get_settings()

        for key, value in payload.items():
            if key not in DEFAULT_PLATFORM_SETTINGS:
                continue
            next_settings[key] = value
            self.repository.upsert_setting(
                key=key,
                value_json=value,
                updated_by=user.domain_account,
                description=SETTING_DESCRIPTIONS.get(key),
            )

        self.repository.commit()
        return {"settings": next_settings}

    def create_announcement(self, user_identity: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        user = self._get_valid_user_or_raise(user_identity)
        item = Announcement(
            title=str(payload["title"]).strip(),
            content=str(payload["content"]).strip(),
            level=str(payload.get("level") or "info").strip() or "info",
            is_active=1 if payload.get("is_active", True) else 0,
            dismissible=1 if payload.get("dismissible", True) else 0,
            sort=int(payload.get("sort") or 100),
            start_at=payload.get("start_at"),
            end_at=payload.get("end_at"),
            link_text=str(payload.get("link_text") or "").strip() or None,
            link_url=str(payload.get("link_url") or "").strip() or None,
            created_by=user.domain_account,
            updated_by=user.domain_account,
        )
        self.repository.save_announcement(item)
        self.repository.commit()
        return self._serialize_announcement(item)

    def update_announcement(
        self, user_identity: Any, announcement_id: int, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        user = self._get_valid_user_or_raise(user_identity)
        item = self.repository.get_announcement(announcement_id)
        if not item:
            raise NotFoundError("公告不存在")

        item.title = str(payload["title"]).strip()
        item.content = str(payload["content"]).strip()
        item.level = str(payload.get("level") or "info").strip() or "info"
        item.is_active = 1 if payload.get("is_active", True) else 0
        item.dismissible = 1 if payload.get("dismissible", True) else 0
        item.sort = int(payload.get("sort") or 100)
        item.start_at = payload.get("start_at")
        item.end_at = payload.get("end_at")
        item.link_text = str(payload.get("link_text") or "").strip() or None
        item.link_url = str(payload.get("link_url") or "").strip() or None
        item.updated_by = user.domain_account
        self.repository.save_announcement(item)
        self.repository.commit()
        return self._serialize_announcement(item)

    def delete_announcement(self, user_identity: Any, announcement_id: int) -> None:
        self._get_valid_user_or_raise(user_identity)
        item = self.repository.get_announcement(announcement_id)
        if not item:
            raise NotFoundError("公告不存在")
        self.repository.delete_announcement(item)
        self.repository.commit()

    def track_events(self, user_identity: Any, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        user = self._get_valid_user_or_raise(user_identity)
        settings = self._get_settings()
        if not bool(settings["tracking_enabled"]):
            return {"accepted_count": 0, "tracking_enabled": False}

        now_ts = _now_ts()
        rows: List[TrackingEvent] = []
        for item in events:
            rows.append(
                TrackingEvent(
                    event_name=str(item["event_name"]).strip(),
                    event_type=str(item.get("event_type") or "interaction").strip() or "interaction",
                    page_path=str(item.get("page_path") or "").strip() or None,
                    target=str(item.get("target") or "").strip() or None,
                    session_id=str(item.get("session_id") or "").strip() or None,
                    domain_account=user.domain_account,
                    metadata_json=item.get("metadata") or {},
                    created_at=int(item.get("occurred_at") or now_ts),
                )
            )
        self.repository.add_tracking_events(rows)
        self.repository.commit()
        return {"accepted_count": len(rows), "tracking_enabled": True}

    def get_analytics_summary(self, user_identity: Any, days: int) -> Dict[str, Any]:
        self._get_valid_user_or_raise(user_identity)
        now_ts = _now_ts()
        start_ts = now_ts - days * 24 * 60 * 60
        events = self.repository.list_tracking_events_since(start_ts)

        total_events = len(events)
        unique_users = {item.domain_account for item in events if item.domain_account}
        page_view_count = 0
        event_counter: Counter[str] = Counter()
        page_counter: Counter[str] = Counter()
        timeline_counter: defaultdict[str, int] = defaultdict(int)

        for item in events:
            event_counter[item.event_name] += 1
            if item.page_path:
                page_counter[item.page_path] += 1
            if item.event_name == "page_view":
                page_view_count += 1
            day_key = time.strftime("%Y-%m-%d", time.localtime(item.created_at))
            timeline_counter[day_key] += 1

        acceptances = event_counter.get("privacy_accept", 0)
        announcement_views = event_counter.get("announcement_view", 0)

        timeline = [
            {"date": day, "count": count}
            for day, count in sorted(timeline_counter.items(), key=lambda pair: pair[0])
        ]
        top_events = [{"name": name, "count": count} for name, count in event_counter.most_common(8)]
        top_pages = [{"path": path, "count": count} for path, count in page_counter.most_common(8)]

        return {
            "summary": {
                "days": days,
                "total_events": total_events,
                "unique_users": len(unique_users),
                "page_views": page_view_count,
                "privacy_acceptances": acceptances,
                "announcement_views": announcement_views,
            },
            "timeline": timeline,
            "top_events": top_events,
            "top_pages": top_pages,
        }


platform_service = PlatformService()

