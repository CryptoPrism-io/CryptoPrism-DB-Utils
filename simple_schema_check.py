#!/usr/bin/env python3
"""
Quick schema check for three specific tables
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def quick_schema_check():
    """Check the basic schema of the three target tables."""

    print("="*60)
    print("DATABASE SCHEMA ANALYSIS")
    print("="*60)

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

    tables = [
        ('crypto_listings', 'PRIMARY KEY (slug, last_updated)'),
        ('crypto_global_latest', 'PRIMARY KEY (last_updated)'),
        ('FE_FEAR_GREED_CMC', 'PRIMARY KEY (timestamp)')
    ]

    for table_name, proposed_pk in tables:
        print(f"\n{'='*20} {table_name} {'='*20}")

        try:
            # Check if table exists and get basic info
            with engine.connect() as conn:
                # Get column count
                col_query = conn.execute(text(f"""
                    SELECT COUNT(*) as col_count
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}' AND table_schema = 'public'
                """))
                col_count = col_query.fetchone()[0]
                print(f"Columns: {col_count}")

                # Check for existing primary key
                pk_query = conn.execute(text(f"""
                    SELECT string_agg(column_name, ', ') as pk_columns
                    FROM information_schema.key_column_usage kcu
                    JOIN information_schema.table_constraints tc ON kcu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND kcu.table_name = '{table_name}'
                        AND kcu.table_schema = 'public'
                """))
                pk_result = pk_query.fetchone()
                if pk_result[0]:
                    print(f"Current PK: ({pk_result[0]})")
                else:
                    print(f"NO PRIMARY KEY - will add: {proposed_pk}")

                # Get row count
                row_query = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = row_query.fetchone()[0]
                print(f"Rows: {row_count:,}")

        except Exception as e:
            print(f"ERROR: {e}")

    engine.dispose()

if __name__ == "__main__":
    quick_schema_check()