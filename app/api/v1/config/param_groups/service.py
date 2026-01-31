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
                param_data['param_name'] = param_def.name
                param_data['param_key'] = param_def.key
                param_data['unit'] = param_def.unit
                param_data['val_type'] = param_def.val_type
            params.append(param_data)
        
        result = group.to_dict()
        result['params'] = params
        return result
    
    def create_group(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建参数组合"""
        # 同名校验
        name = data.get('name', '').strip()
        if not name:
            raise BusinessError("组合名称不能为空")
        existing = self.repo.find_by_name(name)
        if existing:
            raise BusinessError(f"参数组合名称「{name}」已存在")

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

        # 同名校验（排除自身）
        name = data.get('name', '').strip()
        if name:
            existing = self.repo.find_by_name(name, exclude_id=group_id)
            if existing:
                raise BusinessError(f"参数组合名称「{name}」已存在")

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
                param_data['param_name'] = param_def.name
                param_data['param_key'] = param_def.key
                param_data['unit'] = param_def.unit
                param_data['val_type'] = param_def.val_type
            params.append(param_data)
        
        return params
    
    def add_param_to_group(self, group_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """添加参数到组合"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")

        param_def_id = data['param_def_id']
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
            'default_value': data.get('default_value'),
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
            raise BusinessError(f"添加参数到组合失败: {str(e)}")

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

    def clear_group_params(self, group_id: int) -> Dict[str, Any]:
        """清空组合的所有参数"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")

        try:
            param_rels = self.rel_repo.find_by_group_id(group_id)
            count = len(param_rels)
            for rel in param_rels:
                self.rel_repo.delete(rel)
            db.session.commit()
            return {'clearedCount': count}
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"清空参数失败: {str(e)}")

    def batch_add_params(self, group_id: int, params: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量添加参数到组合"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")

        added = []
        skipped = []
        errors = []

        try:
            for idx, param in enumerate(params):
                param_def_id = param.get('param_def_id')
                if not param_def_id:
                    errors.append({'index': idx, 'reason': '缺少param_def_id'})
                    continue

                param_def = self.rel_repo.find_param_def_by_id(param_def_id)
                if not param_def:
                    errors.append({'index': idx, 'paramDefId': param_def_id, 'reason': '参数定义不存在'})
                    continue

                existing = self.rel_repo.find_by_group_and_param(group_id, param_def_id)
                if existing:
                    skipped.append({'paramDefId': param_def_id, 'paramKey': param_def.key, 'reason': '已存在'})
                    continue

                rel_data = {
                    'param_group_id': group_id,
                    'param_def_id': param_def_id,
                    'default_value': param.get('default_value'),
                    'sort': param.get('sort', 100 + idx),
                    'created_at': int(time.time())
                }
                rel = self.rel_repo.create(rel_data)
                added.append({'paramDefId': param_def_id, 'paramKey': param_def.key})

            db.session.commit()
            return {
                'addedCount': len(added),
                'skippedCount': len(skipped),
                'errorCount': len(errors),
                'added': added,
                'skipped': skipped,
                'errors': errors
            }
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"批量添加参数失败: {str(e)}")

    def batch_remove_params(self, group_id: int, param_def_ids: List[int]) -> Dict[str, Any]:
        """批量移除参数"""
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")

        removed = []
        not_found = []

        try:
            for param_def_id in param_def_ids:
                rel = self.rel_repo.find_by_group_and_param(group_id, param_def_id)
                if rel:
                    self.rel_repo.delete(rel)
                    removed.append(param_def_id)
                else:
                    not_found.append(param_def_id)

            db.session.commit()
            return {
                'removedCount': len(removed),
                'notFoundCount': len(not_found),
                'removed': removed,
                'notFound': not_found
            }
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"批量移除参数失败: {str(e)}")

    def replace_group_params(self, group_id: int, params: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        清空并重新配置组合参数（一键重配）
        先清空所有参数，再批量添加新参数
        """
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")

        try:
            # 1. 清空现有参数
            old_rels = self.rel_repo.find_by_group_id(group_id)
            cleared_count = len(old_rels)
            for rel in old_rels:
                self.rel_repo.delete(rel)

            # 2. 添加新参数
            added = []
            errors = []
            for idx, param in enumerate(params):
                param_def_id = param.get('param_def_id')
                if not param_def_id:
                    errors.append({'index': idx, 'reason': '缺少param_def_id'})
                    continue

                param_def = self.rel_repo.find_param_def_by_id(param_def_id)
                if not param_def:
                    errors.append({'index': idx, 'paramDefId': param_def_id, 'reason': '参数定义不存在'})
                    continue

                rel_data = {
                    'param_group_id': group_id,
                    'param_def_id': param_def_id,
                    'default_value': param.get('default_value'),
                    'sort': param.get('sort', 100 + idx),
                    'created_at': int(time.time())
                }
                rel = self.rel_repo.create(rel_data)
                added.append({'paramDefId': param_def_id, 'paramKey': param_def.key})

            db.session.commit()
            return {
                'clearedCount': cleared_count,
                'addedCount': len(added),
                'errorCount': len(errors),
                'added': added,
                'errors': errors
            }
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"重配参数失败: {str(e)}")

    def search_params(self, keyword: str, group_id: Optional[int] = None) -> Dict[str, Any]:
        """
        搜索参数定义
        返回匹配的参数列表，并标记是否已在指定组合中
        """
        param_defs = self.rel_repo.search_param_defs(keyword)

        # 获取组合中已有的参数ID
        existing_ids = set()
        if group_id:
            rels = self.rel_repo.find_by_group_id(group_id)
            existing_ids = {rel.param_def_id for rel in rels}

        results = []
        for p in param_defs:
            results.append({
                'paramDefId': p.id,
                'paramKey': p.key,
                'paramName': p.name,
                'unit': p.unit,
                'valType': p.val_type,
                'inGroup': p.id in existing_ids
            })

        return {
            'params': results,
            'total': len(results),
            'keyword': keyword
        }

    def check_param_exists(self, key: str = None, name: str = None) -> Dict[str, Any]:
        """
        检查参数是否存在
        返回存在状态和匹配的参数信息
        """
        result = {'exists': False, 'param': None}

        if key:
            param_def = self.rel_repo.find_param_def_by_key(key)
            if param_def:
                result['exists'] = True
                result['matchBy'] = 'key'
                result['param'] = {
                    'paramDefId': param_def.id,
                    'paramKey': param_def.key,
                    'paramName': param_def.name,
                    'unit': param_def.unit,
                    'valType': param_def.val_type
                }
                return result

        if name:
            param_def = self.rel_repo.find_param_def_by_name(name)
            if param_def:
                result['exists'] = True
                result['matchBy'] = 'name'
                result['param'] = {
                    'paramDefId': param_def.id,
                    'paramKey': param_def.key,
                    'paramName': param_def.name,
                    'unit': param_def.unit,
                    'valType': param_def.val_type
                }

        return result

    def create_and_add_param(
        self,
        group_id: int,
        param_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        快速创建参数定义并添加到组合
        如果key已存在则直接添加，不存在则先创建再添加
        """
        group = self.repo.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"参数组合 {group_id} 不存在")

        key = param_data.get('key', '').strip()
        if not key:
            raise BusinessError("参数key不能为空")

        try:
            # 检查key是否已存在
            param_def = self.rel_repo.find_param_def_by_key(key)
            created = False

            if not param_def:
                # 创建新参数定义
                now = int(time.time())
                new_param = {
                    'key': key,
                    'name': param_data.get('name') or key,
                    'unit': param_data.get('unit'),
                    'val_type': param_data.get('val_type', 1),
                    'min_val': param_data.get('min_val'),
                    'max_val': param_data.get('max_val'),
                    'precision': param_data.get('precision', 3),
                    'default_val': param_data.get('default_val'),
                    'required': param_data.get('required', 0),
                    'valid': 1,
                    'sort': param_data.get('sort', 100),
                    'created_at': now,
                    'updated_at': now
                }
                param_def = self.rel_repo.create_param_def(new_param)
                created = True

            # 检查是否已在组合中
            existing = self.rel_repo.find_by_group_and_param(group_id, param_def.id)
            if existing:
                db.session.commit()
                return {
                    'created': created,
                    'added': False,
                    'reason': '参数已在组合中',
                    'param': {
                        'paramDefId': param_def.id,
                        'paramKey': param_def.key,
                        'paramName': param_def.name
                    }
                }

            # 添加到组合
            rel_data = {
                'param_group_id': group_id,
                'param_def_id': param_def.id,
                'default_value': param_data.get('default_value'),
                'sort': param_data.get('rel_sort', 100),
                'created_at': int(time.time())
            }
            self.rel_repo.create(rel_data)
            db.session.commit()

            return {
                'created': created,
                'added': True,
                'param': {
                    'paramDefId': param_def.id,
                    'paramKey': param_def.key,
                    'paramName': param_def.name,
                    'unit': param_def.unit,
                    'valType': param_def.val_type
                }
            }
        except Exception as e:
            db.session.rollback()
            raise BusinessError(f"创建并添加参数失败: {str(e)}")

