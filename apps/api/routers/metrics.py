"""
Prometheus Metrics Endpoint
"""
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
from services.metrics_service import get_metrics_service

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_class=PlainTextResponse)
async def get_metrics():
    """
    Get Prometheus metrics
    
    Returns metrics in Prometheus format for scraping.
    """
    metrics_service = get_metrics_service()
    metrics_text = await metrics_service.get_metrics()
    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )

