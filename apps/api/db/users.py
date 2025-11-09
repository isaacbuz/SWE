"""
Database service for Users operations.
"""
import logging
from typing import Optional
from uuid import UUID
import asyncpg
from asyncpg import Pool

logger = logging.getLogger(__name__)


class UsersService:
    """Database service for Users operations"""
    
    def __init__(self, pool: Pool):
        """Initialize users service"""
        self.pool = pool
    
    async def get_user_id_by_uuid(self, user_uuid: UUID) -> Optional[int]:
        """Get user integer ID from UUID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM users WHERE user_id = $1 AND is_active = true",
                user_uuid
            )
            return row["id"] if row else None
    
    async def get_user_by_uuid(self, user_uuid: UUID) -> Optional[dict]:
        """Get user by UUID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, username, email, display_name, role, is_active
                FROM users
                WHERE user_id = $1 AND is_active = true
                """,
                user_uuid
            )
            return dict(row) if row else None

