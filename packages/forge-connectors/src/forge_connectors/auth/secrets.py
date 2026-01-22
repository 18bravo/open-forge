"""
Secrets management for connector credentials.

Provides a unified interface for retrieving credentials from:
- HashiCorp Vault
- AWS Secrets Manager
- Kubernetes Secrets
- Environment variables (for development)
"""

import base64
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SecretsBackend(str, Enum):
    """Supported secrets backends."""

    VAULT = "vault"
    AWS = "aws"
    KUBERNETES = "kubernetes"
    ENV = "env"


@dataclass
class SecretsConfig:
    """Configuration for secrets provider."""

    backend: SecretsBackend

    # Vault settings
    vault_addr: Optional[str] = None
    vault_auth_method: Optional[str] = None  # 'token', 'kubernetes', 'approle'
    vault_mount_path: str = "secret"
    vault_token: Optional[str] = None
    vault_role: Optional[str] = None

    # AWS settings
    aws_region: Optional[str] = None

    # Kubernetes settings
    k8s_namespace: str = "default"


class SecretsProvider(ABC):
    """
    Abstract interface for secrets backends.

    All secrets providers must implement get, set, delete, and exists methods.
    Credentials are stored as dictionaries of string key-value pairs.
    """

    @abstractmethod
    async def get(self, secret_ref: str) -> dict[str, str]:
        """
        Retrieve a secret by reference.

        Args:
            secret_ref: Reference/path to the secret.

        Returns:
            Dictionary of credential key-value pairs.

        Raises:
            SecretNotFoundError: If secret does not exist.
        """
        ...

    @abstractmethod
    async def set(self, secret_ref: str, values: dict[str, str]) -> None:
        """
        Store a secret.

        Used for OAuth token refresh and similar scenarios.

        Args:
            secret_ref: Reference/path for the secret.
            values: Credential key-value pairs.
        """
        ...

    @abstractmethod
    async def delete(self, secret_ref: str) -> None:
        """
        Delete a secret.

        Args:
            secret_ref: Reference/path to the secret.
        """
        ...

    @abstractmethod
    async def exists(self, secret_ref: str) -> bool:
        """
        Check if a secret exists.

        Args:
            secret_ref: Reference/path to check.

        Returns:
            True if secret exists, False otherwise.
        """
        ...


class SecretNotFoundError(Exception):
    """Raised when a requested secret does not exist."""

    pass


class VaultSecretsProvider(SecretsProvider):
    """
    HashiCorp Vault secrets backend.

    Supports KV v2 secrets engine with multiple authentication methods.

    Note: Requires `hvac` package (install with `pip install forge-connectors[vault]`).
    """

    def __init__(
        self,
        vault_addr: str,
        auth_method: str = "token",
        mount_path: str = "secret",
        token: Optional[str] = None,
        role: Optional[str] = None,
    ):
        """
        Initialize Vault provider.

        Args:
            vault_addr: Vault server address.
            auth_method: Authentication method ('token', 'kubernetes', 'approle').
            mount_path: KV secrets mount path.
            token: Vault token (for token auth).
            role: Vault role (for kubernetes/approle auth).
        """
        try:
            import hvac
        except ImportError:
            raise ImportError(
                "hvac package required for Vault support. "
                "Install with: pip install forge-connectors[vault]"
            )

        self.client = hvac.Client(url=vault_addr)
        self.mount = mount_path
        self._authenticate(auth_method, token, role)

    def _authenticate(
        self, auth_method: str, token: Optional[str], role: Optional[str]
    ) -> None:
        """Authenticate to Vault."""
        if auth_method == "token":
            if token:
                self.client.token = token
            elif os.environ.get("VAULT_TOKEN"):
                self.client.token = os.environ["VAULT_TOKEN"]
            else:
                raise ValueError("Vault token required for token authentication")

        elif auth_method == "kubernetes":
            jwt_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
            if os.path.exists(jwt_path):
                with open(jwt_path) as f:
                    jwt = f.read()
                self.client.auth.kubernetes.login(role=role, jwt=jwt)
            else:
                raise ValueError("Kubernetes service account token not found")

        elif auth_method == "approle":
            role_id = os.environ.get("VAULT_ROLE_ID")
            secret_id = os.environ.get("VAULT_SECRET_ID")
            if role_id and secret_id:
                self.client.auth.approle.login(role_id=role_id, secret_id=secret_id)
            else:
                raise ValueError("VAULT_ROLE_ID and VAULT_SECRET_ID required for AppRole auth")

        else:
            raise ValueError(f"Unknown Vault auth method: {auth_method}")

    async def get(self, secret_ref: str) -> dict[str, str]:
        """Retrieve secret from Vault KV v2."""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=secret_ref, mount_point=self.mount
            )
            return response["data"]["data"]
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise SecretNotFoundError(f"Secret not found: {secret_ref}")
            raise

    async def set(self, secret_ref: str, values: dict[str, str]) -> None:
        """Store secret in Vault KV v2."""
        self.client.secrets.kv.v2.create_or_update_secret(
            path=secret_ref, secret=values, mount_point=self.mount
        )

    async def delete(self, secret_ref: str) -> None:
        """Delete secret from Vault."""
        self.client.secrets.kv.v2.delete_metadata_and_all_versions(
            path=secret_ref, mount_point=self.mount
        )

    async def exists(self, secret_ref: str) -> bool:
        """Check if secret exists in Vault."""
        try:
            self.client.secrets.kv.v2.read_secret_version(
                path=secret_ref, mount_point=self.mount
            )
            return True
        except Exception:
            return False


class AWSSecretsProvider(SecretsProvider):
    """
    AWS Secrets Manager backend.

    Note: Requires `boto3` package (install with `pip install forge-connectors[aws]`).
    """

    def __init__(self, region: Optional[str] = None):
        """
        Initialize AWS Secrets Manager provider.

        Args:
            region: AWS region (defaults to AWS_DEFAULT_REGION or us-east-1).
        """
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "boto3 package required for AWS support. "
                "Install with: pip install forge-connectors[aws]"
            )

        self.client = boto3.client(
            "secretsmanager",
            region_name=region or os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        )

    async def get(self, secret_ref: str) -> dict[str, str]:
        """Retrieve secret from AWS Secrets Manager."""
        try:
            response = self.client.get_secret_value(SecretId=secret_ref)
            secret_string = response.get("SecretString")
            if secret_string:
                return json.loads(secret_string)

            # Handle binary secrets
            secret_binary = response.get("SecretBinary")
            if secret_binary:
                return json.loads(base64.b64decode(secret_binary).decode())

            return {}
        except self.client.exceptions.ResourceNotFoundException:
            raise SecretNotFoundError(f"Secret not found: {secret_ref}")

    async def set(self, secret_ref: str, values: dict[str, str]) -> None:
        """Store secret in AWS Secrets Manager."""
        try:
            self.client.put_secret_value(
                SecretId=secret_ref, SecretString=json.dumps(values)
            )
        except self.client.exceptions.ResourceNotFoundException:
            # Create new secret
            self.client.create_secret(
                Name=secret_ref, SecretString=json.dumps(values)
            )

    async def delete(self, secret_ref: str) -> None:
        """Delete secret from AWS Secrets Manager."""
        self.client.delete_secret(
            SecretId=secret_ref, ForceDeleteWithoutRecovery=True
        )

    async def exists(self, secret_ref: str) -> bool:
        """Check if secret exists in AWS Secrets Manager."""
        try:
            self.client.describe_secret(SecretId=secret_ref)
            return True
        except self.client.exceptions.ResourceNotFoundException:
            return False


class K8sSecretsProvider(SecretsProvider):
    """
    Kubernetes Secrets backend.

    Note: Requires `kubernetes` package (install with `pip install forge-connectors[kubernetes]`).
    """

    def __init__(self, namespace: str = "default"):
        """
        Initialize Kubernetes Secrets provider.

        Args:
            namespace: Kubernetes namespace.
        """
        try:
            from kubernetes import client, config
        except ImportError:
            raise ImportError(
                "kubernetes package required for K8s support. "
                "Install with: pip install forge-connectors[kubernetes]"
            )

        # Try in-cluster config first, fall back to kubeconfig
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        self.v1 = client.CoreV1Api()
        self.namespace = namespace

    async def get(self, secret_ref: str) -> dict[str, str]:
        """Retrieve secret from Kubernetes."""
        try:
            secret = self.v1.read_namespaced_secret(secret_ref, self.namespace)
            if secret.data:
                return {
                    k: base64.b64decode(v).decode() for k, v in secret.data.items()
                }
            return {}
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise SecretNotFoundError(f"Secret not found: {secret_ref}")
            raise

    async def set(self, secret_ref: str, values: dict[str, str]) -> None:
        """Store secret in Kubernetes."""
        from kubernetes import client

        secret = client.V1Secret(
            metadata=client.V1ObjectMeta(name=secret_ref),
            string_data=values,
        )

        try:
            self.v1.read_namespaced_secret(secret_ref, self.namespace)
            self.v1.replace_namespaced_secret(secret_ref, self.namespace, secret)
        except Exception:
            self.v1.create_namespaced_secret(self.namespace, secret)

    async def delete(self, secret_ref: str) -> None:
        """Delete secret from Kubernetes."""
        self.v1.delete_namespaced_secret(secret_ref, self.namespace)

    async def exists(self, secret_ref: str) -> bool:
        """Check if secret exists in Kubernetes."""
        try:
            self.v1.read_namespaced_secret(secret_ref, self.namespace)
            return True
        except Exception:
            return False


class EnvSecretsProvider(SecretsProvider):
    """
    Environment variables backend for development/testing.

    Secrets are stored as environment variables with a prefix:
    FORGE_SECRET_{SECRET_REF}_{KEY}=value

    Example:
        FORGE_SECRET_MYDB_USERNAME=admin
        FORGE_SECRET_MYDB_PASSWORD=secret

        provider.get("mydb") -> {"username": "admin", "password": "secret"}
    """

    def __init__(self, prefix: str = "FORGE_SECRET"):
        """
        Initialize environment secrets provider.

        Args:
            prefix: Environment variable prefix.
        """
        self.prefix = prefix
        self._cache: dict[str, dict[str, str]] = {}

    async def get(self, secret_ref: str) -> dict[str, str]:
        """Retrieve secret from environment variables."""
        # Check cache first
        if secret_ref in self._cache:
            return self._cache[secret_ref]

        env_prefix = f"{self.prefix}_{secret_ref.upper().replace('-', '_').replace('/', '_')}_"
        result: dict[str, str] = {}

        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                secret_key = key[len(env_prefix):].lower()
                result[secret_key] = value

        if not result:
            raise SecretNotFoundError(f"No environment variables found for: {secret_ref}")

        return result

    async def set(self, secret_ref: str, values: dict[str, str]) -> None:
        """
        Store secret in cache (env vars are read-only).

        Note: This only affects the in-memory cache, not actual environment.
        """
        self._cache[secret_ref] = values
        logger.warning(
            f"EnvSecretsProvider.set() only caches values, does not modify environment"
        )

    async def delete(self, secret_ref: str) -> None:
        """Remove secret from cache."""
        self._cache.pop(secret_ref, None)

    async def exists(self, secret_ref: str) -> bool:
        """Check if secret exists in environment or cache."""
        if secret_ref in self._cache:
            return True

        env_prefix = f"{self.prefix}_{secret_ref.upper().replace('-', '_').replace('/', '_')}_"
        return any(k.startswith(env_prefix) for k in os.environ)


class SecretsFactory:
    """
    Factory for creating secrets providers based on configuration.

    Example:
        config = SecretsConfig(backend=SecretsBackend.VAULT, vault_addr="https://vault:8200")
        provider = SecretsFactory.create(config)
    """

    @staticmethod
    def create(config: SecretsConfig) -> SecretsProvider:
        """
        Create a secrets provider based on configuration.

        Args:
            config: Secrets configuration.

        Returns:
            Configured SecretsProvider instance.

        Raises:
            ValueError: If backend is unknown.
        """
        match config.backend:
            case SecretsBackend.VAULT:
                if not config.vault_addr:
                    raise ValueError("vault_addr required for Vault backend")
                return VaultSecretsProvider(
                    vault_addr=config.vault_addr,
                    auth_method=config.vault_auth_method or "token",
                    mount_path=config.vault_mount_path,
                    token=config.vault_token,
                    role=config.vault_role,
                )

            case SecretsBackend.AWS:
                return AWSSecretsProvider(region=config.aws_region)

            case SecretsBackend.KUBERNETES:
                return K8sSecretsProvider(namespace=config.k8s_namespace)

            case SecretsBackend.ENV:
                return EnvSecretsProvider()

            case _:
                raise ValueError(f"Unknown secrets backend: {config.backend}")
