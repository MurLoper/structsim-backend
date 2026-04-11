from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import requests
from flask import current_app

from .mock_union_writer import mock_union_writer


class AutomationSubmissionError(Exception):
    """Raised when the automation distribution service cannot accept a job."""


@dataclass(frozen=True)
class AutomationSubmitResult:
    issue_id: int
    job_id: int
    status: str
    raw: Dict[str, Any]


class AutomationDistributionClient:
    """Adapter for the company automation distribution API."""

    def submit_condition(
        self,
        order,
        condition,
        issue_id: int | None = None,
        resubmit_attempt: int = 0,
    ) -> AutomationSubmitResult:
        mode = str(current_app.config.get('AUTOMATION_SUBMIT_MODE', 'mock') or 'mock').lower()
        url = str(current_app.config.get('AUTOMATION_DISTRIBUTION_URL') or '').strip()
        if mode == 'real' and url:
            return self._submit_real(order, condition, issue_id)
        if mode == 'real' and not url:
            raise AutomationSubmissionError('未配置自动化分发接口地址')
        return self._submit_mock(order, condition, issue_id, resubmit_attempt)

    def _submit_real(self, order, condition, issue_id: int | None) -> AutomationSubmitResult:
        url = str(current_app.config.get('AUTOMATION_DISTRIBUTION_URL') or '').strip()
        timeout = float(current_app.config.get('AUTOMATION_DISTRIBUTION_TIMEOUT', 15.0))
        payload = self._build_payload(order, condition, issue_id)
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            body = response.json()
        except requests.RequestException as exc:
            raise AutomationSubmissionError(f'自动化分发接口调用失败: {exc}') from exc
        except ValueError as exc:
            raise AutomationSubmissionError('自动化分发接口返回非 JSON 数据') from exc

        data = body.get('data') if isinstance(body, dict) and isinstance(body.get('data'), dict) else body
        if not isinstance(data, dict):
            raise AutomationSubmissionError('自动化分发接口返回结构无效')

        resolved_issue_id = self._to_int(
            data.get('issueId', data.get('issue_id', data.get('opt_issue_id', issue_id))),
            0,
        )
        resolved_job_id = self._to_int(
            data.get('jobId', data.get('job_id', data.get('opt_job_id'))),
            0,
        )
        if resolved_issue_id <= 0 or resolved_job_id <= 0:
            raise AutomationSubmissionError('自动化分发接口未返回有效 issue/job 标识')

        return AutomationSubmitResult(
            issue_id=resolved_issue_id,
            job_id=resolved_job_id,
            status=str(data.get('status') or 'submitted'),
            raw=data,
        )

    def _submit_mock(
        self,
        order,
        condition,
        issue_id: int | None,
        resubmit_attempt: int = 0,
    ) -> AutomationSubmitResult:
        resolved_issue_id = self._to_int(issue_id, 0) or self._build_mock_issue_id(order)
        resolved_job_id = self._build_mock_job_id(condition, resubmit_attempt)
        raw = {
            'mode': 'mock',
            'issueId': resolved_issue_id,
            'jobId': resolved_job_id,
            'orderId': getattr(order, 'id', None),
            'orderNo': getattr(order, 'order_no', None),
            'orderConditionId': getattr(condition, 'id', None),
        }
        if current_app.config.get('AUTOMATION_MOCK_WRITE_UNION_OPT', False):
            try:
                mock_union_writer.write_submission(order, condition, resolved_issue_id, resolved_job_id)
            except Exception as exc:
                raise AutomationSubmissionError(f'mock 外部优化库写入失败: {exc}') from exc
            raw['mockExternalWrite'] = True

        return AutomationSubmitResult(
            issue_id=resolved_issue_id,
            job_id=resolved_job_id,
            status='submitted',
            raw=raw,
        )

    @staticmethod
    def _build_payload(order, condition, issue_id: int | None) -> Dict[str, Any]:
        return {
            'issueId': issue_id,
            'orderId': getattr(order, 'id', None),
            'orderNo': getattr(order, 'order_no', None),
            'projectId': getattr(order, 'project_id', None),
            'phaseId': getattr(order, 'phase_id', None),
            'domainAccount': getattr(order, 'domain_account', None) or getattr(order, 'created_by', None),
            'baseDir': getattr(order, 'base_dir', None),
            'remark': getattr(condition, 'remark', None) or getattr(order, 'remark', None),
            'condition': getattr(condition, 'condition_snapshot', None) or {},
            'conditionRef': {
                'orderConditionId': getattr(condition, 'id', None),
                'conditionId': getattr(condition, 'condition_id', None),
                'foldTypeId': getattr(condition, 'fold_type_id', None),
                'simTypeId': getattr(condition, 'sim_type_id', None),
            },
        }

    @staticmethod
    def _build_mock_issue_id(order) -> int:
        return 600_000_000 + max(int(getattr(order, 'id', 0) or 0), 0)

    @staticmethod
    def _build_mock_job_id(condition, resubmit_attempt: int = 0) -> int:
        condition_id = max(int(getattr(condition, 'id', 0) or 0), 0)
        return 700_000_000 + condition_id * 10 + max(int(resubmit_attempt or 0), 0)

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default


automation_distribution_client = AutomationDistributionClient()
