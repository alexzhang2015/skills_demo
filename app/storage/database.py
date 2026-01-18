"""
数据库连接管理

支持 SQLite 和 PostgreSQL
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# 数据库 URL（默认使用 SQLite）
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./data/skills_demo.db"
)

# 创建引擎
if DATABASE_URL.startswith("sqlite"):
    # SQLite 特殊配置
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=os.environ.get("SQL_DEBUG", "").lower() == "true"
    )

    # 启用 SQLite 外键约束
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL 或其他数据库
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        echo=os.environ.get("SQL_DEBUG", "").lower() == "true"
    )

# 创建 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def init_db():
    """
    初始化数据库

    创建所有表结构
    """
    # 确保数据目录存在
    if DATABASE_URL.startswith("sqlite"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = db_path[2:]
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    # 导入所有模型以确保它们被注册
    from . import models  # noqa

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    print(f"Database initialized: {DATABASE_URL}")


def get_session() -> Generator[Session, None, None]:
    """
    获取数据库会话（依赖注入用）

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_session)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    会话上下文管理器

    Usage:
        with session_scope() as session:
            session.add(item)
            session.commit()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def drop_all_tables():
    """删除所有表（仅用于测试）"""
    Base.metadata.drop_all(bind=engine)


def reset_database():
    """重置数据库（删除并重建所有表）"""
    drop_all_tables()
    init_db()
