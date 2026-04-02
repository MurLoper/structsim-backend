"""
平台内容与埋点相关请求模型。
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PlatformSettingsUpdateRequest(BaseModel):
    announcement_poll_interval_seconds: Optional[int] = Field(default=None, ge=15, le=3600)
    tracking_enabled: Optional[bool] = None
    privacy_policy_required: Optional[bool] = None
    privacy_policy_title: Optional[str] = Field(default=None, max_length=120)
    privacy_policy_version: Optional[str] = Field(default=None, max_length=32)
    privacy_policy_summary: Optional[str] = Field(default=None, max_length=255)
    privacy_policy_content: Optional[str] = None


class AnnouncementUpsertRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    content: str = Field(..., min_length=1)
    level: str = Field(default="info", max_length=16)
    is_active: bool = True
    dismissible: bool = True
    sort: int = Field(default=100, ge=0, le=9999)
    start_at: Optional[int] = None
    end_at: Optional[int] = None
    link_text: Optional[str] = Field(default=None, max_length=60)
    link_url: Optional[str] = Field(default=None, max_length=255)


class PrivacyAcceptRequest(BaseModel):
    policy_version: Optional[str] = Field(default=None, max_length=32)


class TrackingEventItem(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=64)
    event_type: str = Field(default="interaction", min_length=1, max_length=32)
    page_path: Optional[str] = Field(default=None, max_length=255)
    target: Optional[str] = Field(default=None, max_length=120)
    session_id: Optional[str] = Field(default=None, max_length=64)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: Optional[int] = None


class TrackingEventBatchRequest(BaseModel):
    events: List[TrackingEventItem] = Field(default_factory=list, min_length=1, max_length=100)


class AnalyticsQueryRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=90)

