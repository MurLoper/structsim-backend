#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态配置数据库迁移脚本
添加 icon 字段并更新状态配置数据
"""
import sys
import io
import os
import json
from pathlib import Path

# 解决 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models.config import StatusDef
from sqlalchemy import text


def load_status_config():
    """加载状态配置数据"""
    config_file = project_root / 'database' / 'init-data' / 'base_config.json'
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('status_defs', [])


def migrate_add_icon_column():
    """添加 icon 列到 status_defs 表"""
    print("正在添加 icon 列...")
    try:
        # 检查列是否已存在
        result = db.session.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_name='status_defs' AND column_name='icon'"
        ))
        exists = result.scalar() > 0
        
        if not exists:
            db.session.execute(text(
                "ALTER TABLE status_defs ADD COLUMN icon VARCHAR(100) COMMENT '图标样式'"
            ))
            db.session.commit()
            print("✓ icon 列添加成功")
        else:
            print("✓ icon 列已存在，跳过")
    except Exception as e:
        db.session.rollback()
        print(f"✗ 添加 icon 列失败: {e}")
        raise


def normalize_timestamp(ts) -> int:
    """标准化时间戳为秒级（处理毫秒级时间戳）"""
    if ts is None or ts == 0:
        from datetime import datetime
        return int(datetime.now().timestamp())
    ts = int(ts)
    if ts > 10**12:
        return ts // 1000
    return ts


def migrate_update_status_data():
    """更新状态配置数据"""
    print("\n正在更新状态配置数据...")

    status_configs = load_status_config()

    try:
        # 使用原生 SQL 删除现有数据
        db.session.execute(text('DELETE FROM status_defs'))
        db.session.commit()

        # 插入新数据
        for config in status_configs:
            status = StatusDef(
                id=config['status_id'],
                name=config['status_name'],
                code=config['status_code'],
                type=config.get('status_type', 'PROCESS'),
                color=config.get('color_tag', '#808080'),
                icon=config.get('icon', ''),
                valid=1,
                sort=config['status_id'],
                created_at=normalize_timestamp(config.get('created_at', 0)),
                updated_at=normalize_timestamp(config.get('updated_at', 0))
            )
            db.session.add(status)

        db.session.commit()
        print(f"✓ 成功更新 {len(status_configs)} 条状态配置")

        # 显示更新后的数据
        print("\n更新后的状态配置:")
        statuses = StatusDef.query.order_by(StatusDef.id).all()
        for status in statuses:
            print(f"  [{status.id}] {status.name} ({status.code}) - {status.icon} - {status.color}")

    except Exception as e:
        db.session.rollback()
        print(f"✗ 更新状态配置失败: {e}")
        raise


def main():
    """主函数"""
    print("=" * 60)
    print("状态配置数据库迁移")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 步骤1: 添加 icon 列
            migrate_add_icon_column()
            
            # 步骤2: 更新状态配置数据
            migrate_update_status_data()
            
            print("\n" + "=" * 60)
            print("✓ 迁移完成!")
            print("=" * 60)
            
        except Exception as e:
            print("\n" + "=" * 60)
            print(f"✗ 迁移失败: {e}")
            print("=" * 60)
            sys.exit(1)


if __name__ == '__main__':
    main()

