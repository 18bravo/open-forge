"""
OAuth 2.0 authentication support for API connectors.

Provides:
- OAuth2 authorization code flow
- Client credentials flow
- Token refresh and caching
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import httpx
from pydantic import BaseModel

from forge_connectors.auth.secrets import SecretsProvider

logger = logging.getLogger(__name__)


class OAuthFlow(str, Enum):
    """Supported OAuth2 flows."""

    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"


class OAuthConfig(BaseModel):
    """Configuration for OAuth2 authentication."""

    client_id: str
    client_secret_ref: str  # Reference to secret containing client_secret
    authorize_url: Optional[str] = None  # For authorization code flow
    token_url: str
    scopes: list[str] = []
    flow: OAuthFlow = OAuthFlow.CLIENT_CREDENTIALS

    # Token endpoint auth method
    token_auth_method: str = "client_secret_post"  # or "client_secret_basic"

    # Additional parameters
    extra_params: dict[str, str] = {}


@dataclass
class OAuthCredentials:
    """OAuth2 credentials with token and metadata."""

    access_token: str
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """Check if token is expired (with buffer)."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at - timedelta(seconds=buffer_seconds)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "refresh_token": self.refresh_token,
            "scope": self.scope,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OAuthCredentials":
        """Create from dictionary."""
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
        )


@dataclass
class OAuthState:
    """State for OAuth authorization code flow."""

    state: str
    redirect_uri: str
    code_verifier: Optional[str] = None  # For PKCE
    created_at: datetime = field(default_factory=datetime.utcnow)


class OAuthManager:
    """
    Manager for OAuth2 authentication flows.

    Handles token acquisition, refresh, and caching for API connectors.

    Example:
        config = OAuthConfig(
            client_id="my-client",
            client_secret_ref="vault/oauth/my-client",
            token_url="https://api.example.com/oauth/token",
            scopes=["read", "write"],
        )

        manager = OAuthManager(config, secrets_provider)
        credentials = await manager.get_credentials()

        # Use credentials
        headers = {"Authorization": f"{credentials.token_type} {credentials.access_token}"}
    """

    def __init__(
        self,
        config: OAuthConfig,
        secrets: SecretsProvider,
        token_cache_ref: Optional[str] = None,
    ):
        """
        Initialize OAuth manager.

        Args:
            config: OAuth configuration.
            secrets: Secrets provider for client secret and token storage.
            token_cache_ref: Secret reference for caching tokens.
        """
        self.config = config
        self.secrets = secrets
        self.token_cache_ref = token_cache_ref
        self._credentials: Optional[OAuthCredentials] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def get_credentials(self, force_refresh: bool = False) -> OAuthCredentials:
        """
        Get valid OAuth credentials, refreshing if necessary.

        Args:
            force_refresh: Force token refresh even if not expired.

        Returns:
            Valid OAuthCredentials.
        """
        # Check cached credentials
        if not force_refresh and self._credentials and not self._credentials.is_expired():
            return self._credentials

        # Try to load from secrets cache
        if not force_refresh and self.token_cache_ref:
            try:
                cached = await self.secrets.get(self.token_cache_ref)
                self._credentials = OAuthCredentials.from_dict(cached)
                if not self._credentials.is_expired():
                    return self._credentials
            except Exception:
                pass  # Cache miss, need to get new token

        # Refresh or get new token
        if self._credentials and self._credentials.refresh_token:
            self._credentials = await self._refresh_token()
        else:
            self._credentials = await self._get_new_token()

        # Cache the new credentials
        if self.token_cache_ref:
            try:
                await self.secrets.set(
                    self.token_cache_ref, self._credentials.to_dict()
                )
            except Exception as e:
                logger.warning(f"Failed to cache OAuth token: {e}")

        return self._credentials

    async def _get_new_token(self) -> OAuthCredentials:
        """Get a new access token using configured flow."""
        if self.config.flow == OAuthFlow.CLIENT_CREDENTIALS:
            return await self._client_credentials_flow()
        else:
            raise ValueError(
                f"Flow {self.config.flow} requires user interaction. "
                "Use get_authorization_url() and exchange_code() instead."
            )

    async def _client_credentials_flow(self) -> OAuthCredentials:
        """Execute client credentials flow."""
        # Get client secret
        secret_data = await self.secrets.get(self.config.client_secret_ref)
        client_secret = secret_data.get("client_secret") or secret_data.get("secret")

        if not client_secret:
            raise ValueError("client_secret not found in secrets")

        # Build request
        data = {
            "grant_type": "client_credentials",
        }

        if self.config.scopes:
            data["scope"] = " ".join(self.config.scopes)

        data.update(self.config.extra_params)

        # Auth method
        auth = None
        if self.config.token_auth_method == "client_secret_basic":
            auth = (self.config.client_id, client_secret)
        else:  # client_secret_post
            data["client_id"] = self.config.client_id
            data["client_secret"] = client_secret

        # Make token request
        client = await self._get_http_client()
        response = await client.post(self.config.token_url, data=data, auth=auth)
        response.raise_for_status()

        return self._parse_token_response(response.json())

    async def _refresh_token(self) -> OAuthCredentials:
        """Refresh an existing access token."""
        if not self._credentials or not self._credentials.refresh_token:
            raise ValueError("No refresh token available")

        # Get client secret
        secret_data = await self.secrets.get(self.config.client_secret_ref)
        client_secret = secret_data.get("client_secret") or secret_data.get("secret")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._credentials.refresh_token,
            "client_id": self.config.client_id,
            "client_secret": client_secret,
        }

        client = await self._get_http_client()
        response = await client.post(self.config.token_url, data=data)
        response.raise_for_status()

        return self._parse_token_response(response.json())

    def get_authorization_url(
        self, redirect_uri: str, state: str, code_challenge: Optional[str] = None
    ) -> str:
        """
        Get authorization URL for authorization code flow.

        Args:
            redirect_uri: Callback URL.
            state: CSRF protection state.
            code_challenge: PKCE code challenge (optional).

        Returns:
            Authorization URL to redirect user to.
        """
        if not self.config.authorize_url:
            raise ValueError("authorize_url required for authorization code flow")

        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        }

        if self.config.scopes:
            params["scope"] = " ".join(self.config.scopes)

        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        params.update(self.config.extra_params)

        # Build URL
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.config.authorize_url}?{query}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None,
    ) -> OAuthCredentials:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback.
            redirect_uri: Same redirect_uri used in authorization.
            code_verifier: PKCE code verifier (if using PKCE).

        Returns:
            OAuthCredentials with access and refresh tokens.
        """
        secret_data = await self.secrets.get(self.config.client_secret_ref)
        client_secret = secret_data.get("client_secret") or secret_data.get("secret")

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.config.client_id,
            "client_secret": client_secret,
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        client = await self._get_http_client()
        response = await client.post(self.config.token_url, data=data)
        response.raise_for_status()

        self._credentials = self._parse_token_response(response.json())

        # Cache credentials
        if self.token_cache_ref:
            await self.secrets.set(self.token_cache_ref, self._credentials.to_dict())

        return self._credentials

    def _parse_token_response(self, data: dict[str, Any]) -> OAuthCredentials:
        """Parse token endpoint response."""
        expires_at = None
        if "expires_in" in data:
            expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"])

        return OAuthCredentials(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
        )

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
