"""
Database connection management using asyncpg.
"""
import logging
from typing import Optional
import asyncpg
from asyncpg import Pool

from config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_db_pool: Optional[Pool] = None


async def get_db_pool() -> Pool:
    """
    Get or create database connection pool.
    
    Returns:
        asyncpg Pool instance
    """
    global _db_pool
    
    if _db_pool is None:
        # Parse database URL (postgresql+asyncpg://user:pass@host:port/db)
        db_url = str(settings.database_url).replace("postgresql+asyncpg://", "postgresql://")
        
        _db_pool = await asyncpg.create_pool(
            db_url,
            min_size=5,
            max_size=settings.database_pool_size,
            command_timeout=60,
        )
        logger.info("Database connection pool created")
    
    return _db_pool


async def close_db_pool():
    """Close database connection pool."""
    global _db_pool
    
    if _db_pool:
        await _db_pool.close()
        _db_pool = None
        logger.info("Database connection pool closed")

