"""
数据库迁移脚本 - 创建配置关联关系表
执行此脚本将创建新的配置组合表和关联关系表
"""
import time
from app import create_app, db
from app.models import (
    ParamGroup,
    ConditionOutputGroup,
    ProjectSimTypeRel,
    SimTypeParamGroupRel,
    SimTypeCondOutGroupRel,
    SimTypeSolverRel,
    ParamGroupParamRel,
    CondOutGroupConditionRel,
    CondOutGroupOutputRel,
    # 基础表
    Project,
    SimType,
    ParamDef,
    ConditionDef,
    OutputDef,
    Solver
)


def migrate_config_relations():
    """创建配置关联关系表并填充示例数据"""
    app = create_app()
    
    with app.app_context():
        print("开始创建配置关联关系表...")
        
        # 创建所有表
        db.create_all()
        print("✓ 表结构创建完成")
        
        # 清除现有数据（如果有）
        print("\n清除现有关联数据...")
        db.session.query(CondOutGroupOutputRel).delete()
        db.session.query(CondOutGroupConditionRel).delete()
        db.session.query(ParamGroupParamRel).delete()
        db.session.query(SimTypeSolverRel).delete()
        db.session.query(SimTypeCondOutGroupRel).delete()
        db.session.query(SimTypeParamGroupRel).delete()
        db.session.query(ProjectSimTypeRel).delete()
        db.session.query(ConditionOutputGroup).delete()
        db.session.query(ParamGroup).delete()
        db.session.commit()
        print("✓ 清除完成")
        
        now = int(time.time())
        
        # ============ 创建参数组合 ============
        print("\n创建参数组合...")
        param_groups = [
            ParamGroup(
                id=1,
                name='基础参数组',
                description='包含最基本的必填参数',
                valid=1,
                sort=10,
                created_at=now
            ),
            ParamGroup(
                id=2,
                name='高级参数组',
                description='包含更多高级参数配置',
                valid=1,
                sort=20,
                created_at=now
            ),
            ParamGroup(
                id=3,
                name='轻量化参数组',
                description='针对轻量化设计的参数配置',
                valid=1,
                sort=30,
                created_at=now
            ),
        ]
        for pg in param_groups:
            db.session.add(pg)
        db.session.flush()
        print(f"✓ 创建了 {len(param_groups)} 个参数组合")
        
        # ============ 创建工况输出组合 ============
        print("\n创建工况输出组合...")
        cond_out_groups = [
            ConditionOutputGroup(
                id=1,
                name='标准工况组',
                description='标准的工况和输出配置',
                valid=1,
                sort=10,
                created_at=now
            ),
            ConditionOutputGroup(
                id=2,
                name='完整工况组',
                description='包含所有工况和输出的完整配置',
                valid=1,
                sort=20,
                created_at=now
            ),
            ConditionOutputGroup(
                id=3,
                name='快速验证组',
                description='用于快速验证的精简配置',
                valid=1,
                sort=30,
                created_at=now
            ),
        ]
        for cog in cond_out_groups:
            db.session.add(cog)
        db.session.flush()
        print(f"✓ 创建了 {len(cond_out_groups)} 个工况输出组合")
        
        # ============ 参数组合-参数关联 ============
        print("\n创建参数组合-参数关联...")
        # 基础参数组：包含厚度、密度、弹性模量、泊松比
        param_group_param_rels = [
            # 基础参数组
            ParamGroupParamRel(param_group_id=1, param_def_id=1, default_value='2.5', sort=10, created_at=now),
            ParamGroupParamRel(param_group_id=1, param_def_id=2, default_value='2700', sort=20, created_at=now),
            ParamGroupParamRel(param_group_id=1, param_def_id=3, default_value='70', sort=30, created_at=now),
            ParamGroupParamRel(param_group_id=1, param_def_id=4, default_value='0.33', sort=40, created_at=now),
            # 高级参数组：包含更多参数
            ParamGroupParamRel(param_group_id=2, param_def_id=1, default_value='3.0', sort=10, created_at=now),
            ParamGroupParamRel(param_group_id=2, param_def_id=2, default_value='2700', sort=20, created_at=now),
            ParamGroupParamRel(param_group_id=2, param_def_id=3, default_value='70', sort=30, created_at=now),
            ParamGroupParamRel(param_group_id=2, param_def_id=4, default_value='0.33', sort=40, created_at=now),
            ParamGroupParamRel(param_group_id=2, param_def_id=5, default_value='AL6061', sort=50, created_at=now),
            # 轻量化参数组
            ParamGroupParamRel(param_group_id=3, param_def_id=1, default_value='1.5', sort=10, created_at=now),
            ParamGroupParamRel(param_group_id=3, param_def_id=2, default_value='2700', sort=20, created_at=now),
            ParamGroupParamRel(param_group_id=3, param_def_id=3, default_value='70', sort=30, created_at=now),
            ParamGroupParamRel(param_group_id=3, param_def_id=4, default_value='0.33', sort=40, created_at=now),
        ]
        for rel in param_group_param_rels:
            db.session.add(rel)
        db.session.flush()
        print(f"✓ 创建了 {len(param_group_param_rels)} 个参数关联")
        
        # ============ 工况输出组合-工况关联 ============
        print("\n创建工况输出组合-工况关联...")
        cond_rels = [
            # 标准工况组：弯曲、扭转
            CondOutGroupConditionRel(
                cond_out_group_id=1, condition_def_id=1,
                config_data={'load': 1000, 'direction': 'Z'},
                sort=10, created_at=now
            ),
            CondOutGroupConditionRel(
                cond_out_group_id=1, condition_def_id=2,
                config_data={'torque': 500, 'axis': 'Y'},
                sort=20, created_at=now
            ),
            # 完整工况组：所有工况
            CondOutGroupConditionRel(
                cond_out_group_id=2, condition_def_id=1,
                config_data={'load': 1000, 'direction': 'Z'},
                sort=10, created_at=now
            ),
            CondOutGroupConditionRel(
                cond_out_group_id=2, condition_def_id=2,
                config_data={'torque': 500, 'axis': 'Y'},
                sort=20, created_at=now
            ),
            CondOutGroupConditionRel(
                cond_out_group_id=2, condition_def_id=3,
                config_data={'deceleration': 1.5},
                sort=30, created_at=now
            ),
            CondOutGroupConditionRel(
                cond_out_group_id=2, condition_def_id=4,
                config_data={'lateral_g': 1.2},
                sort=40, created_at=now
            ),
            # 快速验证组：仅弯曲工况
            CondOutGroupConditionRel(
                cond_out_group_id=3, condition_def_id=1,
                config_data={'load': 500, 'direction': 'Z'},
                sort=10, created_at=now
            ),
        ]
        for rel in cond_rels:
            db.session.add(rel)
        db.session.flush()
        print(f"✓ 创建了 {len(cond_rels)} 个工况关联")

        # ============ 工况输出组合-输出关联 ============
        print("\n创建工况输出组合-输出关联...")
        output_rels = [
            # 标准工况组：最大变形、最大应力、安全系数
            CondOutGroupOutputRel(cond_out_group_id=1, output_def_id=1, sort=10, created_at=now),
            CondOutGroupOutputRel(cond_out_group_id=1, output_def_id=2, sort=20, created_at=now),
            CondOutGroupOutputRel(cond_out_group_id=1, output_def_id=3, sort=30, created_at=now),
            # 完整工况组：所有输出
            CondOutGroupOutputRel(cond_out_group_id=2, output_def_id=1, sort=10, created_at=now),
            CondOutGroupOutputRel(cond_out_group_id=2, output_def_id=2, sort=20, created_at=now),
            CondOutGroupOutputRel(cond_out_group_id=2, output_def_id=3, sort=30, created_at=now),
            CondOutGroupOutputRel(cond_out_group_id=2, output_def_id=4, sort=40, created_at=now),
            CondOutGroupOutputRel(cond_out_group_id=2, output_def_id=5, sort=50, created_at=now),
            CondOutGroupOutputRel(cond_out_group_id=2, output_def_id=6, sort=60, created_at=now),
            # 快速验证组：最大变形、最大应力
            CondOutGroupOutputRel(cond_out_group_id=3, output_def_id=1, sort=10, created_at=now),
            CondOutGroupOutputRel(cond_out_group_id=3, output_def_id=2, sort=20, created_at=now),
        ]
        for rel in output_rels:
            db.session.add(rel)
        db.session.flush()
        print(f"✓ 创建了 {len(output_rels)} 个输出关联")

        # ============ 项目-仿真类型关联 ============
        print("\n创建项目-仿真类型关联...")
        project_sim_type_rels = [
            # 项目1关联仿真类型1和2，默认为类型1
            ProjectSimTypeRel(project_id=1, sim_type_id=1, is_default=1, sort=10, created_at=now),
            ProjectSimTypeRel(project_id=1, sim_type_id=2, is_default=0, sort=20, created_at=now),
            # 项目2关联仿真类型2和3，默认为类型2
            ProjectSimTypeRel(project_id=2, sim_type_id=2, is_default=1, sort=10, created_at=now),
            ProjectSimTypeRel(project_id=2, sim_type_id=3, is_default=0, sort=20, created_at=now),
        ]
        for rel in project_sim_type_rels:
            db.session.add(rel)
        db.session.flush()
        print(f"✓ 创建了 {len(project_sim_type_rels)} 个项目-仿真类型关联")

        # ============ 仿真类型-参数组合关联 ============
        print("\n创建仿真类型-参数组合关联...")
        sim_type_param_group_rels = [
            # 仿真类型1关联参数组1和2，默认为组1
            SimTypeParamGroupRel(sim_type_id=1, param_group_id=1, is_default=1, sort=10, created_at=now),
            SimTypeParamGroupRel(sim_type_id=1, param_group_id=2, is_default=0, sort=20, created_at=now),
            # 仿真类型2关联参数组2和3，默认为组2
            SimTypeParamGroupRel(sim_type_id=2, param_group_id=2, is_default=1, sort=10, created_at=now),
            SimTypeParamGroupRel(sim_type_id=2, param_group_id=3, is_default=0, sort=20, created_at=now),
        ]
        for rel in sim_type_param_group_rels:
            db.session.add(rel)
        db.session.flush()
        print(f"✓ 创建了 {len(sim_type_param_group_rels)} 个仿真类型-参数组合关联")

        # ============ 仿真类型-工况输出组合关联 ============
        print("\n创建仿真类型-工况输出组合关联...")
        sim_type_cond_out_group_rels = [
            # 仿真类型1关联工况输出组1和2，默认为组1
            SimTypeCondOutGroupRel(sim_type_id=1, cond_out_group_id=1, is_default=1, sort=10, created_at=now),
            SimTypeCondOutGroupRel(sim_type_id=1, cond_out_group_id=2, is_default=0, sort=20, created_at=now),
            # 仿真类型2关联工况输出组2和3，默认为组2
            SimTypeCondOutGroupRel(sim_type_id=2, cond_out_group_id=2, is_default=1, sort=10, created_at=now),
            SimTypeCondOutGroupRel(sim_type_id=2, cond_out_group_id=3, is_default=0, sort=20, created_at=now),
        ]
        for rel in sim_type_cond_out_group_rels:
            db.session.add(rel)
        db.session.flush()
        print(f"✓ 创建了 {len(sim_type_cond_out_group_rels)} 个仿真类型-工况输出组合关联")

        # ============ 仿真类型-求解器关联 ============
        print("\n创建仿真类型-求解器关联...")
        sim_type_solver_rels = [
            # 仿真类型1关联求解器1和2，默认为求解器1
            SimTypeSolverRel(sim_type_id=1, solver_id=1, is_default=1, sort=10, created_at=now),
            SimTypeSolverRel(sim_type_id=1, solver_id=2, is_default=0, sort=20, created_at=now),
            # 仿真类型2关联求解器2和3，默认为求解器2
            SimTypeSolverRel(sim_type_id=2, solver_id=2, is_default=1, sort=10, created_at=now),
            SimTypeSolverRel(sim_type_id=2, solver_id=3, is_default=0, sort=20, created_at=now),
        ]
        for rel in sim_type_solver_rels:
            db.session.add(rel)
        db.session.flush()
        print(f"✓ 创建了 {len(sim_type_solver_rels)} 个仿真类型-求解器关联")

        # 提交所有更改
        db.session.commit()

        print("\n" + "="*60)
        print("✓ 配置关联关系表创建完成！")
        print("="*60)
        print("\n数据统计：")
        print(f"  - 参数组合: {len(param_groups)} 个")
        print(f"  - 工况输出组合: {len(cond_out_groups)} 个")
        print(f"  - 参数组合-参数关联: {len(param_group_param_rels)} 个")
        print(f"  - 工况输出组合-工况关联: {len(cond_rels)} 个")
        print(f"  - 工况输出组合-输出关联: {len(output_rels)} 个")
        print(f"  - 项目-仿真类型关联: {len(project_sim_type_rels)} 个")
        print(f"  - 仿真类型-参数组合关联: {len(sim_type_param_group_rels)} 个")
        print(f"  - 仿真类型-工况输出组合关联: {len(sim_type_cond_out_group_rels)} 个")
        print(f"  - 仿真类型-求解器关联: {len(sim_type_solver_rels)} 个")


if __name__ == '__main__':
    migrate_config_relations()

