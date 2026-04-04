"""
平台内容与埋点业务层。
"""
from __future__ import annotations

import time
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional

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
    "announcement_poll_interval_seconds": "公告轮询周期(秒)",
    "tracking_enabled": "是否启用前端埋点",
    "privacy_policy_required": "是否要求用户同意隐私协议",
    "privacy_policy_title": "隐私协议标题",
    "privacy_policy_version": "隐私协议版本",
    "privacy_policy_summary": "隐私协议摘要",
    "privacy_policy_content": "隐私协议正文",
}


FUNNEL_DEFINITIONS = [
    {
        "key": "submission_to_result",
        "title": "新建仿真到结果查看",
        "steps": [
            {"event_name": "dashboard.shortcut_click", "feature_key": "dashboard.new_sim"},
            {"event_name": "submission.submit_success", "feature_key": "submission.submit"},
            {"event_name": "results.view", "feature_key": "results.page"},
        ],
    },
    {
        "key": "orders_to_results",
        "title": "申请单到结果查看",
        "steps": [
            {"event_name": "orders.page_interaction", "feature_key": "orders.result_open"},
            {"event_name": "results.view", "feature_key": "results.page"},
        ],
    },
]


def _now_ts() -> int:
    return int(time.time())


def _safe_str(value: Any) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def _safe_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
            "announcements": [
                self._serialize_announcement(item) for item in self.repository.list_announcements()
            ],
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
            link_text=_safe_str(payload.get("link_text")),
            link_url=_safe_str(payload.get("link_url")),
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
        item.link_text = _safe_str(payload.get("link_text"))
        item.link_url = _safe_str(payload.get("link_url"))
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

    def _normalize_tracking_event(
        self, user: User, item: Dict[str, Any], now_ts: int
    ) -> TrackingEvent:
        metadata = item.get("metadata") or {}
        return TrackingEvent(
            event_name=str(item["event_name"]).strip(),
            event_type=str(item.get("event_type") or "interaction").strip() or "interaction",
            page_path=_safe_str(item.get("page_path")),
            page_key=_safe_str(metadata.get("pageKey")),
            feature_key=_safe_str(metadata.get("featureKey")),
            module_key=_safe_str(metadata.get("moduleKey")),
            result=_safe_str(metadata.get("result")),
            target=_safe_str(item.get("target")),
            session_id=_safe_str(item.get("session_id")),
            domain_account=user.domain_account,
            metadata_json=metadata,
            duration_ms=_safe_int(metadata.get("durationMs")),
            created_at=_safe_int(item.get("occurred_at")) or now_ts,
        )

    def track_events(self, user_identity: Any, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        user = self._get_valid_user_or_raise(user_identity)
        settings = self._get_settings()
        if not bool(settings["tracking_enabled"]):
            return {"accepted_count": 0, "tracking_enabled": False}

        now_ts = _now_ts()
        rows = [self._normalize_tracking_event(user, item, now_ts) for item in events]
        self.repository.add_tracking_events(rows)
        self.repository.commit()
        return {"accepted_count": len(rows), "tracking_enabled": True}

    def _load_analytics_events(self, days: int) -> List[TrackingEvent]:
        now_ts = _now_ts()
        start_ts = now_ts - days * 24 * 60 * 60
        return self.repository.list_tracking_events_since(start_ts)

    def get_analytics_summary(self, user_identity: Any, days: int) -> Dict[str, Any]:
        self._get_valid_user_or_raise(user_identity)
        events = self._load_analytics_events(days)

        total_events = len(events)
        unique_users = {item.domain_account for item in events if item.domain_account}
        page_views = 0
        event_counter: Counter[str] = Counter()
        page_counter: Counter[str] = Counter()
        module_counter: Counter[str] = Counter()
        success_events = 0
        failure_events = 0
        timeline_counter: defaultdict[str, int] = defaultdict(int)

        for item in events:
            event_counter[item.event_name] += 1
            if item.event_name == "page_view":
                if item.page_key:
                    page_counter[item.page_key] += 1
                elif item.page_path:
                    page_counter[item.page_path] += 1
            if item.module_key:
                module_counter[item.module_key] += 1
            if item.event_name == "page_view":
                page_views += 1
            if item.result == "success":
                success_events += 1
            if item.result == "failure" or item.event_name.endswith("failure"):
                failure_events += 1
            day_key = time.strftime("%Y-%m-%d", time.localtime(item.created_at))
            timeline_counter[day_key] += 1

        announcement_views = event_counter.get("platform.announcement_view", 0)
        privacy_acceptances = event_counter.get("platform.privacy_accept", 0)
        feature_events = sum(
            count
            for name, count in event_counter.items()
            if name != "page_view" and "." in name
        )

        return {
            "summary": {
                "days": days,
                "total_events": total_events,
                "unique_users": len(unique_users),
                "page_views": page_views,
                "privacy_acceptances": privacy_acceptances,
                "announcement_views": announcement_views,
                "feature_events": feature_events,
                "success_events": success_events,
                "failure_events": failure_events,
            },
            "timeline": [
                {"date": day, "count": count}
                for day, count in sorted(timeline_counter.items(), key=lambda pair: pair[0])
            ],
            "top_events": [{"name": name, "count": count} for name, count in event_counter.most_common(10)],
            "top_pages": [{"path": name, "count": count} for name, count in page_counter.most_common(10)],
            "top_modules": [{"name": name, "count": count} for name, count in module_counter.most_common(10)],
        }

    def get_analytics_features(self, user_identity: Any, days: int) -> Dict[str, Any]:
        self._get_valid_user_or_raise(user_identity)
        events = self._load_analytics_events(days)

        page_stats: dict[str, dict[str, Any]] = {}
        feature_stats: dict[str, dict[str, Any]] = {}
        module_stats: dict[str, dict[str, Any]] = {}

        for item in events:
            user_key = item.domain_account or "anonymous"

            if item.event_name == "page_view" and (item.page_key or item.page_path):
                page_key = item.page_key or item.page_path
                current = page_stats.setdefault(
                    page_key,
                    {
                        "page_key": item.page_key or page_key,
                        "page_path": item.page_path or page_key,
                        "count": 0,
                        "users": set(),
                    },
                )
                current["count"] += 1
                current["users"].add(user_key)

            if item.feature_key:
                current = feature_stats.setdefault(
                    item.feature_key,
                    {
                        "feature_key": item.feature_key,
                        "event_name": item.event_name,
                        "module_key": item.module_key,
                        "page_key": item.page_key,
                        "count": 0,
                        "users": set(),
                    },
                )
                current["count"] += 1
                current["users"].add(user_key)

            if item.module_key:
                current = module_stats.setdefault(
                    item.module_key,
                    {"module_key": item.module_key, "count": 0, "users": set()},
                )
                current["count"] += 1
                current["users"].add(user_key)

        def _normalize(items: Iterable[dict[str, Any]], user_key: str) -> List[dict[str, Any]]:
            result: List[dict[str, Any]] = []
            for item in items:
                next_item = dict(item)
                next_item[user_key] = len(item["users"])
                del next_item["users"]
                result.append(next_item)
            return result

        pages = sorted(
            _normalize(page_stats.values(), "unique_users"),
            key=lambda item: item["count"],
            reverse=True,
        )
        features = sorted(
            _normalize(feature_stats.values(), "unique_users"),
            key=lambda item: item["count"],
            reverse=True,
        )
        modules = sorted(
            _normalize(module_stats.values(), "unique_users"),
            key=lambda item: item["count"],
            reverse=True,
        )

        return {"days": days, "pages": pages[:20], "features": features[:30], "modules": modules[:20]}

    def get_analytics_funnels(self, user_identity: Any, days: int) -> Dict[str, Any]:
        self._get_valid_user_or_raise(user_identity)
        events = sorted(self._load_analytics_events(days), key=lambda item: (item.created_at, item.id))

        sessions: dict[str, List[TrackingEvent]] = defaultdict(list)
        for item in events:
            session_key = item.session_id or f"user:{item.domain_account or 'anonymous'}"
            sessions[session_key].append(item)

        funnels: List[dict[str, Any]] = []
        for definition in FUNNEL_DEFINITIONS:
            step_counts = [0 for _ in definition["steps"]]
            for session_events in sessions.values():
                step_index = 0
                for item in session_events:
                    if step_index >= len(definition["steps"]):
                        break
                    step = definition["steps"][step_index]
                    if item.event_name != step["event_name"]:
                        continue
                    if step.get("feature_key") and item.feature_key != step["feature_key"]:
                        continue
                    step_counts[step_index] += 1
                    step_index += 1

            steps = []
            previous = step_counts[0] if step_counts else 0
            for index, step in enumerate(definition["steps"]):
                count = step_counts[index]
                conversion_rate = 0 if previous == 0 else round(count / previous * 100, 2)
                steps.append(
                    {
                        "index": index + 1,
                        "event_name": step["event_name"],
                        "feature_key": step.get("feature_key"),
                        "count": count,
                        "conversion_rate": conversion_rate if index > 0 else 100.0,
                    }
                )
                previous = count or previous

            funnels.append({"key": definition["key"], "title": definition["title"], "steps": steps})

        return {"days": days, "funnels": funnels}

    def get_analytics_failures(self, user_identity: Any, days: int) -> Dict[str, Any]:
        self._get_valid_user_or_raise(user_identity)
        events = self._load_analytics_events(days)

        failed_events = [
            item
            for item in events
            if item.result == "failure" or item.event_name.endswith("failure")
        ]

        event_counter: Counter[str] = Counter()
        page_counter: Counter[str] = Counter()
        feature_counter: Counter[str] = Counter()

        for item in failed_events:
            event_counter[item.event_name] += 1
            if item.page_key:
                page_counter[item.page_key] += 1
            elif item.page_path:
                page_counter[item.page_path] += 1
            if item.feature_key:
                feature_counter[item.feature_key] += 1

        return {
            "days": days,
            "total_failures": len(failed_events),
            "top_failed_events": [
                {"name": name, "count": count} for name, count in event_counter.most_common(12)
            ],
            "top_failed_pages": [
                {"page_key": name, "count": count} for name, count in page_counter.most_common(12)
            ],
            "top_failed_features": [
                {"feature_key": name, "count": count}
                for name, count in feature_counter.most_common(12)
            ],
        }


platform_service = PlatformService()
