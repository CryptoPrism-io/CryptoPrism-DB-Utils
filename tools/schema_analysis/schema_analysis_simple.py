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
            print(f"ERROR: Table '{table_name}' does not exist!")
            continue

        # Get column information
        columns = inspector.get_columns(table_name, schema='public')
        print(f"\nCOLUMNS ({len(columns)}):")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f"DEFAULT {col['default']}" if col['default'] else ""
            print(f"  {col['name']:30} | {col['type']:15} | {nullable:8} | {default}")

        # Check for existing primary key
        pk_constraint = inspector.get_pk_constraint(table_name, schema='public')
        if pk_constraint and pk_constraint['constrained_columns']:
            pk_cols = ', '.join(pk_constraint['constrained_columns'])
            print(f"\nPRIMARY KEY EXISTS: ({pk_cols})")
        else:
            print(f"\nPRIMARY KEY MISSING")
    engine.dispose()

if __name__ == "__main__":
    analyze_table_schemas()