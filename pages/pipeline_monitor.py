#!/usr/bin/env python3
"""
Data Pipeline Monitoring Page

Monitor and track actual data flow between pipeline stages,
check table freshness, and analyze data pipeline health.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text

from components.ui_components import (
    DashboardLayout, StatusIndicators, DataVisualization,
    DataDisplay
)
from services.database_service import db_service
from utils.helpers import (
    format_timestamp, format_number, get_age_hours,
    get_freshness_status, status_indicator
)


def render_pipeline_monitor_page():
    """Render the data pipeline monitoring page."""
    DashboardLayout.render_header(
        "CryptoPrism Data Pipeline Monitor",
        "Monitor and track data flow across analysis pipeline stages"
    )

    try:
        pipeline_tables = {
            'Raw Data Stage': {
                'LATEST_QUOTES': 'Latest market quotes',
                'LATEST_COINS': 'Latest coin information'
            },
            'Stage 1 - Listings Data': {
                'crypto_listings': 'CoinMarketCap listings data',
                'crypto_listings_latest_1000': 'Filtered top 1000 listings'
            },
            'Stage 2 - Historical Data': {
                '1K_coins_ohlcv': 'OHLCV price data for 1000 coins'
            },
            'Stage 3 - Sentiment Data': {
                'FE_FEAR_GREED_CMC': 'Fear & Greed Index'
            },
            'Stage 4 - Technical Analysis': {
                'FE_MOMENTUM_SIGNALS': 'Momentum indicators',
                'FE_OSCILLATORS_SIGNALS': 'Oscillator indicators',
                'FE_RATIOS_SIGNALS': 'Ratio-based signals',
                'FE_METRICS_SIGNAL': 'Technical metrics',
                'FE_TVV_SIGNALS': 'Volume & trend signals'
            },
            'Stage 5 - Aggregation': {
                'FE_DMV_ALL': 'Complete signal aggregation',
                'FE_DMV_SCORES': 'Final scoring results'
            }
        }

        # Pipeline status dashboard
        st.subheader("🔧 Pipeline Stage Status")

        pipeline_status = []

        # Check each pipeline stage
        for stage_name, tables in pipeline_tables.items():
            stage_status = check_pipeline_stage(stage_name, tables)
            pipeline_status.append(stage_status)

        # Display pipeline status summary
        render_pipeline_status_summary(pipeline_status)

        # Detailed pipeline status
        st.subheader("📊 Detailed Pipeline Status")
        pipeline_df = pd.DataFrame(pipeline_status)
        DataDisplay.render_dataframe_with_styling(pipeline_df, height=500)

        # Data Flow Analysis
        st.subheader("🔄 Data Flow Analysis")

        flow_checks = [
            {
                'name': 'Listings → OHLCV Flow',
                'description': 'Check if OHLCV data exists for listed cryptocurrencies',
                'query': '''
                SELECT
                    COUNT(DISTINCT cl.symbol) as listings_count,
                    COUNT(DISTINCT o.slug) as ohlcv_count
                FROM crypto_listings_latest_1000 cl
                LEFT JOIN "1K_coins_ohlcv" o ON cl.symbol = o.slug
                ''',
                'source_table': 'crypto_listings_latest_1000',
                'target_table': '1K_coins_ohlcv'
            },
            {
                'name': 'OHLCV → FE_DMV_ALL Flow',
                'description': 'Check data flow from price data to final analysis',
                'query': '''
                SELECT
                    COUNT(DISTINCT o.slug) as ohlcv_symbols,
                    COUNT(DISTINCT dmv.slug) as analysis_symbols
                FROM "1K_coins_ohlcv" o
                LEFT JOIN "FE_DMV_ALL" dmv ON o.slug = dmv.slug
                ''',
                'source_table': '1K_coins_ohlcv',
                'target_table': 'FE_DMV_ALL'
            },
            {
                'name': 'FE Tables Internal Flow',
                'description': 'Check data consistency between FE analysis tables',
                'query': '''
                SELECT
                    COUNT(DISTINCT momentum.slug) as momentum_records,
                    COUNT(DISTINCT osc. slug) as oscillator_records,
                    COUNT(DISTINCT dmv.slug) as dmv_records
                FROM FE_MOMENTUM_SIGNALS momentum
                LEFT JOIN FE_OSCILLATORS_SIGNALS osc ON momentum.slug = osc.slug
                LEFT JOIN FE_DMV_ALL dmv ON momentum.slug = dmv.slug
                ''',
                'source_table': 'FE_MOMENTUM_SIGNALS',
                'target_table': 'FE_DMV_ALL'
            }
        ]

        # Execute flow checks and display results
        for flow_check in flow_checks:
            render_data_flow_check(flow_check)

        # Recent data updates timeline
        st.subheader("📈 Recent Data Activity")

        key_tables = [
            'crypto_listings_latest_1000',
            '1K_coins_ohlcv',
            'FE_FEAR_GREED_CMC',
            'FE_DMV_ALL'
        ]

        render_recent_updates_dashboard(key_tables)

    except Exception as e:
        st.error(f"Pipeline monitoring failed: {str(e)}")


def check_pipeline_stage(stage_name: str, tables: dict) -> dict:
    """Check the status of a pipeline stage."""
    stage_records = 0
    stage_size = 0
    stage_fresh = 'Unknown'
    latest_update = None
    stage_health = 'Unknown'

    for table_name, description in tables.items():
        try:
            # Check if table exists
            if db_service.get_table_exists(table_name):
                # Get table statistics
                record_count = db_service.get_table_count(table_name)
                table_size = db_service.get_table_size(table_name)

                stage_records += record_count

                # Get latest timestamp (try multiple column names)
                timestamp_cols = ['updated_at', 'created_at', 'timestamp', 'last_updated', 'date']

                for col in timestamp_cols:
                    try:
                        query = f'SELECT MAX("{col}") FROM "{table_name}"'
                        result = db_service.execute_scalar(query)
                        if result:
                            result = result.replace(tzinfo=None) if hasattr(result, 'replace') else result
                            if latest_update is None or result > latest_update:
                                latest_update = result
                            break
                    except:
                        continue

                # Try to determine stage health
                if record_count > 0:
                    stage_health = 'Active'
                    break  # At least one table in stage is active
                else:
                    stage_health = 'Inactive'

            else:
                stage_health = 'Missing'

        except Exception as e:
            print(f"Error checking table {table_name}: {str(e)}")
            stage_health = 'Error'

    # Determine freshness status
    if latest_update:
        age_hours = get_age_hours(latest_update)
        stage_fresh = get_freshness_status(age_hours)
    else:
        stage_fresh = 'Unknown'

    return {
        'stage': stage_name,
        'description': f"Contains {len(tables)} data tables",
        'total_records': stage_records,
        'last_update': latest_update.isoformat() if latest_update else None,
        'freshness': stage_fresh,
        'health': stage_health,
        'tables': list(tables.keys())
    }


def render_pipeline_status_summary(pipeline_status: list):
    """Render pipeline status summary metrics."""
    # Calculate summary metrics
    active_stages = sum(1 for s in pipeline_status if s['health'] == 'Active')
    total_stages = len(pipeline_status)
    total_records = sum(s['total_records'] for s in pipeline_status)

    # Pipeline health score
    health_score = (active_stages / total_stages) * 100 if total_stages > 0 else 0

    metrics = [
        {
            'title': "Active Stages",
            'value': f"{active_stages}/{total_stages}",
            'color': "#28a745" if active_stages == total_stages else "#ffc107"
        },
        {
            'title': "Total Records",
            'value': format_number(total_records),
            'color': "#1f77b4"
        },
        {
            'title': "Pipeline Health",
            'value': f"{health_score:.1f}%",
            'color': "#17a2b8"
        }
    ]

    DashboardLayout.render_metric_grid(metrics, columns=3)


def render_data_flow_check(flow_check: dict):
    """Render a data flow check with results."""
    col1, col2 = st.columns([2, 1])

    with col1:
        st.write(f"**{flow_check['name']}**")
        st.write(flow_check['description'])

        try:
            result = db_service.execute_query_single(flow_check['query'])
            if result:
                source_count = result.get(list(result.keys())[0], 0)
                target_count = result.get(list(result.keys())[1], 0)

                if source_count > 0:
                    flow_rate = (target_count / source_count) * 100

                    with col2:
                        st.metric(f"Flow Rate",
                                f"{flow_rate:.1f}%" if flow_rate <= 100 else f"{flow_rate:.1f}%")

                        if flow_rate > 90:
                            st.success("✅ Good Flow")
                        elif flow_rate > 50:
                            st.warning("⚠️ Moderate Flow")
                        else:
                            st.error("❌ Poor Flow")

                    st.write(f"Source: {format_number(source_count)} | Target: {format_number(target_count)}")
                else:
                    st.warning("No source data to analyze")
            else:
                st.error("Flow check failed")

        except Exception as e:
            st.error(f"Flow analysis failed: {str(e)}")
            print(f"Flow check error: {str(e)}")


def render_recent_updates_dashboard(key_tables: list):
    """Render recent updates dashboard for key tables."""
    updates_info = []

    for table in key_tables:
        try:
            if db_service.get_table_exists(table):
                # Try to find timestamp column and get latest update
                timestamp_cols = ['updated_at', 'created_at', 'timestamp', 'last_updated']

                for col in timestamp_cols:
                    try:
                        query = f'SELECT MAX("{col}") FROM "{table_name}"'
                        latest = db_service.execute_scalar(query.replace('{table_name}', table))
                        if latest:
                            latest_timestamp = latest.replace(tzinfo=None)
                            age_hours = get_age_hours(latest_timestamp)

                            updates_info.append({
                                'table': table.replace('_', ' ').title(),
                                'last_update': format_timestamp(latest_timestamp),
                                'hours_ago': age_hours,
                                'status': 'updated' if age_hours < 24 else 'stale'
                            })
                            break
                    except:
                        continue
                else:
                    updates_info.append({
                        'table': table.replace('_', ' ').title(),
                        'last_update': 'No timestamp column',
                        'hours_ago': None,
                        'status': 'unknown'
                    })
            else:
                updates_info.append({
                    'table': table.replace('_', ' ').title(),
                    'last_update': 'Table not found',
                    'hours_ago': None,
                    'status': 'missing'
                })

        except Exception as e:
            updates_info.append({
                'table': table.replace('_', ' ').title(),
                'last_update': f'Error: {str(e)}',
                'hours_ago': None,
                'status': 'error'
            })

    # Display updates in cards
    if updates_info:
        from config.settings import config
        ui_theme = config.ui_config

        cols = st.columns(min(len(updates_info), 4))

        for i, update in enumerate(updates_info):
            with cols[i % len(cols)]:
                color = {
                    'updated': '#28a745',
                    'stale': '#ffc107',
                    'unknown': '#6c757d',
                    'missing': '#dc3545',
                    'error': '#dc3545'
                }.get(update['status'], ui_theme['primary_color'])

                if update['hours_ago'] is not None and update['hours_ago'] < 24:
                    delta_value = f"Updated {update['hours_ago']:.1f}h ago"
                else:
                    delta_value = update['last_update']

                styled_metric_card(
                    title=f"📊 {update['table']}",
                    value=delta_value,
                    delta=None,
                    color=color
                )
    else:
        st.warning("No recent update information available")