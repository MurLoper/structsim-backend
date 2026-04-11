from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models.order import Order  # noqa: E402
from app.models.order_condition_opti import OrderConditionOpti  # noqa: E402
from app.services.automation.mock_union_writer import mock_union_writer  # noqa: E402


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _build_query(args: argparse.Namespace):
    query = OrderConditionOpti.query
    if args.order_id:
        query = query.filter(OrderConditionOpti.order_id == args.order_id)
    if args.order_condition_id:
        query = query.filter(OrderConditionOpti.id == args.order_condition_id)
    return query.order_by(OrderConditionOpti.order_id.asc(), OrderConditionOpti.id.asc())


def _build_mock_issue_id(order: Order) -> int:
    return 600_000_000 + max(int(getattr(order, 'id', 0) or 0), 0)


def _build_mock_job_id(condition: OrderConditionOpti) -> int:
    return 700_000_000 + max(int(getattr(condition, 'id', 0) or 0), 0) * 10


def _seed_condition(condition: OrderConditionOpti, assign_missing: bool) -> Dict[str, Any]:
    order = Order.query.filter(Order.id == condition.order_id).first()
    if not order:
        return {'conditionId': condition.id, 'status': 'skipped', 'reason': 'order_not_found'}

    order_issue_id = _to_int(getattr(order, 'opt_issue_id', None), 0)
    condition_issue_id = _to_int(condition.opt_issue_id, 0)
    issue_id = condition_issue_id or order_issue_id
    job_id = _to_int(condition.opt_job_id, 0)
    assigned_local = False
    if assign_missing and issue_id <= 0:
        issue_id = _build_mock_issue_id(order)
    if assign_missing and issue_id > 0 and order_issue_id <= 0:
        order.opt_issue_id = issue_id
        assigned_local = True
    if assign_missing and issue_id > 0 and condition_issue_id <= 0:
        condition.opt_issue_id = issue_id
        assigned_local = True
    if assign_missing and job_id <= 0:
        job_id = _build_mock_job_id(condition)
        condition.opt_job_id = job_id
        if _to_int(condition.status, 0) == 0:
            condition.status = 1
        assigned_local = True

    if issue_id <= 0:
        return {'conditionId': condition.id, 'status': 'skipped', 'reason': 'missing_issue_id'}
    if job_id <= 0:
        return {'conditionId': condition.id, 'status': 'skipped', 'reason': 'missing_job_id'}

    mock_union_writer.write_submission(order, condition, issue_id, job_id)
    return {
        'conditionId': condition.id,
        'orderId': condition.order_id,
        'issueId': issue_id,
        'jobId': job_id,
        'assignedLocalIds': assigned_local,
        'status': 'seeded',
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Seed mock union_opt_kernal result rows for existing platform order conditions.'
    )
    parser.add_argument('--order-id', type=int, default=None, help='Only seed one platform order.')
    parser.add_argument(
        '--order-condition-id',
        type=int,
        default=None,
        help='Only seed one order_condition_opti row.',
    )
    parser.add_argument(
        '--config',
        default=os.getenv('FLASK_ENV', 'development'),
        help='Flask config name. Default: FLASK_ENV or development.',
    )
    parser.add_argument(
        '--assign-missing',
        action='store_true',
        help='Assign deterministic mock issue/job ids to local rows before seeding external mock results.',
    )
    args = parser.parse_args()

    app = create_app(args.config)
    with app.app_context():
        results: List[Dict[str, Any]] = []
        for condition in _build_query(args).all():
            results.append(_seed_condition(condition, args.assign_missing))
        if args.assign_missing:
            db.session.commit()

    print(json.dumps({'results': results}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
