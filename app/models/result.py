"""
结果表模型 - 仿真类型结果、轮次数据
按照 requirement_and_design.md 规范设计
支持分页查询，轮次可能达到2万条
"""
from datetime import datetime
from app import db
from app.models.base import ToDictMixin


class SimTypeResult(db.Model, ToDictMixin):
    """单仿真类型结果表"""
    __tablename__ = 'sim_type_results'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    sim_type_id = db.Column(db.Integer, db.ForeignKey('sim_types.id'), nullable=False)
    
    # 状态与进度
    status = db.Column(db.SmallInteger, default=1, comment='状态')
    progress = db.Column(db.SmallInteger, default=0, comment='进度百分比')
    cur_node_id = db.Column(db.Integer, comment='当前节点')
    stuck_node_id = db.Column(db.Integer, comment='卡住的节点')
    stuck_module_id = db.Column(db.Integer, comment='卡住的模块')
    
    # 最优结果（贝叶斯寻优场景）
    best_exists = db.Column(db.SmallInteger, default=0, comment='是否存在最优结果')
    best_rule_id = db.Column(db.Integer, comment='最优规则ID')
    best_round_index = db.Column(db.Integer, comment='最优轮次索引')
    best_metrics = db.Column(db.JSON, comment='最优指标值')
    
    # 轮次统计
    total_rounds = db.Column(db.Integer, default=0, comment='总轮次数')
    completed_rounds = db.Column(db.Integer, default=0, comment='已完成轮次数')
    failed_rounds = db.Column(db.Integer, default=0, comment='失败轮次数')
    
    # 时间戳
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))
    
    # 复合索引
    __table_args__ = (
        db.Index('idx_order_simtype', 'order_id', 'sim_type_id'),
    )


class Round(db.Model, ToDictMixin):
    """轮次数据表 - 可能有大量数据，需要分页"""
    __tablename__ = 'rounds'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sim_type_result_id = db.Column(db.Integer, db.ForeignKey('sim_type_results.id'), 
                                   nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    sim_type_id = db.Column(db.Integer, nullable=False, index=True)
    
    # 轮次索引
    round_index = db.Column(db.Integer, nullable=False, comment='轮次索引，从1开始')
    
    # 参数值
    params = db.Column(db.JSON, comment='参数值 {param_id: value}')
    
    # 输出结果（可能为空，等待计算）
    outputs = db.Column(db.JSON, comment='输出结果 {output_id: value}')
    
    # 状态
    status = db.Column(db.SmallInteger, default=1, comment='状态')
    
    # 流程进度
    flow_cur_node_id = db.Column(db.Integer, comment='当前流程节点')
    flow_node_progress = db.Column(db.JSON, comment='各节点进度')
    stuck_module_id = db.Column(db.Integer, comment='卡住的模块ID')
    
    # 错误信息
    error_code = db.Column(db.String(50), comment='错误码')
    error_msg = db.Column(db.Text, comment='错误信息')
    
    # 时间戳
    started_at = db.Column(db.Integer, comment='开始时间')
    finished_at = db.Column(db.Integer, comment='结束时间')
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))
    
    # 复合索引
    __table_args__ = (
        db.Index('idx_simresult_round', 'sim_type_result_id', 'round_index'),
        db.Index('idx_order_simtype_round', 'order_id', 'sim_type_id', 'round_index'),
    )

    def to_list_dict(self):
        """列表展示用的精简字典"""
        return {
            'id': self.id,
            'round_index': self.round_index,
            'params': self.params,
            'outputs': self.outputs,
            'status': self.status,
            'flow_cur_node_id': self.flow_cur_node_id,
            'stuck_module_id': self.stuck_module_id
        }

