from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.collector import collector
from loguru import logger

# Forced model registries for metadata synchronization mapping
from app.models.auth import Base, User, Tenant  

# These will be initialized lazily to avoid top-level python import racing conditions
_async_engine = None
_async_session_factory = None

def get_database_url() -> str:
    """Runtime reference generator from the Pydantic memory box"""
    url = collector.get("DATABASE_URL")
    if not url:
        logger.critical("❌ DATABASE_URL lookup failed in ObjectCollector matrix! Routing mismatch.")
        raise RuntimeError("Database credentials not pre-warmed by configuration manager.")
    return url


def get_async_engine():
    """
    Lazy Initializer for SQLAlchemy Async Engine.
    Ensures engine creation happens AFTER Pydantic has populated the ObjectCollector.
    """
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            get_database_url(),
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )
    return _async_engine


def get_session_factory():
    """Lazy Initializer for Async Sessionmaker."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_async_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=AsyncSession
        )
    return _async_session_factory


async def get_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields dynamic isolated transactional session boundaries per request.
    Handles automatic cleanup and rollbacks natively.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"❌ Relational Rollback executed due to transaction error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()