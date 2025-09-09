#!/usr/bin/env python3
"""
CryptoPrism Database Monitoring Dashboard - Enhanced Analytics Platform
A sophisticated Streamlit application for advanced crypto trading analytics, real-time monitoring, and comprehensive data visualization.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import altair as alt
import os
from datetime import datetime, timedelta, timezone
import time
import requests
import json
from services.database_service import db_service
from config.settings import config
from utils.helpers import check_authentication_status, login_user, logout_user, send_slack_alert
from dotenv import load_dotenv

# Load environment variables (handled by config.settings)
# load_dotenv()

# Configuration
st.set_page_config(
    page_title="🚀 CryptoPrism Analytics Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io/',
        'Report a bug': "https://github.com/streamlit/streamlit/issues",
        'About': "CryptoPrism Database Analytics Platform v2.0"
    }
)

# Enhanced CSS with modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(45deg, #1f77b4, #ff4b4b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 5px solid #ff4b4b;
        color: white;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
        margin-bottom: 1rem;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }

    .status-success {
        color: #28a745;
        font-weight: bold;
    }

    .status-error {
        color: #dc3545;
        font-weight: bold;
    }

    .viz-container {
        background: white;
        border-radius: 1rem;
        padding: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
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

    .advanced-metric {
        text-align: center;
        margin-bottom: 2rem;
    }

    .advanced-metric h3 {
        margin-bottom: 0.5rem;
        color: #1f77b4;
    }

    .advanced-metric h2 {
        margin: 0;
        font-size: 2.5rem;
        background: linear-gradient(45deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    div[data-testid="stMetricValue"] > div {
        color: #ff6b6b !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)


from pages.logs import render_logs_page



# Authentication
def check_authentication():
    """Authentication handler using utility functions."""
    if config.auth_config['enabled']:
        if not check_authentication_status():
            st.markdown('<div class="main-header">🔒 CryptoPrism Dashboard Login</div>', unsafe_allow_html=True)
            password = st.text_input("Enter dashboard password:", type="password")
            if st.button("Login"):
                if login_user(password):
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid password. Please try again.")
            st.stop()


# Utility functions
@st.cache_data(ttl=config.cache_config['data_ttl'])  # Cache for 5 minutes
def load_etl_data():
    """Load ETL runs data from database."""
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
            error_message,
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

        return pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to load ETL data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=config.cache_config['data_ttl'])
def load_dashboard_summary():
    """Load dashboard summary statistics."""
    try:
        query = "SELECT * FROM etl_dashboard_summary"
        result = db_service.execute_query_single(query)

        if result:
            return {
                'total_runs': result.get('total_runs', 0) or 0,
                'successful_runs': result.get('successful_runs', 0) or 0,
                'failed_runs': result.get('failed_runs', 0) or 0,
                'running_runs': result.get('running_runs', 0) or 0,
                'avg_duration': round(float(result.get('avg_duration', 0) or 0), 2),
                'last_run_time': result.get('last_run_time'),
                'total_rows_processed': result.get('total_rows_processed', 0) or 0
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

@st.cache_data(ttl=config.cache_config['metrics_ttl'])  # Cache for 10 minutes
def load_data_quality_checks():
    """Load data quality check results."""
    try:
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
        rows = db_service.execute_query(query)

        if rows:
            df = pd.DataFrame(rows)
            if not df.empty:
                df['check_time'] = pd.to_datetime(df['check_time'])
            return df

        return pd.DataFrame()
    except Exception as e:
        st.warning(f"Data quality checks not available: {str(e)}")
        return pd.DataFrame()

def send_slack_alert(message, level="info"):
    """Send alert to Slack webhook using common utility."""
    return send_slack_alert(message, level)

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
                (etl_data['start_time'] > datetime.now(timezone.utc) - timedelta(hours=24))
            ]
            if len(long_jobs) > 0:
                st.warning(f"⏱️ {len(long_jobs)} Long-running Jobs")
            else:
                st.success("✅ Normal Job Duration")
        else:
            st.info("ℹ️ No Data Available")

def etl_runs_page():
    """CryptoPrism Pipeline Monitoring - Track actual data flow and pipeline stages."""
    st.markdown('<div class="main-header">CryptoPrism Data Pipeline Monitor</div>', unsafe_allow_html=True)
    
    try:
        engine = get_db_connection()
        
        # Pipeline Stage Monitoring
        st.subheader("Data Pipeline Status")
        
        # SQLAlchemy connections are already in autocommit mode by default
        with engine.connect() as conn:
            # Check core data tables that feed the pipeline
            pipeline_tables = {
                'Stage 1 - Listings Data': 'crypto_listings',
                'Stage 2 - OHLCV Data': '108_1K_coins_ohlcv',
                'Stage 3 - Fear & Greed': 'FE_FEAR_GREED_CMC',
                'Stage 4 - Momentum Analysis': 'FE_MOMENTUM_SIGNALS',
                'Stage 5 - Oscillators Analysis': 'FE_OSCILLATORS_SIGNALS',
                'Stage 6 - Ratios Analysis': 'FE_RATIOS_SIGNALS',
                'Stage 7 - Metrics Analysis': 'FE_METRICS_SIGNAL',
                'Stage 8 - Volume Analysis': 'FE_TVV_SIGNALS',
                'Stage 9 - Final Aggregation': 'FE_DMV_ALL',
                'Stage 10 - Scoring': 'FE_DMV_SCORES'
            }
            
            pipeline_status = []
            
            for stage, table_name in pipeline_tables.items():
                try:
                    # Check if table exists
                    exists_check = f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table_name}'
                    )
                    """
                    exists = conn.execute(text(exists_check)).scalar()
                    
                    if exists:
                        # Get row count and latest timestamp
                        count_query = f'SELECT COUNT(*) FROM "{table_name}"'
                        count = conn.execute(text(count_query)).scalar()
                        
                        # Try to find timestamp column
                        latest_update = None
                        latest_update_ist = None
                        for col in ['updated_at', 'created_at', 'timestamp', 'date', 'last_updated']:
                            try:
                                timestamp_query = f'SELECT MAX({col}) FROM "{table_name}" WHERE {col} IS NOT NULL'
                                latest = conn.execute(text(timestamp_query)).scalar()
                                if latest:
                                    latest_update = latest
                                    latest_update_ist = (latest + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M IST')
                                    break
                            except:
                                continue
                        
                        # Determine freshness status
                        if latest_update:
                            hours_old = (datetime.now(timezone.utc) - latest_update.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                            if hours_old < 24:
                                freshness = 'Fresh'
                                status = 'Active'
                            elif hours_old < 72:
                                freshness = 'Stale'
                                status = 'Warning'
                            else:
                                freshness = 'Very Old'
                                status = 'Critical'
                        else:
                            freshness = 'Unknown'
                            status = 'Warning'
                        
                        pipeline_status.append({
                            'stage': stage,
                            'table': table_name,
                            'status': status,
                            'records': f"{count:,}",
                            'last_update': latest_update_ist or 'No timestamp found',
                            'freshness': freshness
                        })
                    else:
                        pipeline_status.append({
                            'stage': stage,
                            'table': table_name,
                            'status': 'Missing',
                            'records': '0',
                            'last_update': 'Table not found',
                            'freshness': 'N/A'
                        })
                        
                except Exception as e:
                    pipeline_status.append({
                        'stage': stage,
                        'table': table_name,
                        'status': 'Error',
                        'records': 'Error',
                        'last_update': f'Error: {str(e)[:50]}...',
                        'freshness': 'Error'
                    })
        
        # Display pipeline status
        if pipeline_status:
            df_pipeline = pd.DataFrame(pipeline_status)
            
            # Metrics summary
            col1, col2, col3, col4 = st.columns(4)
            
            active_stages = len([s for s in pipeline_status if s['status'] == 'Active'])
            warning_stages = len([s for s in pipeline_status if s['status'] == 'Warning'])
            missing_stages = len([s for s in pipeline_status if s['status'] == 'Missing'])
            total_records = sum([int(str(s['records']).replace(',', '')) for s in pipeline_status if str(s['records']).replace(',', '').isdigit()])
            
            with col1:
                st.metric("Active Stages", f"{active_stages}/{len(pipeline_status)}")
            with col2:
                st.metric("Warning Stages", warning_stages)
            with col3:
                st.metric("Missing Stages", missing_stages)
            with col4:
                st.metric("Total Records", f"{total_records:,}")
            
            # Pipeline status table with styling
            st.subheader("Pipeline Stage Details")
            
            def style_pipeline_status(val):
                if 'Active' in str(val):
                    return 'color: #28a745; font-weight: bold'
                elif 'Warning' in str(val):
                    return 'color: #ffc107; font-weight: bold'
                elif 'Missing' in str(val) or 'Critical' in str(val):
                    return 'color: #dc3545; font-weight: bold'
                return ''
            
            styled_pipeline = df_pipeline.style.applymap(style_pipeline_status, subset=['status'])
            st.dataframe(styled_pipeline, use_container_width=True, height=400)
        
        # Data Flow Analysis
        st.subheader("Data Flow Analysis")
        
        with engine.connect() as conn:
            # Analyze data flow between key stages
            data_flow_checks = [
                {
                    'flow': 'Listings → OHLCV',
                    'description': 'Check if OHLCV has data for listed cryptocurrencies',
                    'query': '''
                    SELECT COUNT(DISTINCT l.symbol) as listings_count,
                           COUNT(DISTINCT o.slug) as ohlcv_count
                    FROM "crypto_listings_latest_1000" l
                    LEFT JOIN "1K_coins_ohlcv" o ON l.symbol = o.slug
                    '''
                },
                {
                    'flow': 'OHLCV → FE_DMV_ALL',
                    'description': 'Check data flow from price data to final analysis',
                    'query': '''
                    SELECT COUNT(DISTINCT o.slug) as ohlcv_symbols,
                           COUNT(DISTINCT d.slug) as analysis_symbols  
                    FROM "1K_coins_ohlcv" o
                    LEFT JOIN "FE_DMV_ALL" d ON o.slug = d.slug
                    '''
                }
            ]
            
            flow_results = []
            for flow_check in data_flow_checks:
                try:
                    result = conn.execute(text(flow_check['query'])).fetchone()
                    flow_results.append({
                        'flow': flow_check['flow'],
                        'description': flow_check['description'],
                        'source_count': result[0] if result[0] else 0,
                        'target_count': result[1] if result[1] else 0,
                        'flow_rate': f"{(result[1]/result[0]*100):.1f}%" if result[0] and result[0] > 0 else "0%"
                    })
                except Exception as e:
                    flow_results.append({
                        'flow': flow_check['flow'],
                        'description': flow_check['description'],
                        'source_count': 'Error',
                        'target_count': 'Error', 
                        'flow_rate': f'Error: {str(e)[:30]}...'
                    })
            
            if flow_results:
                st.subheader("Data Flow Efficiency")
                for flow in flow_results:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**{flow['flow']}**")
                        st.write(flow['description'])
                    with col2:
                        st.metric("Flow Rate", flow['flow_rate'])
                    with col3:
                        st.write(f"Source: {flow['source_count']}")
                        st.write(f"Target: {flow['target_count']}")
        
        # Recent Data Updates
        st.subheader("Recent Data Activity")
        
        try:
            recent_updates = []
            key_tables = ['crypto_listings_latest_1000', '1K_coins_ohlcv', 'FE_DMV_ALL']
            
            with engine.connect() as conn:
                for table in key_tables:
                    try:
                        # Check if table exists first
                        exists_check = f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' AND table_name = '{table}'
                        )
                        """
                        if conn.execute(text(exists_check)).scalar():
                            # Find timestamp column and get latest update
                            for col in ['updated_at', 'timestamp', 'created_at', 'date']:
                                try:
                                    update_query = f'SELECT MAX({col}) FROM "{table}"'
                                    latest = conn.execute(text(update_query)).scalar()
                                    if latest:
                                        latest_ist = (latest + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M IST')
                                        hours_ago = (datetime.now(timezone.utc) - latest.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                                        recent_updates.append({
                                            'table': table,
                                            'last_update': latest_ist,
                                            'hours_ago': f"{hours_ago:.1f}h ago"
                                        })
                                        break
                                except:
                                    continue
                    except Exception as e:
                        recent_updates.append({
                            'table': table,
                            'last_update': f'Error: {str(e)[:30]}...',
                            'hours_ago': 'Error'
                        })
            
            if recent_updates:
                update_col1, update_col2, update_col3 = st.columns(3)
                for i, update in enumerate(recent_updates):
                    with [update_col1, update_col2, update_col3][i % 3]:
                        st.metric(
                            update['table'].replace('_', ' ').title(),
                            update['hours_ago'],
                            delta=update['last_update']
                        )
        
        except Exception as e:
            st.error(f"Recent activity check failed: {str(e)}")
    
    except Exception as e:
        st.error(f"Pipeline monitoring failed: {str(e)}")

def run_database_quality_checks():
    """Run comprehensive database quality checks directly."""
    try:
        engine = get_db_connection()
        validation_results = []
        
        with engine.connect() as conn:
            # Check 1: FE Tables Existence
            fe_table_check = """
            SELECT table_name
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'FE_%'
            """
            fe_tables = conn.execute(text(fe_table_check)).fetchall()
            
            validation_results.append({
                'test': 'FE Tables Existence',
                'status': 'PASSED' if len(fe_tables) > 0 else 'FAILED',
                'description': f'Found {len(fe_tables)} FE tables in database',
                'details': [row[0] for row in fe_tables]
            })
            
            # Check 2: Primary Keys Validation
            pk_check = """
            SELECT t.table_name
            FROM information_schema.tables t
            LEFT JOIN information_schema.table_constraints tc 
                ON t.table_name = tc.table_name 
                AND tc.constraint_type = 'PRIMARY KEY'
            WHERE t.table_schema = 'public' 
                AND t.table_type = 'BASE TABLE'
                AND tc.constraint_name IS NULL
            """
            missing_pk_tables = conn.execute(text(pk_check)).fetchall()
            
            validation_results.append({
                'test': 'Primary Keys Validation',
                'status': 'PASSED' if len(missing_pk_tables) == 0 else 'WARNING',
                'description': f'{len(missing_pk_tables)} tables without primary keys',
                'details': [row[0] for row in missing_pk_tables] if missing_pk_tables else []
            })
            
            # Check 3: FE Tables Data Validation
            for table_row in fe_tables[:5]:  # Check first 5 FE tables
                table_name = table_row[0]
                try:
                    data_check = f'SELECT COUNT(*) FROM "{table_name}"'
                    count = conn.execute(text(data_check)).scalar()
                    
                    validation_results.append({
                        'test': f'{table_name} Data Check',
                        'status': 'PASSED' if count > 0 else 'WARNING',
                        'description': f'Table contains {count:,} records',
                        'details': f'Row count: {count:,}'
                    })
                except Exception as e:
                    validation_results.append({
                        'test': f'{table_name} Data Check',
                        'status': 'FAILED',
                        'description': f'Error accessing table: {str(e)}',
                        'details': str(e)
                    })
            
            # Check 4: Timestamp Validation for FE Tables
            timestamp_issues = []
            for table_row in fe_tables[:3]:
                table_name = table_row[0]
                try:
                    timestamp_check = f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    AND data_type IN ('timestamp without time zone', 'timestamp with time zone', 'date')
                    """
                    timestamp_cols = conn.execute(text(timestamp_check)).fetchall()
                    
                    if not timestamp_cols:
                        timestamp_issues.append(f'{table_name}: No timestamp columns')
                    
                except Exception:
                    timestamp_issues.append(f'{table_name}: Error checking timestamps')
            
            validation_results.append({
                'test': 'FE Tables Timestamp Validation',
                'status': 'PASSED' if len(timestamp_issues) == 0 else 'WARNING',
                'description': f'{len(timestamp_issues)} timestamp-related issues found',
                'details': timestamp_issues
            })
            
            # Check 5: Database Connection and Performance
            start_time = time.time()
            conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
            query_time = (time.time() - start_time) * 1000
            
            validation_results.append({
                'test': 'Database Performance Check',
                'status': 'PASSED' if query_time < 1000 else 'WARNING',
                'description': f'Schema query executed in {query_time:.2f}ms',
                'details': f'Query time: {query_time:.2f}ms'
            })
        
        return validation_results
    
    except Exception as e:
        return [{
            'test': 'Database Connection',
            'status': 'FAILED',
            'description': f'Failed to connect to database: {str(e)}',
            'details': str(e)
        }]

def qa_checks_page():
    """Data quality assurance page with direct database validation."""
    st.markdown('<div class="main-header">Data Quality Assurance</div>', unsafe_allow_html=True)
    
    # Run Quality Validation
    st.subheader("Run Database Validation")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Run Complete Database Validation", type="primary"):
            with st.spinner("Running comprehensive database validation..."):
                results = run_database_quality_checks()
                
                # Display results summary
                total_tests = len(results)
                passed_tests = sum(1 for r in results if r.get('status') == 'PASSED')
                warning_tests = sum(1 for r in results if r.get('status') == 'WARNING')
                failed_tests = sum(1 for r in results if r.get('status') == 'FAILED')
                
                st.success(f"Validation completed! {total_tests} tests run")
                
                # Metrics row
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Tests", total_tests)
                with col2:
                    st.metric("Passed", passed_tests, delta=None)
                with col3:
                    st.metric("Warnings", warning_tests, delta=None)
                with col4:
                    st.metric("Failed", failed_tests, delta=None)
                
                # Show detailed results
                st.subheader("Validation Results")
                
                for result in results:
                    status = result.get('status', 'UNKNOWN')
                    if status == 'PASSED':
                        st.success(f"✅ **{result['test']}**: {result['description']}")
                    elif status == 'WARNING':
                        st.warning(f"⚠️ **{result['test']}**: {result['description']}")
                    elif status == 'FAILED':
                        st.error(f"❌ **{result['test']}**: {result['description']}")
                    
                    if result.get('details') and isinstance(result['details'], list) and len(result['details']) > 0:
                        with st.expander(f"Details for {result['test']}"):
                            for detail in result['details']:
                                st.write(f"• {detail}")
                    elif result.get('details') and isinstance(result['details'], str):
                        st.write(f"  Details: {result['details']}")
    
    with col2:
        st.subheader("Quick Tests")
        
        if st.button("Test FE Tables", type="secondary"):
            with st.spinner("Checking FE tables..."):
                try:
                    engine = get_db_connection()
                    with engine.connect() as conn:
                        fe_check = """
                        SELECT table_name, 
                               (SELECT COUNT(*) FROM information_schema.columns 
                                WHERE table_name = t.table_name) as column_count
                        FROM information_schema.tables t
                        WHERE table_schema = 'public' 
                        AND table_name LIKE 'FE_%'
                        ORDER BY table_name
                        """
                        fe_results = conn.execute(text(fe_check)).fetchall()
                    
                    if fe_results:
                        st.success(f"Found {len(fe_results)} FE tables")
                        for table, cols in fe_results:
                            st.write(f"• **{table}**: {cols} columns")
                    else:
                        st.warning("No FE tables found")
                        
                except Exception as e:
                    st.error(f"FE tables check failed: {str(e)}")
    
    # Live Database Health Monitor
    st.subheader("Live Database Health Monitor")
    
    # Auto-refresh health stats
    health_placeholder = st.empty()
    
    try:
        engine = get_db_connection()
        with engine.connect() as conn:
            # Get real-time stats
            stats_query = """
            SELECT 
                (SELECT COUNT(*) FROM information_schema.tables 
                 WHERE table_schema = 'public' AND table_type = 'BASE TABLE') as total_tables,
                (SELECT COUNT(*) FROM information_schema.tables 
                 WHERE table_schema = 'public' AND table_name LIKE 'FE_%') as fe_tables,
                (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                (SELECT pg_size_pretty(pg_database_size(current_database()))) as db_size
            """
            stats = conn.execute(text(stats_query)).fetchone()
        
        # Display health metrics
        with health_placeholder.container():
            health_col1, health_col2, health_col3, health_col4 = st.columns(4)
            
            with health_col1:
                st.metric("Total Tables", stats[0])
            with health_col2: 
                st.metric("FE Tables", stats[1])
            with health_col3:
                st.metric("Active Connections", stats[2])
            with health_col4:
                st.metric("Database Size", stats[3])
                
    except Exception as e:
        st.error(f"Health monitor unavailable: {str(e)}")
    
    # Historical Quality Checks (if data_quality_checks table exists)
    st.subheader("Historical Quality Checks")
    
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
            if st.button("Database Query Analysis", type="primary"):
                with st.spinner("Running database query analysis..."):
                    try:
                        engine = get_db_connection()
                        start_time = time.time()
                        
                        # Run primary key analysis directly
                        with engine.connect() as conn:
                            pk_query = """
                            SELECT 
                                c.conname as constraint_name,
                                t.relname as table_name,
                                'PRIMARY KEY' as constraint_type
                            FROM pg_constraint c
                            JOIN pg_class t ON c.conrelid = t.oid
                            JOIN pg_namespace n ON t.relnamespace = n.oid
                            WHERE c.contype = 'p'
                                AND n.nspname = 'public'
                            ORDER BY t.relname
                            """
                            result = conn.execute(text(pk_query))
                            pk_results = [row._asdict() for row in result]
                        
                        exec_time = (time.time() - start_time) * 1000
                        
                        st.success("Database analysis completed!")
                        st.metric("Execution Time", f"{exec_time:.2f} ms")
                        st.metric("Primary Keys Found", len(pk_results))
                        
                        if pk_results:
                            st.subheader("Primary Key Analysis Results")
                            for result in pk_results[:15]:  # Show first 15
                                st.write(f"• {result['table_name']} [{result['constraint_name']}]")
                        
                        # Query performance metrics
                        with engine.connect() as conn:
                            perf_query = """
                            SELECT 
                                schemaname,
                                tablename,
                                n_tup_ins as inserts,
                                n_tup_upd as updates,
                                n_tup_del as deletes
                            FROM pg_stat_user_tables 
                            WHERE schemaname = 'public'
                            ORDER BY (n_tup_ins + n_tup_upd + n_tup_del) DESC
                            LIMIT 10
                            """
                            result = conn.execute(text(perf_query))
                            perf_results = [row._asdict() for row in result]
                        
                        if perf_results:
                            st.subheader("Table Activity Statistics")
                            for result in perf_results:
                                total_ops = result['inserts'] + result['updates'] + result['deletes']
                                st.write(f"• {result['tablename']}: {total_ops:,} total operations")
                        
                    except Exception as e:
                        st.error(f"Database analysis failed: {str(e)}")
        
        with col2:
            if st.button("Table Schema Analysis", type="secondary"):
                with st.spinner("Running table schema analysis..."):
                    try:
                        engine = get_db_connection()
                        
                        # Get table and column information
                        with engine.connect() as conn:
                            schema_query = """
                            SELECT 
                                t.table_name,
                                COUNT(c.column_name) as column_count,
                                STRING_AGG(DISTINCT c.data_type, ', ') as data_types
                            FROM information_schema.tables t
                            LEFT JOIN information_schema.columns c 
                                ON t.table_name = c.table_name 
                                AND t.table_schema = c.table_schema
                            WHERE t.table_schema = 'public'
                                AND t.table_type = 'BASE TABLE'
                            GROUP BY t.table_name
                            ORDER BY column_count DESC
                            """
                            result = conn.execute(text(schema_query))
                            schema_results = [row._asdict() for row in result]
                        
                        st.success("Schema analysis completed!")
                        st.metric("Tables Analyzed", len(schema_results))
                        
                        if schema_results:
                            st.subheader("Table Schema Summary")
                            for result in schema_results[:15]:  # Show first 15
                                st.write(f"• **{result['table_name']}**: {result['column_count']} columns")
                                if result['data_types']:
                                    st.write(f"  Types: {result['data_types']}")
                        
                        # Check for FE tables specifically
                        fe_tables_found = [r for r in schema_results if r['table_name'].startswith('FE_')]
                        if fe_tables_found:
                            st.subheader(f"FE Tables Found: {len(fe_tables_found)}")
                            for fe_table in fe_tables_found:
                                st.write(f"• **{fe_table['table_name']}**: {fe_table['column_count']} columns")
                        
                    except Exception as e:
                        st.error(f"Schema analysis failed: {str(e)}")
        
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
                
                # Table sizes - Fixed for case-sensitive PostgreSQL table names
                table_sizes_query = """
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size('"' || tablename || '"')) as size,
                    pg_total_relation_size('"' || tablename || '"') as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size('"' || tablename || '"') DESC
                LIMIT 10;
                """
                result = conn.execute(text(table_sizes_query))
                table_sizes = pd.DataFrame([row._asdict() for row in result])
            
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
    """Business intelligence and signals page with FE tables monitoring."""
    st.markdown('<div class="main-header">📈 Technical Analysis & FE Tables Monitor</div>', unsafe_allow_html=True)
    
    try:
        engine = get_db_connection()
        
        # Core FE Tables from CryptoPrism pipeline (correct naming from validation suite)
        fe_tables = [
            'FE_MOMENTUM_SIGNALS',
            'FE_OSCILLATORS_SIGNALS', 
            'FE_RATIOS_SIGNALS',
            'FE_METRICS_SIGNAL',
            'FE_TVV_SIGNALS',
            'FE_DMV_ALL',
            'FE_DMV_SCORES',
            'FE_MOMENTUM',  # Additional FE tables found in validation
            'FE_OSCILLATORS'  # Additional FE tables found in validation
        ]
        
        # FE Tables Status Dashboard
        st.subheader("🔧 Core FE Tables Pipeline Status")
        
        fe_table_stats = []
        
        for table in fe_tables:
            try:
                with engine.connect() as conn:
                    # Check if table exists (using exact case-sensitive table name)
                    exists_query = f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table}'
                    );
                    """
                    table_exists = conn.execute(text(exists_query)).scalar()
                    
                    if table_exists:
                        # Get row count (using double quotes for PostgreSQL case sensitivity)
                        count_query = f'SELECT COUNT(*) as row_count FROM "{table}"'
                        count = conn.execute(text(count_query)).scalar()
                        
                        # Get table size (using double quotes)
                        size_query = f"""
                        SELECT pg_size_pretty(pg_total_relation_size('public."{table}"')) as table_size
                        """
                        size = conn.execute(text(size_query)).scalar()
                        
                        # Get last update time in IST
                        timestamp_columns = ['updated_at', 'created_at', 'timestamp', 'last_updated', 'date_created']
                        latest_update = None
                        latest_update_ist = None
                        
                        for col in timestamp_columns:
                            try:
                                latest_query = f"""
                                SELECT MAX({col}) as latest_update
                                FROM "{table}"
                                WHERE {col} IS NOT NULL
                                """
                                latest = conn.execute(text(latest_query)).scalar()
                                if latest:
                                    latest_update = latest
                                    # Convert to IST (UTC + 5:30)
                                    if latest_update:
                                        latest_update_ist = latest_update + timedelta(hours=5, minutes=30)
                                    break
                            except:
                                continue
                        
                        # Get today's data count
                        today_count = 0
                        try:
                            if latest_update:
                                working_col = None
                                for col in timestamp_columns:
                                    try:
                                        # Test if column exists first
                                        test_query = f'SELECT {col} FROM "{table}" LIMIT 1'
                                        conn.execute(text(test_query)).fetchone()
                                        working_col = col
                                        break
                                    except:
                                        continue
                                
                                if working_col:
                                    today_query = f"""
                                    SELECT COUNT(*) 
                                    FROM "{table}"
                                    WHERE DATE({working_col}) = CURRENT_DATE
                                    """
                                    today_count = conn.execute(text(today_query)).scalar() or 0
                        except:
                            pass
                        
                        fe_table_stats.append({
                            'table_name': table,
                            'status': '✅ Active',
                            'row_count': f"{count:,}",
                            'table_size': size,
                            'last_update_utc': latest_update.strftime('%Y-%m-%d %H:%M:%S UTC') if latest_update else 'No timestamp found',
                            'last_update_ist': latest_update_ist.strftime('%Y-%m-%d %H:%M:%S IST') if latest_update_ist else 'No timestamp found',
                            'today_records': today_count,
                            'pipeline_stage': get_pipeline_stage(table)
                        })
                    else:
                        fe_table_stats.append({
                            'table_name': table,
                            'status': '❌ Missing',
                            'row_count': 0,
                            'table_size': 'N/A',
                            'last_update_utc': 'Table not found',
                            'last_update_ist': 'Table not found', 
                            'today_records': 0,
                            'pipeline_stage': get_pipeline_stage(table)
                        })
            except Exception as e:
                fe_table_stats.append({
                    'table_name': table,
                    'status': f"❌ Error: {str(e)[:50]}...",
                    'row_count': 'Error',
                    'table_size': 'Error',
                    'last_update_utc': 'Error',
                    'last_update_ist': 'Error',
                    'today_records': 'Error',
                    'pipeline_stage': get_pipeline_stage(table)
                })
        
        # Display FE Tables Status
        fe_stats_df = pd.DataFrame(fe_table_stats)
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        active_tables = len([s for s in fe_table_stats if '✅ Active' in s['status']])
        total_records = sum([int(str(s['row_count']).replace(',', '')) for s in fe_table_stats if str(s['row_count']).replace(',', '').isdigit()])
        tables_updated_today = len([s for s in fe_table_stats if str(s['today_records']).isdigit() and int(s['today_records']) > 0])
        
        with col1:
            st.metric("Active FE Tables", f"{active_tables}/{len(fe_tables)}")
        with col2:
            st.metric("Total Records", f"{total_records:,}")
        with col3:
            st.metric("Updated Today", tables_updated_today)
        with col4:
            # Pipeline health score
            health_score = (active_tables / len(fe_tables)) * 100
            st.metric("Pipeline Health", f"{health_score:.1f}%")
        
        # Detailed table view
        st.subheader("📊 Detailed FE Tables Status")
        
        # Style the dataframe based on status
        def style_fe_status(val):
            if '✅ Active' in str(val):
                return 'color: #28a745; font-weight: bold'
            elif '❌' in str(val):
                return 'color: #dc3545; font-weight: bold'
            return ''
        
        styled_fe_df = fe_stats_df.style.applymap(style_fe_status, subset=['status'])
        st.dataframe(styled_fe_df, use_container_width=True, height=400)
        
        # Pipeline Flow Visualization
        st.subheader("🔄 Technical Analysis Pipeline Flow")
        
        pipeline_info = {
            "Stage 1 - Data Ingestion": ["LISTINGS (CMC)", "OHLCV (Historical)", "Fear & Greed Index"],
            "Stage 2 - Technical Analysis": ["FE_METRICS_SIGNAL", "FE_TVV_SIGNALS", "FE_MOMENTUM_SIGNALS"],
            "Stage 3 - Advanced Analysis": ["FE_OSCILLATORS_SIGNALS", "FE_RATIOS_SIGNALS"],
            "Stage 4 - Signal Aggregation": ["FE_DMV_ALL", "FE_DMV_SCORES"]
        }
        
        for stage, tables in pipeline_info.items():
            with st.expander(f"🔍 {stage}"):
                st.write("**Tables/Processes:**")
                for table in tables:
                    # Check if this is an FE table and get its status
                    if table in [s['table_name'] for s in fe_table_stats]:
                        status = next(s['status'] for s in fe_table_stats if s['table_name'] == table)
                        st.write(f"• {table} - {status}")
                    else:
                        st.write(f"• {table}")
        
        # All Signal Tables Discovery
        st.subheader("🔍 All Signal & FE Tables Discovery")
        
        with engine.connect() as conn:
            all_tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE '%SIGNAL%' OR table_name LIKE 'FE_%')
            ORDER BY table_name;
            """
            result = conn.execute(text(all_tables_query))
            all_signal_tables = pd.DataFrame([row._asdict() for row in result])
        
        if not all_signal_tables.empty:
            discovered_stats = []
            
            for table in all_signal_tables['table_name']:
                if table not in fe_tables:  # Show additional tables not in core FE list
                    try:
                        with engine.connect() as conn:
                            count_query = f'SELECT COUNT(*) as row_count FROM "{table}"'
                            count = conn.execute(text(count_query)).scalar()
                            
                            # Try to get latest timestamp
                            latest_update_ist = None
                            try:
                                for col in ['updated_at', 'created_at', 'timestamp']:
                                    try:
                                        latest_query = f'SELECT MAX({col}) FROM "{table}"'
                                        latest = conn.execute(text(latest_query)).scalar()
                                        if latest:
                                            latest_update_ist = (latest + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S IST')
                                            break
                                    except:
                                        continue
                            except:
                                pass
                            
                            discovered_stats.append({
                                'table_name': table,
                                'row_count': f"{count:,}",
                                'last_update_ist': latest_update_ist or 'No timestamp found',
                                'type': 'Additional Signal Table'
                            })
                    except Exception as e:
                        discovered_stats.append({
                            'table_name': table,
                            'row_count': f"Error: {str(e)}",
                            'last_update_ist': 'Error',
                            'type': 'Additional Signal Table'
                        })
            
            if discovered_stats:
                st.write("**Additional Signal Tables Found:**")
                discovered_df = pd.DataFrame(discovered_stats)
                st.dataframe(discovered_df, use_container_width=True)
            else:
                st.info("All signal tables are part of the core FE pipeline.")
        else:
            st.warning("No additional signal tables found beyond core FE tables.")
    
    except Exception as e:
        st.error(f"Unable to load FE tables monitoring: {str(e)}")

def get_pipeline_stage(table_name):
    """Get the pipeline stage for a given FE table."""
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

# Main application
def main():
    """Main Streamlit application."""
    
    # if not check_authentication():
    #     return
    check_authentication()
    
    # Sidebar navigation
        
    pages = {
        "🏠 Overview": render_overview_page,
        "📊 Pipeline Monitor": render_pipeline_monitor_page,
        "✅ QA Checks": render_qa_checks_page,
        "⚡ Performance": render_performance_page,
        "📈 FE Tables Monitor": render_business_signals_page,
        "📜 Logs & Artifacts": render_logs_page
    }
    
    selected_page = st.sidebar.radio("Navigation", list(pages.keys()))
    
    # Auto-refresh toggle
    auto_refresh_enabled = config.ui_config['auto_refresh']
    auto_refresh_interval = config.ui_config['refresh_interval']
    auto_refresh = st.sidebar.checkbox(
        f"Auto-refresh ({auto_refresh_interval}s)",
        value=auto_refresh_enabled
    )
    if auto_refresh:
        time.sleep(auto_refresh_interval)
        st.rerun()

    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

    # Logout button
    if st.sidebar.button("🚪 Logout"):
        logout_user()
        st.rerun()

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**CryptoPrism Dashboard v" + os.getenv('DASHBOARD_VERSION', '1.0.0') + "**")
    st.sidebar.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run selected page
    pages[selected_page]()

if __name__ == "__main__":
    main()