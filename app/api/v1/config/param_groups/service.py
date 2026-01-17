"""
参数组合管理 - Service层
职责：业务逻辑、事务管理
禁止：HTTP相关逻辑
"""
import time
from typing import Optional, List, Dict, Any
from app.extensions import db
from app.common.errors import NotFoundError, BusinessError
from .repository import ParamGroupRepository, ParamGroupParamRelRepository


class ParamGroupService:
    """参数组合服务"""
    
    def __init__(self):
        self.repo = ParamGroupRepository()
        self.rel_repo = ParamGroupParamRelRepository()
    
    def get_all_groups(self, valid: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有参数组合"""
        groups = self.repo.find_all(valid)
        return [group.to_dict() for group in groups]
    
    def get_group_by_id(self, group_id: int) -> Dict[str, Any]:
        """获取参数组合详情"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")
        return group.to_dict()
    
    def get_group_detail(self, group_id: int) -> Dict[str, Any]:
        """获取参数组合详情（包含参数列表）"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")
        
        # 获取组合包含的参数
        param_rels = self.rel_repo.find_by_group_id(group_id)
        params = []
        for rel in param_rels:
            param_def = self.rel_repo.find_param_def_by_id(rel.param_def_id)
            param_data = rel.to_dict()
            if param_def:
                param_data['paramName'] = param_def.name
                param_data['paramKey'] = param_def.key
                param_data['unit'] = param_def.unit
                param_data['valType'] = param_def.val_type
            params.append(param_data)
        
        result = group.to_dict()
        result['params'] = params
        return result
    
    def create_group(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建参数组合"""
        now = int(time.time())
        data['created_at'] = now
        data['updated_at'] = now
        data['valid'] = 1
        
        try:
            group = self.repo.create(data)
            db.session.commit()
            return group.to_dict()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"创建参数组合失败: {str(e)}")
    
    def update_group(self, group_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新参数组合"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")
        
        data['updated_at'] = int(time.time())
        
        try:
            updated_group = self.repo.update(group, data)
            db.session.commit()
            return updated_group.to_dict()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"更新参数组合失败: {str(e)}")
    
    def delete_group(self, group_id: int) -> None:
        """删除参数组合"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")
        
        try:
            # 先删除所有参数关联
            param_rels = self.rel_repo.find_by_group_id(group_id)
            for rel in param_rels:
                self.rel_repo.delete(rel)
            
            # 再删除组合本身
            self.repo.delete(group)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"删除参数组合失败: {str(e)}")
    
    def get_group_params(self, group_id: int) -> List[Dict[str, Any]]:
        """获取组合包含的参数"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")
        
        param_rels = self.rel_repo.find_by_group_id(group_id)
        params = []
        for rel in param_rels:
            param_def = self.rel_repo.find_param_def_by_id(rel.param_def_id)
            param_data = rel.to_dict()
            if param_def:
                param_data['paramName'] = param_def.name
                param_data['paramKey'] = param_def.key
                param_data['unit'] = param_def.unit
                param_data['valType'] = param_def.val_type
            params.append(param_data)
        
        return params
    
    def add_param_to_group(self, group_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """添加参数到组合"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")
        
        param_def_id = data['paramDefId']
        param_def = self.rel_repo.find_param_def_by_id(param_def_id)
        if not param_def:
            raise NotFoundError(f"参数定义 {param_def_id} 不存在")
        
        # 检查是否已存在
        existing = self.rel_repo.find_by_group_and_param(group_id, param_def_id)
        if existing:
            raise BusinessError(f"参数 {param_def_id} 已在组合中")
        
        rel_data = {
            'param_group_id': group_id,
            'param_def_id': param_def_id,
            'default_value': data.get('defaultValue'),
            'sort': data.get('sort', 100),
            'created_at': int(time.time())
        }
        
        try:
            rel = self.rel_repo.create(rel_data)
            db.session.commit()
            
            result = rel.to_dict()
            result['paramName'] = param_def.name
            result['paramKey'] = param_def.key
            result['unit'] = param_def.unit
            result['valType'] = param_def.val_type
            return result
        except Exception as e:
            db.session.rollback()
    def remove_param_from_group(self, group_id: int, param_def_id: int) -> None:
        """从组合移除参数"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")

        rel = self.rel_repo.find_by_group_and_param(group_id, param_def_id)
        if not rel:
            raise NotFoundError(f"参数 {param_def_id} 不在组合中")

        try:
            self.rel_repo.delete(rel)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"从组合移除参数失败: {str(e)}")

