#!/usr/bin/env python3
"""
Focused script to add primary keys to the three specific tables:
1. crypto_listings
2. crypto_global_latest
3. FE_FEAR_GREED_CMC
"""

import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def add_primary_keys_focused():
    """Add primary keys to the three specific tables."""

    print("="*70)
    print("ADDING PRIMARY KEYS TO THREE SPECIFIC TABLES")
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

    # Primary key creation commands for the three tables
    pk_commands = [
        {
            'table': 'crypto_listings',
            'sql': 'ALTER TABLE "crypto_listings" ADD CONSTRAINT pk_crypto_listings PRIMARY KEY (slug, last_updated)',
            'description': 'Crypto listings time-series data'
        },
        {
            'table': 'crypto_global_latest',
            'sql': 'ALTER TABLE "crypto_global_latest" ADD CONSTRAINT pk_crypto_global_latest PRIMARY KEY (last_updated)',
            'description': 'Global market metrics snapshots'
        },
        {
            'table': 'FE_FEAR_GREED_CMC',
            'sql': 'ALTER TABLE "FE_FEAR_GREED_CMC" ADD CONSTRAINT pk_fe_fear_greed_cmc PRIMARY KEY (timestamp)',
            'description': 'Fear/Greed index daily metrics'
        }
    ]

    print(f"Executing primary key creation for {len(pk_commands)} tables...")
    print()

    success_count = 0
    failed_tables = []

    for i, cmd in enumerate(pk_commands, 1):
        print(f"[{i}/3] Creating PK for {cmd['table']}")
        print(f"      Description: {cmd['description']}")

        try:
            start_time = time.time()
            with engine.connect() as conn:
                # Start transaction
                trans = conn.begin()
                try:
                    result = conn.execute(text(cmd['sql']))
                    trans.commit()
                    end_time = time.time()

                    execution_time = (end_time - start_time) * 1000
                    print(f"      Status: SUCCESS ({execution_time:.1f}ms)")
                    success_count += 1

                except Exception as e:
                    trans.rollback()
                    print(f"      Status: FAILED - {str(e)}")
                    failed_tables.append(cmd['table'])

        except Exception as e:
            print(f"      Status: CONNECTION ERROR - {str(e)}")
            failed_tables.append(cmd['table'])

        print()

    print("="*70)
    print("PRIMARY KEY CREATION SUMMARY")
    print("="*70)
    print(f"Successful: {success_count}/3 tables")
    print(f"Failed: {len(failed_tables)}/3 tables")

    if failed_tables:
        print(f"\nFailed tables:")
        for table in failed_tables:
            print(f"  - {table}")
        print(f"\nRecommendation: Check for duplicate data in failed tables")
    else:
        print("\nALL PRIMARY KEYS CREATED SUCCESSFULLY!")
    return success_count, failed_tables

def verify_primary_keys():
    """Verify that the primary keys were created successfully."""

    print("\n" + "="*70)
    print("VERIFYING PRIMARY KEY CREATION")
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

    # Query to check primary keys for the three tables
    verification_query = """
    SELECT
        kcu.table_name,
        STRING_AGG(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as primary_key_columns
    FROM information_schema.key_column_usage kcu
    JOIN information_schema.table_constraints tc ON kcu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'PRIMARY KEY'
        AND kcu.table_schema = 'public'
        AND kcu.table_name IN (
            'crypto_listings',
            'crypto_global_latest',
            'FE_FEAR_GREED_CMC'
        )
    GROUP BY kcu.table_name
    ORDER BY kcu.table_name;
    """

    try:
        with engine.connect() as conn:
            result = conn.execute(text(verification_query))
            pk_results = result.fetchall()

            print(f"Primary keys found for {len(pk_results)} tables:")
            for row in pk_results:
                table_name, pk_columns = row
                print(f"  {table_name:30} | PK: ({pk_columns})")
            # Overall database status check
            if len(pk_results) == 3:
                print("\nSUCCESS: All 3 tables now have primary keys!")
            else:
                missing_count = 3 - len(pk_results)
                print(f"\nWARNING: {missing_count} tables still missing primary keys")

    except Exception as e:
        print(f"ERROR during verification: {e}")

    engine.dispose()

if __name__ == "__main__":
    print("Starting focused primary key creation process...")

    success_count, failed_tables = add_primary_keys_focused()

    if success_count > 0:
        verify_primary_keys()

        if not failed_tables:
            print("\n" + "="*70)
            print("PRIMARY KEY ADDITION COMPLETE!")
            print("="*70)
            print("All targeted tables now have primary keys")
            print("Database optimization enhanced!")

    print(f"\nNext steps:")
    print("1. Consider adding strategic indexes for improved query performance")
    print("2. Run ANALYZE to update table statistics")