"""
Database connection management with connection pooling.
Supports both sync and async operations.
"""
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker
from core.config import get_settings

settings = get_settings()

# Sync engine
sync_engine = create_engine(
    settings.database.connection_string,
    pool_size=settings.database.pool_size,
    pool_pre_ping=True,
    echo=settings.debug
)

SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

# Async engine
async_engine = create_async_engine(
    settings.database.async_connection_string,
    pool_size=settings.database.pool_size,
    pool_pre_ping=True,
    echo=settings.debug
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get synchronous database session."""
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise