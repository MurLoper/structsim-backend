"""
参数合并服务
职责：处理基础参数与用户自定义参数的合并逻辑
策略：
  - 同名key：合并更新基础参数配置（用户值覆盖，其他属性可选更新）
  - 新参数：插入到基础参数配置中
"""
from typing import Dict, Any, List, Optional
from app.extensions import db
from app.models import ParamDef, ParamGroup, ParamGroupParamRel


class ParamMergeService:
    """参数合并服务"""

    # 参数来源常量
    SOURCE_BASE = "base"      # 基础配置
    SOURCE_CUSTOM = "custom"  # 用户自定义（新增）
    SOURCE_MERGED = "merged"  # 合并更新（同名key覆盖）

    def merge_params(
        self,
        base_params: List[Dict[str, Any]],
        custom_params: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        合并基础参数和用户自定义参数

        规则：
        1. 以 paramKey 为唯一标识
        2. 同名key：合并更新基础参数（用户值覆盖，保留基础参数元数据）
        3. 新参数：插入到参数列表中

        Args:
            base_params: 基础配置参数列表
            custom_params: 用户自定义参数列表

        Returns:
            合并后的参数列表
        """
        # 构建基础参数字典 {paramKey: param}
        merged = {}

        # 先添加基础参数
        for param in base_params:
            key = param.get('paramKey')
            if key:
                merged[key] = {
                    **param,
                    'source': self.SOURCE_BASE
                }

        # 处理用户自定义参数
        for param in custom_params:
            key = param.get('paramKey')
            if not key:
                continue

            if key in merged:
                # 同名key：合并更新基础参数配置
                base = merged[key]
                merged[key] = {
                    'paramDefId': base.get('paramDefId'),  # 保留基础参数关联ID
                    'paramKey': key,
                    'paramName': param.get('paramName') or base.get('paramName'),
                    'value': param.get('value'),  # 用户值覆盖
                    'defaultValue': base.get('defaultValue'),  # 保留默认值
                    'unit': param.get('unit') or base.get('unit'),
                    'valType': param.get('valType') or base.get('valType'),
                    'minVal': base.get('minVal'),
                    'maxVal': base.get('maxVal'),
                    'precision': base.get('precision'),
                    'required': base.get('required', 1),
                    'source': self.SOURCE_MERGED,  # 标记为合并更新
                }
            else:
                # 新参数：插入
                merged[key] = {
                    'paramDefId': None,  # 无基础参数关联
                    'paramKey': key,
                    'paramName': param.get('paramName') or key,
                    'value': param.get('value'),
                    'defaultValue': param.get('value'),
                    'unit': param.get('unit'),
                    'valType': param.get('valType') or self._infer_val_type(param.get('value')),
                    'required': param.get('required', 0),
                    'source': self.SOURCE_CUSTOM,  # 标记为新增
                }

        return list(merged.values())

    def parse_excel_params(self, excel_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        解析Excel模板中的参数数据

        Excel格式预期：
        | paramKey | paramName | value | unit |
        |----------|-----------|-------|------|
        | thickness| 厚度      | 2.5   | mm   |

        Args:
            excel_data: Excel解析后的行数据列表

        Returns:
            标准化的参数列表
        """
        params = []
        for row in excel_data:
            key = row.get('paramKey') or row.get('param_key') or row.get('key')
            if not key:
                continue

            params.append({
                'paramKey': key,
                'paramName': row.get('paramName') or row.get('param_name') or row.get('name') or key,
                'value': row.get('value'),
                'unit': row.get('unit'),
                'valType': self._infer_val_type(row.get('value'))
            })

        return params

    def validate_params(
        self,
        params: List[Dict[str, Any]],
        param_group_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        验证参数列表

        Args:
            params: 参数列表
            param_group_id: 参数组ID（可选，用于验证必填项）

        Returns:
            验证结果 {valid: bool, errors: [], warnings: []}
        """
        errors = []
        warnings = []

        # 获取必填参数
        required_keys = set()
        if param_group_id:
            rels = db.session.query(ParamGroupParamRel).filter_by(
                param_group_id=param_group_id
            ).all()
            for rel in rels:
                param_def = db.session.get(ParamDef, rel.param_def_id)
                if param_def and param_def.required == 1:
                    required_keys.add(param_def.key)

        # 检查参数
        provided_keys = set()
        for param in params:
            key = param.get('paramKey')
            if not key:
                errors.append({'type': 'missing_key', 'message': '参数缺少key'})
                continue

            provided_keys.add(key)

            # 检查值
            value = param.get('value')
            if value is None or value == '':
                if key in required_keys:
                    errors.append({
                        'type': 'required_missing',
                        'paramKey': key,
                        'message': f'必填参数 {key} 缺少值'
                    })

            # 检查是否覆盖了基础参数
            if param.get('source') == self.SOURCE_CUSTOM and param.get('overridden'):
                warnings.append({
                    'type': 'overridden',
                    'paramKey': key,
                    'message': f'参数 {key} 覆盖了基础配置'
                })

        # 检查必填参数是否都提供了
        missing_required = required_keys - provided_keys
        for key in missing_required:
            errors.append({
                'type': 'required_missing',
                'paramKey': key,
                'message': f'缺少必填参数 {key}'
            })

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def get_merge_report(
        self,
        base_params: List[Dict[str, Any]],
        custom_params: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        获取参数合并报告

        Args:
            base_params: 基础配置参数
            custom_params: 用户自定义参数

        Returns:
            合并报告，包含更新和新增的详细信息
        """
        base_keys = {p.get('paramKey') for p in base_params if p.get('paramKey')}
        custom_keys = {p.get('paramKey') for p in custom_params if p.get('paramKey')}

        # 同名key = 更新的参数
        updated_keys = base_keys & custom_keys
        # 新增参数
        new_keys = custom_keys - base_keys

        # 更新参数详情
        updated_params = []
        for key in updated_keys:
            base_param = next((p for p in base_params if p.get('paramKey') == key), {})
            custom_param = next((p for p in custom_params if p.get('paramKey') == key), {})
            updated_params.append({
                'paramKey': key,
                'paramName': base_param.get('paramName'),
                'oldValue': base_param.get('value') or base_param.get('defaultValue'),
                'newValue': custom_param.get('value'),
                'unit': custom_param.get('unit') or base_param.get('unit'),
            })

        # 新增参数详情
        new_params = []
        for key in new_keys:
            custom_param = next((p for p in custom_params if p.get('paramKey') == key), )
            new_params.append({
                'paramKey': key,
                'paramName': custom_param.get('paramName') or key,
                'value': custom_param.get('value'),
                'unit': custom_param.get('unit'),
            })

        return {
            'updatedCount': len(updated_keys),
            'newCount': len(new_keys),
            'updatedParams': updated_params,
            'newParams': new_params,
            'summary': f'更新了 {len(updated_keys)} 个参数，新增了 {len(new_keys)} 个参数'
        }

    def _infer_val_type(self, value: Any) -> int:
        """
        推断值类型

        Returns:
            1=number, 2=int, 3=string, 4=enum
        """
        if value is None:
            return 1  # 默认number

        if isinstance(value, int):
            return 2
        if isinstance(value, float):
            return 1
        if isinstance(value, str):
            try:
                float(value)
                if '.' in value:
                    return 1  # number
                return 2  # int
            except ValueError:
                return 3  # string

        return 3  # 默认string


# 单例
param_merge_service = ParamMergeService()
