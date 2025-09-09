#!/usr/bin/env python3
"""
Schema Correction Toolkit - Fix table JOIN mismatches

This module provides corrected table schemas and JOIN queries for database
schema mismatches identified in performance testing. Focus: FE_MOMENTUM vs FE_MOMENTUM_SIGNALS.

Author: CryptoPrism-DB-Utils
Version: 1.0.1
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

class SchemaCorrectionToolkit:
    """Schema analysis and correction tools for table mismatches."""
    
    def __init__(self):
        """Initialize database connection."""
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
    
    def analyze_table_schemas(self):
        """
        Analyze the schema differences between FE_MOMENTUM and FE_MOMENTUM_SIGNALS tables.
        
        This helps understand why the JOIN failed and what the correct schema should be.
        """
        print("\n" + "="*70)
        print("TABLE SCHEMA ANALYSIS")
        print("="*70)
        
        tables_to_analyze = [
            'FE_MOMENTUM',
            'FE_MOMENTUM_SIGNALS',
            'FE_OSCILLATORS_SIGNALS'
        ]
        
        for table_name in tables_to_analyze:
            print(f"\n📋 Table: {table_name}")
            print("-" * 50)
            
            # Get column information
            column_query = '''
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = :table_name
                    AND table_schema = 'public'
                ORDER BY ordinal_position
            '''
            
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(column_query), {"table_name": table_name})
                    columns = result.fetchall()
                
                if columns:
                    for col in columns:
                        nullable = "NULL" if col.is_nullable == "YES" else "NOT NULL"
                        print(f"  {col.column_name} | {col.data_type} | {nullable}")
                else:
                    print(f"  ❌ Table not found or no columns")
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
        
        return self.identify_schema_differences()
    
    def identify_schema_differences(self):
        """
        Identify specific differences between momentum tables.
        
        Returns schema mapping for corrected JOIN queries.
        """
        print("\n" + "="*70)
        print("SCHEMA DIFFERENCE ANALYSIS")
        print("="*70)
        
        # Check for RSI columns in both tables
        rsi_check_queries = {
            'FE_MOMENTUM': '''
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'FE_MOMENTUM' 
                    AND column_name LIKE '%rsi%'
                ORDER BY column_name
            ''',
            'FE_MOMENTUM_SIGNALS': '''
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'FE_MOMENTUM_SIGNALS' 
                    AND column_name LIKE '%rsi%'
                ORDER BY column_name
            '''
        }
        
        schema_map = {}
        
        for table_name, query in rsi_check_queries.items():
            print(f"\n🔍 RSI Columns in {table_name}:")
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(query))
                    rsi_columns = [row[0] for row in result.fetchall()]
                
                schema_map[table_name] = rsi_columns
                
                if rsi_columns:
                    for col in rsi_columns:
                        print(f"  ✅ {col}")
                else:
                    print("  ❌ No RSI columns found")
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                schema_map[table_name] = []
        
        # Analysis summary
        print(f"\n📊 ANALYSIS SUMMARY:")
        print("-" * 40)
        fe_momentum_rsi = len(schema_map.get('FE_MOMENTUM', []))
        fe_signals_rsi = len(schema_map.get('FE_MOMENTUM_SIGNALS', []))
        
        print(f"FE_MOMENTUM RSI columns: {fe_momentum_rsi}")
        print(f"FE_MOMENTUM_SIGNALS RSI columns: {fe_signals_rsi}")
        
        if fe_momentum_rsi > 0 and fe_signals_rsi == 0:
            print("✅ CONFIRMED: RSI data is in FE_MOMENTUM, not FE_MOMENTUM_SIGNALS")
            print("🔧 SOLUTION: Use FE_MOMENTUM table for RSI columns in JOINs")
        
        return schema_map
    
    def test_corrected_join_query(self):
        """
        Test the corrected multi-table JOIN query with proper table references.
        
        Original failed query tried to get m_mom_rsi_9 from FE_MOMENTUM_SIGNALS.
        Corrected query gets RSI data from FE_MOMENTUM instead.
        """
        print("\n" + "="*70)
        print("CORRECTED JOIN QUERY TEST")
        print("="*70)
        
        # Corrected JOIN query using FE_MOMENTUM for RSI data
        corrected_query = '''
            SELECT 
                d.slug,
                d.timestamp,
                d.bullish,
                m.m_mom_rsi_9,              -- Get RSI from FE_MOMENTUM
                m.m_mom_roc,                -- Additional momentum data
                o.MACD                      -- Oscillator data
            FROM "FE_DMV_ALL" d
            JOIN "FE_MOMENTUM" m ON d.slug = m.slug AND d.timestamp = m.timestamp
            JOIN "FE_OSCILLATORS_SIGNALS" o ON d.slug = o.slug AND d.timestamp = o.timestamp
            WHERE d.timestamp >= CURRENT_DATE - INTERVAL '7 days'
            LIMIT 15
        '''
        
        print("Testing corrected multi-table JOIN query...")
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(corrected_query))
                rows = result.fetchall()
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            print(f"✅ SUCCESS: Corrected JOIN executed in {execution_time:.1f}ms")
            print(f"📊 Retrieved {len(rows)} rows")
            
            # Display sample results
            if rows:
                print("\n📋 Sample Results (first 5 rows):")
                print("-" * 50)
                for i, row in enumerate(rows[:5], 1):
                    print(f"  {i}. {row.slug}: RSI_9={row.m_mom_rsi_9}, Bullish={row.bullish}")
            
            return True, execution_time, len(rows)
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False, None, 0
    
    def generate_corrected_queries(self):
        """
        Generate a collection of corrected queries with proper table references.
        
        Returns a dictionary of corrected queries for common use cases.
        """
        print("\n" + "="*70)
        print("GENERATING CORRECTED QUERY TEMPLATES")
        print("="*70)
        
        corrected_queries = {
            'multi_table_join_corrected': '''
                -- Multi-table JOIN using correct table references
                SELECT 
                    d.slug,
                    d.timestamp,
                    d.bullish,
                    d.bearish,
                    m.m_mom_rsi_9,              -- RSI from FE_MOMENTUM
                    m.m_mom_roc,                -- ROC from FE_MOMENTUM
                    ms.m_mom_roc_bin,           -- Binary signals from FE_MOMENTUM_SIGNALS
                    o.MACD,                     -- MACD from FE_OSCILLATORS_SIGNALS
                    o.CCI                       -- CCI from FE_OSCILLATORS_SIGNALS
                FROM "FE_DMV_ALL" d
                JOIN "FE_MOMENTUM" m ON d.slug = m.slug AND d.timestamp = m.timestamp
                JOIN "FE_MOMENTUM_SIGNALS" ms ON d.slug = ms.slug AND d.timestamp = ms.timestamp
                JOIN "FE_OSCILLATORS_SIGNALS" o ON d.slug = o.slug AND d.timestamp = o.timestamp
                WHERE d.timestamp >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY d.timestamp DESC, d.bullish DESC
                LIMIT 20
            ''',
            
            'momentum_analysis_corrected': '''
                -- Momentum analysis with correct RSI source
                SELECT 
                    m.slug,
                    m.name,
                    m.timestamp,
                    m.m_mom_rsi_9,
                    m.m_mom_rsi_18,
                    m.m_mom_roc,
                    m.m_mom_williams_% as williams_percent,
                    ms.m_mom_roc_bin as roc_signal,
                    ms.m_mom_williams_%_bin as williams_signal
                FROM "FE_MOMENTUM" m
                JOIN "FE_MOMENTUM_SIGNALS" ms ON m.slug = ms.slug AND m.timestamp = ms.timestamp
                WHERE m.timestamp >= CURRENT_DATE - INTERVAL '3 days'
                    AND m.m_mom_rsi_9 IS NOT NULL
                ORDER BY m.timestamp DESC, m.m_mom_rsi_9 DESC
            ''',
            
            'comprehensive_technical_analysis': '''
                -- Comprehensive technical analysis with all corrected references
                SELECT 
                    d.slug,
                    d.timestamp,
                    d.bullish,
                    d.bearish,
                    d.neutral,
                    -- Momentum indicators from FE_MOMENTUM
                    m.m_mom_rsi_9,
                    m.m_mom_roc,
                    m.m_mom_williams_%,
                    -- Momentum signals from FE_MOMENTUM_SIGNALS  
                    ms.m_mom_roc_bin,
                    ms.m_mom_williams_%_bin,
                    -- Oscillator data from FE_OSCILLATORS_SIGNALS
                    o.MACD,
                    o.CCI,
                    o.ADX
                FROM "FE_DMV_ALL" d
                JOIN "FE_MOMENTUM" m ON d.slug = m.slug AND d.timestamp = m.timestamp
                JOIN "FE_MOMENTUM_SIGNALS" ms ON d.slug = ms.slug AND d.timestamp = ms.timestamp  
                JOIN "FE_OSCILLATORS_SIGNALS" o ON d.slug = o.slug AND d.timestamp = o.timestamp
                WHERE d.timestamp >= CURRENT_DATE - INTERVAL '1 day'
                    AND d.bullish > d.bearish  -- Filter for bullish signals
                ORDER BY d.bullish DESC, m.m_mom_rsi_9 DESC
            '''
        }
        
        # Test each corrected query
        print("\n🧪 Testing corrected query templates...")
        test_results = {}
        
        for query_name, query in corrected_queries.items():
            print(f"\n  Testing: {query_name}")
            try:
                start_time = time.time()
                with self.engine.connect() as conn:
                    result = conn.execute(text(query))
                    rows = result.fetchall()
                
                execution_time = (time.time() - start_time) * 1000
                test_results[query_name] = {
                    'status': 'SUCCESS',
                    'execution_time_ms': execution_time,
                    'rows_returned': len(rows)
                }
                print(f"    ✅ SUCCESS: {execution_time:.1f}ms, {len(rows)} rows")
                
            except Exception as e:
                test_results[query_name] = {
                    'status': 'FAILED',
                    'error': str(e)[:100]
                }
                print(f"    ❌ FAILED: {str(e)[:60]}...")
        
        return corrected_queries, test_results
    
    def close(self):
        """Close database connection."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            print("\n🔒 Database connection closed")

def main():
    """Main execution function."""
    print("="*70)
    print("SCHEMA CORRECTION TOOLKIT")
    print("Fixing multi-table JOIN column mismatches")
    print("="*70)
    
    toolkit = SchemaCorrectionToolkit()
    
    try:
        # Analyze table schemas
        schema_map = toolkit.analyze_table_schemas()
        
        # Test corrected JOIN
        success, exec_time, row_count = toolkit.test_corrected_join_query()
        
        # Generate corrected query templates
        corrected_queries, test_results = toolkit.generate_corrected_queries()
        
        # Summary
        print("\n" + "="*70)
        print("SCHEMA CORRECTION SUMMARY")
        print("="*70)
        
        if success:
            print("✅ Schema correction successful!")
            print(f"✅ Corrected JOIN query works: {exec_time:.1f}ms, {row_count} rows")
        else:
            print("❌ Schema correction needs additional work")
        
        successful_queries = sum(1 for result in test_results.values() if result['status'] == 'SUCCESS')
        total_queries = len(test_results)
        print(f"✅ Query templates tested: {successful_queries}/{total_queries} successful")
        
        print("\n🔧 SOLUTION IMPLEMENTED:")
        print("   - Use FE_MOMENTUM for RSI columns (m_mom_rsi_9, etc.)")
        print("   - Use FE_MOMENTUM_SIGNALS for binary signal columns")
        print("   - Updated JOIN queries with correct table references")
        
    except Exception as e:
        print(f"❌ Error during schema correction: {str(e)}")
    
    finally:
        toolkit.close()

if __name__ == "__main__":
    main()