# app/db/postgres.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.collector import collector
from loguru import logger
from app.models.auth import Base, User, Tenant  

def get_database_url() -> str:
    """Runtime reference generator from the Pydantic memory box"""
    url = collector.get("DATABASE_URL")
    if not url:
        logger.critical("❌ DATABASE_URL lookup failed in ObjectCollector matrix! Routing mismatch.")
        raise RuntimeError("Database credentials not pre-warmed by configuration manager.")
    return url

# 🔌 Async engine creation tied to late runtime parsing 
async_engine = create_async_engine(
    get_database_url(),
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

# 🏭 Session Factory initialization bound to engine
async_session_factory = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields dynamic isolated transactional session boundaries per request.
    Handles automatic cleanup and rollbacks natively.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"❌ Relational Rollback executed due to transaction error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()