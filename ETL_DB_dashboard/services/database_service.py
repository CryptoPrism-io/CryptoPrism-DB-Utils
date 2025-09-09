#!/usr/bin/env python3
"""
Database Service Layer for CryptoPrism Dashboard

Provides centralized database connection management, query execution,
caching, and monitoring capabilities.
"""

import time
from typing import Dict, List, Optional, Tuple, Any
import sqlalchemy
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from datetime import datetime, timedelta

from config.settings import config


class DatabaseService:
    """Centralized database service with connection pooling and caching."""

    def __init__(self):
        """Initialize database service with connection pooling."""
        self._engine = None
        self._metadata = None
        self._inspector = None
        self._connection_status = False
        self._last_health_check = None

    @property
    def engine(self):
        """Get or create database engine."""
        if self._engine is None:
            try:
                self._engine = create_engine(
                    config.db_connection_string,
                    **config.db_pool_config
                )
                print(f"✅ Database engine initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize database engine: {str(e)}")
                raise

        return self._engine

    @property
    def inspector(self):
        """Get SQLAlchemy inspector for schema analysis."""
        if self._inspector is None:
            self._inspector = inspect(self.engine)
        return self._inspector

    def get_connection(self):
        """Get database connection with automatic recovery."""
        return self.engine.connect()

    def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            with self.get_connection() as conn:
                conn.execute(text("SELECT 1"))
            self._connection_status = True
            self._last_health_check = datetime.now()
            return True
        except Exception as e:
            print(f"❌ Database connection test failed: {str(e)}")
            self._connection_status = False
            return False

    def execute_query(self, query: str, params: Optional[Dict] = None,
                     timeout: int = None) -> List[Dict]:
        """
        Execute SELECT query with timeout and error handling.

        Args:
            query: SQL query string
            params: Query parameters
            timeout: Query timeout in seconds

        Returns:
            List of dictionaries containing query results
        """
        if timeout is None:
            timeout = config.get('query_timeout', 30)

        try:
            with self.get_connection() as conn:
                result = conn.execute(text(query).bindparams(**params) if params else text(query))

                # Set query timeout if supported
                if hasattr(conn, 'execute'):
                    conn.execute(text(f"SET statement_timeout = {timeout * 1000}"))

                rows = result.fetchall()

                # Convert to list of dictionaries
                if rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                return []

        except Exception as e:
            print(f"❌ Query execution failed: {str(e)}")
            raise SQLAlchemyError(f"Query failed: {str(e)}")

    def execute_query_single(self, query: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Execute query and return single result or None."""
        results = self.execute_query(query, params)
        return results[0] if results else None

    def execute_scalar(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute query and return scalar value."""
        try:
            with self.get_connection() as conn:
                result = conn.execute(text(query).bindparams(**params) if params else text(query))
                return result.scalar()
        except Exception as e:
            print(f"❌ Scalar query failed: {str(e)}")
            return None

    def get_table_exists(self, table_name: str, schema: str = 'public') -> bool:
        """Check if table exists."""
        try:
            return self.inspector.has_table(table_name, schema=schema)
        except Exception:
            return False

    def get_table_columns(self, table_name: str, schema: str = 'public') -> List[Dict]:
        """Get table column information."""
        try:
            return self.inspector.get_columns(table_name, schema=schema)
        except Exception as e:
            print(f"❌ Failed to get columns for {table_name}: {str(e)}")
            return []

    def get_table_count(self, table_name: str) -> int:
        """Get row count for table."""
        try:
            return self.execute_scalar(f'SELECT COUNT(*) FROM "{table_name}"') or 0
        except Exception:
            return 0

    def get_table_size(self, table_name: str) -> str:
        """Get table size in human readable format."""
        try:
            query = f"""
                SELECT pg_size_pretty(pg_total_relation_size('public."{table_name}"')) as table_size
            """
            return self.execute_scalar(query) or 'Unknown'
        except Exception:
            return 'Error'

    def get_primary_keys(self) -> List[Dict]:
        """Get all primary key constraints."""
        query = """
            SELECT
                n.nspname as schema_name,
                t.relname as table_name,
                c.conname as constraint_name,
                'PRIMARY KEY' as constraint_type
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE c.contype = 'p'
                AND n.nspname = 'public'
            ORDER BY t.relname
        """

        return self.execute_query(query)

    def get_tables_missing_pk(self) -> List[str]:
        """Get tables missing primary keys."""
        query = """
            SELECT t.table_name
            FROM information_schema.tables t
            LEFT JOIN information_schema.table_constraints tc
                ON t.table_name = tc.table_name
                AND tc.constraint_type = 'PRIMARY KEY'
            WHERE t.table_schema = 'public'
                AND t.table_type = 'BASE TABLE'
                AND tc.constraint_name IS NULL
            ORDER BY t.table_name
        """

        results = self.execute_query(query)
        return [row['table_name'] for row in results]

    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        try:
            stats_queries = {
                'total_tables': """
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """,
                'fe_tables': """
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name LIKE 'FE_%'
                """,
                'active_connections': """
                    SELECT count(*) FROM pg_stat_activity WHERE state = 'active'
                """,
                'database_size': """
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """
            }

            stats = {}
            for key, query in stats_queries.items():
                stats[key] = self.execute_scalar(query)

            # Add connection status
            stats['connection_healthy'] = self.test_connection()

            return stats

        except Exception as e:
            print(f"❌ Failed to get database stats: {str(e)}")
            return {
                'total_tables': 0,
                'fe_tables': 0,
                'active_connections': 0,
                'database_size': 'Unknown',
                'connection_healthy': False
            }

    def get_fe_tables_status(self) -> List[Dict]:
        """Get status of all FE tables."""
        fe_tables = [
            'FE_MOMENTUM_SIGNALS', 'FE_OSCILLATORS_SIGNALS', 'FE_RATIOS_SIGNALS',
            'FE_METRICS_SIGNAL', 'FE_TVV_SIGNALS', 'FE_DMV_ALL', 'FE_DMV_SCORES',
            'FE_MOMENTUM', 'FE_OSCILLATORS'
        ]

        return self._get_tables_status(fe_tables)

    def get_table_io_stats(self) -> List[Dict]:
        """Get table I/O statistics."""
        query = """
        SELECT
            relname as table_name,
            seq_scan, seq_tup_read, idx_scan, idx_tup_fetch,
            n_tup_ins, n_tup_upd, n_tup_del, n_tup_hot_upd
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY (seq_scan + idx_scan) DESC
        LIMIT 10
        """
        try:
            return self.execute_query(query)
        except Exception as e:
            print(f"❌ Failed to get table I/O stats: {str(e)}")
            return []

    def get_index_usage_stats(self) -> List[Dict]:
        """Get index usage statistics."""
        query = """
        SELECT
            relname as table_name,
            indexrelname as index_name,
            idx_scan, idx_tup_read, idx_tup_fetch,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        ORDER BY idx_scan ASC
        LIMIT 10
        """
        try:
            return self.execute_query(query)
        except Exception as e:
            print(f"❌ Failed to get index usage stats: {str(e)}")
            return []

    def get_long_running_queries(self) -> List[Dict]:
        """Get currently active long-running queries."""
        query = """
        SELECT
            pid,
            datname,
            usename,
            client_addr,
            application_name,
            backend_start,
            state,
            query,
            query_start,
            now() - query_start AS duration
        FROM pg_stat_activity
        WHERE state = 'active'
          AND usename <> 'postgres' -- Exclude system queries
          AND now() - query_start > INTERVAL '5 second' -- Queries running longer than 5 seconds
        ORDER BY duration DESC
        LIMIT 10
        """
        try:
            return self.execute_query(query)
        except Exception as e:
            print(f"❌ Failed to get long-running queries: {str(e)}")
            return []
    
    def _get_tables_status(self, table_names: List[str]) -> List[Dict]:
        """Get status information for specified tables."""
        results = []

        for table_name in table_names:
            try:
                exists = self.get_table_exists(table_name)
                if exists:
                    count = self.get_table_count(table_name)
                    table_size = self.get_table_size(table_name)

                    latest_update = self._get_latest_timestamp(table_name)

                    results.append({
                        'table_name': table_name,
                        'status': 'Active',
                        'row_count': count,
                        'table_size': table_size,
                        'last_update': latest_update,
                        'health': self._calculate_table_health(table_name, count, latest_update)
                    })
                else:
                    results.append({
                        'table_name': table_name,
                        'status': 'Missing',
                        'row_count': 0,
                        'table_size': 'N/A',
                        'last_update': None,
                        'health': 'Critical'
                    })

            except Exception as e:
                results.append({
                    'table_name': table_name,
                    'status': 'Error',
                    'row_count': 0,
                    'table_size': 'Error',
                    'last_update': None,
                    'health': 'Error',
                    'error_message': str(e)
                })

        return results

    def _get_latest_timestamp(self, table_name: str) -> Optional[datetime]:
        """Get latest timestamp from table."""
        timestamp_columns = ['updated_at', 'created_at', 'timestamp', 'last_updated', 'date']

        for col in timestamp_columns:
            try:
                query = f'SELECT MAX("{col}") FROM "{table_name}" WHERE "{col}" IS NOT NULL'
                result = self.execute_scalar(query)
                if result:
                    return result if isinstance(result, datetime) else None
            except:
                continue

        return None

    def _calculate_table_health(self, table_name: str, count: int,
                               last_update: Optional[datetime]) -> str:
        """Calculate table health based on data freshness and volume."""
        if count == 0:
            return 'Warning'  # Empty table

        if last_update:
            hours_old = (datetime.now() - last_update.replace(tzinfo=None)).total_seconds() / 3600
            if hours_old < 24:
                return 'Good'
            elif hours_old < 72:
                return 'Warning'
            else:
                return 'Critical'

        return 'Unknown'  # No timestamp data


# Global database service instance
db_service = DatabaseService()