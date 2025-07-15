from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.core.config import settings
from app.db.database import db_manager
from app.schemas.metrics import (
    MetricResponse, 
    MetricDataPoint, 
    AvailableMetrics, 
    HealthResponse
)
from app.db.queries import (
    get_metrics_data,
    get_available_metrics,
    get_available_users,
    get_metric_summary,
    get_data_count
)
from app.api import participants
from app.api import adherence
from app.api import imputation
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for accessing Fitbit data from TimescaleDB"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(participants.router, prefix="/api")
app.include_router(adherence.router, prefix="/api")
app.include_router(imputation.router, prefix="/api")

# Prometheus metrics
ingestion_error_count = Counter(
    'ingestion_error_count', 'Number of ingestion errors encountered by the API')
ingestion_latency_seconds = Histogram(
    'ingestion_latency_seconds', 'Latency of ingestion operations in seconds')

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    logger.info("Starting up FastAPI application...")
    if not db_manager.health_check():
        logger.error("Database connection failed on startup")
        raise Exception("Database connection failed")
    db_manager.create_continuous_aggregates()

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Fitbit Data API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    db_healthy = db_manager.health_check()
    return HealthResponse(
        status="healthy" if db_healthy else "unhealthy",
        database=db_healthy,
        timestamp=datetime.now()
    )

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/metrics", response_model=MetricResponse, tags=["Metrics"])
async def get_metrics(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    user_id: int = Query(..., description="User ID"),
    metric: str = Query(..., description="Metric name"),
    granularity: Optional[str] = Query(None, description="Granularity: raw, minute, hour, day")
):
    """
    Get metric data for a specific user and time range, with optional granularity
    """
    start_time = time.time()
    try:
        # Validate date range
        if start_date >= end_date:
            raise HTTPException(
                status_code=400, 
                detail="Start date must be before end date"
            )
        
        # Get data from database
        raw_data = get_metrics_data(start_date, end_date, user_id, metric, granularity)
        
        # Convert to response format
        data_points = []
        for row in raw_data:
            data_points.append(MetricDataPoint(
                timestamp=row.get('ts'),
                value=float(row.get('avg_value', row.get('value', 0))),
                metric_name=row.get('metric_name'),
                user_id=row.get('user_id')
            ))
        
        return MetricResponse(
            data=data_points,
            count=len(data_points),
            metric=metric,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
    except Exception as e:
        ingestion_error_count.inc()
        logger.error(f"Error in get_metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        elapsed = time.time() - start_time
        ingestion_latency_seconds.observe(elapsed)

@app.get("/api/metrics/available", response_model=AvailableMetrics, tags=["Metrics"])
async def get_available_metrics_and_users():
    """
    Get list of available metrics and users
    """
    try:
        metrics = get_available_metrics()
        users = get_available_users()
        
        return AvailableMetrics(
            metrics=metrics,
            users=users
        )
        
    except Exception as e:
        logger.error(f"Error in get_available_metrics_and_users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats", tags=["Stats"])
async def get_stats():
    """
    Get basic statistics about the database
    """
    try:
        total_records = get_data_count()
        metrics = get_available_metrics()
        users = get_available_users()
        
        return {
            "total_records": total_records,
            "available_metrics": len(metrics),
            "available_users": len(users),
            "metrics": metrics,
            "users": users
        }
        
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    ) 