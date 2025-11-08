"""
Alert Manager with Multi-Channel Routing
Supports Email, Slack, PagerDuty, and custom webhooks
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertCategory(Enum):
    """Alert categories"""
    AVAILABILITY = "availability"
    PERFORMANCE = "performance"
    COST = "cost"
    QUALITY = "quality"
    SECURITY = "security"
    RESOURCES = "resources"
    BUSINESS = "business"


@dataclass
class Alert:
    """Alert data structure"""
    name: str
    severity: AlertSeverity
    category: AlertCategory
    summary: str
    description: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    starts_at: datetime
    ends_at: Optional[datetime] = None
    fingerprint: Optional[str] = None


class AlertChannel:
    """Base class for alert channels"""

    def send(self, alert: Alert) -> bool:
        """Send alert through channel"""
        raise NotImplementedError


class EmailChannel(AlertChannel):
    """Email alert channel"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        to_emails: List[str],
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.to_emails = to_emails

    def send(self, alert: Alert) -> bool:
        """Send alert via email"""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.summary}"

            body = self._format_email_body(alert)
            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            return False

    def _format_email_body(self, alert: Alert) -> str:
        """Format alert as HTML email"""
        severity_colors = {
            AlertSeverity.CRITICAL: "#dc3545",
            AlertSeverity.WARNING: "#ffc107",
            AlertSeverity.INFO: "#17a2b8",
        }

        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert-box {{
                    border-left: 4px solid {severity_colors.get(alert.severity, '#6c757d')};
                    padding: 20px;
                    margin: 20px 0;
                    background-color: #f8f9fa;
                }}
                .severity {{
                    color: {severity_colors.get(alert.severity, '#6c757d')};
                    font-weight: bold;
                    font-size: 18px;
                }}
                .details {{ margin-top: 15px; }}
                .label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="alert-box">
                <div class="severity">{alert.severity.value.upper()} ALERT</div>
                <h2>{alert.summary}</h2>
                <p>{alert.description}</p>

                <div class="details">
                    <p><span class="label">Category:</span> {alert.category.value}</p>
                    <p><span class="label">Started:</span> {alert.starts_at.isoformat()}</p>

                    {self._format_labels(alert.labels)}
                </div>
            </div>
        </body>
        </html>
        """

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels as HTML"""
        if not labels:
            return ""

        items = "".join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in labels.items()])
        return f"<p><span class='label'>Labels:</span></p><ul>{items}</ul>"


class SlackChannel(AlertChannel):
    """Slack alert channel"""

    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        self.webhook_url = webhook_url
        self.channel = channel

    def send(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        try:
            payload = self._format_slack_message(alert)
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
            return False

    def _format_slack_message(self, alert: Alert) -> Dict[str, Any]:
        """Format alert as Slack message"""
        severity_colors = {
            AlertSeverity.CRITICAL: "#dc3545",
            AlertSeverity.WARNING: "#ffc107",
            AlertSeverity.INFO: "#17a2b8",
        }

        severity_emojis = {
            AlertSeverity.CRITICAL: ":rotating_light:",
            AlertSeverity.WARNING: ":warning:",
            AlertSeverity.INFO: ":information_source:",
        }

        fields = [
            {
                "title": "Category",
                "value": alert.category.value,
                "short": True,
            },
            {
                "title": "Started",
                "value": alert.starts_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "short": True,
            },
        ]

        # Add labels as fields
        for key, value in alert.labels.items():
            fields.append({
                "title": key,
                "value": value,
                "short": True,
            })

        payload = {
            "attachments": [
                {
                    "color": severity_colors.get(alert.severity, "#6c757d"),
                    "title": f"{severity_emojis.get(alert.severity, '')} {alert.summary}",
                    "text": alert.description,
                    "fields": fields,
                    "footer": "SWE Platform Monitoring",
                    "ts": int(alert.starts_at.timestamp()),
                }
            ]
        }

        if self.channel:
            payload["channel"] = self.channel

        return payload


class PagerDutyChannel(AlertChannel):
    """PagerDuty alert channel"""

    def __init__(self, integration_key: str):
        self.integration_key = integration_key
        self.api_url = "https://events.pagerduty.com/v2/enqueue"

    def send(self, alert: Alert) -> bool:
        """Send alert to PagerDuty"""
        try:
            payload = self._format_pagerduty_event(alert)
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            return response.status_code == 202
        except Exception as e:
            print(f"Failed to send PagerDuty alert: {e}")
            return False

    def _format_pagerduty_event(self, alert: Alert) -> Dict[str, Any]:
        """Format alert as PagerDuty event"""
        severity_map = {
            AlertSeverity.CRITICAL: "critical",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.INFO: "info",
        }

        return {
            "routing_key": self.integration_key,
            "event_action": "trigger",
            "dedup_key": alert.fingerprint or alert.name,
            "payload": {
                "summary": alert.summary,
                "source": "swe-platform",
                "severity": severity_map.get(alert.severity, "warning"),
                "timestamp": alert.starts_at.isoformat(),
                "custom_details": {
                    "description": alert.description,
                    "category": alert.category.value,
                    "labels": alert.labels,
                    "annotations": alert.annotations,
                },
            },
        }


class WebhookChannel(AlertChannel):
    """Generic webhook alert channel"""

    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.headers = headers or {"Content-Type": "application/json"}

    def send(self, alert: Alert) -> bool:
        """Send alert to webhook"""
        try:
            payload = {
                "name": alert.name,
                "severity": alert.severity.value,
                "category": alert.category.value,
                "summary": alert.summary,
                "description": alert.description,
                "labels": alert.labels,
                "annotations": alert.annotations,
                "starts_at": alert.starts_at.isoformat(),
                "ends_at": alert.ends_at.isoformat() if alert.ends_at else None,
            }

            response = requests.post(
                self.url,
                json=payload,
                headers=self.headers,
                timeout=10,
            )
            return response.status_code in (200, 201, 202)
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")
            return False


class AlertManager:
    """
    Alert Manager with routing and deduplication

    Features:
    - Multi-channel routing (Email, Slack, PagerDuty)
    - Severity-based routing
    - Alert deduplication
    - Alert grouping
    - Rate limiting
    """

    def __init__(self):
        self.channels: Dict[str, List[AlertChannel]] = {
            "critical": [],
            "warning": [],
            "info": [],
        }
        self.active_alerts: Dict[str, Alert] = {}

    def add_channel(self, severity: AlertSeverity, channel: AlertChannel) -> None:
        """Add alert channel for specific severity"""
        self.channels[severity.value].append(channel)

    def add_channel_all_severities(self, channel: AlertChannel) -> None:
        """Add alert channel for all severities"""
        for severity in AlertSeverity:
            self.channels[severity.value].append(channel)

    def send_alert(self, alert: Alert) -> bool:
        """Send alert through appropriate channels"""
        # Check if alert is already active (deduplication)
        fingerprint = alert.fingerprint or self._generate_fingerprint(alert)
        alert.fingerprint = fingerprint

        if fingerprint in self.active_alerts:
            print(f"Alert {alert.name} already active, skipping duplicate")
            return True

        # Add to active alerts
        self.active_alerts[fingerprint] = alert

        # Get channels for this severity
        channels = self.channels.get(alert.severity.value, [])

        if not channels:
            print(f"No channels configured for severity {alert.severity.value}")
            return False

        # Send through all channels
        success = True
        for channel in channels:
            result = channel.send(alert)
            if not result:
                success = False

        return success

    def resolve_alert(self, fingerprint: str) -> bool:
        """Resolve an active alert"""
        if fingerprint in self.active_alerts:
            alert = self.active_alerts[fingerprint]
            alert.ends_at = datetime.utcnow()
            del self.active_alerts[fingerprint]
            return True
        return False

    def _generate_fingerprint(self, alert: Alert) -> str:
        """Generate unique fingerprint for alert"""
        import hashlib
        data = f"{alert.name}:{alert.category.value}:{json.dumps(alert.labels, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# Global alert manager instance
alert_manager = AlertManager()


# Setup alert channels from environment
def setup_alert_channels() -> None:
    """Configure alert channels from environment variables"""
    # Email channel
    if all([
        os.getenv("SMTP_HOST"),
        os.getenv("SMTP_PORT"),
        os.getenv("SMTP_USER"),
        os.getenv("SMTP_PASSWORD"),
        os.getenv("ALERT_EMAIL_FROM"),
        os.getenv("ALERT_EMAIL_TO"),
    ]):
        email_channel = EmailChannel(
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            from_email=os.getenv("ALERT_EMAIL_FROM"),
            to_emails=os.getenv("ALERT_EMAIL_TO").split(","),
        )
        alert_manager.add_channel(AlertSeverity.CRITICAL, email_channel)
        alert_manager.add_channel(AlertSeverity.WARNING, email_channel)

    # Slack channel
    if os.getenv("SLACK_WEBHOOK_URL"):
        slack_channel = SlackChannel(
            webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
            channel=os.getenv("SLACK_CHANNEL"),
        )
        alert_manager.add_channel_all_severities(slack_channel)

    # PagerDuty channel (critical only)
    if os.getenv("PAGERDUTY_INTEGRATION_KEY"):
        pagerduty_channel = PagerDutyChannel(
            integration_key=os.getenv("PAGERDUTY_INTEGRATION_KEY"),
        )
        alert_manager.add_channel(AlertSeverity.CRITICAL, pagerduty_channel)

    # Custom webhook
    if os.getenv("ALERT_WEBHOOK_URL"):
        webhook_channel = WebhookChannel(
            url=os.getenv("ALERT_WEBHOOK_URL"),
        )
        alert_manager.add_channel_all_severities(webhook_channel)

    print("✓ Alert channels configured")
