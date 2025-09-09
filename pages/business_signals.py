#!/usr/bin/env python3
"""
Business Intelligence Signals Dashboard Page

Analyzes and monitors Feature Engineering (FE) tables for business signals
and data integrity.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text

from services.database_service import db_service
from utils.helpers import format_number, styled_metric_card


def render_business_signals_page():
    """Business intelligence and signals page with FE tables monitoring."""
    st.markdown('<div class="main-header">📈 Technical Analysis & FE Tables Monitor</div>', unsafe_allow_html=True)
    
    try:
        # Core FE Tables from CryptoPrism pipeline 
        fe_tables = [
            'FE_MOMENTUM_SIGNALS',
            'FE_OSCILLATORS_SIGNALS', 
            'FE_RATIOS_SIGNALS',
            'FE_METRICS_SIGNAL',
            'FE_TVV_SIGNALS',
            'FE_DMV_ALL',
            'FE_DMV_SCORES',
            'FE_MOMENTUM',
            'FE_OSCILLATORS'
        ]
        
        # FE Tables Status Dashboard
        st.subheader("🔧 Core FE Tables Pipeline Status")
        
        fe_table_stats = []
        
        # Use db_service to get table status efficiently
        fe_table_stats = db_service.get_fe_tables_status() # Assuming this method exists in db_service.py
        
        # Display FE Tables Status
        fe_stats_df = pd.DataFrame(fe_table_stats)
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        active_tables = len([s for s in fe_table_stats if 'Active' in s['status']])
        total_records = sum([s['row_count'] for s in fe_table_stats if isinstance(s['row_count'], int)])
        tables_updated_today = sum([1 for s in fe_table_stats if s.get('last_update') and (datetime.now() - s['last_update']).total_seconds() / 3600 < 24])
        
        with col1:
            st.metric("Active FE Tables", f"{active_tables}/{len(fe_tables)}")
        with col2:
            st.metric("Total Records", f"{total_records:,}")
        with col3:
            st.metric("Updated Today", tables_updated_today)
        with col4:
            # Pipeline health score
            health_score = (active_tables / len(fe_tables)) * 100 if len(fe_tables) > 0 else 0
            st.metric("Pipeline Health", f"{health_score:.1f}%")
        
        # Detailed table view
        st.subheader("📊 Detailed FE Tables Status")
        
        # Style the dataframe based on status
        def style_fe_status(val):
            if 'Active' in str(val):
                return 'color: #28a745; font-weight: bold'
            elif 'Missing' in str(val) or 'Error' in str(val):
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
        
        # Using db_service for querying all signal tables
        all_tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%SIGNAL%' OR table_name LIKE 'FE_%')
        ORDER BY table_name;
        """
        all_signal_tables = db_service.execute_query(all_tables_query)
        
        if all_signal_tables:
            discovered_stats = []
            
            for table_row in all_signal_tables:
                table_name = table_row['table_name']
                if table_name not in fe_tables:  # Show additional tables not in core FE list
                    try:
                        count = db_service.get_table_count(table_name)
                        latest_update = db_service._get_latest_timestamp(table_name) # Internal helper
                        
                        discovered_stats.append({
                            'table_name': table_name,
                            'row_count': f"{count:,}",
                            'last_update': latest_update.strftime('%Y-%m-%d %H:%M:%S UTC') if latest_update else 'No timestamp found',
                            'type': 'Additional Signal Table'
                        })
                    except Exception as e:
                        discovered_stats.append({
                            'table_name': table_name,
                            'row_count': f"Error: {str(e)}",
                            'last_update': 'Error',
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
    }
    return stage_mapping.get(table_name, 'Unknown Stage')
