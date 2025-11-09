"""
Secret Management Module

Provides secure secret management with GCP Secret Manager integration,
secret rotation, versioning, and audit logging.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

try:
    from google.cloud import secretmanager
    from google.api_core import exceptions as gcp_exceptions
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    logging.warning("google-cloud-secret-manager not installed. GCP Secret Manager features disabled.")

logger = logging.getLogger(__name__)


class SecretType(Enum):
    """Secret types for categorization"""
    DATABASE = "database"
    API_KEY = "api_key"
    ENCRYPTION_KEY = "encryption_key"
    JWT = "jwt"
    OAUTH_TOKEN = "oauth_token"
    TLS_CERT = "tls_cert"
    OTHER = "other"


class SecretManager:
    """
    Secret Manager for GCP Secret Manager integration.
    
    Provides secure secret storage, retrieval, rotation, and versioning.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        default_location: str = "us-central1",
    ):
        """
        Initialize Secret Manager.
        
        Args:
            project_id: GCP project ID (defaults to environment variable)
            default_location: Default location for secrets
        """
        if not GCP_AVAILABLE:
            raise RuntimeError("google-cloud-secret-manager is required but not installed")
        
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID must be set")
        
        self.default_location = default_location
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_path = f"projects/{self.project_id}"

    def _get_secret_path(self, secret_id: str) -> str:
        """Get full secret path."""
        return f"{self.project_path}/secrets/{secret_id}"

    def _get_version_path(self, secret_id: str, version: str = "latest") -> str:
        """Get full version path."""
        return f"{self.project_path}/secrets/{secret_id}/versions/{version}"

    async def create_secret(
        self,
        secret_id: str,
        secret_data: str,
        labels: Optional[Dict[str, str]] = None,
        secret_type: SecretType = SecretType.OTHER,
    ) -> str:
        """
        Create a new secret in Secret Manager.
        
        Args:
            secret_id: Unique identifier for the secret
            secret_data: Secret value to store
            labels: Optional labels for categorization
            secret_type: Type of secret
        
        Returns:
            Secret name path
        """
        try:
            # Prepare labels
            secret_labels = labels or {}
            secret_labels["type"] = secret_type.value
            secret_labels["created_at"] = datetime.utcnow().isoformat()

            # Create secret
            parent = self.project_path
            secret = {
                "replication": {
                    "automatic": {}
                },
                "labels": secret_labels,
            }

            secret_name = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": secret,
                }
            ).name

            # Add secret version
            version = self.client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {
                        "data": secret_data.encode("UTF-8"),
                    },
                }
            )

            logger.info(f"Created secret: {secret_id}")
            return secret_name
        except gcp_exceptions.AlreadyExists:
            logger.warning(f"Secret {secret_id} already exists")
            return self._get_secret_path(secret_id)
        except Exception as e:
            logger.error(f"Failed to create secret {secret_id}: {e}")
            raise

    async def get_secret(
        self,
        secret_id: str,
        version: str = "latest",
    ) -> str:
        """
        Get secret value from Secret Manager.
        
        Args:
            secret_id: Secret identifier
            version: Secret version (default: "latest")
        
        Returns:
            Secret value as string
        """
        try:
            name = self._get_version_path(secret_id, version)
            response = self.client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            
            logger.debug(f"Retrieved secret: {secret_id} (version: {version})")
            return secret_value
        except gcp_exceptions.NotFound:
            logger.error(f"Secret {secret_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to get secret {secret_id}: {e}")
            raise

    async def rotate_secret(
        self,
        secret_id: str,
        new_secret_data: Optional[str] = None,
    ) -> str:
        """
        Rotate secret by adding a new version.
        
        Args:
            secret_id: Secret identifier
            new_secret_data: New secret value (generates if not provided)
        
        Returns:
            New version name
        """
        try:
            # Generate new secret if not provided
            if new_secret_data is None:
                import secrets
                new_secret_data = secrets.token_urlsafe(32)

            # Add new version
            parent = self._get_secret_path(secret_id)
            version = self.client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {
                        "data": new_secret_data.encode("UTF-8"),
                    },
                }
            )

            logger.info(f"Rotated secret: {secret_id} (new version: {version.name})")
            return version.name
        except Exception as e:
            logger.error(f"Failed to rotate secret {secret_id}: {e}")
            raise

    async def list_secrets(
        self,
        filter_str: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all secrets.
        
        Args:
            filter_str: Optional filter string
        
        Returns:
            List of secret metadata
        """
        try:
            secrets_list = []
            for secret in self.client.list_secrets(
                request={"parent": self.project_path, "filter": filter_str}
            ):
                secrets_list.append({
                    "name": secret.name,
                    "labels": dict(secret.labels),
                    "create_time": secret.create_time,
                })
            return secrets_list
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            raise

    async def list_versions(
        self,
        secret_id: str,
    ) -> List[Dict[str, Any]]:
        """
        List all versions of a secret.
        
        Args:
            secret_id: Secret identifier
        
        Returns:
            List of version metadata
        """
        try:
            versions_list = []
            parent = self._get_secret_path(secret_id)
            for version in self.client.list_secret_versions(request={"parent": parent}):
                versions_list.append({
                    "name": version.name,
                    "state": version.state.name,
                    "create_time": version.create_time,
                })
            return versions_list
        except Exception as e:
            logger.error(f"Failed to list versions for {secret_id}: {e}")
            raise

    async def disable_version(
        self,
        secret_id: str,
        version: str,
    ) -> None:
        """Disable a secret version."""
        try:
            name = self._get_version_path(secret_id, version)
            self.client.disable_secret_version(request={"name": name})
            logger.info(f"Disabled secret version: {secret_id}/{version}")
        except Exception as e:
            logger.error(f"Failed to disable version {secret_id}/{version}: {e}")
            raise

    async def enable_version(
        self,
        secret_id: str,
        version: str,
    ) -> None:
        """Enable a secret version."""
        try:
            name = self._get_version_path(secret_id, version)
            self.client.enable_secret_version(request={"name": name})
            logger.info(f"Enabled secret version: {secret_id}/{version}")
        except Exception as e:
            logger.error(f"Failed to enable version {secret_id}/{version}: {e}")
            raise

    async def delete_secret(
        self,
        secret_id: str,
    ) -> None:
        """Delete a secret (soft delete)."""
        try:
            name = self._get_secret_path(secret_id)
            self.client.delete_secret(request={"name": name})
            logger.info(f"Deleted secret: {secret_id}")
        except Exception as e:
            logger.error(f"Failed to delete secret {secret_id}: {e}")
            raise


class LocalSecretManager:
    """
    Local secret manager for development.
    Uses environment variables and .env files.
    """

    def __init__(self, env_file: str = ".env"):
        """Initialize local secret manager."""
        self.env_file = env_file
        self._load_env_file()

    def _load_env_file(self) -> None:
        """Load environment variables from .env file."""
        if os.path.exists(self.env_file):
            with open(self.env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()

    async def get_secret(self, secret_id: str, version: Optional[str] = None) -> str:
        """Get secret from environment variables."""
        value = os.getenv(secret_id)
        if value is None:
            raise ValueError(f"Secret {secret_id} not found in environment")
        return value

    async def create_secret(
        self,
        secret_id: str,
        secret_data: str,
        labels: Optional[Dict[str, str]] = None,
        secret_type: SecretType = SecretType.OTHER,
    ) -> str:
        """Create secret in .env file."""
        # Append to .env file
        with open(self.env_file, "a") as f:
            f.write(f"\n{secret_id}={secret_data}\n")
        return secret_id

    async def rotate_secret(
        self,
        secret_id: str,
        new_secret_data: Optional[str] = None,
    ) -> str:
        """Rotate secret in .env file."""
        if new_secret_data is None:
            import secrets
            new_secret_data = secrets.token_urlsafe(32)
        
        # Update in .env file
        if os.path.exists(self.env_file):
            with open(self.env_file, "r") as f:
                lines = f.readlines()
            
            with open(self.env_file, "w") as f:
                for line in lines:
                    if line.startswith(f"{secret_id}="):
                        f.write(f"{secret_id}={new_secret_data}\n")
                    else:
                        f.write(line)
        
        return "local"


def get_secret_manager() -> SecretManager:
    """
    Get appropriate secret manager based on environment.
    
    Returns:
        SecretManager instance (GCP in production, Local in development)
    """
    if os.getenv("ENVIRONMENT") == "production" and GCP_AVAILABLE:
        return SecretManager()
    else:
        return LocalSecretManager()


# Convenience functions
async def get_secret(secret_id: str, version: str = "latest") -> str:
    """Get secret value."""
    manager = get_secret_manager()
    return await manager.get_secret(secret_id, version)


async def rotate_secret(secret_id: str, new_secret_data: Optional[str] = None) -> str:
    """Rotate secret."""
    manager = get_secret_manager()
    return await manager.rotate_secret(secret_id, new_secret_data)

