"""
Async database initialization script using asyncpg.

This script initializes the database, runs migrations, and loads seed data.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)


class AsyncDatabaseSetup:
    """Async database setup using asyncpg."""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
    ):
        """Initialize database setup parameters from environment or explicit values."""
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = port or int(os.getenv("POSTGRES_PORT", 5432))
        self.database = database or os.getenv("POSTGRES_DB", "piehr")
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "postgres")
        self.db_dir = Path(__file__).parent

    async def create_connection(self) -> asyncpg.Connection:
        """Create a database connection."""
        return await asyncpg.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )

    async def create_database(self) -> bool:
        """Create the PostgreSQL database if it doesn't exist."""
        logger.info(f"Creating database '{self.database}'...")
        try:
            # Connect to postgres database to create the target database
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                database="postgres",
                user=self.user,
                password=self.password,
            )
            
            # Check if database exists
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.database
            )
            
            if not exists:
                await conn.execute(f'CREATE DATABASE "{self.database}"')
                logger.info("Database created successfully")
            else:
                logger.info("Database already exists, skipping creation")
            
            await conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False

    async def run_migration(self, migration_file: str) -> bool:
        """Run a migration SQL file."""
        migration_path = self.db_dir / "migrations" / migration_file
        if not migration_path.exists():
            logger.error(f"Migration file not found: {migration_path}")
            return False

        logger.info(f"Running migration: {migration_file}")
        try:
            conn = await self.create_connection()
            with open(migration_path, "r") as f:
                sql = f.read()
            
            await conn.execute(sql)
            await conn.close()
            logger.info(f"Migration '{migration_file}' completed successfully")
            return True
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    async def load_seeds(self, seed_dir: str = "seeds") -> bool:
        """Load seed data from SQL files."""
        seeds_path = self.db_dir / seed_dir
        if not seeds_path.exists():
            logger.warning(f"Seeds directory not found: {seeds_path}")
            return False

        seed_files = sorted([f for f in seeds_path.glob("*.sql")])
        if not seed_files:
            logger.warning("No seed files found")
            return False

        logger.info(f"Loading {len(seed_files)} seed files...")
        conn = await self.create_connection()
        
        try:
            for seed_file in seed_files:
                logger.info(f"Loading seed: {seed_file.name}")
                with open(seed_file, "r") as f:
                    sql = f.read()
                await conn.execute(sql)
                logger.info(f"Seed '{seed_file.name}' loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Seed loading failed: {e}")
            return False
        finally:
            await conn.close()

    async def verify_setup(self) -> bool:
        """Verify the database setup by checking table counts."""
        logger.info("Verifying database setup...")
        try:
            conn = await self.create_connection()
            table_count = await conn.fetchval(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            await conn.close()
            logger.info(f"Found {table_count} tables in database")
            return table_count > 0
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False

    async def full_setup(self, skip_seeds: bool = False) -> bool:
        """Run full database setup including migrations and seeds."""
        logger.info("Starting full database setup...")

        # Step 1: Create database
        if not await self.create_database():
            logger.error("Failed to create database")
            return False

        # Step 2: Run migrations
        if not await self.run_migration("001_initial_schema.sql"):
            logger.error("Failed to run migrations")
            return False

        # Step 3: Load seed data (optional)
        if not skip_seeds:
            if not await self.load_seeds():
                logger.warning("Failed to load seed data (continuing anyway)")

        # Step 4: Verify setup
        if not await self.verify_setup():
            logger.error("Database setup verification failed")
            return False

        logger.info("Database setup completed successfully!")
        return True


async def main():
    """Main entry point for async database setup."""
    import argparse

    parser = argparse.ArgumentParser(description="Async database setup utility")
    parser.add_argument(
        "--host", default=os.getenv("POSTGRES_HOST", "localhost"),
        help="PostgreSQL host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=int(os.getenv("POSTGRES_PORT", 5432)),
        help="PostgreSQL port (default: 5432)"
    )
    parser.add_argument(
        "--database", default=os.getenv("POSTGRES_DB", "piehr"),
        help="Database name (default: piehr)"
    )
    parser.add_argument(
        "--user", default=os.getenv("POSTGRES_USER", "postgres"),
        help="PostgreSQL user (default: postgres)"
    )
    parser.add_argument(
        "--password", default=os.getenv("POSTGRES_PASSWORD", "postgres"),
        help="PostgreSQL password (default: from env)"
    )
    parser.add_argument(
        "--skip-seeds", action="store_true",
        help="Skip loading seed data"
    )
    parser.add_argument(
        "--verify-only", action="store_true",
        help="Only verify existing setup, don't modify"
    )

    args = parser.parse_args()

    setup = AsyncDatabaseSetup(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
    )

    if args.verify_only:
        success = await setup.verify_setup()
    else:
        success = await setup.full_setup(skip_seeds=args.skip_seeds)

    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

