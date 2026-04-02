"""
订单表模型 - 提单主表及相关
按照 requirement_and_design.md 规范设计
"""
from datetime import datetime
from app import db
from app.models.base import ToDictMixin


class Order(db.Model):
    """订单/申请单主表"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False, comment='订单编号')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, comment='项目ID')

    # 模型层级
    model_level_id = db.Column(db.Integer, comment='模型层级ID')

    # 源文件信息
    origin_file_type = db.Column(db.SmallInteger, default=1, comment='1=路径,2=文件ID,3=上传')
    origin_file_name = db.Column(db.String(255), comment='文件名')
    origin_file_path = db.Column(db.String(500), comment='文件路径')
    origin_file_id = db.Column(db.Integer, comment='文件ID')

    # 姿态
    origin_fold_type_id = db.Column(db.Integer, comment='原始姿态类型ID')
    fold_type_id = db.Column(db.Integer, db.ForeignKey('fold_types.id'), comment='姿态类型ID')
    fold_type_ids = db.Column(db.JSON, comment='姿态类型ID列表')

    # 参与人
    participant_uids = db.Column(db.JSON, comment='参与人用户ID列表')

    # 备注
    remark = db.Column(db.Text, comment='备注')

    # 选中的仿真类型列表
    sim_type_ids = db.Column(db.JSON, comment='选中的仿真类型ID列表')

    input_json = db.Column(db.JSON, comment='输入JSON完整配置')
    opt_issue_id = db.Column(db.Integer, index=True, comment='自动优化申请单ID')
    domain_account = db.Column(db.String(32), index=True, comment='提交用户域账号')
    base_dir = db.Column(db.String(500), comment='申请单工作目录')
    
    # 工作流
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'), comment='工作流ID')
    
    # 状态与进度
    status = db.Column(db.SmallInteger, default=0, comment='状态: 0=未开始/排队,1=运行中,2=完成,3=失败,4=草稿,5=取消')
    progress = db.Column(db.SmallInteger, default=0, comment='进度百分比 0-100')
    cur_node_id = db.Column(db.Integer, comment='当前流程节点ID')
    
    # 提交校验配置
    submit_check = db.Column(db.JSON, comment='提交校验配置')
    
    # 工况概览（冗余存储，供列表展示）
    condition_summary = db.Column(db.JSON, comment='工况概览 {姿态名: [仿真类型名,...]}')

    # 客户端元数据
    client_meta = db.Column(db.JSON, comment='客户端元数据 {lang, theme, ui_ver}')
    
    # 创建人（域账号）
    created_by = db.Column(db.String(32), index=True, comment='创建人域账号')
    
    # 时间戳
    created_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()),
                          onupdate=lambda: int(datetime.utcnow().timestamp()))
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'project_id': self.project_id,
            'model_level_id': self.model_level_id,
            'origin_file': {
                'type': self.origin_file_type,
                'name': self.origin_file_name,
                'path': self.origin_file_path,
                'file_id': self.origin_file_id
            },
            'origin_fold_type_id': self.origin_fold_type_id,
            'fold_type_id': self.fold_type_id,
            'fold_type_ids': self.fold_type_ids,
            'participant_uids': self.participant_uids,
            'remark': self.remark,
            'sim_type_ids': self.sim_type_ids,
            'input_json': self.input_json,
            'opt_issue_id': self.__dict__.get('opt_issue_id'),
            'domain_account': self.__dict__.get('domain_account'),
            'base_dir': self.__dict__.get('base_dir'),
            'workflow_id': self.workflow_id,
            'status': self.status,
            'progress': self.progress,
            'cur_node_id': self.cur_node_id,
            'submit_check': self.submit_check,
            'condition_summary': self.__dict__.get('condition_summary'),
            'client_meta': self.client_meta,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def to_list_dict(self):
        """列表展示用的精简字典"""
        return {
            'id': self.id,
            'order_no': self.order_no,
            'project_id': self.project_id,
            'remark': self.remark,
            'sim_type_ids': self.sim_type_ids,
            'fold_type_ids': self.fold_type_ids,
            'condition_summary': self.__dict__.get('condition_summary'),
            'opt_issue_id': self.__dict__.get('opt_issue_id'),
            'domain_account': self.__dict__.get('domain_account'),
            'base_dir': self.__dict__.get('base_dir'),
            'status': self.status,
            'progress': self.progress,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class OrderResult(db.Model, ToDictMixin):
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
