#!/usr/bin/env python3
"""
Reusable UI Components for CryptoPrism Dashboard

Provides common UI elements, layouts, and styling components
to reduce code duplication and improve maintainability.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

from config.settings import config
from utils.helpers import (
    styled_metric_card, status_indicator, format_number,
    format_timestamp, cleanup_dataframe_for_display
)


class DashboardLayout:
    """Common layout components for the dashboard."""

    @staticmethod
    def render_header(title: str, subtitle: Optional[str] = None):
        """Render standardized dashboard header."""
        st.markdown(f'<div class="main-header">{title}</div>', unsafe_allow_html=True)

        if subtitle:
            st.markdown(f'<p style="font-size: 1.1rem; color: #666; margin-bottom: 2rem;">{subtitle}</p>',
                       unsafe_allow_html=True)

    @staticmethod
    def render_metric_grid(metrics: List[Dict[str, Any]], columns: int = 4):
        """Render metrics in a responsive grid layout."""
        for i in range(0, len(metrics), columns):
            cols = st.columns(columns)

            for j, metric in enumerate(metrics[i:i + columns]):
                with cols[j]:
                    styled_metric_card(
                        title=metric['title'],
                        value=metric['value'],
                        delta=metric.get('delta'),
                        color=metric.get('color', config.get('theme_primary'))
                    )

    @staticmethod
    def render_two_column_layout(
        left_content: callable,
        right_content: callable,
        left_title: Optional[str] = None,
        right_title: Optional[str] = None,
        left_ratio: int = 2,
        right_ratio: int = 1
    ):
        """Render two-column layout with content functions."""
        col1, col2 = st.columns([left_ratio, right_ratio])

        with col1:
            if left_title:
                st.subheader(left_title)
            left_content()

        with col2:
            if right_title:
                st.subheader(right_title)
            right_content()


class StatusIndicators:
    """Status and health indicators."""

    @staticmethod
    def render_health_status(healthy: bool, title: str = "System Health"):
        """Render system health indicator."""
        if healthy:
            st.success(f"✅ {title}: All systems operational")
        else:
            st.error(f"❌ {title}: Issues detected - check logs")

    @staticmethod
    def render_table_status_grid(tables_status: List[Dict[str, Any]]):
        """Render table status grid with color coding."""
        if not tables_status:
            st.info("No table status data available")
            return

        status_icons = {
            'Active': '✅',
            'Warning': '⚠️',
            'Missing': '❌',
            'Error': '🔧',
            'Critical': '🚨'
        }

        cols = st.columns(min(len(tables_status), 3))

        for i, table_info in enumerate(tables_status[:3]):
            with cols[i]:
                icon = status_icons.get(table_info.get('status', 'Unknown'), '❓')
                st.metric(
                    f"{icon} {table_info.get('table_name', 'Unknown').replace('_', ' ').title()}",
                    table_info.get('row_count', '0'),
                    delta=format_timestamp(table_info.get('last_update')) if table_info.get('last_update') else 'No data'
                )


class DataVisualization:
    """Data visualization components."""

    @staticmethod
    def render_metric_chart(
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        chart_type: str = 'bar',
        title: str = '',
        **kwargs
    ):
        """Render metric chart with consistent styling."""
        if data.empty:
            st.info("No data available for visualization")
            return

        height = kwargs.get('height', 400)

        try:
            if chart_type == 'bar':
                fig = px.bar(
                    data,
                    x=x_col,
                    y=y_col,
                    title=title,
                    template='plotly_white',
                    **kwargs
                )
            elif chart_type == 'line':
                fig = px.line(
                    data,
                    x=x_col,
                    y=y_col,
                    title=title,
                    template='plotly_white',
                    **kwargs
                )
            elif chart_type == 'timeline':
                fig = px.timeline(
                    data,
                    x_start=x_col,
                    x_end=y_col,
                    y='job_name',
                    title=title,
                    template='plotly_white',
                    **kwargs
                )
            else:
                st.error(f"Unsupported chart type: {chart_type}")
                return

            fig.update_layout(
                height=height,
                font=dict(size=12),
                title_font=dict(size=14, color='#333')
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Failed to render chart: {str(e)}")

    @staticmethod
    def render_timeline_gantt(
        data: pd.DataFrame,
        start_col: str = 'start_time',
        end_col: str = 'end_time',
        group_col: str = 'job_name',
        title: str = 'Timeline Visualization'
    ):
        """Render Gantt/timeline chart for ETL jobs."""
        if data.empty or start_col not in data.columns or end_col not in data.columns:
            st.info("No timeline data available")
            return

        try:
            fig = px.timeline(
                data,
                x_start=start_col,
                x_end=end_col,
                y=group_col,
                color='status',
                title=title,
                color_discrete_map={
                    'success': '#28a745',
                    'failed': '#dc3545',
                    'running': '#ffc107'
                }
            )

            fig.update_layout(
                height=400,
                font=dict(size=10)
            )

            # Add vertical line for current time
            fig.add_vline(
                x=datetime.now(),
                line_dash="dash",
                line_color="red",
                annotation_text="Now"
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Failed to render timeline: {str(e)}")

    @staticmethod
    def render_status_pie_chart(status_counts: Dict[str, int], title: str = 'Status Distribution'):
        """Render status distribution pie chart."""
        if not status_counts:
            st.info("No status data available")
            return

        labels = list(status_counts.keys())
        values = list(status_counts.values())

        colors = ['#28a745', '#dc3545', '#ffc107', '#17a2b8']

        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors[:len(labels)]
            )
        ])

        fig.update_layout(
            title=title,
            height=300,
            font=dict(size=12)
        )

        st.plotly_chart(fig, use_container_width=True)


class DataDisplay:
    """Data display and formatting components."""

    @staticmethod
    def render_dataframe_with_styling(
        df: pd.DataFrame,
        title: Optional[str] = None,
        max_rows: int = 1000,
        height: int = 400,
        key: Optional[str] = None
    ):
        """Render dataframe with consistent styling."""
        if df is None or df.empty:
            st.info("No data to display")
            return

        if title:
            st.subheader(title)

        # Clean up dataframe for display
        display_df = cleanup_dataframe_for_display(df.copy(), max_rows)

        # Add row count info
        st.caption(f"Showing {len(display_df)} of {len(df)} rows")

        # Display with enhanced styling
        st.dataframe(
            display_df,
            use_container_width=True,
            height=min(height, len(display_df) * 35 + 40),  # Auto-adjust height
            key=key
        )

    @staticmethod
    def render_expanded_view(title: str, content_func: callable, expanded: bool = False):
        """Render content in expandable container."""
        with st.expander(title, expanded=expanded):
            content_func()

    @staticmethod
    def render_progress_bar(value: float, total: float, label: str):
        """Render custom progress bar."""
        if total == 0:
            percentage = 0
        else:
            percentage = min(value / total * 100, 100)

        st.progress(percentage / 100)

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{label}**")
        with col2:
            st.write(f"{value:.1f} / {total}")
        with col3:
            st.write(f"{percentage:.1f}%")


class NavigationComponents:
    """Navigation and sidebar components."""

    @staticmethod
    def render_sidebar_header():
        """Render standardized sidebar header."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🚀 CryptoPrism Analytics**")
        st.sidebar.markdown(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        st.sidebar.markdown("---")

    @staticmethod
    def render_refresh_controls():
        """Render refresh and navigation controls."""
        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.sidebar.button("🔄 Refresh Data"):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.rerun()

        with col2:
            disable = not config.get('enable_auto_refresh', 'false').lower() == 'true'
            auto_refresh = st.sidebar.checkbox(
                "Auto-refresh",
                value=False,
                disabled=disable,
                help=f"Refresh every {config.get('auto_refresh_interval', '30')} seconds"
            )

            if auto_refresh:
                import time
                interval = int(config.get('auto_refresh_interval', '30'))
                time.sleep(interval)
                st.rerun()


class PerformanceMonitors:
    """Performance monitoring components."""

    @staticmethod
    def render_query_timer(title: str = "Query Execution"):
        """Render query execution timer (context manager)."""
        from contextlib import contextmanager

        @contextmanager
        def timer():
            start_time = time.time()
            try:
                yield
            finally:
                end_time = time.time()
                execution_time = (end_time - start_time) * 1000
                st.info(f"⚡ {title}: {execution_time:.2f}ms")

        return timer()

    @staticmethod
    def render_performance_metrics(execution_times: List[float]):
        """Render performance metrics summary."""
        if not execution_times:
            return

        import statistics

        try:
            avg_time = statistics.mean(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            median_time = statistics.median(execution_times)

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("Avg Time", f"{avg_time:.1f}ms")
            with col2:
                st.metric("Min Time", f"{min_time:.1f}ms")
            with col3:
                st.metric("Max Time", f"{max_time:.1f}ms")
            with col4:
                st.metric("Median", f"{median_time:.1f}ms")
            with col5:
                st.metric("Total Queries", len(execution_times))

        except Exception as e:
            st.error(f"Failed to calculate performance metrics: {str(e)}")