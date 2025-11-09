"""
Database backup and restore utilities.
"""

import asyncio
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Database backup and restore operations."""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        backup_dir: str = None,
    ):
        """Initialize backup parameters."""
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = port or int(os.getenv("POSTGRES_PORT", 5432))
        self.database = database or os.getenv("POSTGRES_DB", "piehr")
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "postgres")
        self.backup_dir = Path(backup_dir or os.getenv("BACKUP_DIR", "./backups"))

    def _get_pg_env(self) -> dict:
        """Get environment variables for pg_dump/pg_restore."""
        env = os.environ.copy()
        if self.password:
            env["PGPASSWORD"] = self.password
        return env

    def backup(self, backup_file: Optional[str] = None) -> Optional[Path]:
        """
        Create a database backup.
        
        Args:
            backup_file: Optional backup file path. If not provided, generates one.
        
        Returns:
            Path to backup file if successful, None otherwise.
        """
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename if not provided
        if not backup_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.database}_backup_{timestamp}.sql"
        
        backup_path = self.backup_dir / backup_file

        logger.info(f"Creating backup: {backup_path}")
        try:
            cmd = [
                "pg_dump",
                "-h", self.host,
                "-p", str(self.port),
                "-U", self.user,
                "-d", self.database,
                "-F", "c",  # Custom format
                "-f", str(backup_path),
            ]
            
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                env=self._get_pg_env()
            )
            
            logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Backup failed: {e.stderr.decode()}")
            return None

    def restore(self, backup_file: str, drop_existing: bool = False) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_file: Path to backup file
            drop_existing: Whether to drop existing database first
        
        Returns:
            True if successful, False otherwise.
        """
        backup_path = Path(backup_file)
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        logger.info(f"Restoring from backup: {backup_path}")
        
        try:
            # Drop existing database if requested
            if drop_existing:
                logger.info("Dropping existing database...")
                drop_cmd = [
                    "dropdb",
                    "-h", self.host,
                    "-p", str(self.port),
                    "-U", self.user,
                    self.database,
                ]
                subprocess.run(
                    drop_cmd,
                    check=False,  # Don't fail if database doesn't exist
                    capture_output=True,
                    env=self._get_pg_env()
                )

            # Restore from backup
            cmd = [
                "pg_restore",
                "-h", self.host,
                "-p", str(self.port),
                "-U", self.user,
                "-d", self.database,
                "-c",  # Clean (drop) before restore
                str(backup_path),
            ]
            
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                env=self._get_pg_env()
            )
            
            logger.info("Restore completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Restore failed: {e.stderr.decode()}")
            return False

    def list_backups(self) -> list[Path]:
        """List all backup files."""
        if not self.backup_dir.exists():
            return []
        
        return sorted(
            self.backup_dir.glob("*.sql"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )


def main():
    """CLI entry point for backup/restore."""
    import argparse

    parser = argparse.ArgumentParser(description="Database backup/restore utility")
    parser.add_argument(
        "action",
        choices=["backup", "restore", "list"],
        help="Action to perform"
    )
    parser.add_argument(
        "--backup-file",
        help="Backup file path (for restore) or name (for backup)"
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing database before restore"
    )
    parser.add_argument(
        "--host", default=os.getenv("POSTGRES_HOST", "localhost"),
        help="PostgreSQL host"
    )
    parser.add_argument(
        "--port", type=int, default=int(os.getenv("POSTGRES_PORT", 5432)),
        help="PostgreSQL port"
    )
    parser.add_argument(
        "--database", default=os.getenv("POSTGRES_DB", "piehr"),
        help="Database name"
    )
    parser.add_argument(
        "--user", default=os.getenv("POSTGRES_USER", "postgres"),
        help="PostgreSQL user"
    )
    parser.add_argument(
        "--password", default=os.getenv("POSTGRES_PASSWORD", "postgres"),
        help="PostgreSQL password"
    )

    args = parser.parse_args()

    backup = DatabaseBackup(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
    )

    if args.action == "backup":
        result = backup.backup(args.backup_file)
        exit(0 if result else 1)
    elif args.action == "restore":
        if not args.backup_file:
            logger.error("--backup-file required for restore")
            exit(1)
        success = backup.restore(args.backup_file, args.drop_existing)
        exit(0 if success else 1)
    elif args.action == "list":
        backups = backup.list_backups()
        for backup_file in backups:
            print(backup_file)
        exit(0)


if __name__ == "__main__":
    main()

