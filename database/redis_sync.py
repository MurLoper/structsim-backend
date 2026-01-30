#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 数据同步脚本
将 MySQL 配置数据同步到 Redis 缓存

使用方法:
    python database/redis_sync.py sync          # 同步所有配置数据到 Redis
    python database/redis_sync.py clear         # 清理所有 Redis 缓存
    python database/redis_sync.py status        # 查看 Redis 缓存状态
    python database/redis_sync.py warmup        # 预热常用配置缓存
"""
import sys
import io
import argparse
from pathlib import Path

# 解决 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.common.redis_client import redis_client
from app.common.cache_service import CacheKeys, ConfigCache


def sync_config_data():
    """同步所有配置数据到 Redis"""
    from app.models.config import (
        Project, SimType, FoldType, ParamDef, OutputDef,
        ConditionDef, Solver, StatusDef, ParamTplSet, CondOutSet
    )
    from app.models.config_relations import FoldTypeSimTypeRel

    print("\n📦 同步配置数据到 Redis...")

    # 配置映射: (CacheKey, Model, 描述)
    config_maps = [
        (CacheKeys.PROJECTS, Project, "项目"),
        (CacheKeys.SIM_TYPES, SimType, "仿真类型"),
        (CacheKeys.FOLD_TYPES, FoldType, "姿态"),
        (CacheKeys.PARAM_DEFS, ParamDef, "参数定义"),
        (CacheKeys.OUTPUT_DEFS, OutputDef, "输出定义"),
        (CacheKeys.CONDITION_DEFS, ConditionDef, "工况定义"),
        (CacheKeys.SOLVERS, Solver, "求解器"),
        (CacheKeys.STATUS_DEFS, StatusDef, "状态定义"),
        (CacheKeys.PARAM_TPL_SETS, ParamTplSet, "参数模板集"),
        (CacheKeys.COND_OUT_SETS, CondOutSet, "工况输出集"),
    ]

    for cache_key, model, desc in config_maps:
        try:
            items = model.query.filter_by(valid=1).all()
            data = [item.to_dict() for item in items]
            ConfigCache.set(cache_key, data, ConfigCache.TTL_CONFIG)
            print(f"  ✓ {desc}: {len(data)} 条")
        except Exception as e:
            print(f"  ✗ {desc}: {e}")

    # 同步姿态-仿真类型关联
    try:
        rels = FoldTypeSimTypeRel.query.all()
        data = [r.to_dict() for r in rels]
        ConfigCache.set(CacheKeys.FOLD_TYPE_SIM_TYPE_RELS, data, ConfigCache.TTL_CONFIG)
        print(f"  ✓ 姿态-仿真类型关联: {len(data)} 条")
    except Exception as e:
        print(f"  ✗ 姿态-仿真类型关联: {e}")

    print("✅ 配置数据同步完成")


def sync_conditions():
    """同步工况配置到 Redis"""
    from app.models.config import ConditionConfig

    print("\n📦 同步工况配置到 Redis...")

    try:
        # 同步所有工况列表
        conditions = ConditionConfig.query.filter_by(valid=1).all()
        data = [c.to_dict() for c in conditions]
        ConfigCache.set(CacheKeys.CONDITIONS_ALL, data, ConfigCache.TTL_CONDITIONS)
        print(f"  ✓ 工况配置列表: {len(data)} 条")

        # 同步每个工况的单独缓存
        for cond in conditions:
            cond_data = cond.to_dict()
            # 单个工况缓存
            ConfigCache.set(
                CacheKeys.condition(cond.id),
                cond_data,
                ConfigCache.TTL_CONDITIONS
            )
            # 姿态+仿真类型组合缓存
            ConfigCache.set(
                CacheKeys.condition_by_fold_sim(cond.fold_type_id, cond.sim_type_id),
                cond_data,
                ConfigCache.TTL_CONDITIONS
            )
        print(f"  ✓ 工况单独缓存: {len(conditions)} 条")

    except Exception as e:
        print(f"  ✗ 工况配置: {e}")

    print("✅ 工况配置同步完成")


def clear_cache():
    """清理所有 Redis 缓存"""
    print("\n🗑️  清理 Redis 缓存...")

    try:
        client = redis_client.client
        prefix = redis_client._prefix

        # 获取所有匹配前缀的 key
        keys = client.keys(f"{prefix}*")
        if keys:
            client.delete(*keys)
            print(f"  ✓ 已删除 {len(keys)} 个缓存 key")
        else:
            print("  ✓ 没有需要清理的缓存")

        print("✅ 缓存清理完成")
    except Exception as e:
        print(f"  ✗ 清理失败: {e}")


def show_status():
    """显示 Redis 缓存状态"""
    print("\n📊 Redis 缓存状态:")

    try:
        client = redis_client.client
        prefix = redis_client._prefix

        # 获取 Redis 信息
        info = client.info()
        print(f"  Redis 版本: {info.get('redis_version', 'N/A')}")
        print(f"  已用内存: {info.get('used_memory_human', 'N/A')}")
        print(f"  连接客户端数: {info.get('connected_clients', 'N/A')}")

        # 统计缓存 key 数量
        keys = client.keys(f"{prefix}*")
        print(f"\n  缓存 Key 总数: {len(keys)}")

        # 按类型统计
        config_keys = [k for k in keys if 'config:' in k]
        condition_keys = [k for k in keys if 'condition' in k]
        print(f"  配置缓存: {len(config_keys)} 个")
        print(f"  工况缓存: {len(condition_keys)} 个")

    except Exception as e:
        print(f"  ✗ 获取状态失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Redis 数据同步工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'command',
        choices=['sync', 'clear', 'status', 'warmup'],
        help='要执行的命令'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='强制执行，不提示确认'
    )
    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        # 初始化 Redis
        redis_client.init_app(app)

        print("\n" + "=" * 50)
        print("🔄 Redis 数据同步工具")
        print("=" * 50)

        if args.command == 'sync':
            sync_config_data()
            sync_conditions()
        elif args.command == 'clear':
            if not args.force:
                confirm = input("\n⚠️  确定要清理所有缓存吗？(y/N): ")
                if confirm.lower() != 'y':
                    print("已取消")
                    return
            clear_cache()
        elif args.command == 'status':
            show_status()
        elif args.command == 'warmup':
            sync_config_data()
            sync_conditions()

        print("\n" + "=" * 50)
        print("✅ 操作完成！")
        print("=" * 50 + "\n")


if __name__ == '__main__':
    main()
