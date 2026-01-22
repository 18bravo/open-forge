"""Notification channels - Email, Slack, Webhook delivery."""

from abc import ABC, abstractmethod
from typing import Any
import logging

import httpx
from jinja2 import Template
from pydantic import BaseModel

from forge_collab.alerts.rules import Severity


logger = logging.getLogger(__name__)


class Notification(BaseModel):
    """Notification payload to be sent via channels."""

    id: str
    title: str
    message: str
    severity: Severity = Severity.INFO
    resource_type: str | None = None
    resource_id: str | None = None
    resource_url: str | None = None
    metadata: dict[str, Any] = {}


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Channel name identifier."""
        ...

    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Send a notification through this channel.

        Args:
            notification: The notification to send

        Returns:
            True if sent successfully, False otherwise
        """
        ...

    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate that the channel is properly configured.

        Returns:
            True if configuration is valid
        """
        ...


class EmailChannel(NotificationChannel):
    """Email notification channel.

    Scaffold implementation - full version requires SMTP configuration
    or email service integration (SendGrid, SES, etc.).
    """

    def __init__(
        self,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        from_address: str = "",
        template: str | None = None,
    ):
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._smtp_user = smtp_user
        self._smtp_password = smtp_password
        self._from_address = from_address
        self._template = Template(template) if template else self._default_template()

    @property
    def name(self) -> str:
        return "email"

    def _default_template(self) -> Template:
        return Template("""
<html>
<body>
<h2>{{ title }}</h2>
<p>{{ message }}</p>
{% if resource_type and resource_id %}
<p><strong>Resource:</strong> {{ resource_type }}/{{ resource_id }}</p>
{% endif %}
{% if resource_url %}
<p><a href="{{ resource_url }}">View Resource</a></p>
{% endif %}
</body>
</html>
        """.strip())

    async def send(self, notification: Notification) -> bool:
        """Send email notification.

        Args:
            notification: The notification to send

        Returns:
            True if sent successfully
        """
        # Render email body
        body = self._template.render(
            title=notification.title,
            message=notification.message,
            severity=notification.severity.value,
            resource_type=notification.resource_type,
            resource_id=notification.resource_id,
            resource_url=notification.resource_url,
            **notification.metadata,
        )

        # TODO: Implement actual email sending with smtplib or email service
        logger.info(f"[EMAIL] Would send: {notification.title}")
        raise NotImplementedError("Email sending not implemented")

    async def validate_config(self) -> bool:
        """Validate email configuration."""
        return bool(self._smtp_host and self._from_address)


class SlackChannel(NotificationChannel):
    """Slack notification channel via webhook."""

    SEVERITY_COLORS = {
        Severity.INFO: "#36a64f",
        Severity.WARNING: "#ffcc00",
        Severity.ERROR: "#ff6600",
        Severity.CRITICAL: "#ff0000",
    }

    def __init__(self, webhook_url: str):
        self._webhook_url = webhook_url

    @property
    def name(self) -> str:
        return "slack"

    async def send(self, notification: Notification) -> bool:
        """Send Slack notification via webhook.

        Args:
            notification: The notification to send

        Returns:
            True if sent successfully
        """
        color = self.SEVERITY_COLORS.get(notification.severity, "#36a64f")

        fields = []
        if notification.resource_type and notification.resource_id:
            fields.append({
                "title": "Resource",
                "value": f"{notification.resource_type}/{notification.resource_id}",
                "short": True,
            })
        fields.append({
            "title": "Severity",
            "value": notification.severity.value.upper(),
            "short": True,
        })

        payload = {
            "attachments": [{
                "color": color,
                "title": notification.title,
                "text": notification.message,
                "fields": fields,
            }]
        }

        if notification.resource_url:
            payload["attachments"][0]["title_link"] = notification.resource_url

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._webhook_url,
                    json=payload,
                    timeout=10.0,
                )
                response.raise_for_status()
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    async def validate_config(self) -> bool:
        """Validate Slack webhook URL."""
        return bool(
            self._webhook_url
            and self._webhook_url.startswith("https://hooks.slack.com/")
        )


class WebhookChannel(NotificationChannel):
    """Generic webhook notification channel."""

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        method: str = "POST",
    ):
        self._url = url
        self._headers = headers or {}
        self._method = method

    @property
    def name(self) -> str:
        return "webhook"

    async def send(self, notification: Notification) -> bool:
        """Send notification to webhook endpoint.

        Args:
            notification: The notification to send

        Returns:
            True if sent successfully
        """
        payload = {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "severity": notification.severity.value,
            "resource_type": notification.resource_type,
            "resource_id": notification.resource_id,
            "metadata": notification.metadata,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=self._method,
                    url=self._url,
                    json=payload,
                    headers=self._headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False

    async def validate_config(self) -> bool:
        """Validate webhook URL."""
        return bool(self._url and self._url.startswith(("http://", "https://")))
