#!/usr/bin/env python3
"""
Analyze the 8 remaining tables to determine optimal primary key strategies
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

load_dotenv()

def analyze_remaining_tables():
    """Analyze the 8 tables that still need primary keys."""
    
    print("="*70)
    print("ANALYZING REMAINING 8 TABLES FOR PRIMARY KEY DESIGN")
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
    
    # The 8 tables without primary keys
    tables_to_analyze = [
        'crypto_listings',
        'crypto_listings_latest_1000', 
        'crypto_global_latest',
        'crypto_ratings',
        'NEWS_TOKENOMICS_W',
        'NEWS_AIRDROPS_W', 
        'FE_CC_INFO_URL',
        'FE_FEAR_GREED_CMC'
    ]
    
    pk_recommendations = {}
    
    for table_name in tables_to_analyze:
        print(f"\n{'='*50}")
        print(f"ANALYZING: {table_name}")
        print(f"{'='*50}")
        
        try:
            # Get column information
            columns = inspector.get_columns(table_name)
            print(f"Columns ({len(columns)}):")
            
            # Show all columns with types
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"  {col['name']:25} | {str(col['type']):20} | {nullable}")
            
            # Analyze column patterns for PK recommendations
            column_names = [col['name'].lower() for col in columns]
            
            has_slug = any('slug' in col for col in column_names)
            has_timestamp = any('timestamp' in col for col in column_names)
            has_date = any('date' in col for col in column_names)  
            has_id = any(col == 'id' for col in column_names)
            has_last_updated = any('last_updated' in col for col in column_names)
            has_event_date = any('event_date' in col for col in column_names)
            has_updatetime = any('updatetime' in col for col in column_names)
            
            print(f"\nColumn Patterns:")
            print(f"  Has 'slug': {has_slug}")
            print(f"  Has 'timestamp': {has_timestamp}")
            print(f"  Has 'date' field: {has_date}")
            print(f"  Has 'id': {has_id}")
            print(f"  Has 'last_updated': {has_last_updated}")
            print(f"  Has 'event_date': {has_event_date}")
            print(f"  Has 'updateTime': {has_updatetime}")
            
            # Get sample data to understand the table better
            sample_query = f'SELECT * FROM "{table_name}" LIMIT 3'
            with engine.connect() as conn:
                result = conn.execute(text(sample_query))
                sample_rows = result.fetchall()
                
                if sample_rows:
                    print(f"\nSample Data (first 3 rows):")
                    for i, row in enumerate(sample_rows, 1):
                        print(f"  Row {i}: {len(row)} columns with data")
                        # Show key columns that might be useful for PK
                        row_dict = dict(row._mapping)
                        for key, value in row_dict.items():
                            if any(pattern in key.lower() for pattern in ['slug', 'timestamp', 'id', 'date', 'update']):
                                print(f"    {key}: {value}")
                
                # Get row count
                count_query = f'SELECT COUNT(*) FROM "{table_name}"'
                count_result = conn.execute(text(count_query))
                row_count = count_result.scalar()
                print(f"\nTotal rows: {row_count:,}")
            
            # Make primary key recommendation
            print(f"\nPRIMARY KEY RECOMMENDATION:")
            if table_name in ['crypto_listings', 'crypto_listings_latest_1000']:
                if has_slug and has_last_updated:
                    recommendation = "(slug, last_updated)"
                    reason = "Crypto listings change over time, slug+last_updated ensures uniqueness"
                elif has_slug and has_timestamp:
                    recommendation = "(slug, timestamp)"
                    reason = "Crypto listings change over time, slug+timestamp ensures uniqueness"
                else:
                    recommendation = "(slug, id)" if has_id else "(slug)"
                    reason = "Fallback to slug-based key"
            elif table_name == 'crypto_global_latest':
                if has_last_updated:
                    recommendation = "(last_updated)"
                    reason = "Global metrics are time-based snapshots, last_updated is unique"
                elif has_timestamp:
                    recommendation = "(timestamp)"
                    reason = "Global metrics are time-based snapshots, timestamp is unique"
                else:
                    recommendation = "Need to examine data pattern"
                    reason = "No clear time-based column identified"
            elif table_name == 'crypto_ratings':
                if has_slug and has_updatetime:
                    recommendation = "(slug, updateTime)"
                    reason = "Ratings change over time per asset"
                elif has_slug and has_timestamp:
                    recommendation = "(slug, timestamp)"
                    reason = "Ratings change over time per asset"
                else:
                    recommendation = "(slug, type)" if 'type' in column_names else "(slug)"
                    reason = "Fallback based on available columns"
            elif table_name in ['NEWS_TOKENOMICS_W', 'NEWS_AIRDROPS_W']:
                if has_slug and has_event_date:
                    recommendation = "(slug, event_date)"
                    reason = "News events are unique per asset per date"
                else:
                    recommendation = "(slug, title)" if 'title' in column_names else "(slug)"
                    reason = "Fallback to slug+title for uniqueness"
            elif table_name == 'FE_CC_INFO_URL':
                if has_slug:
                    recommendation = "(slug)"
                    reason = "Reference data - one record per asset"
                else:
                    recommendation = "(id)" if has_id else "(name)"
                    reason = "Fallback to available unique identifier"
            elif table_name == 'FE_FEAR_GREED_CMC':
                if has_timestamp:
                    recommendation = "(timestamp)"
                    reason = "Fear/Greed index is daily metric, timestamp is unique"
                else:
                    recommendation = "Need to examine data pattern"
                    reason = "No clear unique column identified"
            else:
                recommendation = "To be determined"
                reason = "Needs manual analysis"
            
            pk_recommendations[table_name] = {
                'recommended_pk': recommendation,
                'reason': reason,
                'row_count': row_count,
                'has_slug': has_slug,
                'has_timestamp': has_timestamp or has_last_updated or has_updatetime,
                'columns': [col['name'] for col in columns]
            }
            
            print(f"  Recommended PK: {recommendation}")
            print(f"  Reason: {reason}")
            
        except Exception as e:
            print(f"ERROR analyzing {table_name}: {e}")
            pk_recommendations[table_name] = {
                'recommended_pk': 'ERROR',
                'reason': str(e),
                'row_count': 0,
                'has_slug': False,
                'has_timestamp': False,
                'columns': []
            }
    
    # Summary of recommendations
    print(f"\n{'='*70}")
    print("SUMMARY OF PRIMARY KEY RECOMMENDATIONS")
    print(f"{'='*70}")
    
    for table_name, info in pk_recommendations.items():
        status = "✓" if info['recommended_pk'] != 'ERROR' else "✗"
        print(f"{status} {table_name:30} | {info['recommended_pk']:20} | {info['row_count']:>8,} rows")
    
    engine.dispose()
    return pk_recommendations

if __name__ == "__main__":
    recommendations = analyze_remaining_tables()
    
    print(f"\nNEXT STEP: Use these recommendations to generate the SQL script")
    print(f"All tables analyzed successfully: {len([r for r in recommendations.values() if r['recommended_pk'] != 'ERROR'])}/8")