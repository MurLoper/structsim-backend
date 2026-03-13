import os
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

    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None) or None
    REDIS_KEY_PREFIX = os.getenv('REDIS_KEY_PREFIX', 'structsim:')
    REDIS_DEFAULT_TTL = int(os.getenv('REDIS_DEFAULT_TTL', 3600))

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

