# 数据库迁移脚本 - 基于配置文件

"""
创建工况相关表和调整现有表结构
基于 config/ 目录下的配置文件
"""

from app import db
from datetime import datetime

def upgrade():
    """执行数据库升级"""
    
    # 1. 创建模型层级表
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS model_levels (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(50) NOT NULL COMMENT '层级名称',
            code VARCHAR(20) UNIQUE COMMENT '层级编码',
            sort INT DEFAULT 100,
            valid TINYINT DEFAULT 1,
            created_at INT,
            updated_at INT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模型层级表';
    """)
    
    # 插入初始数据
    db.session.execute("""
        INSERT INTO model_levels (id, name, code, sort) VALUES
        (1, '整机', 'FULL', 1),
        (2, '单件', 'PART', 2)
        ON DUPLICATE KEY UPDATE name=VALUES(name);
    """)
    
    # 2. 创建折叠态类型表
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS fold_types (
            id INT PRIMARY KEY,
            name VARCHAR(50) NOT NULL COMMENT '折叠态名称',
            code VARCHAR(20) UNIQUE COMMENT '折叠态编码',
            sort INT DEFAULT 100,
            valid TINYINT DEFAULT 1,
            created_at INT,
            updated_at INT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='折叠态类型表';
    """)
    
    # 插入初始数据
    db.session.execute("""
        INSERT INTO fold_types (id, name, code, sort) VALUES
        (0, '展开态', 'UNFOLD', 1),
        (1, '折叠态', 'FOLD', 2)
        ON DUPLICATE KEY UPDATE name=VALUES(name);
    """)
    
    # 3. 创建求解器资源表
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS solver_resources (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL COMMENT '资源名称',
            code VARCHAR(50) UNIQUE COMMENT '资源编码',
            cpu_cores INT COMMENT 'CPU核心数',
            memory_gb INT COMMENT '内存大小GB',
            disk_gb INT COMMENT '磁盘大小GB',
            valid TINYINT DEFAULT 1,
            sort INT DEFAULT 100,
            remark TEXT,
            created_at INT,
            updated_at INT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='求解器资源表';
    """)
    
    # 插入初始数据
    db.session.execute("""
        INSERT INTO solver_resources (id, name, code, sort) VALUES
        (1, '标准节点', 'STANDARD', 1),
        (2, '大内存节点', 'LARGE_MEM', 2)
        ON DUPLICATE KEY UPDATE name=VALUES(name);
    """)
    
    # 4. 创建关注器件表
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS care_devices (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL COMMENT '器件名称',
            code VARCHAR(50) UNIQUE COMMENT '器件编码',
            category VARCHAR(50) COMMENT '器件分类',
            valid TINYINT DEFAULT 1,
            sort INT DEFAULT 100,
            remark TEXT,
            created_at INT,
            updated_at INT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='关注器件表';
    """)
    
    # 5. 创建项目-仿真类型关联配置表
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS project_sim_type_configs (
            id INT PRIMARY KEY AUTO_INCREMENT,
            project_id INT NOT NULL COMMENT '项目ID',
            target_fold_type TINYINT NOT NULL COMMENT '目标折叠态: 0=展开态, 1=折叠态',
            sim_type_id INT NOT NULL COMMENT '仿真类型ID',
            opt_param_group_id INT COMMENT '优化参数组ID',
            resp_group_id INT COMMENT '响应参数组ID',
            solver_group_id INT COMMENT '求解器组ID',
            is_default TINYINT DEFAULT 0 COMMENT '是否默认配置',
            created_at INT,
            updated_at INT,
            UNIQUE KEY uk_project_fold_sim (project_id, target_fold_type, sim_type_id),
            INDEX idx_project (project_id),
            INDEX idx_sim_type (sim_type_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目仿真类型关联配置表';
    """)
    
    # 6. 创建工况表
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS conditions (
            id INT PRIMARY KEY AUTO_INCREMENT,
            order_id INT NOT NULL COMMENT '订单ID',
            condition_type INT NOT NULL COMMENT '工况类型',
            condition_name VARCHAR(100) COMMENT '工况名称',
            model_level_id INT COMMENT '模型层级: 1=整机, 2=单件',
            target_fold_type TINYINT COMMENT '目标折叠态: 0=展开态, 1=折叠态',
            sim_type_id INT COMMENT '仿真类型ID',
            care_device_ids JSON COMMENT '关注器件ID列表',
            sort INT DEFAULT 100,
            created_at INT,
            updated_at INT,
            INDEX idx_order (order_id),
            INDEX idx_sim_type (sim_type_id),
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工况表';
    """)
    
    # 7. 创建工况优化参数配置表
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS condition_opt_params (
            id INT PRIMARY KEY AUTO_INCREMENT,
            condition_id INT NOT NULL COMMENT '工况ID',
            alg_type TINYINT NOT NULL COMMENT '算法类型: 1=贝叶斯, 2=DOE遍历, 5=DOE文件导入',
            domain JSON COMMENT '参数域配置',
            doe_param_csv_path VARCHAR(500) COMMENT 'DOE参数CSV路径',
            doe_param_json_path VARCHAR(500) COMMENT 'DOE参数JSON路径',
            doe_param_header JSON COMMENT 'DOE参数表头',
            doe_param_data JSON COMMENT 'DOE参数数据',
            batch_size JSON COMMENT '批次大小配置',
            max_iter INT DEFAULT 1 COMMENT '最大迭代次数',
            created_at INT,
            updated_at INT,
            INDEX idx_condition (condition_id),
            FOREIGN KEY (condition_id) REFERENCES conditions(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工况优化参数配置表';
    """)
    
    # 8. 创建工况响应参数配置表
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS condition_resp_params (
            id INT PRIMARY KEY AUTO_INCREMENT,
            condition_id INT NOT NULL COMMENT '工况ID',
            set_name VARCHAR(50) COMMENT '集合名称',
            output_type VARCHAR(50) COMMENT '输出类型: RF3, LEP2等',
            component VARCHAR(50) COMMENT '组件: 35=other抓取默认值, 18=特殊输出',
            description VARCHAR(255) COMMENT '描述',
            lower_limit DECIMAL(10,4) COMMENT '下限',
            upper_limit DECIMAL(10,4) COMMENT '上限',
            weight DECIMAL(10,4) DEFAULT 1.0 COMMENT '权重',
            multiple DECIMAL(10,4) DEFAULT 1.0 COMMENT '数量级',
            target_value DECIMAL(10,4) COMMENT '目标值',
            target_type VARCHAR(20) COMMENT '目标类型: min, max, target, userdefined',
            sort INT DEFAULT 100,
            created_at INT,
            updated_at INT,
            INDEX idx_condition (condition_id),
            FOREIGN KEY (condition_id) REFERENCES conditions(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工况响应参数配置表';
    """)
    
    # 9. 创建工况求解器配置表
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS condition_solver_configs (
            id INT PRIMARY KEY AUTO_INCREMENT,
            condition_id INT NOT NULL COMMENT '工况ID',
            solver_id INT NOT NULL COMMENT '求解器ID',
            cpu_cores INT DEFAULT 16 COMMENT 'CPU核心数: -1=使用全部核数',
            cpu_type TINYINT DEFAULT 1 COMMENT 'CPU类型: 1=并行, 0=不并行',
            dobule TINYINT DEFAULT 1 COMMENT '双精度: 1=开启, 0=关闭',
            apply_global TINYINT DEFAULT 1 COMMENT '应用全局设置: 1=应用, 0=不应用',
            use_global_config TINYINT DEFAULT 1 COMMENT '使用全局参数: 1=使用, 0=不使用',
            resource_id INT COMMENT '计算资源池ID',
            other_params JSON COMMENT '其他求解器参数',
            created_at INT,
            updated_at INT,
            INDEX idx_condition (condition_id),
            INDEX idx_solver (solver_id),
            FOREIGN KEY (condition_id) REFERENCES conditions(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工况求解器配置表';
    """)
    
    # 10. 调整 orders 表结构
    db.session.execute("""
        ALTER TABLE orders 
        ADD COLUMN IF NOT EXISTS origin_file_type TINYINT COMMENT '原始文件类型: 1=file_path, 2=task_id, 3=upload',
        ADD COLUMN IF NOT EXISTS origin_file_info JSON COMMENT '原始文件信息',
        ADD COLUMN IF NOT EXISTS fold_type TINYINT COMMENT '折叠态: 0=展开态, 1=折叠态',
        ADD COLUMN IF NOT EXISTS invole_users JSON COMMENT '涉及用户ID列表',
        ADD COLUMN IF NOT EXISTS issue_title VARCHAR(255) COMMENT '提单标题';
    """)
    
    # 11. 调整 param_defs 表结构
    db.session.execute("""
        ALTER TABLE param_defs 
        ADD COLUMN IF NOT EXISTS param_unit VARCHAR(20) COMMENT '参数单位',
        ADD COLUMN IF NOT EXISTS param_default_min DECIMAL(10,4) COMMENT '参数默认最小值',
        ADD COLUMN IF NOT EXISTS param_default_max DECIMAL(10,4) COMMENT '参数默认最大值',
        ADD COLUMN IF NOT EXISTS param_default_init DECIMAL(10,4) COMMENT '参数默认初始值';
    """)
    
    # 12. 调整 output_defs 表结构
    db.session.execute("""
        ALTER TABLE output_defs 
        ADD COLUMN IF NOT EXISTS component VARCHAR(50) COMMENT '组件',
        ADD COLUMN IF NOT EXISTS target_type VARCHAR(20) COMMENT '目标类型: min, max, target, userdefined',
        ADD COLUMN IF NOT EXISTS set_name VARCHAR(50) COMMENT '输出集合名称';
    """)
    
    db.session.commit()
    print("✅ 数据库迁移完成")


def downgrade():
    """回滚数据库更改"""
    
    # 删除新增的表（按依赖关系逆序删除）
    db.session.execute("DROP TABLE IF EXISTS condition_solver_configs")
    db.session.execute("DROP TABLE IF EXISTS condition_resp_params")
    db.session.execute("DROP TABLE IF EXISTS condition_opt_params")
    db.session.execute("DROP TABLE IF EXISTS conditions")
    db.session.execute("DROP TABLE IF EXISTS project_sim_type_configs")
    db.session.execute("DROP TABLE IF EXISTS care_devices")
    db.session.execute("DROP TABLE IF EXISTS solver_resources")
    db.session.execute("DROP TABLE IF EXISTS fold_types")
    db.session.execute("DROP TABLE IF EXISTS model_levels")
    
    # 删除 orders 表新增的列
    db.session.execute("""
        ALTER TABLE orders 
        DROP COLUMN IF EXISTS origin_file_type,
        DROP COLUMN IF EXISTS origin_file_info,
        DROP COLUMN IF EXISTS fold_type,
        DROP COLUMN IF EXISTS invole_users,
        DROP COLUMN IF EXISTS issue_title;
    """)
    
    # 删除 param_defs 表新增的列
    db.session.execute("""
        ALTER TABLE param_defs 
        DROP COLUMN IF EXISTS param_unit,
        DROP COLUMN IF EXISTS param_default_min,
        DROP COLUMN IF EXISTS param_default_max,
        DROP COLUMN IF EXISTS param_default_init;
    """)
    
    # 删除 output_defs 表新增的列
    db.session.execute("""
        ALTER TABLE output_defs 
        DROP COLUMN IF EXISTS component,
        DROP COLUMN IF EXISTS target_type,
        DROP COLUMN IF EXISTS set_name;
    """)
    
    db.session.commit()
    print("✅ 数据库回滚完成")


if __name__ == '__main__':
    print("开始执行数据库迁移...")
    upgrade()

