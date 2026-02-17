"""Database utility functions."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import engine, Base

logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables. Use for development only; prefer Alembic migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully.")


async def drop_tables():
    """Drop all database tables. Use with caution."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Database tables dropped.")


async def health_check(db: AsyncSession) -> bool:
    """Check database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
