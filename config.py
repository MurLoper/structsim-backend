import os
import json
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # Database - 主数据库
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///structsim.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

    # Database - MySQL 5.6 低版本数据库（用于订单结果查询）
    SQLALCHEMY_BINDS = {
        'legacy_mysql': os.getenv(
            'LEGACY_MYSQL_URL',
            'mysql+pymysql://user:password@localhost:3306/legacy_db?charset=utf8mb4'
        )
    }
    SQLALCHEMY_BINDS_ENGINE_OPTIONS = {
        'legacy_mysql': {
            'pool_recycle': 300,
            'pool_pre_ping': True,
            'connect_args': {
                'charset': 'utf8mb4',
                'connect_timeout': 10,
            }
        }
    }

    # External MySQL 5.6 (只读聚合查询)
    EXTERNAL_MYSQL_HOST = os.getenv('EXTERNAL_MYSQL_HOST', '154.9.255.18')
    EXTERNAL_MYSQL_PORT = int(os.getenv('EXTERNAL_MYSQL_PORT', 3306))
    EXTERNAL_MYSQL_USER = os.getenv('EXTERNAL_MYSQL_USER', 'root')
    EXTERNAL_MYSQL_PASSWORD = os.getenv('EXTERNAL_MYSQL_PASSWORD', 'Ndgsyxn.7')
    EXTERNAL_MYSQL_CHARSET = os.getenv('EXTERNAL_MYSQL_CHARSET', 'utf8mb4')
    EXTERNAL_MYSQL_CONNECT_TIMEOUT = float(os.getenv('EXTERNAL_MYSQL_CONNECT_TIMEOUT', 10))
    EXTERNAL_MYSQL_READ_TIMEOUT = float(os.getenv('EXTERNAL_MYSQL_READ_TIMEOUT', 20))
    EXTERNAL_MYSQL_WRITE_TIMEOUT = float(os.getenv('EXTERNAL_MYSQL_WRITE_TIMEOUT', 20))
    EXTERNAL_MYSQL_SCHEMA_SIMLATION_PROJECT = os.getenv(
        'EXTERNAL_MYSQL_SCHEMA_SIMLATION_PROJECT', 'simlation_project'
    )
    EXTERNAL_MYSQL_SCHEMA_STRUCT_MODULE = os.getenv(
        'EXTERNAL_MYSQL_SCHEMA_STRUCT_MODULE', 'struct_module'
    )
    EXTERNAL_MYSQL_SCHEMA_UNION_OPT_KERNAL = os.getenv(
        'EXTERNAL_MYSQL_SCHEMA_UNION_OPT_KERNAL', 'union_opt_kernal'
    )
    EXTERNAL_MYSQL_SCHEMA_UNION_OPT_CONF = os.getenv(
        'EXTERNAL_MYSQL_SCHEMA_UNION_OPT_CONF', 'union_opt_conf'
    )
    EXTERNAL_MYSQL_SCHEMA_SQRS_HW = os.getenv('EXTERNAL_MYSQL_SCHEMA_SQRS_HW', 'sqrs_hw')

    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None) or None
    REDIS_KEY_PREFIX = os.getenv('REDIS_KEY_PREFIX', 'structsim:')
    REDIS_DEFAULT_TTL = int(os.getenv('REDIS_DEFAULT_TTL', 3600))

    # 登录/认证配置
    AUTH_ENABLE_SSO = os.getenv('AUTH_ENABLE_SSO', 'false').lower() == 'true'
    AUTH_SSO_LOGIN_URL = os.getenv('AUTH_SSO_LOGIN_URL', '')
    AUTH_SSO_REDIRECT_URI = os.getenv('AUTH_SSO_REDIRECT_URI', '')

    # 公司账号密码校验接口（后端代理校验，不落库存密码）
    AUTH_COMPANY_PASSWORD_VERIFY_URL = os.getenv('AUTH_COMPANY_PASSWORD_VERIFY_URL', '')
    AUTH_COMPANY_PASSWORD_VERIFY_METHOD = os.getenv('AUTH_COMPANY_PASSWORD_VERIFY_METHOD', 'POST').upper()
    AUTH_COMPANY_PASSWORD_VERIFY_TIMEOUT = float(os.getenv('AUTH_COMPANY_PASSWORD_VERIFY_TIMEOUT', 8.0))
    AUTH_USE_FAKE_COMPANY_VERIFY = os.getenv('AUTH_USE_FAKE_COMPANY_VERIFY', 'false').lower() == 'true'
    AUTH_GET_USER_INFO_URL = os.getenv('AUTH_GET_USER_INFO_URL', '')
    AUTH_GET_USER_INFO_METHOD = os.getenv('AUTH_GET_USER_INFO_METHOD', 'GET').upper()
    AUTH_GET_USER_INFO_TIMEOUT = float(os.getenv('AUTH_GET_USER_INFO_TIMEOUT', 8.0))
    AUTH_DEFAULT_ROLE_CODE = os.getenv('AUTH_DEFAULT_ROLE_CODE', 'GUEST')
    AUTH_GET_USER_RESOURCE_POOLS_URL = os.getenv('AUTH_GET_USER_RESOURCE_POOLS_URL', '')
    AUTH_GET_USER_RESOURCE_POOLS_METHOD = os.getenv('AUTH_GET_USER_RESOURCE_POOLS_METHOD', 'GET').upper()
    AUTH_GET_USER_RESOURCE_POOLS_TIMEOUT = float(os.getenv('AUTH_GET_USER_RESOURCE_POOLS_TIMEOUT', 8.0))
    AUTH_USE_FAKE_USER_RESOURCE_POOLS = (
        os.getenv('AUTH_USE_FAKE_USER_RESOURCE_POOLS', 'false').lower() == 'true'
    )
    AUTH_FAKE_USER_RESOURCE_POOLS_JSON = json.loads(
        os.getenv(
            'AUTH_FAKE_USER_RESOURCE_POOLS_JSON',
            (
                '{"source_list":['
                '{"id":19,"name":"OPTI"},'
                '{"id":23,"name":"HPC-CPU"},'
                '{"id":31,"name":"GPU-POOL"}'
                '],"default_source_id":19}'
            )
        )
    )

    # 通过 uid 获取公司用户信息接口（用于 SSO callback）
    AUTH_COMPANY_UID_INFO_URL = os.getenv('AUTH_COMPANY_UID_INFO_URL', '')
    AUTH_COMPANY_UID_EXPIRE_SECONDS = int(os.getenv('AUTH_COMPANY_UID_EXPIRE_SECONDS', 1800))
    AUTH_COMPANY_APP_ID = os.getenv('AUTH_COMPANY_APP_ID', '')
    AUTH_COMPANY_SECRET_CREDIT = os.getenv('AUTH_COMPANY_SECRET_CREDIT', '')
    AUTH_LOGIN_RSA_KEY_ID = os.getenv('AUTH_LOGIN_RSA_KEY_ID', 'default')
    AUTH_LOGIN_RSA_PRIVATE_KEY = os.getenv('AUTH_LOGIN_RSA_PRIVATE_KEY', '')
    AUTH_LOGIN_RSA_PUBLIC_KEY = os.getenv('AUTH_LOGIN_RSA_PUBLIC_KEY', '')
    AUTH_LOGIN_RSA_PRIVATE_KEY_PATH = os.getenv('AUTH_LOGIN_RSA_PRIVATE_KEY_PATH', '')
    AUTH_LOGIN_RSA_PUBLIC_KEY_PATH = os.getenv('AUTH_LOGIN_RSA_PUBLIC_KEY_PATH', '')
    AUTH_ALLOW_TEST_ACCOUNT_BYPASS = (
        os.getenv('AUTH_ALLOW_TEST_ACCOUNT_BYPASS', 'false').lower() == 'true'
    )
    AUTH_TEST_BYPASS_USERS = [
        item.strip().lower()
        for item in os.getenv('AUTH_TEST_BYPASS_USERS', '').split(',')
        if item.strip()
    ]

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001').split(',')

    # File Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './storage')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 4294967296))  # 4GB
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 5242880))  # 5MB


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
