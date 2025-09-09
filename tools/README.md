# CryptoPrism Database Tools

Organized collection of database analysis, optimization, and maintenance tools.

## 📁 Directory Structure

### 🔑 Primary Keys (`primary_keys/`)
Tools for managing and implementing primary keys across database tables.

- **`add_primary_keys_focused.py`** - Focused primary key addition with specific table targeting
- **`direct_pk_addition.py`** - Direct primary key implementation utility
- **`execute_primary_keys.py`** - Execute primary key creation from SQL scripts
- **`primary_key_completion_toolkit.py`** - Comprehensive primary key analysis and completion
- **`simple_pk_check.py`** - Simple primary key existence verification
- **`verify_pk_current.py`** - Verify current primary key status

### 🔍 Schema Analysis (`schema_analysis/`)
Tools for database schema analysis and validation.

- **`analyze_remaining_tables.py`** - Analyze tables without proper schema structure
- **`schema_analysis.py`** - Comprehensive schema structure analysis
- **`schema_analysis_simple.py`** - Simplified schema analysis for quick checks
- **`schema_correction_toolkit.py`** - Schema correction and optimization toolkit
- **`simple_schema_check.py`** - Basic schema validation checks

### ⚡ Performance (`performance/`)
Database performance testing and optimization tools.

- **`comprehensive_performance_test.py`** - Complete database performance testing suite
- **`query_optimization_toolkit.py`** - Query analysis and optimization recommendations

### 📊 Indexing (`indexing/`)
Tools for database index analysis and optimization.

- **`indexing_analysis_tool.py`** - Comprehensive indexing analysis and recommendations
- **`live_indexing_analysis.py`** - Live database indexing performance analysis

### ✅ Validation (`validation/`)
Data integrity and validation tools.

- **`comprehensive_validation_suite.py`** - Complete database validation and quality checks

### 🛠️ Utilities (`utilities/`)
General purpose database utility scripts.

- **`find_table_names.py`** - Database table discovery and naming utilities
- **`fix_crypto_ratings.py`** - Specific fixes for crypto ratings data integrity

## 🚀 Usage

### Running Tools

```bash
# From project root directory

# Primary Key Tools
python tools/primary_keys/simple_pk_check.py
python tools/primary_keys/primary_key_completion_toolkit.py

# Schema Analysis
python tools/schema_analysis/schema_analysis.py
python tools/schema_analysis/schema_correction_toolkit.py

# Performance Testing
python tools/performance/comprehensive_performance_test.py
python tools/performance/query_optimization_toolkit.py

# Validation
python tools/validation/comprehensive_validation_suite.py
```

### Tool Integration
Many tools can be used together in workflows:

1. **Schema Analysis** → **Primary Key Tools** → **Performance Testing**
2. **Validation** → **Schema Correction** → **Indexing Optimization**
3. **Performance Testing** → **Query Optimization** → **Validation**

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database access
- Required packages: `pip install -r requirements.txt`
- Environment configuration: Copy `.env.example` to `.env`

## 🔧 Configuration

Most tools use environment variables from `.env`:
```env
DB_HOST=your_database_host
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=dbcp
```

## 📊 Output

Tools generate structured output in:
- `output/` - Analysis results and generated scripts
- `reports/` - Detailed analysis reports
- `sql_optimizations/` - Generated SQL optimization scripts

## 🏗️ Workflow Recommendations

### New Database Setup
1. `schema_analysis/schema_analysis.py` - Analyze current state
2. `primary_keys/primary_key_completion_toolkit.py` - Ensure primary keys
3. `indexing/indexing_analysis_tool.py` - Optimize indexing
4. `validation/comprehensive_validation_suite.py` - Validate integrity

### Performance Optimization
1. `performance/comprehensive_performance_test.py` - Baseline performance
2. `performance/query_optimization_toolkit.py` - Identify bottlenecks
3. `indexing/live_indexing_analysis.py` - Optimize indexes
4. `validation/comprehensive_validation_suite.py` - Ensure no regressions

### Maintenance Workflow
1. `utilities/find_table_names.py` - Discover schema changes
2. `schema_analysis/simple_schema_check.py` - Quick health check
3. `primary_keys/simple_pk_check.py` - Verify key integrity
4. `performance/comprehensive_performance_test.py` - Monitor performance

## 🚨 Important Notes

- Always backup database before running modification tools
- Test tools in development environment first
- Review generated SQL scripts before execution
- Monitor performance impact of optimization changes
- Use validation tools after any schema modifications

---

**Part of CryptoPrism Database Utilities v1.1.0**