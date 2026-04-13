"""
一键全量同步 MySQL：源库导出 -> 目标库覆盖导入。

默认策略：
1) 导出时移除外键约束，避免跨环境导入冲突；
2) 导入前清空目标库全部表，确保结构和字段与源库完全一致；
3) 导入后校验关键表存在。
"""

from __future__ import annotations

import argparse
import os

try:
    from dotenv import load_dotenv as _load_dotenv
except Exception:  # pragma: no cover
    _load_dotenv = None

try:
    from .export_mysql import build_output_file, export_database, parse_csv
    from .import_mysql import import_database
    from .migrations.user_identity_upgrade import upgrade_identity_schema
    from .migrations.case_opti_upgrade import upgrade_case_opti_schema
    from .migrations.order_phase_upgrade import upgrade_order_phase_schema
except ImportError:
    from export_mysql import build_output_file, export_database, parse_csv  # pyright: ignore[reportImplicitRelativeImport]
    from import_mysql import import_database  # pyright: ignore[reportImplicitRelativeImport]
    from migrations.user_identity_upgrade import upgrade_identity_schema  # pyright: ignore[reportImplicitRelativeImport]
    from migrations.case_opti_upgrade import upgrade_case_opti_schema  # pyright: ignore[reportImplicitRelativeImport]
    from migrations.order_phase_upgrade import upgrade_order_phase_schema  # pyright: ignore[reportImplicitRelativeImport]



def load_env() -> None:
    if _load_dotenv is not None:
        _load_dotenv()


def main() -> int:
    load_env()
    parser = argparse.ArgumentParser(description='一键全量同步 MySQL（覆盖目标库）')
    parser.add_argument('--source-db-url', default=os.getenv('SOURCE_DATABASE_URL'), help='源数据库 URL')
    parser.add_argument('--target-db-url', default=os.getenv('TARGET_DATABASE_URL'), help='目标数据库 URL')
    parser.add_argument('--output-file', default=None, help='导出 SQL 文件路径，不传则自动按时间戳生成')
    parser.add_argument('--chunk-size', type=int, default=500, help='INSERT 批大小')
    parser.add_argument('--required-tables', default='upload_files,upload_chunks', help='关键表，逗号分隔')
    parser.add_argument('--keep-foreign-keys', action='store_true', help='导出时保留外键（默认不保留）')
    parser.add_argument('--apply-foreign-keys', action='store_true', help='导入后恢复外键（依赖 *_foreign_keys.sql）')
    parser.add_argument('--skip-identity-upgrade', action='store_true', help='跳过用户身份字段自动升级')

    args = parser.parse_args()

    if not args.source_db_url:
        print('错误: 未提供源数据库 URL（--source-db-url 或 SOURCE_DATABASE_URL）')
        return 1
    if not args.target_db_url:
        print('错误: 未提供目标数据库 URL（--target-db-url 或 TARGET_DATABASE_URL）')
        return 1

    required_tables = sorted(parse_csv(args.required_tables))
    output_file = build_output_file(args.output_file)

    print('=' * 60)
    print('步骤1/2: 导出源库')
    print('=' * 60)
    print(f'源库: {args.source_db_url}')
    print(f'导出文件: {output_file}')

    if not args.skip_identity_upgrade:
        print('预处理: 升级源库用户身份字段...')
        upgrade_identity_schema(args.source_db_url, verbose=True)
        print('预处理: 升级源库订单 case/condition 新链路...')
        upgrade_case_opti_schema(args.source_db_url, verbose=True)
        print('预处理: 升级源库 orders.phase_id 字段...')
        upgrade_order_phase_schema(args.source_db_url, verbose=True)

    exported = export_database(

        source_db_url=args.source_db_url,
        output_file=output_file,
        include_tables=set(),
        exclude_tables={'order_condition_opti'},
        chunk_size=max(1, args.chunk_size),
        strip_fk=not args.keep_foreign_keys,
        required_tables=required_tables,
    )

    fk_file = exported.with_name(f'{exported.stem}_foreign_keys.sql')
    fk_sql_file = str(fk_file) if args.apply_foreign_keys and fk_file.exists() else None

    print('\n' + '=' * 60)
    print('步骤2/2: 覆盖导入目标库')
    print('=' * 60)
    print(f'目标库: {args.target_db_url}')

    ok = import_database(
        sql_file=str(exported),
        db_url=args.target_db_url,
        stop_on_error=True,
        fk_sql_file=fk_sql_file,
        required_tables=required_tables,
        drop_all_first=True,
    )

    if ok and not args.skip_identity_upgrade:
        print('后处理: 升级目标库用户身份字段...')
        upgrade_identity_schema(args.target_db_url, verbose=True)
        print('后处理: 升级目标库订单 case/condition 新链路...')
        upgrade_case_opti_schema(args.target_db_url, verbose=True)
        print('后处理: 升级目标库 orders.phase_id 字段...')
        upgrade_order_phase_schema(args.target_db_url, verbose=True)

    if not ok:

        print('\n同步失败')
        return 2

    print('\n同步成功')
    if args.apply_foreign_keys:
        if fk_sql_file:
            print(f'已恢复外键: {fk_sql_file}')
        else:
            print('⚠️ 需要恢复外键但未找到 *_foreign_keys.sql，已跳过')
    else:
        print('当前未恢复外键（按默认无外键策略）')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
