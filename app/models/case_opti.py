from datetime import datetime

from app import db
from app.models.base import ToDictMixin


class OrderCaseOpti(db.Model, ToDictMixin):
    """Automation case/job entity under an order."""

    __tablename__ = 'order_case_opti'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.BigInteger, nullable=False, index=True)
    order_no = db.Column(db.String(50), index=True)
    case_index = db.Column(db.Integer, nullable=False, default=1)
    case_name = db.Column(db.String(200))
    opt_issue_id = db.Column(db.Integer, nullable=False, default=0, index=True)
    opt_job_id = db.Column(db.Integer, unique=True, index=True)
    parameter_scope = db.Column(db.String(32), nullable=False, default='per_condition')
    case_snapshot = db.Column(db.JSON)
    external_meta = db.Column(db.JSON)
    status = db.Column(db.SmallInteger, default=0)
    process = db.Column(db.Numeric(5, 2), default=0)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(
        db.Integer,
        default=lambda: int(datetime.utcnow().timestamp()),
        onupdate=lambda: int(datetime.utcnow().timestamp()),
    )

    __table_args__ = (
        db.UniqueConstraint('order_id', 'case_index', name='uk_order_case_index'),
        db.Index('idx_order_case_status', 'order_id', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_no': self.order_no,
            'case_index': self.case_index,
            'case_name': self.case_name,
            'opt_issue_id': self.opt_issue_id,
            'opt_job_id': self.opt_job_id,
            'parameter_scope': self.parameter_scope,
            'case_snapshot': self.case_snapshot,
            'external_meta': self.external_meta,
            'status': self.status,
            'process': float(self.process or 0),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class CaseConditionOpti(db.Model, ToDictMixin):
    """Platform condition mapped to union_opt_kernal.job_condition_config."""

    __tablename__ = 'case_condition_opti'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.BigInteger, nullable=False, index=True)
    order_no = db.Column(db.String(50), index=True)
    order_case_id = db.Column(db.BigInteger, nullable=False, index=True)
    case_index = db.Column(db.Integer, nullable=False, default=1)
    opt_issue_id = db.Column(db.Integer, nullable=False, default=0, index=True)
    opt_job_id = db.Column(db.Integer, index=True)
    opt_condition_config_id = db.Column(db.Integer, unique=True, index=True)
    parameter_scope = db.Column(db.String(32), nullable=False, default='per_condition')
    rotate_drop_flag = db.Column(db.SmallInteger, nullable=False, default=0)
    condition_id = db.Column(db.BigInteger, nullable=False)
    fold_type_id = db.Column(db.Integer, nullable=False)
    fold_type_name = db.Column(db.String(100))
    sim_type_id = db.Column(db.Integer, nullable=False)
    sim_type_name = db.Column(db.String(100))
    algorithm_type = db.Column(db.String(32))
    round_total = db.Column(db.Integer, default=0)
    output_count = db.Column(db.Integer, default=0)
    solver_id = db.Column(db.String(64))
    care_device_ids = db.Column(db.JSON)
    remark = db.Column(db.Text)
    running_module = db.Column(db.String(64))
    process = db.Column(db.Numeric(5, 2), default=0)
    status = db.Column(db.SmallInteger, default=0)
    statistics_json = db.Column(db.JSON)
    result_summary_json = db.Column(db.JSON)
    condition_snapshot = db.Column(db.JSON, nullable=False)
    subject_config = db.Column(db.JSON)
    external_meta = db.Column(db.JSON)
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(
        db.Integer,
        default=lambda: int(datetime.utcnow().timestamp()),
        onupdate=lambda: int(datetime.utcnow().timestamp()),
    )

    __table_args__ = (
        db.UniqueConstraint('order_id', 'condition_id', name='uk_cco_order_condition'),
        db.Index('idx_cco_order_status', 'order_id', 'status'),
        db.Index('idx_cco_order_case', 'order_id', 'order_case_id'),
        db.Index('idx_cco_order_simtype', 'order_id', 'sim_type_id'),
        db.Index('idx_cco_order_foldtype', 'order_id', 'fold_type_id'),
    )

    @property
    def order_case(self):
        return OrderCaseOpti.query.filter_by(id=self.order_case_id).first()

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_no': self.order_no,
            'order_case_id': self.order_case_id,
            'case_index': self.case_index,
            'opt_issue_id': self.opt_issue_id,
            'opt_job_id': self.opt_job_id,
            'opt_condition_config_id': self.opt_condition_config_id,
            'parameter_scope': self.parameter_scope,
            'rotate_drop_flag': self.rotate_drop_flag,
            'condition_id': self.condition_id,
            'fold_type_id': self.fold_type_id,
            'fold_type_name': self.fold_type_name,
            'sim_type_id': self.sim_type_id,
            'sim_type_name': self.sim_type_name,
            'algorithm_type': self.algorithm_type,
            'round_total': self.round_total,
            'output_count': self.output_count,
            'solver_id': self.solver_id,
            'care_device_ids': self.care_device_ids,
            'remark': self.remark,
            'running_module': self.running_module,
            'process': float(self.process or 0),
            'status': self.status,
            'statistics_json': self.statistics_json,
            'result_summary_json': self.result_summary_json,
            'condition_snapshot': self.condition_snapshot,
            'subject_config': self.subject_config,
            'external_meta': self.external_meta,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    def to_list_dict(self):
        payload = self.to_dict()
        payload.pop('condition_snapshot', None)
        payload.pop('subject_config', None)
        payload.pop('external_meta', None)
        payload.pop('statistics_json', None)
        payload.pop('result_summary_json', None)
        return payload
