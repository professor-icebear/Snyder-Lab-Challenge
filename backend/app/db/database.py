import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
from typing import Generator, Dict, Any, List
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection_pool = None
        self._init_pool()
    
    def _init_pool(self):
        """Initialize the connection pool"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASS,
                cursor_factory=RealDictCursor
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """Get a database connection from the pool"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    
    def execute_query_single(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """Execute a SELECT query and return single result"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
    
    def create_continuous_aggregates(self):
        """Create continuous aggregates if they don't exist"""
        aggregates = {
            "data_1m": "1 minute",
            "data_1h": "1 hour",
            "data_1d": "1 day"
        }
        with self.get_connection() as conn:
            # Set autocommit mode to run CREATE MATERIALIZED VIEW
            conn.autocommit = True
            try:
                with conn.cursor() as cursor:
                    for view_name, bucket_size in aggregates.items():
                        # Check if the continuous aggregate already exists in TimescaleDB's metadata
                        cursor.execute("SELECT 1 FROM timescaledb_information.continuous_aggregates WHERE view_name = %s", (view_name,))
                        if cursor.fetchone():
                            logger.info(f"Continuous aggregate '{view_name}' already exists.")
                            continue
                        
                        logger.info(f"Creating continuous aggregate: {view_name}")
                        query = f"""
                            CREATE MATERIALIZED VIEW {view_name}
                            WITH (timescaledb.continuous) AS
                            SELECT
                                user_id,
                                metric_name,
                                time_bucket('{bucket_size}', timestamp) AS bucket,
                                AVG(value) AS avg_value,
                                MIN(value) AS min_value,
                                MAX(value) AS max_value,
                                COUNT(*) as data_points
                            FROM raw_data
                            GROUP BY user_id, metric_name, bucket;
                        """
                        try:
                            cursor.execute(query)
                            logger.info(f"Successfully submitted creation for continuous aggregate '{view_name}'.")
                        except Exception as e:
                            logger.error(f"Failed to create continuous aggregate '{view_name}': {e}")
            finally:
                # Restore default autocommit behavior
                conn.autocommit = False


    def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager() 