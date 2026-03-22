"""
订单模块 - 数据校验层
职责：使用Pydantic定义请求/响应数据结构
字段使用snake_case，由全局中间件自动转换camelCase
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class OrderCreate(BaseModel):
    """创建订单请求"""
    project_id: int = Field(..., description="项目ID")
    model_level_id: Optional[int] = Field(None, description="模型层级ID")
    origin_file: Dict[str, Any] = Field(..., description="原始文件信息")
    origin_fold_type_id: Optional[int] = Field(None, description="原始折叠类型ID")
    fold_type_ids: Optional[List[int]] = Field(default_factory=list, description="折叠类型ID列表")
    participant_ids: Optional[List[str]] = Field(default_factory=list, description="参与者域账号列表")
    remark: Optional[str] = Field(None, description="备注")
    sim_type_ids: Optional[List[int]] = Field(default_factory=list, description="仿真类型ID列表")
    opt_param: Optional[Dict[str, Any]] = Field(default_factory=dict, description="可选参数")
    input_json: Optional[Dict[str, Any]] = Field(default_factory=dict, description="输入JSON")
    condition_summary: Optional[Dict[str, List[str]]] = Field(None, description="工况摘要")
    opt_issue_id: Optional[int] = Field(None, description="自动优化申请单ID")
    workflow_id: Optional[int] = Field(None, description="工作流ID")
    submit_check: Optional[Dict[str, Any]] = Field(None, description="提交检查信息")
    client_meta: Optional[Dict[str, Any]] = Field(None, description="客户端元数据")


class OrderUpdate(BaseModel):
    """更新订单请求"""
    remark: Optional[str] = Field(None, description="备注")
    participant_uids: Optional[List[int]] = Field(None, description="参与者用户ID列表")
    participant_ids: Optional[List[str]] = Field(None, description="参与者域账号列表")
    opt_param: Optional[Dict[str, Any]] = Field(None, description="可选参数")
    input_json: Optional[Dict[str, Any]] = Field(None, description="输入JSON")
    sim_type_ids: Optional[List[int]] = Field(None, description="仿真类型ID列表")
    fold_type_ids: Optional[List[int]] = Field(None, description="姿态ID列表")
    origin_fold_type_id: Optional[int] = Field(None, description="原始姿态ID")
    model_level_id: Optional[int] = Field(None, description="模型层级ID")
    condition_summary: Optional[Dict[str, List[str]]] = Field(None, description="工况摘要")
    workflow_id: Optional[int] = Field(None, description="工作流ID")
    submit_check: Optional[Dict[str, Any]] = Field(None, description="提交检查信息")
    client_meta: Optional[Dict[str, Any]] = Field(None, description="客户端元数据")
    opt_issue_id: Optional[int] = Field(None, description="自动优化申请单ID")


class VerifyFileRequest(BaseModel):
    """文件验证请求"""
    path: str = Field(..., description="文件路径或文件ID")
    type: int = Field(1, description="验证类型: 1=路径验证, 2=文件ID验证")


class OrderQuery(BaseModel):
    """订单查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    status: Optional[int] = Field(None, description="订单状态")
    project_id: Optional[int] = Field(None, description="项目ID")
    sim_type_id: Optional[int] = Field(None, description="仿真类型ID")
    order_no: Optional[str] = Field(None, description="订单编号(模糊搜索)")
    created_by: Optional[str] = Field(None, description="创建人域账号")
    start_date: Optional[int] = Field(None, description="开始日期时间戳")
    end_date: Optional[int] = Field(None, description="结束日期时间戳")
