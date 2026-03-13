"""
修复MySQL菜单数据
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from sqlalchemy import text
import time

def fix_menus():
    app = create_app()
    with app.app_context():
        timestamp = int(time.time())

        # 需要添加的菜单 (id, parent_id, name, path, icon, sort)
        menus = [
            # 姿态类型
            (46, 4, '姿态类型', '/configuration/fold-types', 'Layers', 6),

            # 组合配置
            (50, 4, '组合配置', '#', 'Package', 10),
            (51, 50, '参数配置', '/configuration/param-groups', 'Settings', 1),
            (52, 50, '输出配置', '/configuration/output-groups', 'FileOutput', 2),

            # 关联配置
            (60, 4, '关联配置', '#', 'Link', 20),

            # 系统配置
            (70, 4, '系统配置', '/configuration/system', 'Settings', 30),

            # 权限配置
            (80, 4, '权限配置', '#', 'Shield', 40),
        ]

        print("开始修复菜单数据...")

        for menu in menus:
            exists = db.session.execute(
                text('SELECT COUNT(*) FROM menus WHERE id = :id'),
                {'id': menu[0]}
            ).scalar()

            if exists == 0:
                db.session.execute(text('''
                    INSERT INTO menus (id, parent_id, name, path, icon, sort, valid, created_at, updated_at)
                    VALUES (:id, :parent_id, :name, :path, :icon, :sort, 1, :ts, :ts)
                '''), {
                    'id': menu[0],
                    'parent_id': menu[1],
                    'name': menu[2],
                    'path': menu[3],
                    'icon': menu[4],
                    'sort': menu[5],
                    'ts': timestamp
                })
                print(f"  添加: {menu[2]}")
            else:
                print(f"  已存在: {menu[2]}")

        db.session.commit()
        print("\n菜单修复完成！")

if __name__ == '__main__':
    fix_menus()
