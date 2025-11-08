"""
Observability Integration

Provides integration with observability platforms:
- Datadog APM integration
- Grafana dashboard creation
- Metrics push
- Alert webhook handling
"""

import time
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class ObservabilityClient:
    """
    Observability platform client

    Supports Datadog and Grafana integrations for
    monitoring, metrics, and alerting.
    """

    def __init__(
        self,
        datadog_api_key: Optional[str] = None,
        datadog_app_key: Optional[str] = None,
        datadog_site: str = "datadoghq.com",
        grafana_url: Optional[str] = None,
        grafana_api_key: Optional[str] = None,
    ):
        """
        Initialize observability client

        Args:
            datadog_api_key: Datadog API key
            datadog_app_key: Datadog application key
            datadog_site: Datadog site (e.g., datadoghq.com, datadoghq.eu)
            grafana_url: Grafana instance URL
            grafana_api_key: Grafana API key
        """
        self.datadog_api_key = datadog_api_key
        self.datadog_app_key = datadog_app_key
        self.datadog_base = f"https://api.{datadog_site}"

        self.grafana_url = grafana_url
        self.grafana_api_key = grafana_api_key

    def _get_datadog_headers(self) -> Dict[str, str]:
        """Get Datadog API headers"""
        return {
            "DD-API-KEY": self.datadog_api_key or "",
            "DD-APPLICATION-KEY": self.datadog_app_key or "",
        }

    def _get_grafana_headers(self) -> Dict[str, str]:
        """Get Grafana API headers"""
        return {
            "Authorization": f"Bearer {self.grafana_api_key}",
            "Content-Type": "application/json",
        }

    # Datadog Metrics

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def send_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[List[str]] = None,
        metric_type: str = "gauge",
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Send metric to Datadog

        Args:
            metric_name: Metric name (e.g., "agent.execution.duration")
            value: Metric value
            tags: List of tags (e.g., ["env:prod", "team:ai"])
            metric_type: Metric type ("gauge", "count", "rate")
            timestamp: Unix timestamp (defaults to now)

        Returns:
            API response
        """
        url = f"{self.datadog_base}/api/v2/series"
        headers = self._get_datadog_headers()

        if timestamp is None:
            timestamp = int(time.time())

        payload = {
            "series": [
                {
                    "metric": metric_name,
                    "type": 0 if metric_type == "gauge" else 1,  # 0=gauge, 1=count, 2=rate
                    "points": [
                        {
                            "timestamp": timestamp,
                            "value": value,
                        }
                    ],
                    "tags": tags or [],
                }
            ]
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def send_metrics_batch(
        self,
        metrics: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Send multiple metrics to Datadog

        Args:
            metrics: List of metric dicts with name, value, tags, etc.

        Returns:
            API response
        """
        url = f"{self.datadog_base}/api/v2/series"
        headers = self._get_datadog_headers()

        series = []
        for metric in metrics:
            timestamp = metric.get("timestamp", int(time.time()))
            series.append({
                "metric": metric["name"],
                "type": 0 if metric.get("type", "gauge") == "gauge" else 1,
                "points": [{"timestamp": timestamp, "value": metric["value"]}],
                "tags": metric.get("tags", []),
            })

        payload = {"series": series}

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    # Datadog Events

    async def send_event(
        self,
        title: str,
        text: str,
        tags: Optional[List[str]] = None,
        alert_type: str = "info",
        priority: str = "normal",
    ) -> Dict[str, Any]:
        """
        Send event to Datadog

        Args:
            title: Event title
            text: Event description (markdown)
            tags: List of tags
            alert_type: Alert type ("error", "warning", "info", "success")
            priority: Priority ("normal" or "low")

        Returns:
            Created event data
        """
        url = f"{self.datadog_base}/api/v1/events"
        headers = self._get_datadog_headers()

        payload = {
            "title": title,
            "text": text,
            "tags": tags or [],
            "alert_type": alert_type,
            "priority": priority,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    # Datadog Logs

    async def send_log(
        self,
        message: str,
        service: str,
        level: str = "info",
        tags: Optional[Dict[str, str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send log to Datadog

        Args:
            message: Log message
            service: Service name
            level: Log level ("debug", "info", "warn", "error")
            tags: Tag dictionary
            attributes: Additional attributes

        Returns:
            API response
        """
        url = f"{self.datadog_base}/api/v2/logs"
        headers = self._get_datadog_headers()
        headers["Content-Type"] = "application/json"

        log_entry = {
            "message": message,
            "service": service,
            "ddsource": "agent",
            "ddtags": ",".join([f"{k}:{v}" for k, v in (tags or {}).items()]),
            "level": level,
        }

        if attributes:
            log_entry.update(attributes)

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, json=[log_entry])
            response.raise_for_status()
            return response.json()

    # Datadog APM

    async def get_service_metrics(
        self,
        service_name: str,
        start_time: int,
        end_time: int,
    ) -> Dict[str, Any]:
        """
        Get APM service metrics

        Args:
            service_name: Service name
            start_time: Start time (Unix timestamp)
            end_time: End time (Unix timestamp)

        Returns:
            Service metrics
        """
        url = f"{self.datadog_base}/api/v1/metrics/query"
        headers = self._get_datadog_headers()

        params = {
            "query": f"avg:trace.{service_name}.request.duration{{*}}",
            "from": start_time,
            "to": end_time,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    # Grafana Dashboards

    async def create_dashboard(
        self,
        title: str,
        panels: List[Dict[str, Any]],
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create Grafana dashboard

        Args:
            title: Dashboard title
            panels: List of panel configurations
            tags: Dashboard tags

        Returns:
            Created dashboard data
        """
        if not self.grafana_url:
            raise ValueError("Grafana URL not configured")

        url = f"{self.grafana_url}/api/dashboards/db"
        headers = self._get_grafana_headers()

        dashboard = {
            "dashboard": {
                "title": title,
                "tags": tags or [],
                "timezone": "browser",
                "panels": panels,
                "schemaVersion": 16,
                "version": 0,
            },
            "overwrite": False,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=dashboard)
            response.raise_for_status()
            return response.json()

    async def create_agent_dashboard(
        self,
        agent_name: str,
    ) -> Dict[str, Any]:
        """
        Create dashboard for agent monitoring

        Args:
            agent_name: Agent name

        Returns:
            Created dashboard data
        """
        panels = [
            {
                "id": 1,
                "title": "Execution Duration",
                "type": "graph",
                "targets": [
                    {
                        "expr": f'agent_execution_duration{{agent="{agent_name}"}}',
                        "refId": "A",
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
            },
            {
                "id": 2,
                "title": "Success Rate",
                "type": "stat",
                "targets": [
                    {
                        "expr": f'rate(agent_execution_success{{agent="{agent_name}"}}[5m])',
                        "refId": "A",
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
            },
            {
                "id": 3,
                "title": "Error Count",
                "type": "graph",
                "targets": [
                    {
                        "expr": f'agent_execution_errors{{agent="{agent_name}"}}',
                        "refId": "A",
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
            },
        ]

        return await self.create_dashboard(
            title=f"Agent: {agent_name}",
            panels=panels,
            tags=["agent", agent_name],
        )

    async def get_dashboard(
        self,
        dashboard_uid: str,
    ) -> Dict[str, Any]:
        """
        Get Grafana dashboard

        Args:
            dashboard_uid: Dashboard UID

        Returns:
            Dashboard data
        """
        if not self.grafana_url:
            raise ValueError("Grafana URL not configured")

        url = f"{self.grafana_url}/api/dashboards/uid/{dashboard_uid}"
        headers = self._get_grafana_headers()

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def delete_dashboard(
        self,
        dashboard_uid: str,
    ) -> Dict[str, Any]:
        """
        Delete Grafana dashboard

        Args:
            dashboard_uid: Dashboard UID

        Returns:
            Deletion result
        """
        if not self.grafana_url:
            raise ValueError("Grafana URL not configured")

        url = f"{self.grafana_url}/api/dashboards/uid/{dashboard_uid}"
        headers = self._get_grafana_headers()

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(url, headers=headers)
            response.raise_for_status()
            return response.json()

    # Alert Webhooks

    async def handle_alert_webhook(
        self,
        payload: Dict[str, Any],
        source: str = "datadog",
    ) -> Dict[str, Any]:
        """
        Handle incoming alert webhook

        Args:
            payload: Webhook payload
            source: Alert source ("datadog" or "grafana")

        Returns:
            Parsed alert data
        """
        if source == "datadog":
            return self._parse_datadog_alert(payload)
        elif source == "grafana":
            return self._parse_grafana_alert(payload)
        else:
            raise ValueError(f"Unknown alert source: {source}")

    def _parse_datadog_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Datadog alert webhook"""
        return {
            "source": "datadog",
            "title": payload.get("title"),
            "message": payload.get("body"),
            "alert_type": payload.get("alert_type"),
            "priority": payload.get("priority"),
            "tags": payload.get("tags", []),
            "timestamp": payload.get("date"),
        }

    def _parse_grafana_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Grafana alert webhook"""
        return {
            "source": "grafana",
            "title": payload.get("title"),
            "message": payload.get("message"),
            "state": payload.get("state"),
            "rule_url": payload.get("ruleUrl"),
            "tags": payload.get("tags", {}),
            "timestamp": payload.get("evalMatches", [{}])[0].get("timestamp"),
        }

    # Prometheus Integration (for custom metrics)

    async def push_to_prometheus(
        self,
        job_name: str,
        metrics: Dict[str, float],
        gateway_url: str,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Push metrics to Prometheus Pushgateway

        Args:
            job_name: Job name
            metrics: Dictionary of metric names to values
            gateway_url: Pushgateway URL
            labels: Additional labels
        """
        # Build Prometheus text format
        lines = []
        for metric_name, value in metrics.items():
            label_str = ""
            if labels:
                label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
                label_str = "{" + ",".join(label_pairs) + "}"

            lines.append(f"{metric_name}{label_str} {value}")

        body = "\n".join(lines)

        # Push to gateway
        url = f"{gateway_url}/metrics/job/{job_name}"

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, content=body)
            response.raise_for_status()
