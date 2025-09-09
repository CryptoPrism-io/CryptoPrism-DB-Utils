#!/usr/bin/env python3
"""
Common Utility Functions for CryptoPrism Dashboard

Provides shared helper functions for formatting, validation,
authentication, and common operations.
"""

import time
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
import streamlit as st
import requests
from functools import wraps

from config.settings import config


def format_timestamp(timestamp: datetime, timezone_offset: int = 5) -> str:
    """
    Format timestamp with timezone offset.

    Args:
        timestamp: UTC timestamp
        timezone_offset: Hours to add for local timezone (default +5 for IST)

    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        return "No timestamp"

    try:
        # Ensure timestamp is timezone-naive or handle properly
        if hasattr(timestamp, 'replace'):
            local_time = timestamp + timedelta(hours=timezone_offset, minutes=30)  # IST
            return local_time.strftime('%Y-%m-%d %H:%M IST')
        return str(timestamp)
    except Exception:
        return str(timestamp)


def format_number(num: Optional[float], precision: int = 2) -> str:
    """Format number with thousands separators and specified precision."""
    if num is None:
        return "0"

    try:
        if isinstance(num, int):
            return f"{num:,}"
        elif isinstance(num, float):
            return f"{num:,.{precision}f}"

        return str(num)
    except Exception:
        return str(num)


def calculate_success_rate(success_count: int, total_count: int) -> float:
    """Calculate success rate percentage."""
    if total_count == 0:
        return 0.0
    return round((success_count / total_count) * 100, 1)


def get_age_hours(timestamp: Optional[datetime]) -> Optional[float]:
    """Calculate age in hours from timestamp."""
    if timestamp is None:
        return None

    try:
        age = (datetime.now() - timestamp.replace(tzinfo=None)).total_seconds() / 3600
        return round(age, 1)
    except Exception:
        return None


def get_freshness_status(age_hours: Optional[float]) -> str:
    """Get freshness status based on age in hours."""
    if age_hours is None:
        return "Unknown"

    if age_hours < 1:
        return "Very Fresh (< 1h)"
    elif age_hours < 6:
        return "Fresh (< 6h)"
    elif age_hours < 24:
        return "Recent (< 24h)"
    elif age_hours < 72:
        return "Stale (2-3 days)"
    elif age_hours < 168:  # 7 days
        return "Old (3-7 days)"
    else:
        return "Very Old (> 7 days)"


def send_slack_alert(message: str, level: str = "info",
                    webhook_url: Optional[str] = None) -> bool:
    """
    Send alert message to Slack webhook.

    Args:
        message: Alert message
        level: Alert level (info, warning, error)
        webhook_url: Slack webhook URL (uses config if not provided)

    Returns:
        True if successful, False otherwise
    """
    if webhook_url is None:
        webhook_url = config.get('slack_webhook_url')

    if not webhook_url or not config.get('enable_slack_alerts', 'false').lower() == 'true':
        return False

    try:
        color_map = {
            "info": "#36a64f",
            "warning": "#ffcc02",
            "error": "#f44336",
            "success": "#28a745"
        }

        payload = {
            "attachments": [{
                "color": color_map.get(level, "#36a64f"),
                "title": "CryptoPrism Dashboard Alert",
                "text": message,
                "fields": [{
                    "title": "Timestamp",
                    "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                    "short": True
                }, {
                    "title": "Environment",
                    "value": config.get('db_name', 'Unknown'),
                    "short": True
                }],
                "timestamp": int(time.time())
            }]
        }

        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200

    except Exception as e:
        print(f"Failed to send Slack alert: {str(e)}")
        return False


def validate_password(password: str) -> bool:
    """Validate dashboard password."""
    stored_password = config.get('dashboard_password', 'admin123')

    # For security, use secure comparison
    return hashlib.sha256(password.encode()).hexdigest() == \
           hashlib.sha256(stored_password.encode()).hexdigest()


def check_authentication_status() -> bool:
    """Check if user is authenticated."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if 'auth_timestamp' in st.session_state:
        # Check if auth has expired
        auth_time = st.session_state.auth_timestamp
        timeout_seconds = int(config.get('auth_timeout', '3600'))
        if (datetime.now() - auth_time).seconds > timeout_seconds:
            st.session_state.authenticated = False

    return st.session_state.authenticated


def login_user(password: str) -> bool:
    """Authenticate user with password."""
    if validate_password(password):
        st.session_state.authenticated = True
        st.session_state.auth_timestamp = datetime.now()
        return True

    return False


def logout_user():
    """Log out user and clear session."""
    st.session_state.authenticated = False
    if 'auth_timestamp' in st.session_state:
        del st.session_state.auth_timestamp


def styled_metric_card(title: str, value: str, delta: Optional[str] = None,
                       color: str = "#1f77b4") -> None:
    """
    Display a styled metric card.

    Args:
        title: Metric title
        value: Metric value
        delta: Optional delta value
        color: Card accent color
    """
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color}20 0%, {color}40 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 4px solid {color};
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        color: #333;
    ">
        <h4 style="margin: 0 0 0.5rem 0; color: {color};">{title}</h4>
        <h2 style="margin: 0 0 0.5rem 0; font-size: 2rem; color: #333;">{value}</h2>
        {'<p style="margin: 0; font-size: 0.9rem; color: #666;">' + delta + '</p>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)


def status_indicator(status: str, size: str = "small") -> None:
    """
    Display status indicator.

    Args:
        status: Status text (success, error, warning, info)
        size: Size of indicator (small, medium, large)
    """
    color_map = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8',
        'active': '#007bff',
        'inactive': '#6c757d'
    }

    size_map = {
        'small': '8px',
        'medium': '12px',
        'large': '16px'
    }

    color = color_map.get(status.lower(), '#6c757d')
    indicator_size = size_map.get(size, '12px')

    st.markdown(f"""
    <div style="display: inline-block;">
        <span style="
            display: inline-block;
            width: {indicator_size};
            height: {indicator_size};
            background-color: {color};
            border-radius: 50%;
            margin-right: 8px;
        "></span>
        <span style="vertical-align: middle;">{status.title()}</span>
    </div>
    """, unsafe_allow_html=True)


def cleanup_dataframe_for_display(df: Any, max_rows: int = 1000) -> Any:
    """
    Clean up dataframe for streamlit display.

    Args:
        df: Input dataframe
        max_rows: Maximum rows to display

    Returns:
        Cleaned dataframe ready for display
    """
    if df is None or df.empty:
        return df

    # Limit rows for performance
    if len(df) > max_rows:
        df = df.head(max_rows)

    # Convert datetimes to strings for display
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')

    return df


def get_pipeline_stage(table_name: str) -> str:
    """Get pipeline stage for FE table."""
    stage_mapping = {
        'FE_METRICS_SIGNAL': 'Stage 1: Metrics',
        'FE_TVV_SIGNALS': 'Stage 2: Volume/Trend',
        'FE_MOMENTUM_SIGNALS': 'Stage 3: Momentum Signals',
        'FE_MOMENTUM': 'Stage 3: Momentum Base',
        'FE_OSCILLATORS_SIGNALS': 'Stage 4: Oscillator Signals',
        'FE_OSCILLATORS': 'Stage 4: Oscillator Base',
        'FE_RATIOS_SIGNALS': 'Stage 5: Ratios',
        'FE_DMV_ALL': 'Stage 6: Aggregation',
        'FE_DMV_SCORES': 'Stage 7: Scoring'
    }
    return stage_mapping.get(table_name, 'Unknown Stage')


class DashboardCache:
    """Simple in-memory cache with TTL."""

    def __init__(self):
        self._cache = {}
        self._timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self._cache:
            if self._is_expired(key):
                self.delete(key)
                return None
            return self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Cache value with TTL."""
        self._cache[key] = value
        self._timestamps[key] = datetime.now() + timedelta(seconds=ttl_seconds)

    def delete(self, key: str):
        """Delete cached value."""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self._timestamps:
            return True
        return datetime.now() > self._timestamps[key]

    def clear(self):
        """Clear all cached values."""
        self._cache.clear()
        self._timestamps.clear()


# Global cache instance
dashboard_cache = DashboardCache()