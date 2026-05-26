import os

# 数据库配置
DATABASE_URL = "sqlite:///./mun_os.db"

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "mun-os-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8小时

# 默认管理员
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
