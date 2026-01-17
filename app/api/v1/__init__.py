"""
API v1 模块
"""
from flask import Blueprint

v1_bp = Blueprint('v1', __name__, url_prefix='/v1')

# 注册子模块蓝图
from .config import config_bp, param_groups_bp, cond_out_groups_bp, config_relations_bp
from .auth import auth_bp
from .orders import orders_bp, init_config_bp

v1_bp.register_blueprint(config_bp)
v1_bp.register_blueprint(param_groups_bp)
v1_bp.register_blueprint(cond_out_groups_bp)
v1_bp.register_blueprint(config_relations_bp)
v1_bp.register_blueprint(auth_bp)
v1_bp.register_blueprint(orders_bp)
v1_bp.register_blueprint(init_config_bp)

