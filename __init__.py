"""
Database utilities for Medical Chatbot
Provides helper functions for database operations, connection management, and query optimization
"""

import logging
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect, func
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseHelper:
    """
    Helper class for database operations
    Provides utility methods for common database tasks
    """
    
    def __init__(self, db: SQLAlchemy):
        """
        Initialize database helper
        
        Args:
            db: SQLAlchemy database instance
        """
        self.db = db
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions
        Automatically commits on success, rolls back on error
        
        Usage:
            with db_helper.transaction():
                # perform database operations
                db.session.add(something)
        """
        try:
            yield
            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
    
    def execute_raw_sql(self, sql: str, params: Dict = None) -> List[Dict]:
        """
        Execute raw SQL query and return results as list of dictionaries
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries representing rows
        """
        try:
            result = self.db.session.execute(text(sql), params or {})
            if result.returns_rows:
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
            return []
        except SQLAlchemyError as e:
            logger.error(f"SQL execution error: {e}")
            raise
    
    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table statistics
        """
        try:
            # Get row count
            count_result = self.execute_raw_sql(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = count_result[0]['count'] if count_result else 0
            
            # Get table info
            inspector = inspect(self.db.engine)
            columns = inspector.get_columns(table_name)
            
            return {
                'table_name': table_name,
                'row_count': row_count,
                'columns': len(columns),
                'column_names': [col['name'] for col in columns]
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {table_name}: {e}")
            return {'table_name': table_name, 'error': str(e)}
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Delete sessions older than specified days
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of deleted sessions
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            from models import UserSession
            
            deleted = UserSession.query.filter(
                UserSession.last_active < cutoff_date
            ).delete()
            
            self.db.session.commit()
            logger.info(f"Deleted {deleted} old sessions")
            return deleted
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
            self.db.session.rollback()
            return 0
    
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """
        Get daily conversation statistics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of daily statistics
        """
        try:
            from models import Conversation
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            results = self.db.session.query(
                func.date(Conversation.created_at).label('date'),
                func.count(Conversation.id).label('total_messages'),
                func.count(func.distinct(Conversation.session_id)).label('unique_sessions'),
                func.avg(Conversation.response_time_ms).label('avg_response_time'),
                func.sum(func.cast(Conversation.is_emergency, func.integer)).label('emergency_count')
            ).filter(
                Conversation.created_at >= cutoff_date
            ).group_by(
                func.date(Conversation.created_at)
            ).order_by(
                func.date(Conversation.created_at).desc()
            ).all()
            
            return [{
                'date': str(r.date),
                'total_messages': r.total_messages,
                'unique_sessions': r.unique_sessions,
                'avg_response_time': int(r.avg_response_time) if r.avg_response_time else 0,
                'emergency_count': r.emergency_count or 0
            } for r in results]
        except Exception as e:
            logger.error(f"Failed to get daily stats: {e}")
            return []
    
    def get_intent_distribution(self) -> Dict[str, int]:
        """
        Get distribution of detected intents
        
        Returns:
            Dictionary mapping intent to count
        """
        try:
            from models import Conversation
            
            results = self.db.session.query(
                Conversation.intent,
                func.count(Conversation.id).label('count')
            ).group_by(
                Conversation.intent
            ).all()
            
            return {r.intent: r.count for r in results}
        except Exception as e:
            logger.error(f"Failed to get intent distribution: {e}")
            return {}
    
    def vacuum_database(self):
        """
        Optimize database (SQLite only)
        """
        try:
            if 'sqlite' in str(self.db.engine.url):
                self.execute_raw_sql("VACUUM")
                logger.info("Database vacuum completed")
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")


def init_db(app, db):
    """
    Initialize database with helper
    
    Args:
        app: Flask application
        db: SQLAlchemy instance
    """
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Return database helper
            return DatabaseHelper(db)
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise