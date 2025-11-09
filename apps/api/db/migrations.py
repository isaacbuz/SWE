"""
Database migration runner for the API application.
Runs migrations on application startup if needed.
"""
import logging
import os
from pathlib import Path
from typing import List, Optional
import asyncpg

from config import settings

logger = logging.getLogger(__name__)


async def run_migrations() -> bool:
    """
    Run database migrations if needed.
    
    Returns:
        True if migrations ran successfully, False otherwise
    """
    try:
        # Get migration directory
        db_package_path = Path(__file__).parent.parent.parent.parent / "packages" / "db"
        migrations_dir = db_package_path / "migrations"
        
        if not migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {migrations_dir}")
            return False
        
        # Get database pool
        from db.connection import get_db_pool
        pool = await get_db_pool()
        
        # Check if migrations table exists
        async with pool.acquire() as conn:
            # Check if schema_migrations table exists
            migration_table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'schema_migrations'
                )
            """)
            
            if not migration_table_exists:
                # Create migrations tracking table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version VARCHAR(255) PRIMARY KEY,
                        applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("Created schema_migrations table")
            
            # Get applied migrations
            applied_versions = set(
                row["version"] 
                for row in await conn.fetch("SELECT version FROM schema_migrations")
            )
            
            # Find migration files
            migration_files = sorted(migrations_dir.glob("*.sql"))
            
            if not migration_files:
                logger.info("No migration files found")
                return True
            
            # Run pending migrations
            for migration_file in migration_files:
                version = migration_file.stem
                
                if version in applied_versions:
                    logger.debug(f"Migration {version} already applied, skipping")
                    continue
                
                logger.info(f"Running migration: {version}")
                
                try:
                    # Read and execute migration SQL
                    with open(migration_file, "r") as f:
                        migration_sql = f.read()
                    
                    # Execute migration in a transaction
                    async with conn.transaction():
                        await conn.execute(migration_sql)
                        
                        # Record migration
                        await conn.execute("""
                            INSERT INTO schema_migrations (version)
                            VALUES ($1)
                        """, version)
                    
                    logger.info(f"Migration {version} applied successfully")
                except Exception as e:
                    logger.error(f"Failed to apply migration {version}: {e}")
                    return False
        
        logger.info("All migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration runner failed: {e}")
        return False


async def check_migration_status() -> dict:
    """
    Check migration status without applying migrations.
    
    Returns:
        Dict with migration status information
    """
    try:
        from db.connection import get_db_pool
        pool = await get_db_pool()
        
        db_package_path = Path(__file__).parent.parent.parent.parent / "packages" / "db"
        migrations_dir = db_package_path / "migrations"
        
        async with pool.acquire() as conn:
            # Check if migrations table exists
            migration_table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'schema_migrations'
                )
            """)
            
            if not migration_table_exists:
                return {
                    "status": "not_initialized",
                    "applied": [],
                    "pending": []
                }
            
            # Get applied migrations
            applied_versions = [
                row["version"] 
                for row in await conn.fetch("SELECT version FROM schema_migrations ORDER BY applied_at")
            ]
            
            # Find all migration files
            migration_files = sorted([f.stem for f in migrations_dir.glob("*.sql")])
            pending = [v for v in migration_files if v not in applied_versions]
            
            return {
                "status": "up_to_date" if not pending else "pending",
                "applied": applied_versions,
                "pending": pending
            }
    except Exception as e:
        logger.error(f"Failed to check migration status: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

