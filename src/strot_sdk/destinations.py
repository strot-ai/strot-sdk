"""
STROT SDK — Destinations

Send notifications and data to external services via the STROT API.
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EmailDestination:
    """Send emails via STROT."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from .client import StrotClient
            self._client = StrotClient()
        return self._client

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Plain text body
            html: Optional HTML body
            cc: CC recipients
            bcc: BCC recipients

        Returns:
            Send result
        """
        client = self._get_client()
        return client.send_email(
            to=to, subject=subject, body=body,
            html=html, cc=cc, bcc=bcc,
        )


class SlackDestination:
    """Send Slack messages via STROT."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from .client import StrotClient
            self._client = StrotClient()
        return self._client

    def send(
        self,
        channel: str,
        message: str,
        blocks: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Send a Slack message.

        Args:
            channel: Slack channel name or ID
            message: Message text
            blocks: Optional Slack blocks for rich formatting

        Returns:
            Send result
        """
        client = self._get_client()
        return client.send_slack(
            channel=channel, message=message, blocks=blocks,
        )


class WebhookDestination:
    """Send HTTP requests via STROT."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from .client import StrotClient
            self._client = StrotClient()
        return self._client

    def post(
        self,
        url: str,
        data: Any,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send a POST webhook."""
        client = self._get_client()
        return client.send_webhook(url=url, data_payload=data, headers=headers, method="POST")

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send a GET webhook."""
        client = self._get_client()
        return client.send_webhook(url=url, data_payload=None, headers=headers, method="GET")

    def put(
        self,
        url: str,
        data: Any,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send a PUT webhook."""
        client = self._get_client()
        return client.send_webhook(url=url, data_payload=data, headers=headers, method="PUT")


# Default instances
email = EmailDestination()
slack = SlackDestination()
webhook = WebhookDestination()
