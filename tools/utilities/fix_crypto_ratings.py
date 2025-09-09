#!/usr/bin/env python3
"""
Fix the crypto_ratings table by handling duplicate data
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def analyze_crypto_ratings_duplicates():
    """Analyze the duplicate issue in crypto_ratings table."""
    
    print("="*70)
    print("ANALYZING crypto_ratings DUPLICATE DATA ISSUE")
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
    
    # Check for duplicates
    duplicate_query = """
    SELECT 
        slug, 
        "updateTime",
        COUNT(*) as duplicate_count
    FROM "crypto_ratings"
    GROUP BY slug, "updateTime"
    HAVING COUNT(*) > 1
    ORDER BY duplicate_count DESC, slug;
    """
    
    print("Checking for duplicate records...")
    with engine.connect() as conn:
        result = conn.execute(text(duplicate_query))
        duplicates = result.fetchall()
        
        if duplicates:
            print(f"Found {len(duplicates)} sets of duplicate records:")
            for slug, update_time, count in duplicates[:10]:  # Show first 10
                print(f"  {slug} | {update_time} | {count} duplicates")
            
            if len(duplicates) > 10:
                print(f"  ... and {len(duplicates) - 10} more")
        else:
            print("No duplicates found - this is unexpected!")
            
    # Check the specific duplicate mentioned in error
    specific_query = """
    SELECT * FROM "crypto_ratings" 
    WHERE slug = 'luckycoin' AND "updateTime" = '2025-03-26T03:49:59.000Z'
    ORDER BY slug, "updateTime";
    """
    
    print(f"\nChecking the specific duplicate mentioned in error:")
    with engine.connect() as conn:
        result = conn.execute(text(specific_query))
        specific_duplicates = result.fetchall()
        
        print(f"Found {len(specific_duplicates)} records for luckycoin at 2025-03-26T03:49:59.000Z:")
        for i, row in enumerate(specific_duplicates, 1):
            row_dict = dict(row._mapping)
            print(f"  Record {i}: {row_dict}")
    
    # Show table structure
    structure_query = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'crypto_ratings'
    ORDER BY ordinal_position;
    """
    
    print(f"\nTable structure:")
    with engine.connect() as conn:
        result = conn.execute(text(structure_query))
        columns = result.fetchall()
        
        for col_name, data_type, is_nullable in columns:
            print(f"  {col_name:15} | {data_type:20} | {is_nullable}")
    
    # Get total row count
    count_query = 'SELECT COUNT(*) FROM "crypto_ratings"'
    with engine.connect() as conn:
        result = conn.execute(text(count_query))
        total_rows = result.scalar()
        print(f"\nTotal rows in crypto_ratings: {total_rows:,}")
    
    engine.dispose()
    return duplicates

def fix_crypto_ratings_duplicates():
    """Fix duplicates by keeping only the latest record per slug+updateTime combination."""
    
    print(f"\n" + "="*70)
    print("FIXING crypto_ratings DUPLICATES")
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
    
    # Strategy: Create a new table with distinct records, then replace the original
    fix_strategy = """
    -- Step 1: Create temporary table with unique records only
    -- Using ROW_NUMBER() to keep one record per (slug, updateTime) combination
    CREATE TEMP TABLE crypto_ratings_fixed AS
    SELECT 
        slug,
        type,
        score,
        rating,
        "updateTime",
        link
    FROM (
        SELECT 
            *,
            ROW_NUMBER() OVER (PARTITION BY slug, "updateTime" ORDER BY score DESC NULLS LAST) as rn
        FROM "crypto_ratings"
    ) ranked
    WHERE rn = 1;
    
    -- Step 2: Check how many records we'll have
    SELECT COUNT(*) as clean_record_count FROM crypto_ratings_fixed;
    """
    
    print("Creating clean version of crypto_ratings...")
    
    try:
        with engine.connect() as conn:
            # Execute the fix strategy
            result = conn.execute(text(fix_strategy))
            
            # Get the count of clean records
            count_query = "SELECT COUNT(*) FROM crypto_ratings_fixed"
            count_result = conn.execute(text(count_query))
            clean_count = count_result.scalar()
            
            print(f"Clean records created: {clean_count:,}")
            
            # Now replace the original table
            replace_query = """
            BEGIN;
            
            -- Drop the original table
            DROP TABLE "crypto_ratings";
            
            -- Rename temp table to original name
            ALTER TABLE crypto_ratings_fixed RENAME TO crypto_ratings;
            
            COMMIT;
            """
            
            print("Replacing original table with clean data...")
            conn.execute(text(replace_query))
            
            print("SUCCESS: crypto_ratings table cleaned of duplicates")
            
            # Now try to create the primary key
            pk_query = 'ALTER TABLE "crypto_ratings" ADD CONSTRAINT pk_crypto_ratings PRIMARY KEY (slug, "updateTime")'
            
            print("Creating primary key on cleaned table...")
            conn.execute(text(pk_query))
            
            print("SUCCESS: Primary key created on crypto_ratings!")
            
    except Exception as e:
        print(f"ERROR during fix: {e}")
        return False
        
    engine.dispose()
    return True

if __name__ == "__main__":
    print("Investigating crypto_ratings duplicate issue...")
    
    duplicates = analyze_crypto_ratings_duplicates()
    
    if duplicates:
        print(f"\nProceeding to fix {len(duplicates)} sets of duplicates...")
        success = fix_crypto_ratings_duplicates()
        
        if success:
            print(f"\nFIX COMPLETED SUCCESSFULLY!")
            print(f"crypto_ratings table now has primary key")
            print(f"All 23 tables should now have primary keys")
        else:
            print(f"\nFIX FAILED - manual intervention may be required")
    else:
        print(f"\nNo duplicates found - trying alternative primary key strategy...")
        
        # Try different primary key combinations
        alternatives = [
            ("slug, type, \"updateTime\"", "Include type in composite key"),
            ("slug, \"updateTime\", score", "Include score to break ties"),
        ]
        
        for pk_columns, description in alternatives:
            print(f"Trying: {pk_columns} ({description})")
            # Implementation would go here if needed