#!/usr/bin/env python3
"""
Live Indexing Analysis Tool - Check actual database index status
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

load_dotenv()

def get_live_indexing_status():
    """Get current indexing status from live database."""
    
    print("="*70)
    print("LIVE DATABASE INDEXING ANALYSIS")
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
    inspector = inspect(engine)
    
    print(f"Connected to: {db_config['database']}")
    print(f"Host: {db_config['host']}")
    
    # Get all table names
    table_names = inspector.get_table_names(schema='public')
    print(f"Found {len(table_names)} tables")
    
    print("\nPRIMARY KEY AND INDEX ANALYSIS")
    print("-" * 70)
    
    tables_with_pk = 0
    tables_without_pk = 0
    total_indexes = 0
    
    pk_status = {}
    index_summary = {}
    
    for table_name in sorted(table_names):
        try:
            # Get primary key info
            primary_key = inspector.get_pk_constraint(table_name)
            has_pk = bool(primary_key.get('constrained_columns', []))
            
            if has_pk:
                tables_with_pk += 1
                pk_columns = primary_key.get('constrained_columns', [])
                pk_status[table_name] = {'has_pk': True, 'columns': pk_columns}
            else:
                tables_without_pk += 1
                pk_status[table_name] = {'has_pk': False, 'columns': []}
            
            # Get indexes
            indexes = inspector.get_indexes(table_name)
            index_count = len(indexes)
            total_indexes += index_count
            
            index_summary[table_name] = {
                'count': index_count,
                'indexes': [idx['name'] for idx in indexes]
            }
            
            # Show table summary
            pk_status_str = f"PK: {', '.join(pk_columns)}" if has_pk else "NO PK"
            index_status_str = f"Indexes: {index_count}" if index_count > 0 else "NO INDEXES"
            
            print(f"{table_name:30} | {pk_status_str:25} | {index_status_str}")
            
        except Exception as e:
            print(f"ERROR analyzing {table_name}: {e}")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total tables: {len(table_names)}")
    print(f"Tables WITH primary keys: {tables_with_pk}")
    print(f"Tables WITHOUT primary keys: {tables_without_pk}")
    print(f"Total indexes across all tables: {total_indexes}")
    
    if tables_without_pk > 0:
        print(f"\nTABLES WITHOUT PRIMARY KEYS:")
        for table, status in pk_status.items():
            if not status['has_pk']:
                index_count = index_summary[table]['count']
                print(f"  - {table} (indexes: {index_count})")
    
    # Check specific problematic tables
    print(f"\nSPECIFIC TABLE ANALYSIS:")
    critical_tables = ['FE_DMV_ALL', '1K_coins_ohlcv', 'FE_MOMENTUM_SIGNALS', 
                      'FE_OSCILLATORS_SIGNALS', 'FE_RATIOS_SIGNALS']
    
    for table in critical_tables:
        if table in pk_status:
            status = pk_status[table]
            indexes = index_summary[table]
            
            print(f"\n[CRITICAL] {table}:")
            if status['has_pk']:
                print(f"  Primary Key: ({', '.join(status['columns'])})")
            else:
                print(f"  Primary Key: MISSING")
            
            if indexes['count'] > 0:
                print(f"  Indexes ({indexes['count']}):")
                for idx_name in indexes['indexes']:
                    print(f"    - {idx_name}")
            else:
                print(f"  Indexes: NONE")
    
    engine.dispose()
    return pk_status, index_summary

def check_query_performance():
    """Test some basic queries to check performance."""
    
    print(f"\nQUERY PERFORMANCE TEST")
    print("-" * 70)
    
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
    
    test_queries = [
        {
            'name': 'FE_DMV_ALL count',
            'query': 'SELECT COUNT(*) FROM "FE_DMV_ALL"',
            'description': 'Simple count query'
        },
        {
            'name': 'FE_DMV_ALL recent data',
            'query': 'SELECT slug, timestamp FROM "FE_DMV_ALL" ORDER BY timestamp DESC LIMIT 5',
            'description': 'Recent data with ORDER BY'
        },
        {
            'name': '1K_coins_ohlcv volume query',
            'query': 'SELECT slug, volume FROM "1K_coins_ohlcv" WHERE volume > 1000000 ORDER BY volume DESC LIMIT 10',
            'description': 'Volume filtering and sorting'
        }
    ]
    
    import time
    
    for test in test_queries:
        try:
            start_time = time.time()
            with engine.connect() as conn:
                result = conn.execute(text(test['query']))
                rows = result.fetchall()
            end_time = time.time()
            
            execution_time = (end_time - start_time) * 1000  # Convert to ms
            print(f"{test['name']:25} | {execution_time:6.1f}ms | {len(rows)} rows | {test['description']}")
            
        except Exception as e:
            print(f"{test['name']:25} | ERROR: {str(e)[:50]}...")
    
    engine.dispose()

if __name__ == "__main__":
    try:
        pk_status, index_summary = get_live_indexing_status()
        check_query_performance()
        
        print(f"\nCONCLUSION:")
        tables_without_pk = sum(1 for status in pk_status.values() if not status['has_pk'])
        total_indexes = sum(summary['count'] for summary in index_summary.values())
        
        if tables_without_pk > 0:
            print(f"ACTION REQUIRED: {tables_without_pk} tables still need primary keys")
        else:
            print(f"PRIMARY KEYS: All tables have primary keys")
            
        if total_indexes < len(pk_status) * 2:  # Expect at least 2 indexes per table
            print(f"INDEXING: May need additional strategic indexes")
        else:
            print(f"INDEXING: Good index coverage detected")
            
    except Exception as e:
        print(f"ERROR: {e}")
        print("Make sure database credentials are configured in .env file")