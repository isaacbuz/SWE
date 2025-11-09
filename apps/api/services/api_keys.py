"""
API Key Service

Business logic for API key management operations.
"""
import os
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import asyncpg
from fastapi import HTTPException, status

from apps.api.db import get_db_pool


class APIKeyService:
    """Service for API key operations"""

    async def _get_connection(self):
        """Get database connection from pool"""
        pool = await get_db_pool()
        return await pool.acquire()
    
    async def _release_connection(self, conn):
        """Release database connection back to pool"""
        pool = await get_db_pool()
        await pool.release(conn)

    async def get_api_key_by_prefix(self, key_prefix: str) -> Optional[Dict[str, Any]]:
        """Get API key by prefix"""
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, key_prefix, key_hash, name, 
                       is_active, expires_at, last_used_at, created_at
                FROM api_keys
                WHERE key_prefix = $1 AND is_active = true
                """,
                key_prefix
            )
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "user_id": row["user_id"],
                "key_prefix": row["key_prefix"],
                "key_hash": row["key_hash"],
                "name": row.get("name"),
                "is_active": row.get("is_active", True),
                "expires_at": row["expires_at"].isoformat() if row.get("expires_at") else None,
                "last_used_at": row["last_used_at"].isoformat() if row.get("last_used_at") else None,
                "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            }
        finally:
            await self._release_connection(conn)

    async def create_api_key(
        self,
        user_id: int,
        key_hash: str,
        key_prefix: str,
        name: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a new API key"""
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO api_keys (
                    user_id, key_prefix, key_hash, name, is_active,
                    expires_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, user_id, key_prefix, name, is_active, expires_at, created_at
                """,
                user_id, key_prefix, key_hash, name, True,
                expires_at, datetime.utcnow()
            )
            
            return {
                "id": row["id"],
                "user_id": row["user_id"],
                "key_prefix": row["key_prefix"],
                "name": row.get("name"),
                "is_active": row.get("is_active", True),
                "expires_at": row["expires_at"].isoformat() if row.get("expires_at") else None,
                "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            }
        finally:
            await self._release_connection(conn)

    async def list_api_keys(self, user_id: int) -> list:
        """List all API keys for a user"""
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT id, key_prefix, name, is_active, expires_at, 
                       last_used_at, created_at
                FROM api_keys
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id
            )
            
            return [
                {
                    "id": row["id"],
                    "key_prefix": row["key_prefix"],
                    "name": row.get("name"),
                    "is_active": row.get("is_active", True),
                    "expires_at": row["expires_at"].isoformat() if row.get("expires_at") else None,
                    "last_used_at": row["last_used_at"].isoformat() if row.get("last_used_at") else None,
                    "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                }
                for row in rows
            ]
        finally:
            await self._release_connection(conn)

    async def revoke_api_key(self, key_id: int, user_id: int) -> None:
        """Revoke an API key"""
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                UPDATE api_keys
                SET is_active = false, updated_at = $1
                WHERE id = $2 AND user_id = $3
                """,
                datetime.utcnow(), key_id, user_id
            )
            
            if result == "UPDATE 0":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"API key {key_id} not found"
                )
        finally:
            await self._release_connection(conn)

    async def update_last_used(self, key_id: int) -> None:
        """Update API key last used timestamp"""
        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                UPDATE api_keys
                SET last_used_at = $1
                WHERE id = $2
                """,
                datetime.utcnow(), key_id
            )
        finally:
            await self._release_connection(conn)


# Global service instance
api_key_service = APIKeyService()

