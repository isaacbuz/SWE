"""
User Service

Business logic for user management and authentication operations.
"""
import os
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import asyncpg
from fastapi import HTTPException, status

from apps.api.db import get_db_pool
from auth.models import CurrentUser, UserRole
from uuid import UUID


class UserService:
    """Service for user operations"""

    async def _get_connection(self):
        """Get database connection from pool"""
        pool = await get_db_pool()
        return await pool.acquire()
    
    async def _release_connection(self, conn):
        """Release database connection back to pool"""
        pool = await get_db_pool()
        await pool.release(conn)

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT id, username, email, full_name, role, is_active, 
                       created_at, updated_at, github_username
                FROM users
                WHERE id = $1
                """,
                user_id
            )
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "full_name": row.get("full_name"),
                "role": row.get("role", "user"),
                "is_active": row.get("is_active", True),
                "github_username": row.get("github_username"),
                "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
            }
        finally:
            await self._release_connection(conn)

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT id, username, email, full_name, role, is_active, 
                       password_hash, created_at, updated_at, github_username
                FROM users
                WHERE email = $1
                """,
                email.lower()
            )
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "full_name": row.get("full_name"),
                "role": row.get("role", "user"),
                "is_active": row.get("is_active", True),
                "password_hash": row.get("password_hash"),
                "github_username": row.get("github_username"),
                "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
            }
        finally:
            await self._release_connection(conn)

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT id, username, email, full_name, role, is_active, 
                       password_hash, created_at, updated_at, github_username
                FROM users
                WHERE username = $1
                """,
                username.lower()
            )
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "full_name": row.get("full_name"),
                "role": row.get("role", "user"),
                "is_active": row.get("is_active", True),
                "password_hash": row.get("password_hash"),
                "github_username": row.get("github_username"),
                "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
            }
        finally:
            await self._release_connection(conn)

    async def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        full_name: Optional[str] = None,
        role: str = "user"
    ) -> Dict[str, Any]:
        """Create a new user"""
        conn = await self._get_connection()
        try:
            # Check if user already exists
            existing = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1 OR username = $2",
                email.lower(), username.lower()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email or username already exists"
                )
            
            # Insert user
            row = await conn.fetchrow(
                """
                INSERT INTO users (
                    username, email, password_hash, full_name, role,
                    is_active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, username, email, full_name, role, is_active, created_at, updated_at
                """,
                username.lower(), email.lower(), password_hash, full_name, role,
                True, datetime.utcnow(), datetime.utcnow()
            )
            
            return {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "full_name": row.get("full_name"),
                "role": row.get("role", "user"),
                "is_active": row.get("is_active", True),
                "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
            }
        finally:
            await self._release_connection(conn)

    async def update_user_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp"""
        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                UPDATE users
                SET last_login_at = $1, updated_at = $2
                WHERE id = $3
                """,
                datetime.utcnow(), datetime.utcnow(), user_id
            )
        finally:
            await self._release_connection(conn)

    @staticmethod
    async def to_current_user(user_data: Dict[str, Any]) -> CurrentUser:
        """Convert user data to CurrentUser model"""
        # Map database role to UserRole enum
        role_mapping = {
            "admin": UserRole.ADMIN,
            "manager": UserRole.USER,  # Map manager to USER for now
            "user": UserRole.USER,
            "service": UserRole.AGENT  # Map service to AGENT
        }
        role = role_mapping.get(user_data.get("role", "user"), UserRole.USER)
        
        return CurrentUser(
            id=user_data["id"],
            email=user_data["email"],
            username=user_data.get("username", ""),
            role=role,
            is_active=user_data.get("is_active", True)
        )


# Global service instance
user_service = UserService()

