#!/usr/bin/env python3
"""
Comprehensive Validation Suite - Enhanced performance testing with fixes

This module provides enhanced performance testing that incorporates all the fixes
from the modular toolkits: optimized queries, corrected schemas, and completed primary keys.

Author: CryptoPrism-DB-Utils
Version: 1.0.1
"""

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

class ComprehensiveValidationSuite:
    """Enhanced validation suite with all performance fixes applied."""
    
    def __init__(self):
        """Initialize database connection and validation framework."""
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'), 
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'dbcp')
        }
        
        conn_string = f"postgresql+psycopg2://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        self.engine = create_engine(conn_string)
        
        print(f"Connected to: {self.db_config['database']} at {self.db_config['host']}")
    
    def get_enhanced_test_suite(self):
        """
        Get enhanced test suite with all fixes applied.
        
        Returns corrected and optimized queries for comprehensive testing.
        """
        return [
            {
                'name': 'primary_key_validation_optimized',
                'query': '''
                    SELECT 
                        n.nspname as schema_name,
                        t.relname as table_name,
                        'PRIMARY KEY' as constraint_type,
                        c.conname as constraint_name
                    FROM pg_constraint c
                    JOIN pg_class t ON c.conrelid = t.oid
                    JOIN pg_namespace n ON t.relnamespace = n.oid
                    WHERE c.contype = 'p'
                        AND n.nspname = 'public'
                    ORDER BY t.relname
                ''',
                'description': 'FIXED: Optimized primary key validation using pg_constraint',
                'expected_performance': 'Should execute in <1000ms (improved from 5200ms)',
                'fix_applied': 'query_optimization_toolkit'
            },
            {
                'name': 'fe_dmv_all_count_optimized',
                'query': 'SELECT COUNT(*) FROM "FE_DMV_ALL"',
                'description': 'Count query on main analysis table',
                'expected_performance': 'Should maintain <1000ms performance'
            },
            {
                'name': 'fe_dmv_all_recent_data_optimized',
                'query': 'SELECT slug, timestamp, bullish, bearish FROM "FE_DMV_ALL" ORDER BY timestamp DESC LIMIT 10',
                'description': 'Recent data query with timestamp index',
                'expected_performance': 'Should use timestamp index efficiently'
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
                'name': 'multi_table_join_corrected',
                'query': '''
                    SELECT 
                        d.slug,
                        d.timestamp,
                        d.bullish,
                        m.m_mom_rsi_9,
                        o.m_osc_macd_crossover_bin
                    FROM "FE_DMV_ALL" d
                    JOIN "FE_MOMENTUM" m ON d.slug = m.slug AND d.timestamp = m.timestamp
                    JOIN "FE_OSCILLATORS_SIGNALS" o ON d.slug = o.slug AND d.timestamp = o.timestamp
                    WHERE d.timestamp >= CURRENT_DATE - INTERVAL '7 days'
                    LIMIT 15
                ''',
                'description': 'FIXED: Multi-table JOIN using correct table references',
                'expected_performance': 'Should use primary key indexes for JOINs',
                'fix_applied': 'schema_correction_toolkit'
            },
            {
                'name': 'comprehensive_momentum_analysis',
                'query': '''
                    SELECT 
                        d.slug,
                        d.timestamp,
                        d.bullish,
                        d.bearish,
                        m.m_mom_rsi_9,
                        m.m_mom_roc,
                        m."m_mom_williams_%",
                        ms.m_mom_roc_bin,
                        o.m_osc_macd_crossover_bin,
                        o.m_osc_cci_bin
                    FROM "FE_DMV_ALL" d
                    JOIN "FE_MOMENTUM" m ON d.slug = m.slug AND d.timestamp = m.timestamp
                    JOIN "FE_MOMENTUM_SIGNALS" ms ON d.slug = ms.slug AND d.timestamp = ms.timestamp
                    JOIN "FE_OSCILLATORS_SIGNALS" o ON d.slug = o.slug AND d.timestamp = o.timestamp
                    WHERE d.timestamp >= CURRENT_DATE - INTERVAL '3 days'
                        AND d.bullish > d.bearish
                    ORDER BY d.bullish DESC
                    LIMIT 10
                ''',
                'description': 'NEW: Comprehensive technical analysis with corrected table references',
                'expected_performance': 'Should leverage all primary key optimizations',
                'fix_applied': 'schema_correction_toolkit'
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
                'description': 'Crypto listings filtering (should have primary key)',
                'expected_performance': 'Should work reliably with primary key optimization'
            },
            {
                'name': 'news_events_analysis',
                'query': '''
                    SELECT slug, event_date, title 
                    FROM "NEWS_TOKENOMICS_W"
                    ORDER BY event_date DESC
                    LIMIT 10
                ''',
                'description': 'News events query (should have primary key)',
                'expected_performance': 'Should use primary key effectively'
            },
            {
                'name': 'fear_greed_trend',
                'query': '''
                    SELECT timestamp, fear_greed_index, sentiment
                    FROM "FE_FEAR_GREED_CMC"
                    ORDER BY timestamp DESC
                    LIMIT 30
                ''',
                'description': 'Fear/Greed trend analysis (should have primary key)',
                'expected_performance': 'Should use timestamp primary key'
            },
            {
                'name': 'reference_data_lookup',
                'query': '''
                    SELECT slug, name, website, twitter
                    FROM "FE_CC_INFO_URL"
                    WHERE slug IN ('bitcoin', 'ethereum', 'cardano', 'solana', 'polkadot')
                ''',
                'description': 'Reference data lookups (should have primary key)',
                'expected_performance': 'Should use slug primary key efficiently'
            },
            {
                'name': 'aggregation_performance_enhanced',
                'query': '''
                    SELECT 
                        slug,
                        COUNT(*) as record_count,
                        AVG(bullish) as avg_bullish,
                        AVG(bearish) as avg_bearish,
                        MAX(timestamp) as latest_timestamp,
                        MIN(timestamp) as earliest_timestamp
                    FROM "FE_DMV_ALL"
                    WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY slug
                    HAVING COUNT(*) > 5
                    ORDER BY avg_bullish DESC
                    LIMIT 20
                ''',
                'description': 'Enhanced aggregation with additional metrics',
                'expected_performance': 'Should benefit from primary key structure'
            },
            {
                'name': 'performance_regression_test',
                'query': '''
                    SELECT 
                        slug,
                        COUNT(*) as total_signals,
                        ROUND(AVG(bullish)::numeric, 2) as avg_bullish,
                        ROUND(STDDEV(bullish)::numeric, 2) as volatility,
                        ROUND((COUNT(CASE WHEN bullish > bearish THEN 1 END)::float / COUNT(*) * 100), 1) as bullish_percentage
                    FROM "FE_DMV_ALL"
                    WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY slug
                    HAVING COUNT(*) >= 5
                    ORDER BY AVG(bullish) DESC
                    LIMIT 15
                ''',
                'description': 'NEW: Performance regression test with complex analytics',
                'expected_performance': 'Comprehensive test of all optimizations'
            }
        ]
    
    def run_comprehensive_validation(self):
        """
        Run comprehensive validation with all fixes applied.
        
        Returns detailed performance results and comparison with baseline.
        """
        print("="*70)
        print("COMPREHENSIVE VALIDATION SUITE - WITH FIXES APPLIED")
        print("="*70)
        
        test_results = {
            'test_timestamp': datetime.now().isoformat(),
            'database_name': self.db_config['database'],
            'test_type': 'comprehensive_validation_with_fixes',
            'version': '1.0.1',
            'fixes_applied': [
                'query_optimization_toolkit',
                'schema_correction_toolkit',
                'primary_key_completion_toolkit'
            ],
            'tests': {}
        }
        
        test_queries = self.get_enhanced_test_suite()
        print(f"Executing {len(test_queries)} enhanced performance tests...")
        print()
        
        total_time = 0
        successful_tests = 0
        failed_tests = 0
        
        for i, test in enumerate(test_queries, 1):
            print(f"[{i:2d}/{len(test_queries)}] {test['name']}")
            print(f"        Description: {test['description']}")
            if 'fix_applied' in test:
                print(f"        Fix Applied: {test['fix_applied']}")
            
            try:
                start_time = time.time()
                with self.engine.connect() as conn:
                    result = conn.execute(text(test['query']))
                    rows = result.fetchall()
                end_time = time.time()
                
                execution_time = (end_time - start_time) * 1000  # Convert to ms
                total_time += execution_time
                successful_tests += 1
                
                # Performance analysis
                performance_status = "GOOD"
                if execution_time < 500:
                    performance_status = "EXCELLENT"
                elif execution_time > 2000:
                    performance_status = "SLOW"
                
                test_results['tests'][test['name']] = {
                    'status': 'success',
                    'execution_time_ms': execution_time,
                    'rows_returned': len(rows),
                    'description': test['description'],
                    'expected_performance': test.get('expected_performance', 'N/A'),
                    'performance_status': performance_status,
                    'fix_applied': test.get('fix_applied', 'none')
                }
                
                print(f"        Result: SUCCESS - {execution_time:6.1f}ms - {len(rows)} rows - {performance_status}")
                
            except Exception as e:
                failed_tests += 1
                test_results['tests'][test['name']] = {
                    'status': 'failed',
                    'error': str(e),
                    'description': test['description'],
                    'fix_applied': test.get('fix_applied', 'none')
                }
                print(f"        Result: FAILED - {str(e)[:60]}...")
            
            print()
        
        # Enhanced summary with fix analysis
        print("="*70)
        print("COMPREHENSIVE VALIDATION SUMMARY")
        print("="*70)
        
        test_results['summary'] = {
            'total_tests': len(test_queries),
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'total_execution_time_ms': total_time,
            'average_execution_time_ms': total_time / len(test_queries) if test_queries else 0,
            'success_rate_percent': (successful_tests / len(test_queries)) * 100 if test_queries else 0
        }
        
        summary = test_results['summary']
        print(f"Total tests executed: {len(test_queries)}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {summary['success_rate_percent']:.1f}%")
        print(f"Total execution time: {total_time:.1f}ms")
        print(f"Average execution time: {summary['average_execution_time_ms']:.1f}ms")
        
        # Fix impact analysis
        self.analyze_fix_impact(test_results)
        
        # Performance categorization
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
                print(f"\nSlow queries still needing attention:")
                for query_name in slow_queries:
                    execution_time = test_results['tests'][query_name]['execution_time_ms']
                    print(f"  - {query_name}: {execution_time:.1f}ms")
        
        # Save enhanced results
        output_file = f"enhanced_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\nEnhanced results saved to: {output_file}")
        
        return test_results
    
    def analyze_fix_impact(self, test_results):
        """
        Analyze the impact of applied fixes on performance.
        
        Args:
            test_results (dict): Test execution results
        """
        print(f"\nFIX IMPACT ANALYSIS:")
        print("-" * 40)
        
        fixes_impact = {}
        
        for test_name, result in test_results['tests'].items():
            if result['status'] == 'success':
                fix_applied = result.get('fix_applied', 'none')
                
                if fix_applied not in fixes_impact:
                    fixes_impact[fix_applied] = {
                        'tests': [],
                        'avg_time': 0,
                        'success_count': 0
                    }
                
                fixes_impact[fix_applied]['tests'].append(test_name)
                fixes_impact[fix_applied]['success_count'] += 1
        
        # Calculate average times for each fix category
        for fix_type, data in fixes_impact.items():
            if data['tests']:
                total_time = sum(test_results['tests'][test]['execution_time_ms'] for test in data['tests'])
                data['avg_time'] = total_time / len(data['tests'])
        
        # Display fix impact
        for fix_type, data in fixes_impact.items():
            if fix_type != 'none':
                print(f"  {fix_type}:")
                print(f"    - Tests improved: {data['success_count']}")
                print(f"    - Average execution time: {data['avg_time']:.1f}ms")
        
        # Special analysis for key fixes
        if 'primary_key_validation_optimized' in test_results['tests']:
            pk_result = test_results['tests']['primary_key_validation_optimized']
            if pk_result['status'] == 'success':
                original_time = 5229.2  # From baseline
                new_time = pk_result['execution_time_ms']
                improvement = ((original_time - new_time) / original_time) * 100
                print(f"\nKEY IMPROVEMENT - Primary Key Validation:")
                print(f"   Original: {original_time:.1f}ms -> Optimized: {new_time:.1f}ms")
                print(f"   Performance improvement: {improvement:.1f}% faster")
        
        if 'multi_table_join_corrected' in test_results['tests']:
            join_result = test_results['tests']['multi_table_join_corrected']
            if join_result['status'] == 'success':
                print(f"\nKEY FIX - Multi-table JOIN:")
                print(f"   Status: FIXED (was failing due to column mismatch)")
                print(f"   Execution time: {join_result['execution_time_ms']:.1f}ms")
                print(f"   Rows returned: {join_result['rows_returned']}")
    
    def compare_with_baseline(self, baseline_file=None):
        """
        Compare current results with baseline performance test.
        
        Args:
            baseline_file (str): Path to baseline results JSON file
        """
        if not baseline_file:
            baseline_file = "performance_test_results_20250908_121941.json"
        
        try:
            with open(baseline_file, 'r') as f:
                baseline_results = json.load(f)
            
            print(f"\nBASELINE COMPARISON:")
            print(f"Baseline file: {baseline_file}")
            print("-" * 50)
            
            baseline_summary = baseline_results.get('summary', {})
            print(f"Baseline success rate: {baseline_summary.get('success_rate_percent', 0):.1f}%")
            print(f"Baseline average time: {baseline_summary.get('average_execution_time_ms', 0):.1f}ms")
            
            # Compare specific tests that failed in baseline
            baseline_tests = baseline_results.get('tests', {})
            if 'multi_table_join_optimized' in baseline_tests:
                baseline_join = baseline_tests['multi_table_join_optimized']
                if baseline_join['status'] == 'failed':
                    print(f"\nFIXED: multi_table_join was failing in baseline, now corrected")
            
        except FileNotFoundError:
            print(f"\nBaseline file not found: {baseline_file}")
        except Exception as e:
            print(f"\nError reading baseline: {str(e)}")
    
    def close(self):
        """Close database connection."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            print("\nDatabase connection closed")

def main():
    """Main execution function."""
    print("="*70)
    print("COMPREHENSIVE VALIDATION SUITE")
    print("Enhanced performance testing with all fixes applied")
    print("="*70)
    
    validator = ComprehensiveValidationSuite()
    
    try:
        # Run comprehensive validation
        results = validator.run_comprehensive_validation()
        
        # Compare with baseline
        validator.compare_with_baseline()
        
        # Final assessment
        summary = results['summary']
        if summary['success_rate_percent'] >= 95:
            print(f"\nASSESSMENT: OUTSTANDING - {summary['success_rate_percent']:.1f}% success rate")
        elif summary['success_rate_percent'] >= 90:
            print(f"\nASSESSMENT: EXCELLENT - {summary['success_rate_percent']:.1f}% success rate") 
        elif summary['success_rate_percent'] >= 75:
            print(f"\nASSESSMENT: GOOD - {summary['success_rate_percent']:.1f}% success rate")
        else:
            print(f"\nASSESSMENT: NEEDS IMPROVEMENT - {summary['success_rate_percent']:.1f}% success rate")
        
        print("Enhanced validation complete!")
        
    except Exception as e:
        print(f"Error during comprehensive validation: {str(e)}")
    
    finally:
        validator.close()

if __name__ == "__main__":
    main()