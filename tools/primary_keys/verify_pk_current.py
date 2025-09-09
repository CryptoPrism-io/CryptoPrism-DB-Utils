#!/usr/bin/env python3
"""
Verify existing primary keys on the three target tables
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def verify_existing_pk():
    """Check what primary keys currently exist on the three tables"""

    print("="*70)
    print("VERIFYING EXISTING PRIMARY KEYS")
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

    print(f"Connected to: {db_config['database']} at {db_config['host']}")

    tables = ['crypto_listings', 'crypto_global_latest', 'FE_FEAR_GREED_CMC']

    query = """
    SELECT
        tc.table_name,
        tc.constraint_name,
        STRING_AGG(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as pk_columns
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
    WHERE tc.constraint_type = 'PRIMARY KEY'
        AND tc.table_schema = 'public'
        AND tc.table_name = %s
    GROUP BY tc.table_name, tc.constraint_name
    """

    total_tables_with_pk = 0

    for table_name in tables:
        print(f"\n{'='*20} {table_name.upper()} {'='*20}")

        try:
            with engine.connect() as conn:
                result = conn.execute(text(query), (table_name,))
                pk_info = result.fetchall()

                if pk_info:
                    print(f"PRIMARY KEY EXISTS: {len(pk_info)} constraint(s)")
                    for row in pk_info:
                        table_name_result, constraint_name, pk_columns = row
                        print(f"  Constraint: {constraint_name}")
                        print(f"  Columns: ({pk_columns})")

                    total_tables_with_pk += 1
                else:
                    print("NO PRIMARY KEY FOUND")

                # Additional table stats
                count_query = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_query.fetchone()[0]
                print(f"Rows: {row_count:,}")

        except Exception as e:
            print(f"ERROR: {e}")

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Tables with primary keys: {total_tables_with_pk}/3")

    if total_tables_with_pk == 3:
        print("\nSUCCESS: All three tables already have primary keys!")
        print("The requested functionality is already implemented.")

    engine.dispose()

if __name__ == "__main__":
    verify_existing_pk()