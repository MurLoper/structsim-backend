from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Import routes after blueprint creation to avoid circular imports
from app.api import projects, results

# 注意: auth、orders、config模块已迁移到 v1/，通过v1蓝图注册

