#!/usr/bin/env python3
"""
Primary Key Completion Toolkit - Complete missing primary keys

This module identifies tables missing primary keys and provides optimized
SQL for adding appropriate primary keys. Focus: Complete remaining 3+ missing primary keys.

Author: CryptoPrism-DB-Utils
Version: 1.0.1
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

class PrimaryKeyCompletionToolkit:
    """Tools for identifying and completing missing primary keys."""
    
    def __init__(self):
        """Initialize database connection."""
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'), 
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'dbcp')
        }
        
        conn_string = f"postgresql+psycopg2://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        self.engine = create_engine(conn_string)
        
        print(f"Connected to: {self.db_config['database']} at {self.db_config['host']}")
    
    def identify_missing_primary_keys(self):
        """
        Identify all tables without primary keys.
        
        Returns detailed analysis of tables missing primary keys.
        """
        print("\n" + "="*70)
        print("IDENTIFYING TABLES WITHOUT PRIMARY KEYS")
        print("="*70)
        
        # Get all tables in public schema
        all_tables_query = '''
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            ORDER BY table_name
        '''
        
        # Get tables with primary keys
        tables_with_pk_query = '''
            SELECT DISTINCT table_name
            FROM information_schema.table_constraints
            WHERE constraint_type = 'PRIMARY KEY'
                AND table_schema = 'public'
            ORDER BY table_name
        '''
        
        try:
            with self.engine.connect() as conn:
                # Get all tables
                result = conn.execute(text(all_tables_query))
                all_tables = {row[0] for row in result.fetchall()}
                
                # Get tables with primary keys
                result = conn.execute(text(tables_with_pk_query))
                tables_with_pk = {row[0] for row in result.fetchall()}
                
                # Find tables without primary keys
                tables_without_pk = all_tables - tables_with_pk
            
            print(f"ANALYSIS RESULTS:")
            print(f"   Total tables: {len(all_tables)}")
            print(f"   Tables with primary keys: {len(tables_with_pk)}")
            print(f"   Tables WITHOUT primary keys: {len(tables_without_pk)}")

            print(f"\nTables missing primary keys:")
            for table in sorted(tables_without_pk):
                print(f"   - {table}")
            
            return tables_without_pk, tables_with_pk, all_tables
            
        except Exception as e:
            print(f"Error identifying tables: {str(e)}")
            return set(), set(), set()
    
    def analyze_table_structure(self, table_name):
        """
        Analyze table structure to recommend optimal primary key strategy.
        
        Args:
            table_name (str): Name of the table to analyze
            
        Returns:
            dict: Analysis results with primary key recommendations
        """
        print(f"\nAnalyzing: {table_name}")
        print("-" * 50)
        
        analysis = {
            'table_name': table_name,
            'row_count': 0,
            'columns': [],
            'primary_key_candidates': [],
            'recommended_strategy': None,
            'sql_command': None
        }
        
        try:
            with self.engine.connect() as conn:
                # Get row count
                count_query = f'SELECT COUNT(*) FROM "{table_name}"'
                result = conn.execute(text(count_query))
                analysis['row_count'] = result.scalar()
                
                # Get column information
                columns_query = '''
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = :table_name
                        AND table_schema = 'public'
                    ORDER BY ordinal_position
                '''
                
                result = conn.execute(text(columns_query), {"table_name": table_name})
                columns = result.fetchall()
                analysis['columns'] = [dict(row._mapping) for row in columns]
                
                # Analyze for primary key candidates
                pk_candidates = []
                
                for col in analysis['columns']:
                    col_name = col['column_name']
                    
                    # Check for common primary key patterns
                    if col_name.lower() in ['id', 'pk', 'key']:
                        pk_candidates.append({
                            'column': col_name,
                            'strategy': 'simple_id',
                            'reason': 'Standard ID column'
                        })
                    elif col_name.lower() == 'slug':
                        # Check uniqueness for slug
                        unique_check = f'SELECT COUNT(DISTINCT "{col_name}") FROM "{table_name}"'
                        result = conn.execute(text(unique_check))
                        unique_count = result.scalar()
                        
                        if unique_count == analysis['row_count'] and analysis['row_count'] > 0:
                            pk_candidates.append({
                                'column': col_name,
                                'strategy': 'slug_primary',
                                'reason': 'Unique slug column'
                            })
                    elif col_name.lower() == 'timestamp':
                        pk_candidates.append({
                            'column': col_name,
                            'strategy': 'timestamp_primary',
                            'reason': 'Timestamp-based primary key'
                        })
                
                # If no obvious candidates, check for composite keys
                if not pk_candidates:
                    # Check for slug + timestamp combination (common pattern)
                    slug_cols = [col['column_name'] for col in analysis['columns'] if 'slug' in col['column_name'].lower()]
                    time_cols = [col['column_name'] for col in analysis['columns'] if any(t in col['column_name'].lower() for t in ['timestamp', 'date', 'time'])]
                    
                    if slug_cols and time_cols:
                        pk_candidates.append({
                            'column': f"{slug_cols[0]}, {time_cols[0]}",
                            'strategy': 'composite_slug_time',
                            'reason': 'Composite key: slug + timestamp'
                        })
                
                # If still no candidates, recommend adding ID column
                if not pk_candidates:
                    pk_candidates.append({
                        'column': 'id',
                        'strategy': 'add_serial_id',
                        'reason': 'Add new auto-increment ID column'
                    })
                
                analysis['primary_key_candidates'] = pk_candidates
                analysis['recommended_strategy'] = pk_candidates[0] if pk_candidates else None
                
                # Generate SQL command for recommended strategy
                if analysis['recommended_strategy']:
                    analysis['sql_command'] = self.generate_primary_key_sql(table_name, analysis['recommended_strategy'])
            
            # Display analysis
            print(f"   Rows: {analysis['row_count']:,}")
            print(f"   Columns: {len(analysis['columns'])}")
            
            if analysis['primary_key_candidates']:
                print(f"   Primary key candidates:")
                for candidate in analysis['primary_key_candidates']:
                    print(f"     - {candidate['column']} ({candidate['reason']})")
                
                recommended = analysis['recommended_strategy']
                if recommended:
                    print(f"   RECOMMENDED: {recommended['column']} - {recommended['reason']}")
            else:
                print("   ❌ No suitable primary key candidates found")
            
            return analysis
            
        except Exception as e:
            print(f"   ❌ Error analyzing table: {str(e)}")
            analysis['error'] = str(e)
            return analysis
    
    def generate_primary_key_sql(self, table_name, strategy_info):
        """
        Generate SQL command to add primary key based on strategy.
        
        Args:
            table_name (str): Name of the table
            strategy_info (dict): Strategy information
            
        Returns:
            str: SQL command to add primary key
        """
        strategy = strategy_info['strategy']
        column = strategy_info['column']
        
        if strategy == 'simple_id':
            return f'ALTER TABLE "{table_name}" ADD PRIMARY KEY ("{column}");'
        
        elif strategy == 'slug_primary':
            return f'ALTER TABLE "{table_name}" ADD PRIMARY KEY ("{column}");'
        
        elif strategy == 'timestamp_primary':
            return f'ALTER TABLE "{table_name}" ADD PRIMARY KEY ("{column}");'
        
        elif strategy == 'composite_slug_time':
            columns = column.split(', ')
            col_list = ', '.join([f'"{col.strip()}"' for col in columns])
            return f'ALTER TABLE "{table_name}" ADD PRIMARY KEY ({col_list});'
        
        elif strategy == 'add_serial_id':
            return f'''
-- Add auto-increment ID column and make it primary key
ALTER TABLE "{table_name}" ADD COLUMN id SERIAL PRIMARY KEY;
            '''.strip()
        
        else:
            return f'-- Unknown strategy: {strategy}'
    
    def execute_primary_key_additions(self, table_analyses, dry_run=True):
        """
        Execute primary key additions based on analysis.
        
        Args:
            table_analyses (list): List of table analysis results
            dry_run (bool): If True, only show SQL without executing
            
        Returns:
            dict: Execution results
        """
        print("\n" + "="*70)
        print("PRIMARY KEY ADDITION EXECUTION")
        print("="*70)
        
        results = {
            'total_tables': len(table_analyses),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        if dry_run:
            print("DRY RUN MODE - SQL commands will be displayed but not executed")
        else:
            print("EXECUTION MODE - SQL commands will be executed")
        
        for analysis in table_analyses:
            table_name = analysis['table_name']
            
            if not analysis.get('recommended_strategy'):
                print(f"\nSKIPPING {table_name}: No recommended strategy")
                results['skipped'] += 1
                continue

            sql_command = analysis.get('sql_command')
            if not sql_command:
                print(f"\nSKIPPING {table_name}: No SQL command generated")
                results['skipped'] += 1
                continue
            
            print(f"\n{table_name}:")
            print(f"   Strategy: {analysis['recommended_strategy']['strategy']}")
            print(f"   Column(s): {analysis['recommended_strategy']['column']}")
            print(f"   SQL: {sql_command}")
            
            if dry_run:
                results['successful'] += 1
                results['details'].append({
                    'table': table_name,
                    'status': 'dry_run_success',
                    'sql': sql_command
                })
            else:
                try:
                    with self.engine.connect() as conn:
                        conn.execute(text(sql_command))
                        conn.commit()
                    
                    print(f"   SUCCESS: Primary key added")
                    results['successful'] += 1
                    results['details'].append({
                        'table': table_name,
                        'status': 'success',
                        'sql': sql_command
                    })

                except Exception as e:
                    print(f"   FAILED: {str(e)}")
                    results['failed'] += 1
                    results['details'].append({
                        'table': table_name,
                        'status': 'failed',
                        'error': str(e),
                        'sql': sql_command
                    })
        
        # Summary
        print(f"\nEXECUTION SUMMARY:")
        print(f"   Total tables: {results['total_tables']}")
        print(f"   Successful: {results['successful']}")
        print(f"   Failed: {results['failed']}")
        print(f"   Skipped: {results['skipped']}")
        
        return results
    
    def validate_primary_key_completion(self):
        """
        Validate that primary key additions were successful.
        
        Returns updated count of tables with/without primary keys.
        """
        print("\n" + "="*70)
        print("VALIDATING PRIMARY KEY COMPLETION")
        print("="*70)
        
        tables_without_pk, tables_with_pk, all_tables = self.identify_missing_primary_keys()
        
        improvement = len(tables_with_pk)
        total = len(all_tables)
        completion_rate = (improvement / total * 100) if total > 0 else 0
        
        print(f"\nVALIDATION RESULTS:")
        print(f"   Primary key completion rate: {completion_rate:.1f}% ({improvement}/{total})")
        
        if len(tables_without_pk) == 0:
            print("PERFECT: All tables now have primary keys!")
        elif len(tables_without_pk) <= 3:
            print(f"GOOD: Only {len(tables_without_pk)} tables remaining without primary keys")
        else:
            print(f"More work needed: {len(tables_without_pk)} tables still without primary keys")
        
        return len(tables_without_pk), len(tables_with_pk)
    
    def close(self):
        """Close database connection."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            print("\nDatabase connection closed")

def main():
    """Main execution function."""
    print("="*70)
    print("PRIMARY KEY COMPLETION TOOLKIT")
    print("Completing missing primary keys for database optimization")
    print("="*70)
    
    toolkit = PrimaryKeyCompletionToolkit()
    
    try:
        # Step 1: Identify missing primary keys
        tables_without_pk, tables_with_pk, all_tables = toolkit.identify_missing_primary_keys()
        
        if not tables_without_pk:
            print("\nAll tables already have primary keys!")
            return
        
        # Step 2: Analyze each table without primary key
        print(f"\nAnalyzing {len(tables_without_pk)} tables without primary keys...")
        table_analyses = []
        
        for table_name in sorted(tables_without_pk):
            analysis = toolkit.analyze_table_structure(table_name)
            table_analyses.append(analysis)
        
        # Step 3: Show execution plan (dry run)
        print(f"\nExecution plan for {len(table_analyses)} tables:")
        toolkit.execute_primary_key_additions(table_analyses, dry_run=True)
        
        # Step 4: Ask for confirmation (in production, you might want user confirmation)
        print(f"\nReady to execute primary key additions? (This is a dry run for now)")
        
        # Step 5: Execute primary key additions (set dry_run=False to actually execute)
        results = toolkit.execute_primary_key_additions(table_analyses, dry_run=True)
        
        # Step 6: Validate completion
        remaining, completed = toolkit.validate_primary_key_completion()
        
        print(f"\nPRIMARY KEY COMPLETION STATUS:")
        if remaining == 0:
            print("COMPLETE: All tables now have primary keys!")
        else:
            print(f"REMAINING: {remaining} tables still need primary keys")
        
    except Exception as e:
        print(f"Error during primary key completion: {str(e)}")
    
    finally:
        toolkit.close()

if __name__ == "__main__":
    main()