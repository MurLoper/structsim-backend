"""
工况输出组合管理 - Service层
职责：业务逻辑、事务管理
禁止：HTTP相关逻辑
"""
import time
from typing import Optional, List, Dict, Any
from app.extensions import db
from app.common.errors import NotFoundError, BusinessError
from .repository import (
    CondOutGroupRepository,
    CondOutGroupConditionRelRepository,
    CondOutGroupOutputRelRepository
)


class CondOutGroupService:
    """工况输出组合服务"""
    
    def __init__(self):
        self.repo = CondOutGroupRepository()
        self.cond_rel_repo = CondOutGroupConditionRelRepository()
        self.output_rel_repo = CondOutGroupOutputRelRepository()
    
    def get_all_groups(self, valid: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有工况输出组合"""
        groups = self.repo.find_all(valid)
        return [group.to_dict() for group in groups]
    
    def get_group_by_id(self, group_id: int) -> Dict[str, Any]:
        """获取工况输出组合详情"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"工况输出组合 {group_id} 不存在")
        return group.to_dict()
    
    def get_group_detail(self, group_id: int) -> Dict[str, Any]:
        """获取工况输出组合详情（包含工况和输出列表）"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"工况输出组合 {group_id} 不存在")
        
        # 获取组合包含的工况
        cond_rels = self.cond_rel_repo.find_by_group_id(group_id)
        conditions = []
        for rel in cond_rels:
            cond_def = self.cond_rel_repo.find_condition_def_by_id(rel.condition_def_id)
            cond_data = rel.to_dict()
            if cond_def:
                cond_data['conditionName'] = cond_def.name
                cond_data['conditionCode'] = cond_def.code
                cond_data['conditionSchema'] = cond_def.schema  # 改为 conditionSchema
            conditions.append(cond_data)
        
        # 获取组合包含的输出
        output_rels = self.output_rel_repo.find_by_group_id(group_id)
        outputs = []
        for rel in output_rels:
            output_def = self.output_rel_repo.find_output_def_by_id(rel.output_def_id)
            output_data = rel.to_dict()
            if output_def:
                output_data['outputName'] = output_def.name
                output_data['outputCode'] = output_def.code
                output_data['unit'] = output_def.unit
                output_data['valType'] = output_def.val_type
            outputs.append(output_data)
        
        result = group.to_dict()
        result['conditions'] = conditions
        result['outputs'] = outputs
        return result
    
    def create_group(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建工况输出组合"""
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
            raise BusinessError(f"创建工况输出组合失败: {str(e)}")
    
    def update_group(self, group_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新工况输出组合"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"工况输出组合 {group_id} 不存在")
        
        data['updated_at'] = int(time.time())
        
        try:
            updated_group = self.repo.update(group, data)
            db.session.commit()
            return updated_group.to_dict()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"更新工况输出组合失败: {str(e)}")
    
    def delete_group(self, group_id: int) -> None:
        """删除工况输出组合"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"工况输出组合 {group_id} 不存在")
        
        try:
            # 先删除所有工况关联
            cond_rels = self.cond_rel_repo.find_by_group_id(group_id)
            for rel in cond_rels:
                self.cond_rel_repo.delete(rel)
            
            # 再删除所有输出关联
            output_rels = self.output_rel_repo.find_by_group_id(group_id)
            for rel in output_rels:
                self.output_rel_repo.delete(rel)
            
            # 最后删除组合本身
            self.repo.delete(group)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"删除工况输出组合失败: {str(e)}")
    
    def get_group_conditions(self, group_id: int) -> List[Dict[str, Any]]:
        """获取组合包含的工况"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"工况输出组合 {group_id} 不存在")
        
        cond_rels = self.cond_rel_repo.find_by_group_id(group_id)
        conditions = []
        for rel in cond_rels:
            cond_def = self.cond_rel_repo.find_condition_def_by_id(rel.condition_def_id)
            cond_data = rel.to_dict()
            if cond_def:
                cond_data['conditionName'] = cond_def.name
                cond_data['conditionCode'] = cond_def.code
                cond_data['conditionSchema'] = cond_def.schema  # 改为 conditionSchema
            conditions.append(cond_data)
        
        return conditions

    def add_condition_to_group(self, group_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """添加工况到组合"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"工况输出组合 {group_id} 不存在")

        condition_def_id = data['conditionDefId']
        cond_def = self.cond_rel_repo.find_condition_def_by_id(condition_def_id)
        if not cond_def:
            raise NotFoundError(f"工况定义 {condition_def_id} 不存在")

        # 检查是否已存在
        existing = self.cond_rel_repo.find_by_group_and_condition(group_id, condition_def_id)
        if existing:
            raise BusinessError(f"工况 {condition_def_id} 已在组合中")

        rel_data = {
            'cond_out_group_id': group_id,
            'condition_def_id': condition_def_id,
            'config_data': data.get('configData'),
            'sort': data.get('sort', 100),
            'created_at': int(time.time())
        }

        try:
            rel = self.cond_rel_repo.create(rel_data)
            db.session.commit()

            result = rel.to_dict()
            result['conditionName'] = cond_def.name
            result['conditionCode'] = cond_def.code
            result['conditionSchema'] = cond_def.schema  # 改为 conditionSchema
            return result
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"添加工况到组合失败: {str(e)}")

    def remove_condition_from_group(self, group_id: int, condition_def_id: int) -> None:
        """从组合移除工况"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"工况输出组合 {group_id} 不存在")

        rel = self.cond_rel_repo.find_by_group_and_condition(group_id, condition_def_id)
        if not rel:
            raise NotFoundError(f"工况 {condition_def_id} 不在组合中")

        try:
            self.cond_rel_repo.delete(rel)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"从组合移除工况失败: {str(e)}")

    def get_group_outputs(self, group_id: int) -> List[Dict[str, Any]]:
        """获取组合包含的输出"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"工况输出组合 {group_id} 不存在")

        output_rels = self.output_rel_repo.find_by_group_id(group_id)
        outputs = []
        for rel in output_rels:
            output_def = self.output_rel_repo.find_output_def_by_id(rel.output_def_id)
            output_data = rel.to_dict()
            if output_def:
                output_data['outputName'] = output_def.name
                output_data['outputCode'] = output_def.code
                output_data['unit'] = output_def.unit
                output_data['valType'] = output_def.val_type
            outputs.append(output_data)

        return outputs

    def add_output_to_group(self, group_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """添加输出到组合"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"工况输出组合 {group_id} 不存在")

        output_def_id = data['outputDefId']
        output_def = self.output_rel_repo.find_output_def_by_id(output_def_id)
        if not output_def:
            raise NotFoundError(f"输出定义 {output_def_id} 不存在")

        # 检查是否已存在
        existing = self.output_rel_repo.find_by_group_and_output(group_id, output_def_id)
        if existing:
            raise BusinessError(f"输出 {output_def_id} 已在组合中")

        rel_data = {
            'cond_out_group_id': group_id,
            'output_def_id': output_def_id,
            'sort': data.get('sort', 100),
            'created_at': int(time.time())
        }

        try:
            rel = self.output_rel_repo.create(rel_data)
            db.session.commit()

            result = rel.to_dict()
            result['outputName'] = output_def.name
            result['outputCode'] = output_def.code
            result['unit'] = output_def.unit
            result['valType'] = output_def.val_type
            return result
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"添加输出到组合失败: {str(e)}")

    def remove_output_from_group(self, group_id: int, output_def_id: int) -> None:
        """从组合移除输出"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"工况输出组合 {group_id} 不存在")

        rel = self.output_rel_repo.find_by_group_and_output(group_id, output_def_id)
        if not rel:
            raise NotFoundError(f"输出 {output_def_id} 不在组合中")

        try:
            self.output_rel_repo.delete(rel)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"从组合移除输出失败: {str(e)}")

