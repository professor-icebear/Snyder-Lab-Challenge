from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MetricQuery(BaseModel):
    """Schema for metric query parameters"""
    start_date: datetime = Field(..., description="Start date for data range")
    end_date: datetime = Field(..., description="End date for data range")
    user_id: int = Field(..., description="User ID to query data for")
    metric: str = Field(..., description="Metric name to retrieve")

class MetricDataPoint(BaseModel):
    """Schema for a single metric data point"""
    timestamp: datetime
    value: float
    metric_name: str
    user_id: int

class MetricResponse(BaseModel):
    """Schema for metric query response"""
    data: List[MetricDataPoint]
    count: int
    metric: str
    user_id: int
    start_date: datetime
    end_date: datetime

class AvailableMetrics(BaseModel):
    """Schema for available metrics response"""
    metrics: List[str]
    users: List[int]

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    database: bool
    timestamp: datetime 