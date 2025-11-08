"""
Database connection pool management for Skills Engine.
"""
import logging
import asyncpg
from typing import Optional
import os

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """
    Get or create database connection pool.
    
    Returns:
        AsyncPG connection pool
    """
    global _pool
    
    if _pool is None:
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/swe_agent"
        )
        
        # Parse database URL
        # Format: postgresql://user:pass@host:port/dbname
        # or: postgresql+asyncpg://user:pass@host:port/dbname
        if "+asyncpg" in database_url:
            database_url = database_url.replace("+asyncpg", "")
        
        try:
            _pool = await asyncpg.create_pool(
                database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    return _pool


async def close_db_pool():
    """Close database connection pool"""
    global _pool
    
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")

