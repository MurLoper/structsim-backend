"""
结果分析模块 - Pydantic Schemas
职责：请求/响应数据校验
字段使用snake_case，由全局中间件自动转换camelCase
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RoundsQueryParams(BaseModel):
    """轮次查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(100, ge=1, le=500, description="每页数量，最大500")
    status: Optional[int] = Field(None, description="状态筛选: 1=待处理,2=运行中,3=成功,4=失败")


class SimTypeResultResponse(BaseModel):
    """仿真类型结果响应"""
    id: int
    order_id: int
    sim_type_id: int
    sim_type_name: str
    status: int
    progress: int
    cur_node_id: Optional[int]
    stuck_node_id: Optional[int]
    stuck_module_id: Optional[int]
    best_exists: int
    best_rule_id: Optional[int]
    best_round_index: Optional[int]
    best_metrics: Optional[Dict[str, Any]]
    total_rounds: int
    completed_rounds: int
    failed_rounds: int
    created_at: int
    updated_at: int


class RoundResponse(BaseModel):
    """轮次响应"""
    id: int
    sim_type_result_id: int
    round_index: int
    status: int
    progress: int
    param_values: Optional[Dict[str, Any]]
    condition_config: Optional[Dict[str, Any]]
    output_results: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    error_msg: Optional[str]
    started_at: Optional[int]
    finished_at: Optional[int]
    created_at: int


class RoundsPaginatedResponse(BaseModel):
    """轮次分页响应"""
    items: List[RoundResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UpdateStatusRequest(BaseModel):
    """更新状态请求"""
    status: int = Field(..., ge=1, le=4, description="状态: 1=待处理,2=运行中,3=成功,4=失败")
    progress: Optional[int] = Field(None, ge=0, le=100, description="进度百分比")
    error_msg: Optional[str] = Field(None, description="错误信息")
