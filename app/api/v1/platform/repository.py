"""
平台内容与埋点仓储层。
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import desc

from app import db
from app.models.platform import (
    Announcement,
    PlatformSetting,
    PrivacyPolicyAcceptance,
    TrackingEvent,
)


class PlatformRepository:
    def get_settings(self, keys: Iterable[str]) -> Dict[str, PlatformSetting]:
        items = PlatformSetting.query.filter(PlatformSetting.key.in_(list(keys))).all()
        return {item.key: item for item in items}

    def upsert_setting(
        self,
        key: str,
        value_json: Any,
        updated_by: Optional[str] = None,
        description: Optional[str] = None,
    ) -> PlatformSetting:
        item = PlatformSetting.query.filter_by(key=key).first()
        if not item:
            item = PlatformSetting(key=key, value_json=value_json, description=description)
            db.session.add(item)
        else:
            item.value_json = value_json
            if description is not None:
                item.description = description
        item.updated_by = updated_by
        return item

    def list_announcements(self) -> List[Announcement]:
        return (
            Announcement.query.order_by(
                Announcement.sort.asc(),
                desc(Announcement.updated_at),
                desc(Announcement.id),
            ).all()
        )

    def get_announcement(self, announcement_id: int) -> Optional[Announcement]:
        return Announcement.query.filter_by(id=announcement_id).first()

    def save_announcement(self, announcement: Announcement) -> Announcement:
        db.session.add(announcement)
        return announcement

    def delete_announcement(self, announcement: Announcement) -> None:
        db.session.delete(announcement)

    def list_tracking_events_since(self, start_ts: int) -> List[TrackingEvent]:
        return (
            TrackingEvent.query.filter(TrackingEvent.created_at >= start_ts)
            .order_by(TrackingEvent.created_at.asc(), TrackingEvent.id.asc())
            .all()
        )

    def get_latest_privacy_acceptance(
        self, domain_account: str, policy_version: Optional[str] = None
    ) -> Optional[PrivacyPolicyAcceptance]:
        query = PrivacyPolicyAcceptance.query.filter_by(domain_account=domain_account)
        if policy_version:
            query = query.filter_by(policy_version=policy_version)
        return query.order_by(desc(PrivacyPolicyAcceptance.accepted_at)).first()

    def save_privacy_acceptance(
        self,
        domain_account: str,
        policy_version: str,
        accepted_at: int,
        accepted_ip: Optional[str],
    ) -> PrivacyPolicyAcceptance:
        item = PrivacyPolicyAcceptance(
            domain_account=domain_account,
            policy_version=policy_version,
            accepted_at=accepted_at,
            accepted_ip=accepted_ip,
        )
        db.session.add(item)
        return item

    def add_tracking_events(self, rows: List[TrackingEvent]) -> None:
        db.session.add_all(rows)

    def commit(self) -> None:
        db.session.commit()


platform_repository = PlatformRepository()

