#!/usr/bin/env python3
"""
Query Execution Plan Analysis for Fear/Greed Performance Regression
"""

import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def analyze_fear_greed_query():
    """Analyze the fear/greed query execution plan."""

    print("="*80)
    print("FEAR/GREED QUERY EXECUTION PLAN ANALYSIS")
    print("="*80)

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

    print(f"Connected to: {db_config['database']} at {db_config['host']}")

    # Fear/Greed query from the test
    fear_greed_query = '''
        SELECT timestamp, fear_greed_index, sentiment
        FROM "FE_FEAR_GREED_CMC"
        ORDER BY timestamp DESC
        LIMIT 30
    '''

    print("\nQuery:")
    print(fear_greed_query.strip())

    try:
        with engine.connect() as conn:
            # Get execution plan
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {fear_greed_query}"
            result = conn.execute(text(explain_query))
            row = result.fetchone()
            if row:
                plan = row[0]
            else:
                plan = None

            print("\nEXECUTION PLAN:")
            print(json.dumps(plan, indent=2))

            # Also get actual execution time
            print("\nACTUAL EXECUTION:")
            import time
            start_time = time.time()
            result = conn.execute(text(fear_greed_query))
            rows = result.fetchall()
            end_time = time.time()

            execution_time = (end_time - start_time) * 1000
            print(f"Rows returned: {len(rows)}")
            print(f"Execution time: {execution_time:.2f}ms")

            # Check table structure and indexes
            print("\nTABLE STRUCTURE:")
            table_info = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'FE_FEAR_GREED_CMC'
                ORDER BY ordinal_position
            """))
            for row in table_info:
                print(f"  {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")

            print("\nINDEXES:")
            try:
                indexes = conn.execute(text("""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE tablename = 'FE_FEAR_GREED_CMC'
                """))
                index_count = 0
                for row in indexes:
                    print(f"  {row[0]}: {row[1]}")
                    index_count += 1
                if index_count == 0:
                    print("  No indexes found on this table!")
            except Exception as e:
                print(f"  Error getting indexes: {e}")

            print("\nPRIMARY KEY:")
            try:
                pk = conn.execute(text("""
                    SELECT conname, conkey, confkey
                    FROM pg_constraint
                    WHERE conrelid = '"FE_FEAR_GREED_CMC"'::regclass
                    AND contype = 'p'
                """))
                for row in pk:
                    print(f"  {row[0]}: {row[1]}")
            except Exception as e:
                print(f"  Error getting primary key: {e}")

            # Check table size
            print("\nTABLE STATISTICS:")
            try:
                stats = conn.execute(text("""
                    SELECT
                        schemaname, relname,
                        n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
                    FROM pg_stat_user_tables
                    WHERE relname = 'FE_FEAR_GREED_CMC'
                """))
                for row in stats:
                    print(f"  Live tuples: {row[5]}")
                    print(f"  Dead tuples: {row[6]}")
                    print(f"  Total operations: {row[2] + row[3] + row[4]}")
            except Exception as e:
                print(f"  Error getting table statistics: {e}")

    except Exception as e:
        print(f"Error: {e}")

    engine.dispose()

if __name__ == "__main__":
    analyze_fear_greed_query()