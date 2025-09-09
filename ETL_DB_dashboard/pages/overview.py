#!/usr/bin/env python3
"""
Overview Dashboard Page

Main dashboard overview with key metrics, ETL health monitoring,
and performance trends visualization.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError

from components.ui_components import (
    DashboardLayout, StatusIndicators, DataVisualization,
    DataDisplay
)
from services.database_service import db_service
from utils.helpers import (
    send_slack_alert, styled_metric_card, format_number,
    format_timestamp, calculate_success_rate
)


def render_overview_page():
    """Render the main dashboard overview page."""
    DashboardLayout.render_header(
        "📊 CryptoPrism Database Monitor",
        "Real-time analytics dashboard for cryptocurrency data pipelines"
    )

    try:
        # Load and display summary metrics
        summary = load_dashboard_summary()
        if summary:
            render_key_metrics(summary)

            # Recent ETL activity section
            st.subheader("📈 Recent ETL Activity")
            etl_data = load_etl_activity_data()

            if not etl_data.empty:
                # Recent runs timeline
                DataVisualization.render_timeline_gantt(
                    etl_data.head(20),
                    title="Recent ETL Job Timeline"
                )

                # Performance trends section
                col1, col2 = st.columns(2)

                with col1:
                    render_job_duration_analysis(etl_data)

                with col2:
                    render_job_success_rate_analysis(etl_data)

            else:
                st.info("No ETL activity data available. ETL jobs will appear here once executed.")

            # System health indicators
            render_system_health_section(etl_data)

        else:
            st.error("Unable to load dashboard data. Please check database connection.")
            # Show connection troubleshooting
            render_connection_troubleshooting()

    except Exception as e:
        st.error(f"Dashboard error: {str(e)}")
        send_slack_alert(f"Dashboard Overview Page Error: {str(e)}", "error")


def load_dashboard_summary() -> dict:
    """Load dashboard summary statistics."""
    try:
        query = "SELECT * FROM etl_dashboard_summary"
        results = db_service.execute_query_single(query)

        if results:
            return {
                'total_runs': results.get('total_runs', 0) or 0,
                'successful_runs': results.get('successful_runs', 0) or 0,
                'failed_runs': results.get('failed_runs', 0) or 0,
                'running_runs': results.get('running_runs', 0) or 0,
                'avg_duration': round(float(results.get('avg_duration', 0) or 0), 2),
                'last_run_time': results.get('last_run_time'),
                'total_rows_processed': results.get('total_rows_processed', 0) or 0
            }
        else:
            return _get_default_summary()

    except Exception as e:
        print(f"Failed to load dashboard summary: {str(e)}")
        return _get_default_summary()


def _get_default_summary() -> dict:
    """Get default summary when no data available."""
    return {
        'total_runs': 0, 'successful_runs': 0, 'failed_runs': 0,
        'running_runs': 0, 'avg_duration': 0, 'last_run_time': None,
        'total_rows_processed': 0
    }


def render_key_metrics(summary: dict):
    """Render key performance metrics in a grid."""
    metrics = [
        {
            'title': "Total Runs (7 days)",
            'value': format_number(summary['total_runs']),
            'color': "#1f77b4"
        },
        {
            'title': "Success Rate",
            'value': f"{calculate_success_rate(summary['successful_runs'], summary['total_runs'])}%",
            'color': "#28a745"
        },
        {
            'title': "Failed Runs",
            'value': format_number(summary['failed_runs']),
            'color': "#dc3545"
        },
        {
            'title': "Avg Duration",
            'value': f"{summary['avg_duration']} min",
            'color': "#ffc107"
        },
        {
            'title': "Total Rows",
            'value': format_number(summary['total_rows_processed']),
            'color': "#17a2b8"
        }
    ]

    if summary['running_runs'] > 0:
        metrics.append({
            'title': "Running Jobs",
            'value': format_number(summary['running_runs']),
            'color': "#ffff00"
        })

    DashboardLayout.render_metric_grid(metrics, columns=5)


def load_etl_activity_data() -> pd.DataFrame:
    """Load recent ETL activity data."""
    try:
        query = """
        SELECT
            run_id,
            job_name,
            start_time,
            end_time,
            status,
            rows_processed,
            duration_minutes,
            memory_used_mb
        FROM etl_runs
        WHERE start_time >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY start_time DESC
        LIMIT 1000
        """

        rows = db_service.execute_query(query)

        if rows:
            df = pd.DataFrame(rows)
            if not df.empty:
                df['start_time'] = pd.to_datetime(df['start_time'])
                df['end_time'] = pd.to_datetime(df['end_time'])
            return df

    except Exception as e:
        print(f"Failed to load ETL data: {str(e)}")

    return pd.DataFrame()


def render_job_duration_analysis(etl_data: pd.DataFrame):
    """Render job duration analysis chart."""
    job_durations = etl_data.groupby('job_name')['duration_minutes'].agg(['mean', 'count']).reset_index()
    job_durations = job_durations[job_durations['count'] >= 2]  # Only jobs with multiple runs

    if not job_durations.empty:
        DataVisualization.render_metric_chart(
            job_durations,
            x_col='job_name',
            y_col='mean',
            chart_type='bar',
            title="Average Duration by Job",
            labels={'mean': 'Minutes', 'job_name': 'Job Name'}
        )
    else:
        st.info("Need more job runs for duration analysis")


def render_job_success_rate_analysis(etl_data: pd.DataFrame):
    """Render job success rate analysis chart."""
    success_by_job = etl_data.groupby('job_name').agg({
        'status': ['count', lambda x: (x == 'success').sum()]
    }).round(2)
    success_by_job.columns = ['total', 'successful']
    success_by_job['success_rate'] = (success_by_job['successful'] / success_by_job['total'] * 100).round(1)
    success_by_job = success_by_job.reset_index()

    if not success_by_job.empty:
        DataVisualization.render_metric_chart(
            success_by_job,
            x_col='job_name',
            y_col='success_rate',
            chart_type='bar',
            title="Success Rate by Job (%)",
            labels={'success_rate': 'Success Rate (%)', 'job_name': 'Job Name'}
        )
    else:
        st.info("No job success data available")


def render_system_health_section(etl_data: pd.DataFrame):
    """Render system health indicators."""
    st.subheader("🏥 System Health")

    health_col1, health_col2, health_col3 = st.columns(3)

    with health_col1:
        # Database connectivity
        if db_service.test_connection():
            st.success("✅ Database Connected")
        else:
            st.error("❌ Database Connection Failed")

    with health_col2:
        # Recent failures analysis
        if not etl_data.empty:
            recent_failures = etl_data[
                (etl_data['status'] == 'failed') &
                (etl_data['start_time'] > datetime.now() - timedelta(hours=24))
            ]

            if len(recent_failures) > 0:
                st.warning(f"⚠️ {len(recent_failures)} Recent Failures")
                # Send alert if failure threshold exceeded
                if len(recent_failures) >= 3:
                    send_slack_alert(
                        f"High failure rate detected: {len(recent_failures)} failures in last 24h",
                        "warning"
                    )
            else:
                st.success("✅ No Recent Failures")
        else:
            st.info("ℹ️ No Data Available")

    with health_col3:
        # Long running jobs analysis
        if not etl_data.empty:
            long_jobs = etl_data[
                (etl_data['duration_minutes'] > 30) &
                (etl_data['start_time'] > datetime.now() - timedelta(hours=24))
            ]

            if len(long_jobs) > 0:
                st.warning(f"⏱️ {len(long_jobs)} Long-running Jobs")
                # Show details in expander
                with st.expander("View Long-running Jobs"):
                    display_cols = ['job_name', 'duration_minutes', 'start_time', 'status']
                    DataDisplay.render_dataframe_with_styling(long_jobs[display_cols], height=200)
            else:
                st.success("✅ Normal Job Duration")
        else:
            st.info("ℹ️ No Data Available")


def render_connection_troubleshooting():
    """Render connection troubleshooting guide."""
    with st.expander("🔧 Database Connection Troubleshooting"):
        st.write("**Steps to resolve connection issues:**")

        st.markdown("""
        1. **Check database server status**
        2. **Verify connection credentials in `.env` file**
        3. **Test network connectivity:**
           ```bash
           ping your_database_host
           nc -zv your_database_host your_db_port
           ```
        4. **Check database logs for error messages**
        5. **Verify user permissions in PostgreSQL**
        6. **Restart Streamlit if needed:**
           ```bash
           streamlit run streamlit_app.py --server.port=8501
           ```
        """)

        if st.button("🔄 Retry Connection"):
            if db_service.test_connection():
                st.success("Connection established!")
                st.rerun()
            else:
                st.error("Connection still failing. Check credentials and network.")