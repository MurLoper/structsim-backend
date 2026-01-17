"""
结果表模型 - 仿真类型结果、轮次数据
按照 requirement_and_design.md 规范设计
支持分页查询，轮次可能达到2万条
"""
from datetime import datetime
from app import db


class SimTypeResult(db.Model):
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'orderId': self.order_id,
            'simTypeId': self.sim_type_id,
            'status': self.status,
            'progress': self.progress,
            'curNodeId': self.cur_node_id,
            'stuckNodeId': self.stuck_node_id,
            'stuckModuleId': self.stuck_module_id,
            'bestExists': self.best_exists,
            'bestRuleId': self.best_rule_id,
            'bestRoundIndex': self.best_round_index,
            'bestMetrics': self.best_metrics,
            'totalRounds': self.total_rounds,
            'completedRounds': self.completed_rounds,
            'failedRounds': self.failed_rounds,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }


class Round(db.Model):
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'simTypeResultId': self.sim_type_result_id,
            'orderId': self.order_id,
            'simTypeId': self.sim_type_id,
            'roundIndex': self.round_index,
            'params': self.params,
            'outputs': self.outputs,
            'status': self.status,
            'flowCurNodeId': self.flow_cur_node_id,
            'flowNodeProgress': self.flow_node_progress,
            'stuckModuleId': self.stuck_module_id,
            'errorCode': self.error_code,
            'errorMsg': self.error_msg,
            'startedAt': self.started_at,
            'finishedAt': self.finished_at,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }
    
    def to_list_dict(self):
        """列表展示用的精简字典"""
        return {
            'id': self.id,
            'roundIndex': self.round_index,
            'params': self.params,
            'outputs': self.outputs,
            'status': self.status,
            'flowCurNodeId': self.flow_cur_node_id,
            'stuckModuleId': self.stuck_module_id
        }

