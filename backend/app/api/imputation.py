from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from app.services.imputation import impute_linear_interpolation
from app.api.participants import get_db_session # Reusing the db session from participants api

router = APIRouter(prefix="/impute", tags=["Imputation"])

class ImputationRequest(BaseModel):
    user_id: int
    metric_name: str
    start_date: datetime
    end_date: datetime
    frequency: str = '1T' # Default to 1 minute frequency

@router.post("/", status_code=200)
def impute_data(
    request: ImputationRequest,
    db: Session = Depends(get_db_session)
):
    """
    Triggers the data imputation process for a user, metric, and time range.
    """
    try:
        imputed_count = impute_linear_interpolation(
            db=db,
            user_id=request.user_id,
            metric_name=request.metric_name,
            start_date=request.start_date,
            end_date=request.end_date,
            frequency=request.frequency
        )
        return {"message": f"Imputation successful. {imputed_count} points were imputed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 