"""更新配置管理菜单结构"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models.auth import Menu

def update_menus():
    """更新菜单数据"""
    app = create_app()
    with app.app_context():
        # 更新配置管理父菜单路径
        menu4 = db.session.get(Menu, 4)
        if menu4:
            menu4.path = '/config'

        # 更新配置子菜单
        updates = [
            (41, 'Basic Config', 'nav.config.basic', 'Cube', '/config/basic', 'pages/configuration/BasicConfig'),
            (42, 'Groups Config', 'nav.config.groups', 'Folder', '/config/groups', 'pages/configuration/GroupsConfig'),
            (43, 'Relations Config', 'nav.config.relations', 'Link', '/config/relations', 'pages/configuration/RelationsConfig'),
            (44, 'System Config', 'nav.config.system', 'Server', '/config/system', 'pages/configuration/SystemConfig'),
            (45, 'Permissions', 'nav.config.permissions', 'Shield', '/config/permissions', 'pages/configuration/PermissionsConfig'),
        ]

        for menu_id, name, title_i18n_key, icon, path, component in updates:
            menu = db.session.get(Menu, menu_id)
            if menu:
                menu.name = name
                menu.title_i18n_key = title_i18n_key
                menu.icon = icon
                menu.path = path
                menu.component = component
                print(f"  ✓ 更新菜单 {menu_id}: {name}")

        # 更新新建仿真路径
        menu3 = db.session.get(Menu, 3)
        if menu3:
            menu3.path = '/create'
            print(f"  ✓ 更新菜单 3: path -> /create")

        db.session.commit()
        print("\n✅ 菜单更新完成!")

if __name__ == '__main__':
    update_menus()
