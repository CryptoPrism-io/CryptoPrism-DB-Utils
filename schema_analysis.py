#!/usr/bin/env python3
"""
Analyze the current schema of three specific tables and their primary keys:
1. crypto_listings
2. crypto_global_latest
3. FE_FEAR_GREED_CMC
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

load_dotenv()

def analyze_table_schemas():
    """Analyze the schema and existing primary keys for the three target tables."""

    print("="*70)
    print("ANALYZING CURRENT SCHEMA OF THREE TABLES")
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

    target_tables = ['crypto_listings', 'crypto_global_latest', 'FE_FEAR_GREED_CMC']

    inspector = inspect(engine)

    for table_name in target_tables:
        print(f"\n{'='*20} {table_name.upper()} {'='*20}")

        # Check if table exists
        if not inspector.has_table(table_name, schema='public'):
            print(f"❌ Table '{table_name}' does not exist!")
            continue

        # Get column information
        columns = inspector.get_columns(table_name, schema='public')
        print(f"\n📋 COLUMNS ({len(columns)}):")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f"DEFAULT {col['default']}" if col['default'] else ""
            print(f"  {col['name']:30} | {col['type']:15} | {nullable:8} | {default}")

        # Check for existing primary key
        pk_constraint = inspector.get_pk_constraint(table_name, schema='public')
        if pk_constraint and pk_constraint['constrained_columns']:
            pk_cols = ', '.join(pk_constraint['constrained_columns'])
            print(f"\n🔑 PRIMARY KEY EXISTS: ({pk_cols})")
        else:
            print(f"\n🔑 PRIMARY KEY MISSING")
        # Get row count (safely)
        try:
            with engine.connect() as conn:
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.fetchone()[0]
                print(f"\n📊 ROWS: {row_count:,}")
        except Exception as e:
            print(f"\n📊 ROWS: Error counting - {e}")

        # Check for duplicates in potential primary key columns
        if table_name == 'crypto_listings':
            # Check potential PK columns: slug, last_updated
            print(f"\n🔍 ANALYZING POTENTIAL PRIMARY KEY (slug, last_updated):")
            try:
                with engine.connect() as conn:
                    # Check total rows vs distinct combinations
                    distinct_query = conn.execute(text("SELECT COUNT(DISTINCT (slug, last_updated)) FROM crypto_listings"))
                    distinct_count = distinct_query.fetchone()[0]

                    total_query = conn.execute(text("SELECT COUNT(*) FROM crypto_listings"))
                    total_count = total_query.fetchone()[0]

                    if distinct_count == total_count:
                        print(f"  ✅ (slug, last_updated) WOULD BE UNIQUE ({distinct_count:,} distinct combinations out of {total_count:,} total)")
                    else:
                        duplicates = total_count - distinct_count
                        print(f"  ❌ DUPLICATES FOUND: {duplicates:,} duplicate combinations out of {total_count:,} total")
            except Exception as e:
                print(f"  ⚠️  Error checking uniqueness: {e}")

        elif table_name == 'crypto_global_latest':
            # Check potential PK column: last_updated
            print(f"\n🔍 ANALYZING POTENTIAL PRIMARY KEY (last_updated):")
            try:
                with engine.connect() as conn:
                    distinct_query = conn.execute(text("SELECT COUNT(DISTINCT last_updated) FROM crypto_global_latest"))
                    distinct_count = distinct_query.fetchone()[0]

                    total_query = conn.execute(text("SELECT COUNT(*) FROM crypto_global_latest"))
                    total_count = total_query.fetchone()[0]

                    if distinct_count == total_count:
                        print(f"  ✅ last_updated WOULD BE UNIQUE ({distinct_count:,} distinct values out of {total_count:,} total)")
                    else:
                        duplicates = total_count - distinct_count
                        print(f"  ❌ DUPLICATES FOUND: {duplicates:,} duplicate values out of {total_count:,} total")
            except Exception as e:
                print(f"  ⚠️  Error checking uniqueness: {e}")

        elif table_name == 'FE_FEAR_GREED_CMC':
            # Check potential PK column: timestamp
            print(f"\n🔍 ANALYZING POTENTIAL PRIMARY KEY (timestamp):")
            try:
                with engine.connect() as conn:
                    distinct_query = conn.execute(text("SELECT COUNT(DISTINCT \"timestamp\") FROM \"FE_FEAR_GREED_CMC\""))
                    distinct_count = distinct_query.fetchone()[0]

                    total_query = conn.execute(text("SELECT COUNT(*) FROM \"FE_FEAR_GREED_CMC\""))
                    total_count = total_query.fetchone()[0]

                    if distinct_count == total_count:
                        print(f"  ✅ timestamp WOULD BE UNIQUE ({distinct_count:,} distinct values out of {total_count:,} total)")
                    else:
                        duplicates = total_count - distinct_count
                        print(f"  ❌ DUPLICATES FOUND: {duplicates:,} duplicate values out of {total_count:,} total")
            except Exception as e:
                print(f"  ⚠️  Error checking uniqueness: {e}")

        print()

    engine.dispose()

if __name__ == "__main__":
    analyze_table_schemas()