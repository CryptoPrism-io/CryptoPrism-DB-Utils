#!/usr/bin/env python3
"""
Direct primary key addition for the three tables
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def execute_sql_direct():
    """Execute primary key creation SQL directly"""

    print("="*70)
    print("DIRECT PRIMARY KEY ADDITION")
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

    # Primary key SQL commands
    sql_commands = [
        {
            'table': 'crypto_listings',
            'sql': 'ALTER TABLE "crypto_listings" ADD CONSTRAINT pk_crypto_listings PRIMARY KEY (slug, last_updated)',
            'description': 'PRIMARY KEY (slug, last_updated)'
        },
        {
            'table': 'crypto_global_latest',
            'sql': 'ALTER TABLE "crypto_global_latest" ADD CONSTRAINT pk_crypto_global_latest PRIMARY KEY (last_updated)',
            'description': 'PRIMARY KEY (last_updated)'
        },
        {
            'table': 'FE_FEAR_GREED_CMC',
            'sql': 'ALTER TABLE "FE_FEAR_GREED_CMC" ADD CONSTRAINT pk_fe_fear_greed_cmc PRIMARY KEY (timestamp)',
            'description': 'PRIMARY KEY (timestamp)'
        }
    ]

    print("Executing primary key creation...")
    print()

    success_count = 0

    for i, cmd in enumerate(sql_commands, 1):
        print(f"[{i}/3] {cmd['table']}")
        print(f"   SQL: {cmd['description']}")

        try:
            with engine.connect() as conn:
                result = conn.execute(text(cmd['sql']))
                print("   Status: SUCCESS")

            success_count += 1

        except Exception as e:
            print(f"   Status: FAILED - {str(e)}")

        print()

    print("="*70)
    print(f"SUCCESSFUL: {success_count}/3 tables")
    print("="*70)

    if success_count == 3:
        print("All primary keys added successfully!")

    engine.dispose()

    return success_count

if __name__ == "__main__":
    execute_sql_direct()