#!/usr/bin/env python3
"""
Query Optimization Toolkit - Fix slow database queries

This module provides optimized versions of slow database queries identified
in performance testing. Focus: primary_key_validation query optimization.

Author: CryptoPrism-DB-Utils
Version: 1.0.1
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

class QueryOptimizer:
    """Optimized query implementations for database performance issues."""
    
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
    
    def optimized_primary_key_validation(self):
        """
        Optimized version of primary_key_validation query.
        
        Original query was taking 5.2+ seconds. This optimized version uses:
        1. More efficient system catalog queries
        2. Reduced data scanning with targeted filters
        3. Index-friendly query patterns
        
        Returns:
            tuple: (execution_time_ms, results_list, row_count)
        """
        print("\n" + "="*60)
        print("OPTIMIZED PRIMARY KEY VALIDATION")
        print("="*60)
        
        # Optimized query using pg_constraint instead of information_schema
        optimized_query = '''
            SELECT 
                n.nspname as schema_name,
                t.relname as table_name,
                'PRIMARY KEY' as constraint_type,
                c.conname as constraint_name
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE c.contype = 'p'  -- Primary key constraints only
                AND n.nspname = 'public'  -- Public schema only
            ORDER BY t.relname
        '''
        
        print("Executing optimized primary key validation query...")
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(optimized_query))
                rows = result.fetchall()
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to ms
            
            print(f"✅ SUCCESS: Query executed in {execution_time:.1f}ms")
            print(f"📊 Found {len(rows)} primary key constraints")
            
            # Display results
            print("\nPrimary Key Constraints Found:")
            print("-" * 50)
            for row in rows:
                print(f"  {row.table_name} -> {row.constraint_name}")
            
            return execution_time, rows, len(rows)
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return None, None, 0
    
    def compare_query_performance(self):
        """
        Compare original vs optimized query performance.
        
        Runs both versions and provides performance comparison.
        """
        print("\n" + "="*60)
        print("QUERY PERFORMANCE COMPARISON")
        print("="*60)
        
        # Original slow query
        original_query = '''
            SELECT 
                table_name,
                constraint_type,
                constraint_name
            FROM information_schema.table_constraints 
            WHERE constraint_type = 'PRIMARY KEY' 
                AND table_schema = 'public'
            ORDER BY table_name
        '''
        
        print("\n1. Running ORIGINAL query...")
        start_time = time.time()
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(original_query))
                original_rows = result.fetchall()
            original_time = (time.time() - start_time) * 1000
            print(f"   Original: {original_time:.1f}ms ({len(original_rows)} rows)")
        except Exception as e:
            print(f"   Original: FAILED - {str(e)[:60]}")
            original_time = 999999
            original_rows = []
        
        print("\n2. Running OPTIMIZED query...")
        optimized_time, optimized_rows, optimized_count = self.optimized_primary_key_validation()
        
        # Performance analysis
        print("\n" + "="*60)
        print("PERFORMANCE ANALYSIS")
        print("="*60)
        
        if original_time < 999999 and optimized_time:
            improvement = ((original_time - optimized_time) / original_time) * 100
            speedup = original_time / optimized_time
            
            print(f"Original Query Time:   {original_time:.1f}ms")
            print(f"Optimized Query Time:  {optimized_time:.1f}ms")
            print(f"Performance Improvement: {improvement:.1f}% faster")
            print(f"Speedup Factor:        {speedup:.1f}x faster")
            
            if improvement > 50:
                print("🚀 EXCELLENT: Significant performance improvement!")
            elif improvement > 20:
                print("✅ GOOD: Noticeable performance improvement!")
            else:
                print("⚠️  MINIMAL: Limited performance improvement")
                
        else:
            print("⚠️  Unable to complete performance comparison")
        
        # Data integrity check
        if original_rows and optimized_rows:
            if len(original_rows) == len(optimized_rows):
                print("✅ DATA INTEGRITY: Row counts match")
            else:
                print(f"⚠️  DATA MISMATCH: Original={len(original_rows)}, Optimized={len(optimized_rows)}")
    
    def analyze_query_execution_plan(self):
        """
        Analyze execution plans for both original and optimized queries.
        
        Uses EXPLAIN ANALYZE to understand query performance characteristics.
        """
        print("\n" + "="*60)
        print("QUERY EXECUTION PLAN ANALYSIS")
        print("="*60)
        
        queries = {
            'Original (information_schema)': '''
                EXPLAIN ANALYZE
                SELECT 
                    table_name,
                    constraint_type,
                    constraint_name
                FROM information_schema.table_constraints 
                WHERE constraint_type = 'PRIMARY KEY' 
                    AND table_schema = 'public'
                ORDER BY table_name
            ''',
            'Optimized (pg_constraint)': '''
                EXPLAIN ANALYZE
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
            '''
        }
        
        for query_name, query in queries.items():
            print(f"\n{query_name}:")
            print("-" * 50)
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(query))
                    plan = result.fetchall()
                    
                for row in plan:
                    print(f"  {row[0]}")
                    
            except Exception as e:
                print(f"  ERROR: {str(e)}")
    
    def close(self):
        """Close database connection."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            print("\n🔒 Database connection closed")

def main():
    """Main execution function."""
    print("="*70)
    print("QUERY OPTIMIZATION TOOLKIT")
    print("Fixing slow primary_key_validation query")
    print("="*70)
    
    optimizer = QueryOptimizer()
    
    try:
        # Test optimized query
        optimizer.optimized_primary_key_validation()
        
        # Compare performance
        optimizer.compare_query_performance()
        
        # Analyze execution plans
        optimizer.analyze_query_execution_plan()
        
        print("\n✅ Query optimization analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during optimization: {str(e)}")
    
    finally:
        optimizer.close()

if __name__ == "__main__":
    main()