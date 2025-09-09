#!/usr/bin/env python3
"""
Find the exact table names that match patterns for our target tables
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def find_table_names():
    """Find the exact names of tables matching our targets."""

    db_config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'dbcp')
    }

    conn_string = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    engine = create_engine(conn_string)

    print("Searching for table name variants...")

    # Search patterns for the three tables
    patterns = [
        "crypto_listings",
        "crypto_global_latest",
        "FE_FEAR_GREED_CMC",
        "fe_fear_greed_cmc",
        "fear_greed_cmc",
        "FEAR_GREED_CMC"
    ]

    with engine.connect() as conn:
        for pattern in patterns:
            try:
                result = conn.execute(text(f"""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                        AND table_name ILIKE '%{pattern}%'
                    ORDER BY table_name
                """))

                tables = result.fetchall()
                if tables:
                    print(f"Pattern '{pattern}':")
                    for table in tables:
                        print(f"  - {table[0]}")
                    print()
            except Exception as e:
                print(f"Error with pattern '{pattern}': {e}")

    engine.dispose()

if __name__ == "__main__":
    find_table_names()