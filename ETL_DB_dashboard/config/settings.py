#!/usr/bin/env python3
"""
Centralized Configuration Management for CryptoPrism Dashboard

Provides unified configuration handling for database connections,
authentication, caching, and system settings.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DashboardConfig:
    """Centralized configuration management for the dashboard."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        self._config = {}

        # Database Configuration
        self._config.update({
            'db_host': os.getenv('DB_HOST', 'localhost'),
            'db_user': os.getenv('DB_USER', 'postgres'),
            'db_password': os.getenv('DB_PASSWORD', ''),
            'db_port': os.getenv('DB_PORT', '5432'),
            'db_name': os.getenv('DB_NAME', 'dbcp'),
            'db_pool_size': int(os.getenv('DB_POOL_SIZE', '5')),
            'db_max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '10')),
            'db_pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '300')),  # 5 minutes
        })

        # Authentication
        self._config.update({
            'dashboard_password': os.getenv('DASHBOARD_PASSWORD', 'admin123'),
            'auth_timeout': int(os.getenv('AUTH_TIMEOUT', '3600')),  # 1 hour
            'enable_auth': os.getenv('ENABLE_AUTH', 'true').lower() == 'true',
        })

        # Caching & Performance
        self._config.update({
            'cache_ttl_data': int(os.getenv('CACHE_TTL_DATA', '300')),  # 5 minutes
            'cache_ttl_health': int(os.getenv('CACHE_TTL_HEALTH', '60')),  # 1 minute
            'cache_ttl_metrics': int(os.getenv('CACHE_TTL_METRICS', '600')),  # 10 minutes
            'query_timeout': int(os.getenv('QUERY_TIMEOUT', '30')),  # 30 seconds
        })

        # Monitoring & Alerts
        self._config.update({
            'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL', ''),
            'enable_slack_alerts': os.getenv('ENABLE_SLACK_ALERTS', 'false').lower() == 'true',
            'alert_threshold_failures': int(os.getenv('ALERT_THRESHOLD_FAILURES', '5')),
            'alert_threshold_delay': int(os.getenv('ALERT_THRESHOLD_DELAY', '300')),  # 5 minutes
        })

        # UI Configuration
        self._config.update({
            'theme_primary': os.getenv('THEME_PRIMARY', '#1f77b4'),
            'theme_secondary': os.getenv('THEME_SECONDARY', '#ff4b4b'),
            'enable_auto_refresh': os.getenv('ENABLE_AUTO_REFRESH', 'false').lower() == 'true',
            'auto_refresh_interval': int(os.getenv('AUTO_REFRESH_INTERVAL', '30')),
        })

        # Logging
        self._config.update({
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_file': os.getenv('LOG_FILE', './logs/dashboard.log'),
            'enable_audit_log': os.getenv('ENABLE_AUDIT_LOG', 'true').lower() == 'true',
        })

    @property
    def database_config(self) -> Dict[str, str]:
        """Get database configuration."""
        return {
            'host': self._config['db_host'],
            'user': self._config['db_user'],
            'password': self._config['db_password'],
            'port': self._config['db_port'],
            'database': self._config['db_name'],
        }

    @property
    def db_connection_string(self) -> str:
        """Get SQLAlchemy connection string."""
        return (f"postgresql+psycopg2://{self._config['db_user']}:"
                f"{self._config['db_password']}@{self._config['db_host']}:"
                f"{self._config['db_port']}/{self._config['db_name']}")

    @property
    def db_pool_config(self) -> Dict[str, int]:
        """Get database connection pool configuration."""
        return {
            'pool_size': self._config['db_pool_size'],
            'max_overflow': self._config['db_max_overflow'],
            'pool_recycle': self._config['db_pool_recycle'],
            'pool_pre_ping': True,
        }

    @property
    def auth_config(self) -> Dict[str, str]:
        """Get authentication configuration."""
        return {
            'password': self._config['dashboard_password'],
            'timeout': self._config['auth_timeout'],
            'enabled': self._config['enable_auth'],
        }

    @property
    def cache_config(self) -> Dict[str, int]:
        """Get caching configuration."""
        return {
            'data_ttl': self._config['cache_ttl_data'],
            'health_ttl': self._config['cache_ttl_health'],
            'metrics_ttl': self._config['cache_ttl_metrics'],
        }

    @property
    def ui_config(self) -> Dict[str, str]:
        """Get UI configuration."""
        return {
            'primary_color': self._config['theme_primary'],
            'secondary_color': self._config['theme_secondary'],
            'auto_refresh': self._config['enable_auto_refresh'],
            'refresh_interval': self._config['auto_refresh_interval'],
        }

    def get(self, key: str, default: Optional[str] = None) -> str:
        """Get configuration value by key."""
        return str(self._config.get(key, default))

# Global configuration instance
config = DashboardConfig()