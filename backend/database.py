from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import DATABASE_URL

# 连接池显式配置：默认 5+10 的容量在管理员页面并发拉取列表时会被打满，
# 超出部分要等 pool_timeout（默认 30s）才报错，表现为页面卡死。
# 这里适度放大容量，并把等待时间压到 10s 以便快速失败。
engine = create_engine(
    DATABASE_URL,
    # timeout 为 SQLite 的 busy timeout：并发写入时短暂等待而非立刻报
    # "database is locked"（默认仅 5 秒）
    connect_args={"check_same_thread": False, "timeout": 15},
    pool_size=10,
    max_overflow=20,
    pool_timeout=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
