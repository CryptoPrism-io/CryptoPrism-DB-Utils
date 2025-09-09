#!/usr/bin/env python3
"""
Data Quality Assurance Page

Comprehensive database validation, quality checks, and data integrity
assessment with automated validation testing.
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from sqlalchemy import text

from components.ui_components import (
    DashboardLayout, StatusIndicators, DataVisualization,
    DataDisplay, PerformanceMonitors
)
from services.database_service import db_service
from utils.helpers import (
    send_slack_alert, format_number, format_timestamp,
    calculate_success_rate
)


def render_qa_checks_page():
    """Render data quality assurance page."""
    DashboardLayout.render_header(
        "Data Quality Assurance",
        "Comprehensive database validation and quality monitoring"
    )

    # Main validation execution
    validation_col, quick_test_col = st.columns([2, 1])

    with validation_col:
        st.subheader("🔬 Complete Database Validation")
        if st.button("🚀 Run Complete Validation Suite", type="primary"):
            run_full_validation_suite()

    with quick_test_col:
        st.subheader("⚡ Quick Tests")
        render_quick_validation_tests()

    # Health monitoring section
    st.subheader("📊 Live Database Health Monitor")
    render_live_health_monitor()

    # Historical QA checks
    render_historical_qa_data()


def run_full_validation_suite():
    """Run comprehensive database validation suite."""
    with st.spinner("🔬 Running comprehensive database validation..."):
        start_time = time.time()

        with PerformanceMonitors.render_query_timer("Full Validation Suite"):
            validation_results = perform_comprehensive_validation()

        end_time = time.time()
        total_time = (end_time - start_time) * 1000

        # Display validation results
        display_validation_results(validation_results, total_time)

        # Send alerts for critical issues
        alert_critical_issues(validation_results)


def perform_comprehensive_validation() -> list:
    """Perform comprehensive validation checks."""
    validation_results = []

    # 1. Primary Key Validation
    validation_results.extend(validate_primary_keys())

    # 2. FE Tables Existence Check
    validation_results.extend(validate_fe_tables_existence())

    # 3. Data Completeness Check
    validation_results.extend(validate_data_completeness())

    # 4. Timestamp Validation
    validation_results.extend(validate_timestamp_columns())

    # 5. Database Performance Check
    validation_results.extend(validate_db_performance())

    # 6. Foreign Key Relationships
    validation_results.extend(validate_data_consistency())

    return validation_results


def validate_primary_keys() -> list:
    """Validate primary key constraints."""
    results = []

    try:
        # Get all tables without primary keys
        missing_pk_tables = db_service.get_tables_missing_pk()

        if not missing_pk_tables:
            results.append({
                'test': 'Primary Key Validation',
                'status': 'PASSED',
                'description': 'All tables have primary keys',
                'details': []
            })
        else:
            results.append({
                'test': 'Primary Key Validation',
                'status': 'WARNING' if len(missing_pk_tables) < 5 else 'FAILED',
                'description': f'{len(missing_pk_tables)} tables without primary keys',
                'details': missing_pk_tables
            })
    except Exception as e:
        results.append({
            'test': 'Primary Key Validation',
            'status': 'ERROR',
            'description': f'Failed to validate primary keys: {str(e)}',
            'details': []
        })

    return results


def validate_fe_tables_existence() -> list:
    """Check FE tables existence and structure."""
    results = []

    fe_table_check = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name LIKE 'FE_%'
    ORDER BY table_name
    """

    try:
        fe_tables = db_service.execute_query(fe_table_check)
        fe_table_names = [row['table_name'] for row in fe_tables] if fe_tables else []

        if not fe_table_names:
            results.append({
                'test': 'FE Tables Existence',
                'status': 'FAILED',
                'description': 'No FE tables found in database',
                'details': []
            })
        else:
            results.append({
                'test': 'FE Tables Existence',
                'status': 'PASSED',
                'description': f'Found {len(fe_table_names)} FE tables',
                'details': fe_table_names
            })

            # Validate each FE table has data
            for table in fe_table_names[:5]:  # Check first 5 tables
                count = db_service.get_table_count(table)
                results.append({
                    'test': f'{table} Data Check',
                    'status': 'PASSED' if count > 0 else 'WARNING',
                    'description': f'Table contains {format_number(count)} records',
                    'details': f'Record count: {count}'
                })

    except Exception as e:
        results.append({
            'test': 'FE Tables Existence',
            'status': 'ERROR',
            'description': f'FE table validation failed: {str(e)}',
            'details': []
        })

    return results


def validate_data_completeness() -> list:
    """Validate data completeness across key tables."""
    results = []

    completeness_checks = [
        {
            'table': 'crypto_listings_latest_1000',
            'description': 'Market listings completeness'
        },
        {
            'table': '1K_coins_ohlcv',
            'description': 'OHLCV data completeness'
        },
        {
            'table': 'FE_DMV_ALL',
            'description': 'Final analysis completeness'
        }
    ]

    for check in completeness_checks:
        table_name = check['table']
        try:
            if db_service.get_table_exists(table_name):
                count = db_service.get_table_count(table_name)

                # Check for null values in critical columns
                null_check_query = f"""
                SELECT
                    COUNT(*) as total_rows,
                    SUM(CASE WHEN slug IS NULL THEN 1 ELSE 0 END) as null_slugs,
                    SUM(CASE WHEN "timestamp" IS NULL AND updated_at IS NULL THEN 1 ELSE 0 END) as null_timestamps
                FROM "{table_name}"
                """

                null_stats = db_service.execute_query_single(null_check_query)

                if null_stats:
                    null_percentage = ((null_stats.get('null_slugs', 0) + null_stats.get('null_timestamps', 0)) /
                                     null_stats.get('total_rows', 1)) * 100

                    status = 'PASSED' if null_percentage < 5 else 'WARNING' if null_percentage < 20 else 'FAILED'
                    results.append({
                        'test': f'{table_name} Completeness',
                        'status': status,
                        'description': f'{count:,} records, {null_percentage:.1f}% null values',
                        'details': f'Null rate: {null_percentage:.1f}%'
                    })
                else:
                    results.append({
                        'test': f'{table_name} Completeness',
                        'status': 'UNKNOWN',
                        'description': 'Could not calculate completeness',
                        'details': ''
                    })
            else:
                results.append({
                    'test': f'{table_name} Completeness',
                    'status': 'FAILED',
                    'description': 'Table does not exist',
                    'details': ''
                })

        except Exception as e:
            results.append({
                'test': f'{table_name} Completeness',
                'status': 'ERROR',
                'description': f'Completeness check failed: {str(e)}',
                'details': ''
            })

    return results


def validate_timestamp_columns() -> list:
    """Validate timestamp columns in critical tables."""
    results = []

    critical_tables = [
        {'table': 'crypto_listings', 'required_columns': ['last_updated']},
        {'table': 'FE_FEAR_GREED_CMC', 'required_columns': ['timestamp']},
        {'table': 'FE_DMV_ALL', 'required_columns': ['timestamp']},
        {'table': '1K_coins_ohlcv', 'required_columns': ['timestamp']}
    ]

    for table_info in critical_tables:
        table_name = table_info['table']
        required_cols = table_info['required_columns']

        try:
            if db_service.get_table_exists(table_name):
                columns = db_service.get_table_columns(table_name)
                column_names = [col['name'] for col in columns] if columns else []

                missing_timestamp_cols = [col for col in required_cols if col not in column_names]

                if not missing_timestamp_cols:
                    results.append({
                        'test': f'{table_name} Timestamp Validation',
                        'status': 'PASSED',
                        'description': 'All required timestamp columns present',
                        'details': ', '.join(required_cols)
                    })
                else:
                    results.append({
                        'test': f'{table_name} Timestamp Validation',
                        'status': 'WARNING',
                        'description': f'Missing timestamp columns: {", ".join(missing_timestamp_cols)}',
                        'details': f'Missing: {missing_timestamp_cols}'
                    })
            else:
                results.append({
                    'test': f'{table_name} Timestamp Validation',
                    'status': 'FAILED',
                    'description': 'Table does not exist',
                    'details': ''
                })

        except Exception as e:
            results.append({
                'test': f'{table_name} Timestamp Validation',
                'status': 'ERROR',
                'description': f'Timestamp validation failed: {str(e)}',
                'details': ''
            })

    return results


def validate_db_performance() -> list:
    """Validate database performance characteristics."""
    results = []

    try:
        # Test schema query performance
        start_time = time.time()

        db_service.execute_query("""
        SELECT count(*)
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """)

        query_time = (time.time() - start_time) * 1000

        status = 'PASSED' if query_time < 1000 else 'WARNING' if query_time < 5000 else 'FAILED'
        results.append({
            'test': 'Database Query Performance',
            'status': status,
            'description': f'Schema query executed in {query_time:.2f}ms',
            'details': f'Execution time: {query_time:.2f}ms'
        })

    except Exception as e:
        results.append({
            'test': 'Database Query Performance',
            'status': 'ERROR',
            'description': f'Performance test failed: {str(e)}',
            'details': ''
        })

    return results


def validate_data_consistency() -> list:
    """Validate data consistency between related tables."""
    results = []

    try:
        # Check symbol consistency between listings and analysis tables
        consistency_query = """
        SELECT
            COUNT(DISTINCT cl.symbol) as listing_symbols,
            COUNT(DISTINCT fda.slug) as analysis_symbols,
            COUNT(DISTINCT cl.symbol) - COUNT(DISTINCT fda.slug) as missing_in_analysis
        FROM crypto_listings cl
        LEFT JOIN FE_DMV_ALL fda ON cl.symbol = fda.slug
        """

        consistency_result = db_service.execute_query_single(consistency_query)

        if consistency_result:
            listing_symbols = consistency_result.get('listing_symbols', 0)
            analysis_symbols = consistency_result.get('analysis_symbols', 0)
            missing_count = consistency_result.get('missing_in_analysis', 0)

            if listing_symbols > 0:
                coverage = (analysis_symbols / listing_symbols) * 100
                status = 'PASSED' if coverage > 80 else 'WARNING' if coverage > 50 else 'FAILED'

                results.append({
                    'test': 'Listings vs Analysis Data Consistency',
                    'status': status,
                    'description': f'Analysis coverage: {coverage:.1f}% ({analysis_symbols}/{listing_symbols} symbols)',
                    'details': f'Missing {missing_count} symbols in analysis'
                })
            else:
                results.append({
                    'test': 'Listings vs Analysis Data Consistency',
                    'status': 'FAILED',
                    'description': 'No data found in either listings or analysis tables',
                    'details': ''
                })
        else:
            results.append({
                'test': 'Listings vs Analysis Data Consistency',
                'status': 'ERROR',
                'description': 'Could not perform consistency check',
                'details': ''
            })

    except Exception as e:
        results.append({
            'test': 'Listings vs Analysis Data Consistency',
            'status': 'ERROR',
            'description': f'Consistency validation failed: {str(e)}',
            'details': ''
        })

    return results


def display_validation_results(results: list, total_time: float):
    """Display validation results in organized format."""
    # Summary metrics
    total_tests = len(results)
    passed = sum(1 for r in results if r['status'] == 'PASSED')
    warnings = sum(1 for r in results if r['status'] == 'WARNING')
    failed = sum(1 for r in results if r['status'] == 'FAILED')
    errors = sum(1 for r in results if r['status'] == 'ERROR')

    success_rate = calculate_success_rate(passed, total_tests) if total_tests > 0 else 0

    # Summary section
    st.success(f"✅ Validation completed! {total_tests} tests in {total_time:.1f}ms")

    metrics = [
        {'title': "Total Tests", 'value': str(total_tests), 'color': "#6c757d"},
        {'title': "Passed", 'value': str(passed), 'color': "#28a745"},
        {'title': "Warnings", 'value': str(warnings), 'color': "#ffc107"},
        {'title': "Failed", 'value': str(failed), 'color': "#dc3545"},
        {'title': "Success Rate", 'value': f"{success_rate:.1f}%", 'color': "#17a2b8"}
    ]

    DashboardLayout.render_metric_grid(metrics, columns=5)

    # Detailed results section
    st.subheader("📋 Detailed Validation Results")

    status_order = {'PASSED': 0, 'WARNING': 1, 'FAILED': 2, 'ERROR': 3}

    # Sort results by status severity
    results_sorted = sorted(results, key=lambda x: status_order.get(x['status'], 9))

    for result in results_sorted:
        status = result['status']

        if status == 'PASSED':
            st.success(f"✅ **{result['test']}**: {result['description']}")
        elif status == 'WARNING':
            st.warning(f"⚠️ **{result['test']}**: {result['description']}")
        elif status == 'FAILED':
            st.error(f"❌ **{result['test']}**: {result['description']}")
        elif status == 'ERROR':
            st.error(f"🔧 **{result['test']}**: {result['description']}")

        # Show details if available
        if result.get('details') and isinstance(result['details'], list) and len(result['details']) > 0:
            with st.expander(f"View details for {result['test']}"):
                for detail in result['details']:
                    st.write(f"• {detail}")
        elif result.get('details') and isinstance(result['details'], str) and result['details']:
            st.write(f"  Details: {result['details']}")


def render_quick_validation_tests():
    """Render quick validation test options."""
    if st.button("🔍 Test FE Tables", type="secondary"):
        with st.spinner("Checking FE tables..."):
            try:
                test_fe_tables_existence()
            except Exception as e:
                st.error(f"FE table test failed: {str(e)}")

    if st.button("🔗 Test Data Connections", type="secondary"):
        with st.spinner("Testing data flow connections..."):
            try:
                test_data_flow_connections()
            except Exception as e:
                st.error(f"Connection test failed: {str(e)}")

    if st.button("⏱️ Performance Test", type="secondary"):
        with st.spinner("Running performance tests..."):
            try:
                run_performance_test()
            except Exception as e:
                st.error(f"Performance test failed: {str(e)}")


def test_fe_tables_existence():
    """Quick test for FE tables."""
    fe_check = """
    SELECT table_name,
           (SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = t.table_name) as column_count
    FROM information_schema.tables t
    WHERE table_schema = 'public'
    AND table_name LIKE 'FE_%'
    ORDER BY table_name
    """

    results = db_service.execute_query(fe_check)

    if results:
        st.success(f"Found {len(results)} FE tables")
        for row in results:
            st.write(f"• **{row['table_name']}**: {row['column_count']} columns")
    else:
        st.warning("No FE tables found")


def test_data_flow_connections():
    """Test data flow between key tables."""
    flow_tests = [
        ("Listings → OHLCV", "crypto_listings", "1K_coins_ohlcv"),
        ("OHLCV → Analysis", "1K_coins_ohlcv", "FE_DMV_ALL"),
    ]

    for test_name, source_table, target_table in flow_tests:
        try:
            # Simple existence check
            source_exists = db_service.get_table_exists(source_table)
            target_exists = db_service.get_table_exists(target_table)

            if source_exists and target_exists:
                source_count = db_service.get_table_count(source_table)
                target_count = db_service.get_table_count(target_table)

                st.write(f"✅ **{test_name}**: Source ({source_count:,} records) → Target ({target_count:,} records)")
            else:
                st.warning(f"⚠️ **{test_name}**: Missing tables (Source: {source_exists}, Target: {target_exists})")

        except Exception as e:
            st.error(f"❌ **{test_name}**: Test failed - {str(e)}")


def run_performance_test():
    """Run basic performance test."""
    start_time = time.time()

    # Simple query performance test
    db_service.execute_query("SELECT COUNT(*) FROM information_schema.tables")

    query_time = (time.time() - start_time) * 1000

    if query_time < 1000:
        st.success(f"⚡ Database performance: {query_time:.1f}ms - Excellent!")
    elif query_time < 5000:
        st.warning(f"⚠️ Database performance: {query_time:.1f}ms - Acceptable")
    else:
        st.error(f"❌ Database performance: {query_time:.1f}ms - Needs optimization")


def render_live_health_monitor():
    """Render live database health monitor."""
    try:
        # Get real-time database stats
        db_stats = db_service.get_database_stats()

        if db_stats:
            # Health status indicator
            StatusIndicators.render_health_status(db_stats.get('connection_healthy', False))

            # Health metrics
            health_metrics = [
                {
                    'title': "Active Connections",
                    'value': str(db_stats.get('active_connections', 0)),
                    'color': "#1f77b4"
                },
                {
                    'title': "Database Size",
                    'value': db_stats.get('database_size', 'Unknown'),
                    'color': "#28a745"
                },
                {
                    'title': "FE Tables",
                    'value': f"{db_stats.get('fe_tables', 0)}",
                    'color': "#ffc107"
                },
                {
                    'title': "Total Tables",
                    'value': str(db_stats.get('total_tables', 0)),
                    'color': "#17a2b8"
                }
            ]

            DashboardLayout.render_metric_grid(health_metrics, columns=4)

        else:
            st.error("Unable to load database health statistics")

    except Exception as e:
        st.error(f"Health monitor error: {str(e)}")


def render_historical_qa_data():
    """Render historical QA checks data."""
    st.subheader("📜 Historical Quality Checks")

    try:
        # Load historical QA data
        qa_query = """
        SELECT check_name, table_name, check_type, expected_count,
               actual_count, status, error_details, check_time
        FROM data_quality_checks
        WHERE check_time >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY check_time DESC
        LIMIT 100
        """

        qa_data = db_service.execute_query(qa_query)

        if qa_data:
            df = pd.DataFrame(qa_data)

            # Convert timestamps to readable format
            if 'check_time' in df.columns:
                df['check_time'] = pd.to_datetime(df['check_time'])
                df['check_time_formatted'] = df['check_time'].dt.strftime('%Y-%m-%d %H:%M:%S')

            # Summary metrics
            total_checks = len(df)
            if total_checks > 0:
                passed_checks = len(df[df['status'] == 'passed'])
                failed_checks = len(df[df['status'] == 'failed'])
                success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0

                qa_metrics = [
                    {'title': "Total Checks", 'value': str(total_checks), 'color': "#6c757d"},
                    {'title': "Passed", 'value': str(passed_checks), 'color': "#28a745"},
                    {'title': "Failed", 'value': str(failed_checks), 'color': "#dc3545"},
                    {'title': "Success Rate", 'value': f"{success_rate:.1f}%", 'color': "#17a2b8"}
                ]

                DashboardLayout.render_metric_grid(qa_metrics, columns=4)

            # Display historical QA data
            DataDisplay.render_dataframe_with_styling(
                df,
                title="📋 Recent Quality Check Results",
                max_rows=100,
                height=300
            )

        else:
            st.info("No historical QA check data found. Run validation tests to populate this section.")

    except Exception as e:
        st.error(f"Historical QA data load failed: {str(e)}")


def alert_critical_issues(results: list):
    """Send alerts for critical validation issues."""
    critical_issues = [r for r in results if r['status'] in ['FAILED', 'ERROR']]

    if critical_issues:
        issue_summary = f"Found {len(critical_issues)} critical validation issues"
        send_slack_alert(
            f"Database Validation Alert: {issue_summary}",
            "error"
        )