import os
import secrets
import sys

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mun_os.db")

# JWT 配置
# 生产环境必须显式设置 SECRET_KEY；开发/本地若未设置则生成一次性随机密钥并告警
_env_secret = os.getenv("SECRET_KEY", "").strip()
_is_production = os.getenv("ENV", os.getenv("ENVIRONMENT", "")).lower() in ("prod", "production")

if _env_secret:
    SECRET_KEY = _env_secret
elif _is_production:
    print(
        "FATAL: 生产环境必须设置 SECRET_KEY 环境变量（建议 secrets.token_urlsafe(32)）。",
        file=sys.stderr,
    )
    sys.exit(1)
else:
    SECRET_KEY = secrets.token_urlsafe(32)
    print(
        "WARNING: 未设置 SECRET_KEY，已生成临时随机密钥（重启后旧 token 失效）。"
        "生产部署请设置 SECRET_KEY 环境变量。",
        file=sys.stderr,
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8小时

# 默认管理员（仅首次启动创建）。生产必须通过环境变量覆盖，禁止使用文档中的弱口令。
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "")

# 上传限制
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))  # 20MB
ALLOWED_UPLOAD_EXTENSIONS = {".docx"}

# 委员会图标上传：独立白名单，不放宽文档上传的限制
# 不含 svg —— SVG 可内嵌脚本，作为静态资源直出会有 XSS 风险
MAX_LOGO_BYTES = int(os.getenv("MAX_LOGO_BYTES", str(2 * 1024 * 1024)))  # 2MB
ALLOWED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# CORS：逗号分隔的精确来源；空则开发环境放宽为 localhost
_raw_origins = os.getenv("CORS_ORIGINS", "").strip()
if _raw_origins:
    CORS_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]
elif _is_production:
    CORS_ORIGINS = []
else:
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

# 登录限流（内存态）
LOGIN_RATE_LIMIT_PER_MINUTE = int(os.getenv("LOGIN_RATE_LIMIT_PER_MINUTE", "5"))
LOGIN_LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "300"))
