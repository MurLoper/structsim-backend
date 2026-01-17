"""
通用枚举定义
"""
from enum import Enum, IntEnum


class ValidStatus(IntEnum):
    """有效状态"""
    INVALID = 0
    VALID = 1


class AlgorithmType(str, Enum):
    """优化算法类型"""
    DOE = "doe"
    BAYESIAN = "bayesian"


class OrderStatus(IntEnum):
    """订单状态"""
    DRAFT = 0
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    CANCELLED = 5


class SimCategory(str, Enum):
    """仿真分类"""
    STRUCTURE = "STRUCTURE"
    THERMAL = "THERMAL"
    DYNAMIC = "DYNAMIC"
    ACOUSTIC = "ACOUSTIC"


class ParamValueType(IntEnum):
    """参数值类型"""
    FLOAT = 1
    INT = 2
    STRING = 3
    ENUM = 4
    BOOL = 5


class CpuType(IntEnum):
    """CPU类型"""
    SINGLE = -1  # 单节点
    PARALLEL = 1  # 并行

