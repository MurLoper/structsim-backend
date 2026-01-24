from flask import Blueprint

api_bp = Blueprint('api', __name__)

# 注意: 所有业务模块（auth、orders、config等）已迁移到 v1/，通过v1蓝图注册

