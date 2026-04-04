from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

import requests
from flask import current_app


class UserResourcePoolRepository:
    """按域账号读取用户可用资源池与默认资源池。"""

    @staticmethod
    def _is_success_payload(payload: Dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        if payload.get("success") is True:
            return True
        if payload.get("code") in (0, "0", 200, "200"):
            return True
        return False

    @staticmethod
    def _build_headers() -> Dict[str, str]:
        app_id = current_app.config.get("AUTH_COMPANY_APP_ID", "")
        secret_credit = current_app.config.get("AUTH_COMPANY_SECRET_CREDIT", "")
        headers: Dict[str, str] = {}
        if app_id:
            headers["X-App-Id"] = app_id
        if secret_credit:
            headers["X-Secret-Credit"] = secret_credit
        return headers

    @staticmethod
    def _normalize_resource_rows(raw_items: Any) -> List[Dict[str, Any]]:
        if not isinstance(raw_items, list):
            return []

        normalized: List[Dict[str, Any]] = []
        seen_ids: set[int] = set()
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            raw_id = item.get("id", item.get("source_id"))
            try:
                pool_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if pool_id in seen_ids:
                continue
            seen_ids.add(pool_id)
            name = str(
                item.get("name")
                or item.get("source_name")
                or item.get("label")
                or f"资源池-{pool_id}"
            ).strip() or f"资源池-{pool_id}"
            normalized.append({"id": pool_id, "name": name})
        return normalized

    def _mock_resource_pools(self) -> Dict[str, Any]:
        configured = current_app.config.get("AUTH_FAKE_USER_RESOURCE_POOLS_JSON")
        data = copy.deepcopy(configured if isinstance(configured, dict) else {})
        raw_items = (
            data.get("source_list")
            or data.get("sourceList")
            or data.get("resource_pools")
            or data.get("resourcePools")
            or data.get("sources")
            or data.get("list")
            or []
        )
        resource_pools = self._normalize_resource_rows(raw_items)

        default_resource_id: Optional[int] = None
        for key in (
            "default_source_id",
            "defaultSourceId",
            "default_resource_id",
            "defaultResourceId",
        ):
            raw_default = data.get(key)
            if raw_default is None:
                continue
            try:
                default_resource_id = int(raw_default)
            except (TypeError, ValueError):
                default_resource_id = None
            break

        if default_resource_id is None and resource_pools:
            default_resource_id = resource_pools[0]["id"]

        return {
            "resourcePools": resource_pools,
            "defaultResourceId": default_resource_id,
        }

    def _ensure_non_empty_result(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resource_pools = payload.get("resourcePools") if isinstance(payload, dict) else None
        if isinstance(resource_pools, list) and resource_pools:
            return payload
        return self._mock_resource_pools()

    def get_user_resource_pools(self, domain_account: str) -> Dict[str, Any]:
        resource_url = current_app.config.get("AUTH_GET_USER_RESOURCE_POOLS_URL", "")
        use_fake = bool(current_app.config.get("AUTH_USE_FAKE_USER_RESOURCE_POOLS", False))
        if use_fake or ((current_app.debug or current_app.testing) and not resource_url):
            return self._ensure_non_empty_result(self._mock_resource_pools())
        if not resource_url:
            return self._ensure_non_empty_result(self._mock_resource_pools())

        method = current_app.config.get("AUTH_GET_USER_RESOURCE_POOLS_METHOD", "GET").upper()
        timeout = float(current_app.config.get("AUTH_GET_USER_RESOURCE_POOLS_TIMEOUT", 8.0))
        headers = self._build_headers()
        payload = {"domain_account": str(domain_account or "").strip().lower()}

        try:
            if method == "POST":
                response = requests.post(resource_url, json=payload, headers=headers, timeout=timeout)
            else:
                response = requests.get(resource_url, params=payload, headers=headers, timeout=timeout)
        except requests.RequestException:
            return self._ensure_non_empty_result(self._mock_resource_pools())

        try:
            body = response.json() if response.text else {}
        except ValueError:
            body = {}

        if response.status_code >= 400 or not self._is_success_payload(body):
            return self._ensure_non_empty_result(self._mock_resource_pools())

        data = body.get("data") if isinstance(body.get("data"), dict) else body
        raw_items = None
        if isinstance(data, dict):
            raw_items = (
                data.get("source_list")
                or data.get("sourceList")
                or data.get("resource_pools")
                or data.get("resourcePools")
                or data.get("sources")
                or data.get("list")
            )
        elif isinstance(data, list):
            raw_items = data

        resource_pools = self._normalize_resource_rows(raw_items)
        default_resource_id: Optional[int] = None
        if isinstance(data, dict):
            for key in (
                "default_source_id",
                "defaultSourceId",
                "default_resource_id",
                "defaultResourceId",
            ):
                raw_default = data.get(key)
                if raw_default is None:
                    continue
                try:
                    default_resource_id = int(raw_default)
                except (TypeError, ValueError):
                    default_resource_id = None
                break

        if default_resource_id is None and resource_pools:
            default_resource_id = resource_pools[0]["id"]

        return self._ensure_non_empty_result({
            "resourcePools": resource_pools,
            "defaultResourceId": default_resource_id,
        })


user_resource_pool_repository = UserResourcePoolRepository()
