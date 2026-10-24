from fastapi import APIRouter, Query

from services.metrics_service import metrics

router = APIRouter()


@router.get("/workflow-metrics")
def get_metrics(granularity: str = Query("daily", pattern="^(hourly|daily|weekly|monthly)$")):
    return metrics(granularity)
