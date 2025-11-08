"""
Database setup and initialization script.

This script helps set up the database, run migrations, and load seed data.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseSetup:
    """Helper class for database setup operations."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "ai_company_db",
        user: str = "postgres",
        password: Optional[str] = None,
    ):
        """Initialize database setup parameters."""
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.db_dir = Path(__file__).parent

    def _get_psql_env(self) -> dict:
        """Get environment variables for psql."""
        env = os.environ.copy()
        if self.password:
            env["PGPASSWORD"] = self.password
        return env

    def create_database(self) -> bool:
        """Create the PostgreSQL database."""
        logger.info(f"Creating database '{self.database}'...")
        try:
            cmd = [
                "createdb",
                "-h", self.host,
                "-p", str(self.port),
                "-U", self.user,
                self.database,
            ]
            subprocess.run(cmd, check=True, capture_output=True, env=self._get_psql_env())
            logger.info("Database created successfully")
            return True
        except subprocess.CalledProcessError as e:
            if "already exists" in e.stderr.decode():
                logger.info("Database already exists, skipping creation")
                return True
            logger.error(f"Failed to create database: {e}")
            return False

    def run_migration(self, migration_file: str) -> bool:
        """Run a migration SQL file."""
        migration_path = self.db_dir / "migrations" / migration_file
        if not migration_path.exists():
            logger.error(f"Migration file not found: {migration_path}")
            return False

        logger.info(f"Running migration: {migration_file}")
        try:
            with open(migration_path, "r") as f:
                sql = f.read()

            cmd = [
                "psql",
                "-h", self.host,
                "-p", str(self.port),
                "-U", self.user,
                "-d", self.database,
                "-c", sql,
            ]
            subprocess.run(cmd, check=True, capture_output=True, env=self._get_psql_env())
            logger.info(f"Migration '{migration_file}' completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Migration failed: {e.stderr.decode()}")
            return False

    def load_seeds(self, seed_dir: str = "seeds") -> bool:
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
        all_succeeded = True

        for seed_file in seed_files:
            logger.info(f"Loading seed: {seed_file.name}")
            try:
                with open(seed_file, "r") as f:
                    sql = f.read()

                cmd = [
                    "psql",
                    "-h", self.host,
                    "-p", str(self.port),
                    "-U", self.user,
                    "-d", self.database,
                    "-c", sql,
                ]
                subprocess.run(cmd, check=True, capture_output=True, env=self._get_psql_env())
                logger.info(f"Seed '{seed_file.name}' loaded successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Seed '{seed_file.name}' failed: {e.stderr.decode()}")
                all_succeeded = False

        return all_succeeded

    def verify_setup(self) -> bool:
        """Verify the database setup by checking table counts."""
        logger.info("Verifying database setup...")
        try:
            cmd = [
                "psql",
                "-h", self.host,
                "-p", str(self.port),
                "-U", self.user,
                "-d", self.database,
                "-c", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';",
            ]
            result = subprocess.run(
                cmd, check=True, capture_output=True, text=True, env=self._get_psql_env()
            )
            output = result.stdout.strip().split("\n")[-1].strip()
            table_count = int(output)
            logger.info(f"Found {table_count} tables in database")
            return table_count > 0
        except (subprocess.CalledProcessError, ValueError) as e:
            logger.error(f"Verification failed: {e}")
            return False

    def full_setup(self, skip_seeds: bool = False) -> bool:
        """Run full database setup including migrations and seeds."""
        logger.info("Starting full database setup...")

        # Step 1: Create database
        if not self.create_database():
            logger.error("Failed to create database")
            return False

        # Step 2: Run migrations
        if not self.run_migration("001_initial_schema.sql"):
            logger.error("Failed to run migrations")
            return False

        # Step 3: Load seed data (optional)
        if not skip_seeds:
            if not self.load_seeds():
                logger.warning("Failed to load seed data (continuing anyway)")

        # Step 4: Verify setup
        if not self.verify_setup():
            logger.error("Database setup verification failed")
            return False

        logger.info("Database setup completed successfully!")
        return True


def main():
    """Main entry point for database setup."""
    import argparse

    parser = argparse.ArgumentParser(description="Database setup utility")
    parser.add_argument(
        "--host", default=os.getenv("POSTGRES_HOST", "localhost"),
        help="PostgreSQL host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=int(os.getenv("POSTGRES_PORT", 5432)),
        help="PostgreSQL port (default: 5432)"
    )
    parser.add_argument(
        "--database", default=os.getenv("POSTGRES_DB", "ai_company_db"),
        help="Database name (default: ai_company_db)"
    )
    parser.add_argument(
        "--user", default=os.getenv("POSTGRES_USER", "postgres"),
        help="PostgreSQL user (default: postgres)"
    )
    parser.add_argument(
        "--password", default=os.getenv("POSTGRES_PASSWORD"),
        help="PostgreSQL password (default: from env or prompt)"
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

    setup = DatabaseSetup(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
    )

    if args.verify_only:
        success = setup.verify_setup()
    else:
        success = setup.full_setup(skip_seeds=args.skip_seeds)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
