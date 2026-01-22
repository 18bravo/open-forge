"""
Service account authentication for cloud services.

Provides authentication using:
- GCP service accounts (JSON key files)
- AWS IAM roles
- Azure service principals
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from forge_connectors.auth.secrets import SecretsProvider

logger = logging.getLogger(__name__)


class ServiceAccountType(str, Enum):
    """Supported service account types."""

    GCP = "gcp"
    AWS = "aws"
    AZURE = "azure"


@dataclass
class ServiceAccountConfig:
    """Configuration for service account authentication."""

    account_type: ServiceAccountType
    credentials_ref: str  # Reference to secret containing credentials

    # GCP specific
    project_id: Optional[str] = None
    scopes: Optional[list[str]] = None

    # Azure specific
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None

    # AWS specific
    role_arn: Optional[str] = None
    region: Optional[str] = None


class ServiceAccountAuth:
    """
    Handler for service account authentication.

    Retrieves credentials from secrets manager and provides
    appropriate authentication for each cloud provider.

    Example:
        config = ServiceAccountConfig(
            account_type=ServiceAccountType.GCP,
            credentials_ref="vault/gcp/my-service-account",
            project_id="my-project",
            scopes=["https://www.googleapis.com/auth/bigquery"],
        )

        auth = ServiceAccountAuth(config, secrets_provider)
        credentials = await auth.get_credentials()

        # For GCP:
        from google.cloud import bigquery
        client = bigquery.Client(credentials=credentials)
    """

    def __init__(self, config: ServiceAccountConfig, secrets: SecretsProvider):
        """
        Initialize service account auth.

        Args:
            config: Service account configuration.
            secrets: Secrets provider for retrieving credentials.
        """
        self.config = config
        self.secrets = secrets
        self._credentials: Any = None

    async def get_credentials(self) -> Any:
        """
        Get credentials for the configured service account.

        Returns:
            Cloud-provider-specific credentials object.
        """
        if self._credentials is not None:
            return self._credentials

        match self.config.account_type:
            case ServiceAccountType.GCP:
                self._credentials = await self._get_gcp_credentials()
            case ServiceAccountType.AWS:
                self._credentials = await self._get_aws_credentials()
            case ServiceAccountType.AZURE:
                self._credentials = await self._get_azure_credentials()

        return self._credentials

    async def _get_gcp_credentials(self) -> Any:
        """
        Get GCP service account credentials.

        Returns:
            google.oauth2.service_account.Credentials instance.
        """
        try:
            from google.oauth2 import service_account
        except ImportError:
            raise ImportError(
                "google-auth package required for GCP service accounts. "
                "Install with: pip install google-auth"
            )

        # Get service account key from secrets
        secret_data = await self.secrets.get(self.config.credentials_ref)

        # Secret might contain the JSON key or be the JSON itself
        if "private_key" in secret_data:
            key_data = secret_data
        elif "key_json" in secret_data:
            key_data = json.loads(secret_data["key_json"])
        else:
            # Assume the secret is the JSON key file content
            raise ValueError(
                "GCP credentials should contain 'private_key' field "
                "or 'key_json' with the service account JSON"
            )

        credentials = service_account.Credentials.from_service_account_info(
            key_data,
            scopes=self.config.scopes,
        )

        return credentials

    async def _get_aws_credentials(self) -> Any:
        """
        Get AWS credentials (for assumed roles).

        Returns:
            boto3 credentials or session.
        """
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "boto3 package required for AWS credentials. "
                "Install with: pip install forge-connectors[aws]"
            )

        if self.config.role_arn:
            # Assume role
            sts = boto3.client("sts", region_name=self.config.region)
            response = sts.assume_role(
                RoleArn=self.config.role_arn,
                RoleSessionName="forge-connector",
            )
            credentials = response["Credentials"]
            return {
                "aws_access_key_id": credentials["AccessKeyId"],
                "aws_secret_access_key": credentials["SecretAccessKey"],
                "aws_session_token": credentials["SessionToken"],
            }
        else:
            # Get static credentials from secrets
            secret_data = await self.secrets.get(self.config.credentials_ref)
            return {
                "aws_access_key_id": secret_data.get("access_key_id")
                or secret_data.get("aws_access_key_id"),
                "aws_secret_access_key": secret_data.get("secret_access_key")
                or secret_data.get("aws_secret_access_key"),
            }

    async def _get_azure_credentials(self) -> Any:
        """
        Get Azure service principal credentials.

        Returns:
            azure.identity.ClientSecretCredential instance.
        """
        try:
            from azure.identity import ClientSecretCredential
        except ImportError:
            raise ImportError(
                "azure-identity package required for Azure credentials. "
                "Install with: pip install azure-identity"
            )

        # Get client secret from secrets
        secret_data = await self.secrets.get(self.config.credentials_ref)
        client_secret = secret_data.get("client_secret") or secret_data.get("secret")

        if not client_secret:
            raise ValueError("client_secret not found in secrets")

        tenant_id = self.config.tenant_id or secret_data.get("tenant_id")
        client_id = self.config.client_id or secret_data.get("client_id")

        if not tenant_id or not client_id:
            raise ValueError("tenant_id and client_id required for Azure auth")

        return ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )

    async def get_token(self, resource: Optional[str] = None) -> str:
        """
        Get an access token for the service account.

        Args:
            resource: Resource/audience for the token (provider-specific).

        Returns:
            Access token string.
        """
        credentials = await self.get_credentials()

        match self.config.account_type:
            case ServiceAccountType.GCP:
                # GCP credentials have a token property
                credentials.refresh(None)  # Refresh if needed
                return credentials.token

            case ServiceAccountType.AWS:
                # AWS uses STS tokens
                return credentials.get("aws_session_token", "")

            case ServiceAccountType.AZURE:
                # Azure credentials have get_token method
                token = credentials.get_token(resource or "https://management.azure.com/.default")
                return token.token

        raise ValueError(f"Unknown account type: {self.config.account_type}")
