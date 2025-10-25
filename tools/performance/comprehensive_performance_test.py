#!/usr/bin/env python3
"""
Comprehensive Performance Test - Post-optimization validation
"""

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def run_comprehensive_performance_test():
    """Run comprehensive performance tests to validate optimization."""
    
    print("="*70)
    print("COMPREHENSIVE PERFORMANCE TEST - POST OPTIMIZATION")
    print("="*70)
    
    # Database connection
    db_config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'), 
        'password': os.getenv('DB_PASSWORD'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'dbcp')
    }
    
    conn_string = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    engine = create_engine(conn_string)
    
    test_results = {
        'test_timestamp': datetime.now().isoformat(),
        'database_name': db_config['database'],
        'test_type': 'post_optimization_validation',
        'tests': {}
    }
    
    print(f"Connected to: {db_config['database']} at {db_config['host']}")
    
    # Define comprehensive test suite
    test_queries = [
        {
            'name': 'primary_key_validation',
            'query': '''
                SELECT 
                    table_name,
                    constraint_type,
                    constraint_name
                FROM information_schema.table_constraints 
                WHERE constraint_type = 'PRIMARY KEY' 
                    AND table_schema = 'public'
                ORDER BY table_name
            ''',
            'description': 'Validate all primary keys exist',
            'expected_min_rows': 22
        },
        {
            'name': 'fe_dmv_all_count_optimized',
            'query': 'SELECT COUNT(*) FROM "FE_DMV_ALL"',
            'description': 'Count query on main analysis table',
            'expected_performance': 'Should use primary key for better estimates'
        },
        {
            'name': 'fe_dmv_all_recent_data_optimized',
            'query': 'SELECT slug, timestamp, bullish, bearish FROM "FE_DMV_ALL" ORDER BY timestamp DESC LIMIT 10',
            'description': 'Recent data query with timestamp index',
            'expected_performance': 'Should use timestamp index'
        },
        {
            'name': 'ohlcv_volume_analysis_optimized',
            'query': '''
                SELECT slug, volume, close, market_cap 
                FROM "1K_coins_ohlcv" 
                WHERE volume > 10000000 
                ORDER BY volume DESC 
                LIMIT 20
            ''',
            'description': 'Volume analysis with dedicated volume index',
            'expected_performance': 'Should use volume index efficiently'
        },
        {
            'name': 'multi_table_join_optimized',
            'query': '''
                SELECT
                    d.slug,
                    d.timestamp,
                    d.bullish,
                    m.m_mom_rsi_9,
                    o."MACD"
                FROM "FE_DMV_ALL" d
                JOIN "FE_MOMENTUM" m ON d.slug = m.slug AND d.timestamp = m.timestamp
                JOIN "FE_OSCILLATOR" o ON d.slug = o.slug AND d.timestamp = o.timestamp
                WHERE d.timestamp >= CURRENT_DATE - INTERVAL '7 days'
                LIMIT 15
            ''',
            'description': 'Multi-table JOIN using primary keys',
            'expected_performance': 'Should use primary key indexes for JOINs'
        },
        {
            'name': 'crypto_listings_market_cap',
            'query': '''
                SELECT slug, name, market_cap, percent_change24h 
                FROM "crypto_listings_latest_1000"
                WHERE market_cap > 1000000000
                ORDER BY market_cap DESC
                LIMIT 25
            ''',
            'description': 'Crypto listings filtering (newly optimized table)',
            'expected_performance': 'Should work reliably with new primary key'
        },
        {
            'name': 'news_events_analysis',
            'query': '''
                SELECT slug, event_date, title 
                FROM "NEWS_TOKENOMICS_W"
                ORDER BY event_date DESC
                LIMIT 10
            ''',
            'description': 'News events query (newly optimized table)',
            'expected_performance': 'Should use new primary key effectively'
        },
        {
            'name': 'fear_greed_trend',
            'query': '''
                SELECT timestamp, fear_greed_index, sentiment
                FROM "FE_FEAR_GREED_CMC"
                ORDER BY timestamp DESC
                LIMIT 30
            ''',
            'description': 'Fear/Greed trend analysis (newly optimized)',
            'expected_performance': 'Should use timestamp primary key'
        },
        {
            'name': 'reference_data_lookup',
            'query': '''
                SELECT slug, name, website, twitter
                FROM "FE_CC_INFO_URL"
                WHERE slug IN ('bitcoin', 'ethereum', 'cardano', 'solana', 'polkadot')
            ''',
            'description': 'Reference data lookups (newly optimized)',
            'expected_performance': 'Should use slug primary key efficiently'
        },
        {
            'name': 'aggregation_performance',
            'query': '''
                SELECT 
                    slug,
                    COUNT(*) as record_count,
                    AVG(bullish) as avg_bullish,
                    MAX(timestamp) as latest_timestamp
                FROM "FE_DMV_ALL"
                WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY slug
                HAVING COUNT(*) > 5
                ORDER BY avg_bullish DESC
                LIMIT 20
            ''',
            'description': 'Complex aggregation with grouping',
            'expected_performance': 'Should benefit from primary key structure'
        }
    ]
    
    print(f"Executing {len(test_queries)} performance tests...")
    print()
    
    total_time = 0
    successful_tests = 0
    failed_tests = 0
    
    for i, test in enumerate(test_queries, 1):
        print(f"[{i:2d}/{len(test_queries)}] {test['name']}")
        print(f"        Description: {test['description']}")
        
        try:
            start_time = time.time()
            with engine.connect() as conn:
                result = conn.execute(text(test['query']))
                rows = result.fetchall()
            end_time = time.time()
            
            execution_time = (end_time - start_time) * 1000  # Convert to ms
            total_time += execution_time
            successful_tests += 1
            
            # Validate results if expected criteria provided
            validation_notes = []
            if 'expected_min_rows' in test and len(rows) < test['expected_min_rows']:
                validation_notes.append(f"WARNING: Expected >= {test['expected_min_rows']} rows, got {len(rows)}")
            
            test_results['tests'][test['name']] = {
                'status': 'success',
                'execution_time_ms': execution_time,
                'rows_returned': len(rows),
                'description': test['description'],
                'expected_performance': test.get('expected_performance', 'N/A'),
                'validation_notes': validation_notes
            }
            
            print(f"        Result: SUCCESS - {execution_time:6.1f}ms - {len(rows)} rows")
            if validation_notes:
                for note in validation_notes:
                    print(f"        {note}")
            
        except Exception as e:
            failed_tests += 1
            test_results['tests'][test['name']] = {
                'status': 'failed',
                'error': str(e),
                'description': test['description']
            }
            print(f"        Result: FAILED - {str(e)[:60]}...")
        
        print()
    
    # Summary
    print("="*70)
    print("PERFORMANCE TEST SUMMARY")
    print("="*70)
    
    test_results['summary'] = {
        'total_tests': len(test_queries),
        'successful_tests': successful_tests,
        'failed_tests': failed_tests,
        'total_execution_time_ms': total_time,
        'average_execution_time_ms': total_time / len(test_queries) if test_queries else 0,
        'success_rate_percent': (successful_tests / len(test_queries)) * 100 if test_queries else 0
    }
    
    print(f"Total tests executed: {len(test_queries)}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {(successful_tests/len(test_queries))*100:.1f}%")
    print(f"Total execution time: {total_time:.1f}ms")
    print(f"Average execution time: {total_time/len(test_queries):.1f}ms")
    
    # Performance analysis
    if successful_tests > 0:
        fast_queries = [name for name, result in test_results['tests'].items() 
                       if result.get('status') == 'success' and result.get('execution_time_ms', 999999) < 500]
        medium_queries = [name for name, result in test_results['tests'].items() 
                         if result.get('status') == 'success' and 500 <= result.get('execution_time_ms', 999999) < 2000]
        slow_queries = [name for name, result in test_results['tests'].items() 
                       if result.get('status') == 'success' and result.get('execution_time_ms', 0) >= 2000]
        
        print(f"\nPERFORMANCE BREAKDOWN:")
        print(f"Fast queries (<500ms): {len(fast_queries)}")
        print(f"Medium queries (500-2000ms): {len(medium_queries)}")
        print(f"Slow queries (>2000ms): {len(slow_queries)}")
        
        if slow_queries:
            print(f"\nSlow queries needing attention:")
            for query_name in slow_queries:
                execution_time = test_results['tests'][query_name]['execution_time_ms']
                print(f"  - {query_name}: {execution_time:.1f}ms")
    
    # Save results
    output_file = f"performance_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    engine.dispose()
    return test_results

if __name__ == "__main__":
    print("Starting comprehensive performance validation...")
    results = run_comprehensive_performance_test()
    
    # Final assessment
    summary = results['summary']
    if summary['success_rate_percent'] >= 90:
        print(f"\nASSESSMENT: EXCELLENT - {summary['success_rate_percent']:.1f}% success rate")
    elif summary['success_rate_percent'] >= 75:
        print(f"\nASSESSMENT: GOOD - {summary['success_rate_percent']:.1f}% success rate")
    else:
        print(f"\nASSESSMENT: NEEDS IMPROVEMENT - {summary['success_rate_percent']:.1f}% success rate")
    
    print("Performance validation complete!")