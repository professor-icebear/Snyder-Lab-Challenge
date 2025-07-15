from sqlalchemy.orm import Session
from app.models.raw_data import RawData
from datetime import datetime, timedelta
import pandas as pd
from typing import List

def impute_linear_interpolation(db: Session, user_id: int, metric_name: str, start_date: datetime, end_date: datetime, frequency: str = '1T'):
    """
    Performs linear interpolation for missing data points for a given user and metric.
    'frequency' determines the expected interval between data points (e.g., '1T' for 1 minute).
    """
    # Fetch existing data
    query = db.query(RawData).filter(
        RawData.user_id == user_id,
        RawData.metric_name == metric_name,
        RawData.timestamp >= start_date,
        RawData.timestamp <= end_date
    ).order_by(RawData.timestamp)
    
    existing_data = query.all()

    if not existing_data:
        # No data to interpolate from
        return 0

    # Convert to pandas DataFrame
    df = pd.DataFrame([(d.timestamp, d.value) for d in existing_data], columns=['timestamp', 'value'])
    df.set_index('timestamp', inplace=True)
    
    # Create a full date range at the desired frequency
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq=frequency)
    
    # Reindex the dataframe to introduce NaNs for missing timestamps
    df_reindexed = df.reindex(full_range)
    
    # Perform linear interpolation
    df_interpolated = df_reindexed.interpolate(method='linear')
    
    # Identify the imputed points
    imputed_points_df = df_interpolated[df_reindexed['value'].isnull()]
    
    imputed_count = 0
    new_data_points = []
    for timestamp, row in imputed_points_df.iterrows():
        new_data = RawData(
            user_id=user_id,
            timestamp=timestamp.to_pydatetime(),
            metric_name=metric_name,
            value=row['value'],
            is_imputed=True,
            imputation_method='linear_interpolation',
            imputed_at=datetime.utcnow()
        )
        new_data_points.append(new_data)
        imputed_count += 1
        
    if new_data_points:
        db.add_all(new_data_points)
        db.commit()

    return imputed_count 