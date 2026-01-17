"""
订单表模型 - 提单主表及相关
按照 requirement_and_design.md 规范设计
"""
from datetime import datetime
from app import db


class Order(db.Model):
    """订单/申请单主表"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False, comment='订单编号')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, comment='项目ID')
    
    # 源文件信息
    origin_file_type = db.Column(db.SmallInteger, default=1, comment='1=路径,2=文件ID,3=上传')
    origin_file_name = db.Column(db.String(255), comment='文件名')
    origin_file_path = db.Column(db.String(500), comment='文件路径')
    origin_file_id = db.Column(db.Integer, comment='文件ID')
    
    # 姿态
    fold_type_id = db.Column(db.Integer, db.ForeignKey('fold_types.id'), comment='姿态类型ID')
    
    # 参与人
    participant_uids = db.Column(db.JSON, comment='参与人用户ID列表')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 选中的仿真类型列表
    sim_type_ids = db.Column(db.JSON, comment='选中的仿真类型ID列表')
    
    # 核心：各仿真类型的配置（大JSON）
    opt_param = db.Column(db.JSON, comment='各仿真类型配置 {sim_type_id: {...}}')
    
    # 工作流
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'), comment='工作流ID')
    
    # 状态与进度
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1=待处理,2=运行中,3=完成,4=失败')
    progress = db.Column(db.SmallInteger, default=0, comment='进度百分比 0-100')
    cur_node_id = db.Column(db.Integer, comment='当前流程节点ID')
    
    # 提交校验配置
    submit_check = db.Column(db.JSON, comment='提交校验配置')
    
    # 客户端元数据
    client_meta = db.Column(db.JSON, comment='客户端元数据 {lang, theme, ui_ver}')
    
    # 创建人
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建人ID')
    
    # 时间戳
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))
    
    def to_dict(self):
        return {
            'id': self.id,
            'orderNo': self.order_no,
            'projectId': self.project_id,
            'originFile': {
                'type': self.origin_file_type,
                'name': self.origin_file_name,
                'path': self.origin_file_path,
                'fileId': self.origin_file_id
            },
            'foldTypeId': self.fold_type_id,
            'participantUids': self.participant_uids,
            'remark': self.remark,
            'simTypeIds': self.sim_type_ids,
            'optParam': self.opt_param,
            'workflowId': self.workflow_id,
            'status': self.status,
            'progress': self.progress,
            'curNodeId': self.cur_node_id,
            'submitCheck': self.submit_check,
            'clientMeta': self.client_meta,
            'createdBy': self.created_by,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }
    
    def to_list_dict(self):
        """列表展示用的精简字典"""
        return {
            'id': self.id,
            'orderNo': self.order_no,
            'projectId': self.project_id,
            'simTypeIds': self.sim_type_ids,
            'status': self.status,
            'progress': self.progress,
            'createdBy': self.created_by,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }


class OrderResult(db.Model):
    """订单结果概览表"""
    __tablename__ = 'order_results'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    
    # 总体状态
    status = db.Column(db.SmallInteger, default=1, comment='状态')
    progress = db.Column(db.SmallInteger, default=0, comment='进度百分比')
    cur_node_id = db.Column(db.Integer, comment='当前节点')
    
    # 各仿真类型结果ID列表
    sim_type_result_ids = db.Column(db.JSON, comment='仿真类型结果ID列表')
    
    # 时间戳
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))
    
    def to_dict(self):
        return {
            'id': self.id,
            'orderId': self.order_id,
            'status': self.status,
            'progress': self.progress,
            'curNodeId': self.cur_node_id,
            'simTypeResultIds': self.sim_type_result_ids,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }

