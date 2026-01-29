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
    origin_file: Dict[str, Any] = Field(..., description="原始文件信息")
    fold_type_id: Optional[int] = Field(None, description="折叠类型ID")
    participant_uids: Optional[List[int]] = Field(default_factory=list, description="参与者用户ID列表")
    remark: Optional[str] = Field(None, description="备注")
    sim_type_ids: Optional[List[int]] = Field(default_factory=list, description="仿真类型ID列表")
    opt_param: Optional[Dict[str, Any]] = Field(default_factory=dict, description="可选参数")
    workflow_id: Optional[int] = Field(None, description="工作流ID")
    submit_check: Optional[Dict[str, Any]] = Field(None, description="提交检查信息")
    client_meta: Optional[Dict[str, Any]] = Field(None, description="客户端元数据")


class OrderUpdate(BaseModel):
    """更新订单请求"""
    remark: Optional[str] = Field(None, description="备注")
    participant_uids: Optional[List[int]] = Field(None, description="参与者用户ID列表")
    opt_param: Optional[Dict[str, Any]] = Field(None, description="可选参数")


class OrderQuery(BaseModel):
    """订单查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    status: Optional[int] = Field(None, description="订单状态")
    project_id: Optional[int] = Field(None, description="项目ID")
