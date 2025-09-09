#!/usr/bin/env python3
"""
Performance Analytics Dashboard Page

Provides insights into database performance, query optimization,
and schema analysis, leveraging specialized toolkits.
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime

from components.ui_components import (
    DashboardLayout, DataDisplay, DataVisualization,
    PerformanceMonitors
)
from services.database_service import db_service
from utils.helpers import format_number, send_slack_alert

# Import the optimized toolkits
from crypto_db_utils.validation.comprehensive_validation_suite import ComprehensiveValidationSuite
from crypto_db_utils.optimization.query_optimizer import QueryOptimizer
from crypto_db_utils.analysis.schema_analyzer import SchemaAnalyzer


def render_performance_page():
    """Render the database performance analytics page."""
    DashboardLayout.render_header(
        "⚡ Database Performance Analytics",
        "Gain insights into query performance, schema health, and optimization opportunities."
    )

    st.subheader("🔧 Performance & Schema Toolkits")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Run Primary Key Analysis (Optimized)", type="primary"):
            run_optimized_pk_analysis()

    with col2:
        if st.button("📋 Run Table Schema Analysis", type="secondary"):
            run_optimized_schema_analysis()

    st.subheader("📈 Real-time Database Metrics")
    render_realtime_db_metrics()

    st.subheader("💾 Table & Index Usage")
    render_table_index_stats()

    st.subheader("📊 Benchmarking & Optimization")
    render_benchmarking_section()


def run_optimized_pk_analysis():
    """Run and display results from the optimized primary key validation."""
    with st.spinner("Running optimized primary key analysis..."):
        try:
            start_time = time.time()
            # Use the ComprehensiveValidationSuite which incorporates the optimized PK check
            validator = ComprehensiveValidationSuite(db_service=db_service)
            # Direct call to the optimized PK validation logic if exposed, otherwise rely on full suite
            pk_results = validator.validate_primary_keys()

            end_time = time.time()
            execution_time = (end_time - start_time) * 1000

            if pk_results:
                # Display summary of primary key validation
                missing_pks = [r for r in pk_results if r['status'] in ['WARNING', 'FAILED']]
                if missing_pks:
                    st.warning(f"⚠️ {len(missing_pks)} tables are missing primary keys or have issues.")
                else:
                    st.success("✅ All tables have primary keys.")

                st.subheader("Detailed Primary Key Validation Results")

                # Display detailed results
                for result in pk_results:
                    if result['status'] == 'PASSED':
                        st.success(f"✅ **{result['test']}**: {result['description']}")
                    elif result['status'] == 'WARNING':
                        st.warning(f"⚠️ **{result['test']}**: {result['description']}")
                        if result['details']:
                            with st.expander("Details"):
                                for detail in result['details']:
                                    st.write(f"- {detail}")
                    elif result['status'] == 'FAILED':
                        st.error(f"❌ **{result['test']}**: {result['description']}")
                        if result['details']:
                            with st.expander("Details"):
                                for detail in result['details']:
                                    st.write(f"- {detail}")
            else:
                st.info("No primary key validation results available.")

        except Exception as e:
            st.error(f"Error running optimized primary key analysis: {str(e)}")
            send_slack_alert(f"Performance Page PK Analysis Error: {str(e)}", "error")


def run_optimized_schema_analysis():
    """Run and display results from the schema analysis toolkit."""
    with st.spinner("Running table schema analysis..."):
        try:
            start_time = time.time()
            executor = SchemaAnalyzer(db_service=db_service)
            # The analyze_schema method will return a structured report
            detailed_schema_results = executor.analyze_schema()

            end_time = time.time()
            execution_time = (end_time - start_time) * 1000

            st.success(f"Schema analysis completed in {execution_time:.2f}ms!")
            st.metric("Tables Analyzed", len(detailed_schema_results))

            if detailed_schema_results:
                st.subheader("Detailed Table Schema Summary")
                df_schema = pd.DataFrame(detailed_schema_results)

                # Create columns for better display with expanders
                for i, row in df_schema.iterrows():
                    with st.expander(f"**{row['table_name']}** ({row['column_count']} columns)"):
                        st.write(f"Description: {row['description']}")
                        st.write(f"Data Types: {row['data_types']}")
                        if row['pk_columns']:
                            st.markdown(f"Primary Keys: `{', '.join(row['pk_columns'])}`")
                        if row['indexed_columns']:
                            st.markdown(f"Indexed Columns: `{', '.join(row['indexed_columns'])}`")
                        if row['foreign_keys']:
                            st.markdown("Foreign Keys:")
                            for fk in row['foreign_keys']:
                                st.markdown(f"- `{fk['column_name']}` references `{fk['foreign_table_name']}.{fk['foreign_column_name']}`")
            else:
                st.info("No schema analysis results available.")

        except Exception as e:
            st.error(f"Error running table schema analysis: {str(e)}")
            send_slack_alert(f"Performance Page Schema Analysis Error: {str(e)}", "error")


def render_realtime_db_metrics():
    """Render real-time database metrics using DatabaseService."""
    try:
        db_stats = db_service.get_database_stats()

        if db_stats:
            metrics = [
                {
                    'title': "Total Tables",
                    'value': format_number(db_stats.get('total_tables', 0)),
                    'color': "#1f77b4"
                },
                {
                    'title': "FE Tables",
                    'value': format_number(db_stats.get('fe_tables', 0)),
                    'color': "#ffc107"
                },
                {
                    'title': "Active Connections",
                    'value': format_number(db_stats.get('active_connections', 0)),
                    'color': "#28a745"
                },
                {
                    'title': "Database Size",
                    'value': db_stats.get('database_size', 'N/A'),
                    'color': "#17a2b8"
                }
            ]
            DashboardLayout.render_metric_grid(metrics, columns=4)
        else:
            st.info("No real-time database metrics available.")

    except Exception as e:
        st.error(f"Failed to load real-time DB metrics: {str(e)}")
        send_slack_alert(f"Performance Page Real-time Metrics Error: {str(e)}", "error")


def render_table_index_stats():
    """Render table and index usage statistics."""
    try:
        # Extend DatabaseService to get these stats
        table_io_stats = db_service.get_table_io_stats()

        if table_io_stats:
            df_io = pd.DataFrame(table_io_stats)
            st.subheader("Top 10 Tables by I/O Activity")
            DataDisplay.render_dataframe_with_styling(df_io)

            # Visualize I/O
            df_io['total_scans'] = df_io['seq_scan'] + df_io['idx_scan']
            DataVisualization.render_metric_chart(
                df_io,
                x_col='table_name',
                y_col='total_scans',
                title="Total Scans by Table",
                chart_type='bar',
                color='total_scans'
            )
        else:
            st.info("No table I/O statistics available.")

        index_usage_stats = db_service.get_index_usage_stats()
        if index_usage_stats:
            df_idx = pd.DataFrame(index_usage_stats)
            st.subheader("Least Used Indexes (Potential for Optimization)")
            DataDisplay.render_dataframe_with_styling(df_idx)

            # Recommendations for unused indexes
            unused_indexes = df_idx[df_idx['idx_scan'] == 0]
            if not unused_indexes.empty:
                st.warning("⚠️ The following indexes have not been used and might be candidates for removal to improve write performance:")
                for _, row in unused_indexes.iterrows():
                    st.write(f"- Index: `{row['index_name']}` on table `{row['table_name']}`")
        else:
            st.info("No index usage statistics available.")

    except Exception as e:
        st.error(f"Failed to load table/index stats: {str(e)}")
        send_slack_alert(f"Performance Page Table/Index Stats Error: {str(e)}", "error")


def render_long_running_queries():
    """Render currently running or recently completed long-running queries."""
    try:
        long_queries = db_service.get_long_running_queries()

        if long_queries:
            df_queries = pd.DataFrame(long_queries)
            st.warning("🚫 Potentially long-running queries detected:")
            DataDisplay.render_dataframe_with_styling(df_queries, height=300)

            st.info("Consider optimizing these queries, or adding appropriate indexes.")
        else:
            st.success("✅ No long-running queries detected at the moment.")

    except Exception as e:
        st.error(f"Failed to load long-running queries: {str(e)}")
        send_slack_alert(f"Performance Page Long Queries Error: {str(e)}", "error")

def render_benchmarking_section():
    """Render benchmarking and optimization recommendations section."""
    st.write("Run simulated database workloads and get optimization recommendations.")

    if st.button("🚀 Run Performance Benchmark", type="primary"):
        with st.spinner("Running benchmark. This may take a moment..."):
            try:
                optimizer = QueryOptimizer(db_service=db_service)
                # Assuming compare_query_performance can take a generic query for testing
                # For a real scenario, this would involve more sophisticated workload generation
                sample_query = "SELECT COUNT(*) FROM crypto_listings_latest_1000"
                benchmark_results = optimizer.compare_query_performance(query_to_test=sample_query) # Example usage

                st.success("Benchmark completed!")

                if benchmark_results:
                    st.subheader("Benchmark Results")
                    # Displaying simple benchmark results. This can be expanded with charts.
                    st.write(f"**Tested Query:** `{sample_query}`")
                    st.write(f"**Execution Time:** {benchmark_results.get('execution_time', 'N/A')} ms")
                    st.markdown("---")
                else:
                    st.info("No benchmark results returned.")

            except Exception as e:
                st.error(f"Error running performance benchmark: {str(e)}")
                send_slack_alert(f"Performance Page Benchmark Error: {str(e)}", "error")

    st.subheader("💡 Optimization Recommendations")
    st.write("Based on recent analysis, here are some recommendations:")

    # Recommendation 1: Underutilized Indexes
    try:
        index_usage_stats = db_service.get_index_usage_stats()
        if index_usage_stats:
            unused_indexes = [idx for idx in index_usage_stats if idx['idx_scan'] == 0]
            if unused_indexes:
                st.warning("⚠️ Consider removing or re-evaluating the following unused indexes (0 scans):")
                for idx in unused_indexes:
                    st.write(f"- Index: `{idx['index_name']}` on table `{idx['table_name']}` (Size: {idx['index_size']})")
            else:
                st.success("✅ All observed indexes are being used effectively.")
        else:
            st.info("No index usage statistics available for recommendations.")
    except Exception as e:
        st.error(f"Failed to generate index recommendations: {str(e)}")

    # Recommendation 2: Long-Running Queries
    try:
        long_queries = db_service.get_long_running_queries()
        if long_queries:
            st.warning(" slowest-running queries. Consider optimizing these queries:")
            for query_info in long_queries:
                st.write(f"- Duration: {query_info['duration']} on DB `{query_info['datname']}`. Query: `{query_info['query'][:100]}...`")
        else:
            st.success("✅ No significant long-running queries detected.")
    except Exception as e:
        st.error(f"Failed to generate long-running query recommendations: {str(e)}")

    # Recommendation 3: Missing Primary Keys (re-using run_optimized_pk_analysis result framework)
    try:
        # This would ideally be cached or passed if the analysis was run recently
        validator = ComprehensiveValidationSuite(db_service=db_service)
        pk_results = validator.validate_primary_keys()
        missing_pks = [r for r in pk_results if r['status'] in ['WARNING', 'FAILED'] and "without primary keys" in r['description']]
        if missing_pks:
            st.warning("⚠️ The following tables are missing primary keys. Adding primary keys can significantly improve query performance and data integrity:")
            for res in missing_pks:
                st.write(f"- **{res['description']}**: `{', '.join(res['details'])}`")
        else:
            st.success("✅ All critical tables have primary keys.")
    except Exception as e:
        st.error(f"Failed to generate primary key recommendations: {str(e)}")

    # Recommendation 4: Schema Analysis Insights (e.g., too many generic types, or tables without descriptions)
    try:
        executor = SchemaAnalyzer(db_service=db_service)
        schema_analysis_results = executor.analyze_schema()

        generic_type_tables = [s for s in schema_analysis_results if any(dt in s.get('data_types', '') for dt in ['text', 'jsonb', 'bytea']) and s.get('column_count', 0) > 10]
        if generic_type_tables:
            st.info("ℹ️ Some tables have many columns or use generic data types (e.g., `text`, `jsonb`) which might impact performance or enforce less strict data integrity. Consider more specific types or normalization:")
            for table_info in generic_type_tables:
                st.write(f"- Table `{table_info['table_name']}`: ({table_info['column_count']} columns, types: {table_info['data_types'][:50]}...)")
        else:
            st.success("✅ Schema appears to use appropriate data types for analyzed tables.")

    except Exception as e:
        st.error(f"Failed to generate schema recommendations: {str(e)}")
