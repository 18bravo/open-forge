"""Tests for the JWT authentication provider."""

import pytest
from datetime import datetime, timedelta, timezone

from jose import JWTError

from forge_core.auth.jwt_provider import JWTAuthProvider, JWTConfig
from forge_core.auth.provider import AuthProviderConfig, AuthProviderType


@pytest.fixture
def jwt_config() -> JWTConfig:
    """Create a JWT config for testing."""
    return JWTConfig(
        secret_key="test-secret-key-for-testing-only",
        algorithm="HS256",
        access_token_expire_minutes=30,
    )


@pytest.fixture
def auth_config() -> AuthProviderConfig:
    """Create an auth provider config for testing."""
    return AuthProviderConfig(
        provider_type=AuthProviderType.INTERNAL,
        issuer="test-issuer",
        client_id="test-client",
    )


@pytest.fixture
def jwt_provider(auth_config: AuthProviderConfig, jwt_config: JWTConfig) -> JWTAuthProvider:
    """Create a JWT provider for testing."""
    return JWTAuthProvider(auth_config, jwt_config)


class TestJWTAuthProvider:
    """Tests for the JWTAuthProvider class."""

    def test_create_access_token(self, jwt_provider: JWTAuthProvider) -> None:
        """Test creating an access token."""
        token = jwt_provider.create_access_token(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            roles=["admin", "developer"],
            permissions=["dataset:read", "pipeline:execute"],
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_authenticate_valid_token(self, jwt_provider: JWTAuthProvider) -> None:
        """Test authenticating with a valid token."""
        token = jwt_provider.create_access_token(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            name="Test User",
            roles=["admin"],
            permissions=["*"],
            tenant_id="tenant-1",
        )

        user = await jwt_provider.authenticate(token)

        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert "admin" in user.roles
        assert "*" in user.permissions
        assert user.tenant_id == "tenant-1"

    @pytest.mark.asyncio
    async def test_authenticate_expired_token(
        self, auth_config: AuthProviderConfig, jwt_config: JWTConfig
    ) -> None:
        """Test authenticating with an expired token."""
        provider = JWTAuthProvider(auth_config, jwt_config)

        # Create a token with very short expiration
        token = provider.create_access_token(
            user_id="user-123",
            username="testuser",
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        with pytest.raises(JWTError):
            await provider.authenticate(token)

    @pytest.mark.asyncio
    async def test_authenticate_invalid_token(self, jwt_provider: JWTAuthProvider) -> None:
        """Test authenticating with an invalid token."""
        with pytest.raises(JWTError):
            await jwt_provider.authenticate("invalid-token")

    @pytest.mark.asyncio
    async def test_authorize_admin_has_full_access(self, jwt_provider: JWTAuthProvider) -> None:
        """Test that admin users have full access."""
        token = jwt_provider.create_access_token(
            user_id="admin-123",
            username="admin",
            roles=["admin"],
            permissions=[],
        )
        user = await jwt_provider.authenticate(token)

        assert await jwt_provider.authorize(user, "dataset:123", "delete")
        assert await jwt_provider.authorize(user, "pipeline:456", "execute")
        assert await jwt_provider.authorize(user, "anything", "everything")

    @pytest.mark.asyncio
    async def test_authorize_with_exact_permission(
        self, jwt_provider: JWTAuthProvider
    ) -> None:
        """Test authorization with exact permission match."""
        token = jwt_provider.create_access_token(
            user_id="user-123",
            username="user",
            roles=["developer"],
            permissions=["dataset:read", "pipeline:execute"],
        )
        user = await jwt_provider.authenticate(token)

        assert await jwt_provider.authorize(user, "dataset", "read")
        assert await jwt_provider.authorize(user, "pipeline", "execute")
        assert not await jwt_provider.authorize(user, "dataset", "delete")
        assert not await jwt_provider.authorize(user, "user", "read")

    @pytest.mark.asyncio
    async def test_authorize_with_wildcard_permission(
        self, jwt_provider: JWTAuthProvider
    ) -> None:
        """Test authorization with wildcard permissions."""
        token = jwt_provider.create_access_token(
            user_id="user-123",
            username="user",
            roles=["developer"],
            permissions=["dataset:*"],  # All actions on datasets
        )
        user = await jwt_provider.authenticate(token)

        assert await jwt_provider.authorize(user, "dataset", "read")
        assert await jwt_provider.authorize(user, "dataset", "write")
        assert await jwt_provider.authorize(user, "dataset", "delete")
        assert not await jwt_provider.authorize(user, "pipeline", "execute")

    @pytest.mark.asyncio
    async def test_authorize_with_full_wildcard(
        self, jwt_provider: JWTAuthProvider
    ) -> None:
        """Test authorization with full wildcard permission."""
        token = jwt_provider.create_access_token(
            user_id="user-123",
            username="superuser",
            roles=["user"],
            permissions=["*"],
        )
        user = await jwt_provider.authenticate(token)

        assert await jwt_provider.authorize(user, "anything", "everything")
        assert await jwt_provider.authorize(user, "dataset", "delete")

    @pytest.mark.asyncio
    async def test_refresh_token(self, jwt_provider: JWTAuthProvider) -> None:
        """Test refreshing tokens."""
        refresh_token = jwt_provider.create_refresh_token(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            roles=["developer"],
            permissions=["dataset:read"],
        )

        new_access, new_refresh = await jwt_provider.refresh_token(refresh_token)

        assert new_access is not None
        assert new_refresh is not None

        # Verify new access token works
        user = await jwt_provider.authenticate(new_access)
        assert user.id == "user-123"

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, jwt_provider: JWTAuthProvider) -> None:
        """Test refreshing with an invalid token."""
        with pytest.raises(JWTError):
            await jwt_provider.refresh_token("invalid-refresh-token")

    @pytest.mark.asyncio
    async def test_get_row_filter_returns_none_by_default(
        self, jwt_provider: JWTAuthProvider
    ) -> None:
        """Test that get_row_filter returns None by default."""
        token = jwt_provider.create_access_token(
            user_id="user-123",
            username="user",
        )
        user = await jwt_provider.authenticate(token)

        filter_result = await jwt_provider.get_row_filter(user, "employee")
        assert filter_result is None
