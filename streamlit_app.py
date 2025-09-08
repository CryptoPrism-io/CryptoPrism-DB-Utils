#!/usr/bin/env python3
"""
CryptoPrism Database Monitoring Dashboard
A comprehensive Streamlit application for monitoring ETL jobs, data quality, and performance.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, timedelta
import time
import requests
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
st.set_page_config(
    page_title="CryptoPrism Database Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-failed {
        color: #dc3545;
        font-weight: bold;
    }
    .status-running {
        color: #ffc107;
        font-weight: bold;
    }
    .sidebar-logo {
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_db_connection():
    """Create database connection with connection pooling."""
    try:
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'dbcp')
        }
        
        conn_string = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        engine = create_engine(conn_string, pool_pre_ping=True, pool_recycle=300)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        st.stop()

# Authentication
def check_authentication():
    """Simple password authentication for dashboard access."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown('<div class="main-header">🔒 CryptoPrism Dashboard Login</div>', unsafe_allow_html=True)
        
        password = st.text_input("Enter dashboard password:", type="password")
        if st.button("Login"):
            if password == os.getenv('DASHBOARD_PASSWORD', 'admin123'):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid password!")
        st.stop()

# Utility functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_etl_data():
    """Load ETL runs data from database."""
    try:
        engine = get_db_connection()
        
        query = """
        SELECT 
            run_id,
            job_name,
            start_time,
            end_time,
            status,
            rows_processed,
            duration_minutes,
            error_message,
            memory_used_mb
        FROM etl_runs 
        WHERE start_time >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY start_time DESC
        LIMIT 1000
        """
        
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        if not df.empty:
            df['start_time'] = pd.to_datetime(df['start_time'])
            df['end_time'] = pd.to_datetime(df['end_time'])
        
        return df
    except Exception as e:
        st.error(f"Failed to load ETL data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_dashboard_summary():
    """Load dashboard summary statistics."""
    try:
        engine = get_db_connection()
        
        query = "SELECT * FROM etl_dashboard_summary"
        
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchone()
        
        if result:
            return {
                'total_runs': result[0] or 0,
                'successful_runs': result[1] or 0,
                'failed_runs': result[2] or 0,
                'running_runs': result[3] or 0,
                'avg_duration': round(float(result[4] or 0), 2),
                'last_run_time': result[5],
                'total_rows_processed': result[6] or 0
            }
        else:
            return {
                'total_runs': 0, 'successful_runs': 0, 'failed_runs': 0,
                'running_runs': 0, 'avg_duration': 0, 'last_run_time': None,
                'total_rows_processed': 0
            }
    except Exception as e:
        st.error(f"Failed to load dashboard summary: {str(e)}")
        return {}

@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_data_quality_checks():
    """Load data quality check results."""
    try:
        engine = get_db_connection()
        
        query = """
        SELECT 
            check_name,
            table_name,
            check_type,
            expected_count,
            actual_count,
            status,
            error_details,
            check_time
        FROM data_quality_checks
        WHERE check_time >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY check_time DESC
        LIMIT 100
        """
        
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        if not df.empty:
            df['check_time'] = pd.to_datetime(df['check_time'])
        
        return df
    except Exception as e:
        st.warning(f"Data quality checks not available: {str(e)}")
        return pd.DataFrame()

def send_slack_alert(message, level="info"):
    """Send alert to Slack webhook."""
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return False
    
    try:
        color_map = {
            "info": "#36a64f",
            "warning": "#ffeb3b", 
            "error": "#f44336"
        }
        
        payload = {
            "attachments": [{
                "color": color_map.get(level, "#36a64f"),
                "title": "CryptoPrism Dashboard Alert",
                "text": message,
                "timestamp": int(time.time())
            }]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

# Dashboard Pages
def overview_page():
    """Main dashboard overview page."""
    st.markdown('<div class="main-header">📊 CryptoPrism Database Monitor</div>', unsafe_allow_html=True)
    
    # Load summary data
    summary = load_dashboard_summary()
    
    if not summary:
        st.error("Unable to load dashboard data. Please check database connection.")
        return
    
    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Runs (7 days)", summary['total_runs'])
    
    with col2:
        success_rate = (summary['successful_runs'] / max(summary['total_runs'], 1)) * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        st.metric("Failed Runs", summary['failed_runs'])
    
    with col4:
        st.metric("Avg Duration", f"{summary['avg_duration']:.1f} min")
    
    with col5:
        st.metric("Total Rows", f"{summary['total_rows_processed']:,}")
    
    # Recent activity
    st.subheader("📈 Recent ETL Activity")
    
    etl_data = load_etl_data()
    
    if not etl_data.empty:
        # Recent runs chart
        recent_data = etl_data.head(20)
        
        fig = px.timeline(
            recent_data,
            x_start="start_time",
            x_end="end_time", 
            y="job_name",
            color="status",
            title="Recent ETL Job Timeline",
            color_discrete_map={
                'success': '#28a745',
                'failed': '#dc3545',
                'running': '#ffc107'
            }
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Job performance trends
        st.subheader("🎯 Performance Trends")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Duration trends by job
            job_durations = etl_data.groupby('job_name')['duration_minutes'].agg(['mean', 'count']).reset_index()
            job_durations = job_durations[job_durations['count'] >= 2]  # Only jobs with multiple runs
            
            if not job_durations.empty:
                fig = px.bar(
                    job_durations,
                    x='job_name',
                    y='mean',
                    title="Average Duration by Job",
                    labels={'mean': 'Minutes', 'job_name': 'Job Name'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Success rate by job
            success_by_job = etl_data.groupby('job_name').agg({
                'status': ['count', lambda x: (x == 'success').sum()]
            }).round(2)
            success_by_job.columns = ['total', 'successful']
            success_by_job['success_rate'] = (success_by_job['successful'] / success_by_job['total'] * 100).round(1)
            success_by_job = success_by_job.reset_index()
            
            if not success_by_job.empty:
                fig = px.bar(
                    success_by_job,
                    x='job_name',
                    y='success_rate',
                    title="Success Rate by Job (%)",
                    labels={'success_rate': 'Success Rate (%)', 'job_name': 'Job Name'}
                )
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No ETL data available. Run some instrumented ETL jobs to see activity here.")
    
    # System health indicators
    st.subheader("🏥 System Health")
    
    health_col1, health_col2, health_col3 = st.columns(3)
    
    with health_col1:
        # Database connectivity
        try:
            engine = get_db_connection()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            st.success("✅ Database Connected")
        except Exception:
            st.error("❌ Database Connection Failed")
    
    with health_col2:
        # Recent failures
        if not etl_data.empty:
            recent_failures = etl_data[etl_data['status'] == 'failed'].head(5)
            if len(recent_failures) > 0:
                st.warning(f"⚠️ {len(recent_failures)} Recent Failures")
            else:
                st.success("✅ No Recent Failures")
        else:
            st.info("ℹ️ No Data Available")
    
    with health_col3:
        # Long running jobs
        if not etl_data.empty:
            long_jobs = etl_data[
                (etl_data['duration_minutes'] > 30) & 
                (etl_data['start_time'] > datetime.now() - timedelta(hours=24))
            ]
            if len(long_jobs) > 0:
                st.warning(f"⏱️ {len(long_jobs)} Long-running Jobs")
            else:
                st.success("✅ Normal Job Duration")
        else:
            st.info("ℹ️ No Data Available")

def etl_runs_page():
    """ETL runs monitoring page."""
    st.markdown('<div class="main-header">🔄 ETL Job Monitoring</div>', unsafe_allow_html=True)
    
    etl_data = load_etl_data()
    
    if etl_data.empty:
        st.info("No ETL runs found. Make sure your ETL scripts are instrumented with tracking code.")
        return
    
    # Filters
    st.subheader("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        job_filter = st.selectbox(
            "Job Name",
            ["All"] + list(etl_data['job_name'].unique())
        )
    
    with col2:
        status_filter = st.selectbox(
            "Status", 
            ["All", "success", "failed", "running"]
        )
    
    with col3:
        days_filter = st.selectbox(
            "Time Period",
            [7, 14, 30],
            index=0
        )
    
    # Apply filters
    filtered_data = etl_data.copy()
    
    if job_filter != "All":
        filtered_data = filtered_data[filtered_data['job_name'] == job_filter]
    
    if status_filter != "All":
        filtered_data = filtered_data[filtered_data['status'] == status_filter]
    
    cutoff_date = datetime.now() - timedelta(days=days_filter)
    filtered_data = filtered_data[filtered_data['start_time'] >= cutoff_date]
    
    # Summary stats for filtered data
    st.subheader("📊 Filtered Results Summary")
    
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    
    with summary_col1:
        st.metric("Total Runs", len(filtered_data))
    
    with summary_col2:
        if len(filtered_data) > 0:
            success_count = len(filtered_data[filtered_data['status'] == 'success'])
            success_rate = (success_count / len(filtered_data)) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
        else:
            st.metric("Success Rate", "0%")
    
    with summary_col3:
        if len(filtered_data) > 0:
            avg_duration = filtered_data['duration_minutes'].mean()
            st.metric("Avg Duration", f"{avg_duration:.1f} min")
        else:
            st.metric("Avg Duration", "0 min")
    
    with summary_col4:
        total_rows = filtered_data['rows_processed'].sum()
        st.metric("Total Rows", f"{total_rows:,}")
    
    # ETL runs table
    st.subheader("📋 ETL Runs Detail")
    
    if not filtered_data.empty:
        # Format data for display
        display_data = filtered_data.copy()
        display_data['start_time'] = display_data['start_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_data['end_time'] = display_data['end_time'].fillna('').astype(str)
        display_data['end_time'] = display_data['end_time'].apply(
            lambda x: pd.to_datetime(x).strftime('%Y-%m-%d %H:%M:%S') if x and x != 'NaT' else 'Running'
        )
        
        # Style the dataframe
        def style_status(status):
            if status == 'success':
                return 'color: #28a745; font-weight: bold'
            elif status == 'failed':
                return 'color: #dc3545; font-weight: bold'
            elif status == 'running':
                return 'color: #ffc107; font-weight: bold'
            return ''
        
        styled_df = display_data[['run_id', 'job_name', 'start_time', 'end_time', 'status', 
                                 'duration_minutes', 'rows_processed', 'error_message']].style.applymap(
            style_status, subset=['status']
        )
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Show error details for failed jobs
        failed_jobs = filtered_data[filtered_data['status'] == 'failed']
        if not failed_jobs.empty:
            st.subheader("❌ Recent Failures")
            for _, job in failed_jobs.head(5).iterrows():
                with st.expander(f"❌ {job['job_name']} - {job['start_time'].strftime('%Y-%m-%d %H:%M')}"):
                    st.code(job['error_message'] or "No error message available")
    else:
        st.info("No ETL runs match the selected filters.")

def qa_checks_page():
    """Data quality assurance page."""
    st.markdown('<div class="main-header">✅ Data Quality Assurance</div>', unsafe_allow_html=True)
    
    # Load existing validation results
    try:
        from comprehensive_validation_suite import DatabaseValidator
        
        st.subheader("🔍 Run Validation Suite")
        
        if st.button("🚀 Run Complete Validation", type="primary"):
            with st.spinner("Running comprehensive database validation..."):
                try:
                    validator = DatabaseValidator()
                    results = validator.run_all_tests()
                    
                    st.success("Validation completed!")
                    
                    # Display results summary
                    total_tests = len(results)
                    passed_tests = sum(1 for r in results if r.get('status') == 'PASSED')
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Tests", total_tests)
                    with col2:
                        st.metric("Passed", passed_tests)
                    with col3:
                        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
                        st.metric("Success Rate", f"{success_rate:.1f}%")
                    
                    # Show detailed results
                    st.subheader("📊 Validation Results")
                    
                    for result in results:
                        status = result.get('status', 'UNKNOWN')
                        if status == 'PASSED':
                            st.success(f"✅ {result.get('description', 'Test passed')}")
                        elif status == 'FAILED':
                            st.error(f"❌ {result.get('description', 'Test failed')}")
                            if result.get('details'):
                                st.code(result['details'])
                        else:
                            st.warning(f"⚠️ {result.get('description', 'Test status unknown')}")
                
                except ImportError:
                    st.error("Validation suite not available. Please ensure comprehensive_validation_suite.py is in the current directory.")
                except Exception as e:
                    st.error(f"Validation failed: {str(e)}")
    
    except Exception as e:
        st.warning("Automated validation not available.")
    
    # Data quality checks from database
    st.subheader("📋 Historical Quality Checks")
    
    qa_data = load_data_quality_checks()
    
    if not qa_data.empty:
        # QA summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Checks", len(qa_data))
        
        with col2:
            passed_checks = len(qa_data[qa_data['status'] == 'passed'])
            st.metric("Passed", passed_checks)
        
        with col3:
            failed_checks = len(qa_data[qa_data['status'] == 'failed'])
            st.metric("Failed", failed_checks)
        
        with col4:
            if len(qa_data) > 0:
                success_rate = (passed_checks / len(qa_data)) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # QA checks by table
        if not qa_data.empty:
            table_summary = qa_data.groupby('table_name').agg({
                'status': ['count', lambda x: (x == 'passed').sum()]
            })
            table_summary.columns = ['total_checks', 'passed_checks']
            table_summary['pass_rate'] = (table_summary['passed_checks'] / table_summary['total_checks'] * 100).round(1)
            table_summary = table_summary.reset_index()
            
            st.subheader("📊 Quality by Table")
            
            fig = px.bar(
                table_summary,
                x='table_name',
                y='pass_rate',
                title="Data Quality Pass Rate by Table (%)",
                labels={'pass_rate': 'Pass Rate (%)', 'table_name': 'Table Name'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent checks table
        st.subheader("📋 Recent Quality Checks")
        display_qa = qa_data.head(20).copy()
        display_qa['check_time'] = display_qa['check_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.dataframe(display_qa, use_container_width=True, height=300)
    
    else:
        st.info("No data quality checks found. Quality checks will appear here after running validation tests.")

def performance_page():
    """Database performance monitoring page."""
    st.markdown('<div class="main-header">⚡ Performance Analytics</div>', unsafe_allow_html=True)
    
    # Load performance toolkits
    try:
        st.subheader("🔧 Performance Toolkits")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Run Query Optimization", type="primary"):
                with st.spinner("Running query optimization analysis..."):
                    try:
                        from query_optimization_toolkit import QueryOptimizer
                        optimizer = QueryOptimizer()
                        results = optimizer.analyze_slow_queries()
                        
                        st.success("Query optimization completed!")
                        st.json(results)
                    except ImportError:
                        st.error("Query optimization toolkit not available")
                    except Exception as e:
                        st.error(f"Optimization failed: {str(e)}")
        
        with col2:
            if st.button("📊 Schema Analysis", type="secondary"):
                with st.spinner("Running schema analysis..."):
                    try:
                        from schema_correction_toolkit import SchemaAnalyzer
                        analyzer = SchemaAnalyzer()
                        results = analyzer.analyze_schema_issues()
                        
                        st.success("Schema analysis completed!")
                        st.json(results)
                    except ImportError:
                        st.error("Schema analysis toolkit not available")
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")
        
        # Database performance metrics
        st.subheader("📈 Database Metrics")
        
        try:
            engine = get_db_connection()
            
            with engine.connect() as conn:
                # Active connections
                active_conn_query = """
                SELECT count(*) as active_connections
                FROM pg_stat_activity 
                WHERE state = 'active';
                """
                active_connections = conn.execute(text(active_conn_query)).scalar()
                
                # Database size
                db_size_query = """
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;
                """
                db_size = conn.execute(text(db_size_query)).scalar()
                
                # Table sizes
                table_sizes_query = """
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10;
                """
                table_sizes = pd.read_sql(table_sizes_query, conn)
            
            # Metrics display
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.metric("Database Size", db_size)
            
            with metric_col2:
                st.metric("Active Connections", active_connections)
            
            with metric_col3:
                st.metric("Largest Table", table_sizes.iloc[0]['tablename'] if not table_sizes.empty else "N/A")
            
            # Table sizes chart
            if not table_sizes.empty:
                st.subheader("💾 Table Sizes")
                
                fig = px.bar(
                    table_sizes,
                    x='tablename',
                    y='size_bytes',
                    title="Database Table Sizes",
                    labels={'size_bytes': 'Size (Bytes)', 'tablename': 'Table Name'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        except Exception as e:
            st.error(f"Unable to load database metrics: {str(e)}")
    
    except Exception as e:
        st.error(f"Performance monitoring unavailable: {str(e)}")

def business_signals_page():
    """Business intelligence and signals page."""
    st.markdown('<div class="main-header">📈 Business Intelligence</div>', unsafe_allow_html=True)
    
    try:
        engine = get_db_connection()
        
        # Check for signal tables
        with engine.connect() as conn:
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%SIGNAL%' OR table_name LIKE 'FE_%'
            ORDER BY table_name;
            """
            signal_tables = pd.read_sql(tables_query, conn)
        
        if not signal_tables.empty:
            st.subheader("📊 Signal Tables Overview")
            
            table_stats = []
            
            for table in signal_tables['table_name']:
                try:
                    with engine.connect() as conn:
                        count_query = f"SELECT COUNT(*) as row_count FROM {table}"
                        count = conn.execute(text(count_query)).scalar()
                        
                        # Get latest update if timestamp column exists
                        try:
                            latest_query = f"""
                            SELECT MAX(GREATEST(
                                COALESCE(created_at, '1900-01-01'::timestamp),
                                COALESCE(updated_at, '1900-01-01'::timestamp),
                                COALESCE(timestamp, '1900-01-01'::timestamp)
                            )) as latest_update
                            FROM {table}
                            """
                            latest = conn.execute(text(latest_query)).scalar()
                        except:
                            latest = None
                        
                        table_stats.append({
                            'table_name': table,
                            'row_count': count,
                            'latest_update': latest
                        })
                except Exception as e:
                    table_stats.append({
                        'table_name': table,
                        'row_count': f"Error: {str(e)}",
                        'latest_update': None
                    })
            
            stats_df = pd.DataFrame(table_stats)
            st.dataframe(stats_df, use_container_width=True)
            
            # Show sample data from first signal table
            if len(signal_tables) > 0:
                st.subheader(f"📋 Sample Data: {signal_tables.iloc[0]['table_name']}")
                
                try:
                    with engine.connect() as conn:
                        sample_query = f"SELECT * FROM {signal_tables.iloc[0]['table_name']} LIMIT 10"
                        sample_data = pd.read_sql(sample_query, conn)
                    
                    st.dataframe(sample_data, use_container_width=True)
                except Exception as e:
                    st.error(f"Unable to load sample data: {str(e)}")
        
        else:
            st.info("No signal tables found in the database. Signal data will appear here once technical analysis is running.")
    
    except Exception as e:
        st.error(f"Unable to load business signals: {str(e)}")

def logs_page():
    """Logs and artifacts management page."""
    st.markdown('<div class="main-header">📜 Logs & Artifacts</div>', unsafe_allow_html=True)
    
    st.subheader("📁 Log Files")
    
    # Check for common log locations
    log_locations = [
        "./logs",
        "./output", 
        ".",
        "../logs"
    ]
    
    log_files = []
    for location in log_locations:
        try:
            if os.path.exists(location):
                for file in os.listdir(location):
                    if file.endswith(('.log', '.txt', '.md', '.json')) and 'log' in file.lower():
                        log_files.append(os.path.join(location, file))
        except:
            continue
    
    if log_files:
        selected_log = st.selectbox("Select log file:", log_files)
        
        if selected_log:
            col1, col2 = st.columns([3, 1])
            
            with col2:
                lines_to_show = st.number_input("Lines to show:", min_value=10, max_value=1000, value=50)
            
            try:
                with open(selected_log, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    if len(lines) > lines_to_show:
                        lines = lines[-lines_to_show:]  # Show last N lines
                    
                    content = ''.join(lines)
                    st.code(content, language='text')
            except Exception as e:
                st.error(f"Unable to read log file: {str(e)}")
    else:
        st.info("No log files found in common locations.")
    
    # System information
    st.subheader("🖥️ System Information")
    
    system_info = {
        "Python Version": f"{os.sys.version}",
        "Current Directory": os.getcwd(),
        "Database Host": os.getenv('DB_HOST', 'Not configured'),
        "Dashboard Version": "1.0.0",
        "Last Restart": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    for key, value in system_info.items():
        st.text(f"{key}: {value}")
    
    # Database connection test
    st.subheader("🔌 Connection Test")
    
    if st.button("Test Database Connection"):
        try:
            engine = get_db_connection()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()")).scalar()
            
            st.success(f"✅ Database connected successfully!")
            st.info(f"Database version: {result}")
        except Exception as e:
            st.error(f"❌ Database connection failed: {str(e)}")

# Main application
def main():
    """Main Streamlit application."""
    
    # Check authentication
    check_authentication()
    
    # Sidebar navigation
    st.sidebar.markdown('<div class="sidebar-logo">📊 CryptoPrism Monitor</div>', unsafe_allow_html=True)
    
    pages = {
        "🏠 Overview": overview_page,
        "🔄 ETL Runs": etl_runs_page,
        "✅ QA Checks": qa_checks_page,
        "⚡ Performance": performance_page,
        "📈 Business Signals": business_signals_page,
        "📜 Logs & Artifacts": logs_page
    }
    
    selected_page = st.sidebar.radio("Navigation", list(pages.keys()))
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Logout button
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**CryptoPrism Dashboard v1.0**")
    st.sidebar.markdown(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    # Run selected page
    pages[selected_page]()

if __name__ == "__main__":
    main()