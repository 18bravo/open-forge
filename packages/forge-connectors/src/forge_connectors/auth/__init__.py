"""
Auth module - OAuth, service account, and secrets manager integration.
"""

from forge_connectors.auth.secrets import (
    SecretsProvider,
    SecretsFactory,
    SecretsConfig,
    VaultSecretsProvider,
    AWSSecretsProvider,
    K8sSecretsProvider,
    EnvSecretsProvider,
)
from forge_connectors.auth.oauth import (
    OAuthConfig,
    OAuthCredentials,
    OAuthFlow,
    OAuthManager,
)
from forge_connectors.auth.service_account import (
    ServiceAccountConfig,
    ServiceAccountAuth,
)

__all__ = [
    # Secrets
    "SecretsProvider",
    "SecretsFactory",
    "SecretsConfig",
    "VaultSecretsProvider",
    "AWSSecretsProvider",
    "K8sSecretsProvider",
    "EnvSecretsProvider",
    # OAuth
    "OAuthConfig",
    "OAuthCredentials",
    "OAuthFlow",
    "OAuthManager",
    # Service Account
    "ServiceAccountConfig",
    "ServiceAccountAuth",
]
