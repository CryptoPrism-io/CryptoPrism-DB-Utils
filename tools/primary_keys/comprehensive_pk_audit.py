#!/usr/bin/env python3
"""
Comprehensive Primary Key Audit Tool
Performs a complete audit of primary keys across all database tables
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

class ComprehensivePrimaryKeyAuditor:
    """Comprehensive tool for auditing primary keys across all database tables."""

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

    def get_all_tables_info(self):
        """Get comprehensive information about all tables in the database."""
        print("\n" + "="*80)
        print("COMPREHENSIVE TABLE ANALYSIS")
        print("="*80)

        try:
            with self.engine.connect() as conn:
                # Get all tables with their metadata
                tables_query = '''
                    SELECT
                        t.table_schema,
                        t.table_name,
                        t.table_type,
                        pg_size_pretty(pg_total_relation_size(quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))) as size,
                        pg_total_relation_size(quote_ident(t.table_schema) || '.' || quote_ident(t.table_name)) as size_bytes,
                        c.reltuples::bigint as estimated_rows
                    FROM information_schema.tables t
                    LEFT JOIN pg_class c ON c.relname = t.table_name
                    WHERE t.table_schema = 'public'
                        AND t.table_type = 'BASE TABLE'
                    ORDER BY pg_total_relation_size(quote_ident(t.table_schema) || '.' || quote_ident(t.table_name)) DESC
                '''

                result = conn.execute(text(tables_query))
                tables_info = result.fetchall()

                print(f"Found {len(tables_info)} tables in database")
                print(f"{'Table Name':<35} {'Size':<10} {'Est. Rows':<12} {'Type'}")
                print("-" * 80)

                for row in tables_info:
                    table_name = row[1]
                    size = row[3]
                    est_rows = f"{row[5]:,}" if row[5] else "Unknown"
                    table_type = row[2]
                    print(f"{table_name:<35} {size:<10} {est_rows:<12} {table_type}")

                return tables_info

        except Exception as e:
            print(f"Error getting table information: {str(e)}")
            return []

    def audit_primary_keys(self):
        """Perform comprehensive primary key audit."""
        print("\n" + "="*80)
        print("PRIMARY KEY AUDIT")
        print("="*80)

        try:
            with self.engine.connect() as conn:
                # Get all tables
                all_tables_query = '''
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                '''

                all_tables_result = conn.execute(text(all_tables_query))
                all_tables = {row[0] for row in all_tables_result.fetchall()}

                # Get tables with primary keys
                pk_tables_query = '''
                    SELECT DISTINCT table_name
                    FROM information_schema.table_constraints
                    WHERE constraint_type = 'PRIMARY KEY'
                        AND table_schema = 'public'
                    ORDER BY table_name
                '''

                pk_tables_result = conn.execute(text(pk_tables_query))
                pk_tables = {row[0] for row in pk_tables_result.fetchall()}

                # Find missing primary keys
                missing_pk = all_tables - pk_tables

                print(f"Total tables: {len(all_tables)}")
                print(f"Tables with primary keys: {len(pk_tables)}")
                print(f"Tables missing primary keys: {len(missing_pk)}")
                print(f"Primary key coverage: {(len(pk_tables) / len(all_tables) * 100):.1f}%")

                # Detailed primary key information
                print(f"\n{'='*40} TABLES WITH PRIMARY KEYS {'='*40}")
                pk_details_query = '''
                    SELECT
                        tc.table_name,
                        tc.constraint_name,
                        STRING_AGG(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as pk_columns,
                        COUNT(kcu.column_name) as column_count
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_schema = 'public'
                        AND kcu.table_schema = 'public'
                    GROUP BY tc.table_name, tc.constraint_name
                    ORDER BY tc.table_name
                '''

                pk_details_result = conn.execute(text(pk_details_query))
                pk_details = pk_details_result.fetchall()

                print(f"{'Table Name':<35} {'Constraint':<25} {'Columns':<30} {'Count'}")
                print("-" * 120)
                for row in pk_details:
                    table_name = row[0]
                    constraint = row[1]
                    columns = row[2]
                    count = row[3]
                    print(f"{table_name:<35} {constraint:<25} {columns:<30} {count}")

                # Tables missing primary keys
                if missing_pk:
                    print(f"\n{'='*40} TABLES MISSING PRIMARY KEYS {'='*40}")
                    print(f"{'Table Name':<35} {'Est. Rows':<12} {'Size'}")
                    print("-" * 80)

                    for table_name in sorted(missing_pk):
                        # Get table stats
                        stats_query = f'''
                            SELECT
                                pg_size_pretty(pg_total_relation_size('{table_name}')) as size,
                                c.reltuples::bigint as estimated_rows
                            FROM pg_class c
                            WHERE c.relname = '{table_name}'
                        '''
                        stats_result = conn.execute(text(stats_query))
                        stats = stats_result.fetchone()

                        size = stats[0] if stats else "Unknown"
                        est_rows = f"{stats[1]:,}" if stats and stats[1] else "Unknown"
                        print(f"{table_name:<35} {est_rows:<12} {size}")

                return {
                    'total_tables': len(all_tables),
                    'tables_with_pk': len(pk_tables),
                    'tables_missing_pk': len(missing_pk),
                    'coverage_percent': (len(pk_tables) / len(all_tables) * 100),
                    'missing_tables': sorted(list(missing_pk)),
                    'pk_details': pk_details
                }

        except Exception as e:
            print(f"Error during primary key audit: {str(e)}")
            return None

    def analyze_missing_tables(self, missing_tables):
        """Analyze tables missing primary keys for recommended strategies."""
        print(f"\n{'='*40} ANALYSIS OF MISSING PRIMARY KEYS {'='*40}")

        analysis_results = []

        try:
            with self.engine.connect() as conn:
                for table_name in missing_tables:
                    print(f"\nAnalyzing: {table_name}")
                    print("-" * 50)

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

                    columns_result = conn.execute(text(columns_query), {"table_name": table_name})
                    columns = columns_result.fetchall()

                    # Get row count
                    count_query = f'SELECT COUNT(*) FROM "{table_name}"'
                    count_result = conn.execute(text(count_query))
                    row_count = count_result.scalar()

                    print(f"Rows: {row_count:,}")
                    print(f"Columns: {len(columns)}")

                    # Analyze for primary key candidates
                    pk_candidates = []

                    for col in columns:
                        col_name = col[0]
                        data_type = col[1]
                        is_nullable = col[2]

                        # Check for standard ID columns
                        if col_name.lower() in ['id', 'pk']:
                            pk_candidates.append({
                                'column': col_name,
                                'strategy': 'existing_id',
                                'reason': 'Standard ID column exists'
                            })

                        # Check for slug columns
                        elif col_name.lower() == 'slug':
                            # Check uniqueness
                            unique_query = f'SELECT COUNT(DISTINCT "{col_name}") FROM "{table_name}"'
                            unique_result = conn.execute(text(unique_query))
                            unique_count = unique_result.scalar()

                            if unique_count == row_count and row_count > 0:
                                pk_candidates.append({
                                    'column': col_name,
                                    'strategy': 'unique_slug',
                                    'reason': 'Unique slug column'
                                })

                        # Check for timestamp columns
                        elif 'timestamp' in col_name.lower() or 'date' in col_name.lower():
                            pk_candidates.append({
                                'column': col_name,
                                'strategy': 'timestamp_pk',
                                'reason': 'Timestamp-based primary key'
                            })

                    # Check for composite keys (slug + timestamp)
                    slug_cols = [col[0] for col in columns if 'slug' in col[0].lower()]
                    time_cols = [col[0] for col in columns if any(t in col[0].lower() for t in ['timestamp', 'date', 'time', 'updated'])]

                    if slug_cols and time_cols:
                        pk_candidates.append({
                            'column': f"{slug_cols[0]}, {time_cols[0]}",
                            'strategy': 'composite_slug_time',
                            'reason': 'Composite key: slug + timestamp'
                        })

                    # If no candidates, recommend adding ID
                    if not pk_candidates:
                        pk_candidates.append({
                            'column': 'id',
                            'strategy': 'add_serial_id',
                            'reason': 'Add new auto-increment ID column'
                        })

                    # Display candidates
                    print("Primary key candidates:")
                    for i, candidate in enumerate(pk_candidates, 1):
                        print(f"  {i}. {candidate['column']} - {candidate['reason']}")

                    # Recommend best candidate
                    recommended = pk_candidates[0] if pk_candidates else None
                    if recommended:
                        print(f"RECOMMENDED: {recommended['column']} ({recommended['reason']})")

                        # Generate SQL
                        sql = self.generate_pk_sql(table_name, recommended)
                        print(f"SQL: {sql}")

                    analysis_results.append({
                        'table_name': table_name,
                        'row_count': row_count,
                        'columns': len(columns),
                        'candidates': pk_candidates,
                        'recommended': recommended,
                        'sql': sql if recommended else None
                    })

            return analysis_results

        except Exception as e:
            print(f"Error analyzing missing tables: {str(e)}")
            return []

    def generate_pk_sql(self, table_name, strategy_info):
        """Generate SQL for adding primary key based on strategy."""
        strategy = strategy_info['strategy']
        column = strategy_info['column']

        if strategy == 'existing_id':
            return f'ALTER TABLE "{table_name}" ADD PRIMARY KEY ("{column}");'

        elif strategy == 'unique_slug':
            return f'ALTER TABLE "{table_name}" ADD PRIMARY KEY ("{column}");'

        elif strategy == 'timestamp_pk':
            return f'ALTER TABLE "{table_name}" ADD PRIMARY KEY ("{column}");'

        elif strategy == 'composite_slug_time':
            columns = column.split(', ')
            col_list = ', '.join([f'"{col.strip()}"' for col in columns])
            return f'ALTER TABLE "{table_name}" ADD PRIMARY KEY ({col_list});'

        elif strategy == 'add_serial_id':
            return f'-- Add auto-increment ID column and make it primary key\nALTER TABLE "{table_name}" ADD COLUMN id SERIAL PRIMARY KEY;'

        else:
            return f'-- Unknown strategy: {strategy}'

    def generate_audit_report(self, audit_results, analysis_results):
        """Generate comprehensive audit report."""
        print(f"\n{'='*80}")
        print("PRIMARY KEY AUDIT REPORT")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Database: {self.db_config['database']}")

        if audit_results:
            print(f"\nSUMMARY:")
            print(f"  Total tables: {audit_results['total_tables']}")
            print(f"  Tables with primary keys: {audit_results['tables_with_pk']}")
            print(f"  Tables missing primary keys: {audit_results['tables_missing_pk']}")
            print(f"  Coverage: {audit_results['coverage_percent']:.1f}%")

            if audit_results['missing_tables']:
                print(f"\nMISSING PRIMARY KEYS:")
                for table in audit_results['missing_tables']:
                    print(f"  - {table}")

                print(f"\nRECOMMENDED ACTIONS:")
                for analysis in analysis_results:
                    table = analysis['table_name']
                    recommended = analysis['recommended']
                    if recommended:
                        print(f"  {table}: Add PK on {recommended['column']}")
                        print(f"    SQL: {analysis['sql']}")

        print(f"\n{'='*80}")

    def close(self):
        """Close database connection."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            print("\nDatabase connection closed")

def main():
    """Main execution function."""
    auditor = ComprehensivePrimaryKeyAuditor()

    try:
        # Step 1: Get all table information
        tables_info = auditor.get_all_tables_info()

        # Step 2: Perform primary key audit
        audit_results = auditor.audit_primary_keys()

        # Step 3: Analyze missing primary keys
        if audit_results and audit_results['missing_tables']:
            analysis_results = auditor.analyze_missing_tables(audit_results['missing_tables'])
        else:
            analysis_results = []

        # Step 4: Generate audit report
        auditor.generate_audit_report(audit_results, analysis_results)

    except Exception as e:
        print(f"Error during audit: {str(e)}")

    finally:
        auditor.close()

if __name__ == "__main__":
    main()