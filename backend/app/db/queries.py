from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.db.database import db_manager
import logging

logger = logging.getLogger(__name__)

def select_table(start_date: datetime, end_date: datetime, granularity: Optional[str] = None) -> str:
    """
    Select the appropriate table/view based on time range or requested granularity
    """
    if granularity:
        mapping = {
            'raw': 'raw_data',
            'minute': 'data_1m',
            'hour': 'data_1h',
            'day': 'data_1d',
        }
        return mapping.get(granularity, 'data_1m')
    span = end_date - start_date
    if span < timedelta(days=2):
        return 'data_1m'
    elif span < timedelta(days=60):
        return 'data_1h'
    else:
        return 'data_1d'

def get_metrics_data(
    start_date: datetime,
    end_date: datetime,
    user_id: int,
    metric: str,
    granularity: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get metric data for a specific user and time range, using the appropriate aggregate
    """
    table = select_table(start_date, end_date, granularity)
    if table == 'raw_data':
        query = """
            SELECT 
                timestamp AS ts,
                value AS avg_value,
                metric_name,
                user_id
            FROM raw_data 
            WHERE user_id = %s 
            AND metric_name = %s 
            AND timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """
        params = (user_id, metric, start_date, end_date)
    else:
        query = f"""
            SELECT 
                bucket AS ts,
                avg_value,
                metric_name,
                user_id,
                min_value,
                max_value,
                data_points
            FROM {table}
            WHERE user_id = %s 
            AND metric_name = %s 
            AND bucket BETWEEN %s AND %s
            ORDER BY bucket ASC
        """
        params = (user_id, metric, start_date, end_date)
    try:
        results = db_manager.execute_query(query, params)
        logger.info(f"Retrieved {len(results)} records for metric {metric} from {table}")
        return results
    except Exception as e:
        logger.error(f"Error retrieving metrics data: {e}")
        raise

def get_available_metrics() -> List[str]:
    """
    Get list of available metrics in the database
    """
    query = """
        SELECT DISTINCT metric_name 
        FROM raw_data 
        ORDER BY metric_name
    """
    
    try:
        results = db_manager.execute_query(query)
        metrics = [row['metric_name'] for row in results]
        logger.info(f"Found {len(metrics)} available metrics")
        return metrics
    except Exception as e:
        logger.error(f"Error retrieving available metrics: {e}")
        raise

def get_available_users() -> List[int]:
    """
    Get list of available users in the database
    """
    query = """
        SELECT DISTINCT user_id 
        FROM raw_data 
        ORDER BY user_id
    """
    
    try:
        results = db_manager.execute_query(query)
        users = [row['user_id'] for row in results]
        logger.info(f"Found {len(users)} available users")
        return users
    except Exception as e:
        logger.error(f"Error retrieving available users: {e}")
        raise

def get_metric_summary(
    user_id: int,
    metric: str,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """
    Get summary statistics for a metric
    """
    query = """
        SELECT 
            COUNT(*) as count,
            AVG(value) as avg_value,
            MIN(value) as min_value,
            MAX(value) as max_value,
            STDDEV(value) as std_dev
        FROM raw_data 
        WHERE user_id = %s 
        AND metric_name = %s 
        AND timestamp BETWEEN %s AND %s
    """
    
    try:
        result = db_manager.execute_query_single(
            query, 
            (user_id, metric, start_date, end_date)
        )
        return result
    except Exception as e:
        logger.error(f"Error retrieving metric summary: {e}")
        raise

def get_data_count() -> int:
    """
    Get total number of records in the database
    """
    query = "SELECT COUNT(*) as count FROM raw_data"
    
    try:
        result = db_manager.execute_query_single(query)
        return result['count'] if result else 0
    except Exception as e:
        logger.error(f"Error retrieving data count: {e}")
        raise 