"""
订单 condition 优化运行实体模型。

第一阶段不加外键，避免影响当前数据库导入导出与跨环境同步。
"""
from datetime import datetime

from app import db
from app.models.base import ToDictMixin


class OrderConditionOpti(db.Model, ToDictMixin):
    """订单下单个 condition 的运行实体。"""

    __tablename__ = 'order_condition_opti'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(db.BigInteger, nullable=False, index=True, comment='主单ID')
    order_no = db.Column(db.String(50), comment='主单编号冗余')
    opt_issue_id = db.Column(db.Integer, nullable=False, index=True, comment='自动优化申请单ID')
    opt_job_id = db.Column(db.Integer, unique=True, comment='自动化方案作业ID')
    condition_id = db.Column(db.BigInteger, nullable=False, comment='condition标识')
    fold_type_id = db.Column(db.Integer, nullable=False, comment='姿态ID')
    fold_type_name = db.Column(db.String(100), comment='姿态名称快照')
    sim_type_id = db.Column(db.Integer, nullable=False, comment='仿真类型ID')
    sim_type_name = db.Column(db.String(100), comment='仿真类型名称快照')
    algorithm_type = db.Column(db.String(32), comment='算法类型')
    round_total = db.Column(db.Integer, default=0, comment='轮次数量概览')
    output_count = db.Column(db.Integer, default=0, comment='输出数量概览')
    solver_id = db.Column(db.String(64), comment='求解器标识，包含类型和版本语义')
    care_device_ids = db.Column(db.JSON, comment='关注器件ID列表')
    remark = db.Column(db.Text, comment='condition级备注')
    running_module = db.Column(db.String(64), comment='当前运行模块')
    process = db.Column(db.Numeric(5, 2), default=0, comment='进度百分比')
    status = db.Column(db.SmallInteger, default=0, comment='状态')
    statistics_json = db.Column(db.JSON, comment='统计摘要')
    result_summary_json = db.Column(db.JSON, comment='结果摘要')
    condition_snapshot = db.Column(db.JSON, nullable=False, comment='完整condition快照')
    external_meta = db.Column(db.JSON, comment='外部扩展信息')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(
        db.Integer,
        default=lambda: int(datetime.utcnow().timestamp()),
        onupdate=lambda: int(datetime.utcnow().timestamp()),
    )

    __table_args__ = (
        db.UniqueConstraint('order_id', 'condition_id', name='uk_oco_order_condition'),
        db.Index('idx_oco_order_status', 'order_id', 'status'),
        db.Index('idx_oco_order_simtype', 'order_id', 'sim_type_id'),
        db.Index('idx_oco_order_foldtype', 'order_id', 'fold_type_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_no': self.order_no,
            'opt_issue_id': self.opt_issue_id,
            'opt_job_id': self.opt_job_id,
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
            'external_meta': self.external_meta,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    def to_list_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_no': self.order_no,
            'opt_issue_id': self.opt_issue_id,
            'opt_job_id': self.opt_job_id,
            'condition_id': self.condition_id,
            'fold_type_id': self.fold_type_id,
            'fold_type_name': self.fold_type_name,
            'sim_type_id': self.sim_type_id,
            'sim_type_name': self.sim_type_name,
            'algorithm_type': self.algorithm_type,
            'round_total': self.round_total,
            'output_count': self.output_count,
            'solver_id': self.solver_id,
            'running_module': self.running_module,
            'process': float(self.process or 0),
            'status': self.status,
            'updated_at': self.updated_at,
        }
