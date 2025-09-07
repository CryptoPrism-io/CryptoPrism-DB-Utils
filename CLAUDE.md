# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Install from source for development
pip install -e ".[dev]"

# Install with all optional dependencies  
pip install -e ".[all]"
```

### Testing
```bash
# Run tests with coverage
pytest tests/ --cov=crypto_db_utils
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code  
flake8 src/ tests/

# Type checking
mypy src/
```

### CLI Usage
The package provides a unified CLI accessible via:
```bash
cryptoprism-db <command> [options]
cpdb <command> [options]  # Short alias
```

Main commands:
- `analyze` - Database schema analysis
- `benchmark` - Performance testing
- `optimize` - Database optimization
- `validate` - Data validation
- `visualize` - Generate ERD diagrams
- `utils` - Utility functions

## Architecture

### Package Structure
- **src/crypto_db_utils/** - Main package source
  - **core/** - Base classes (DatabaseConnection, BaseAnalyzer)
  - **analysis/** - Schema analysis and reporting tools
  - **benchmarking/** - Performance testing utilities
  - **optimization/** - Database optimization engines
  - **indexing/** - Index management tools
  - **validation/** - Data integrity checks
- **cli/** - Command-line interface
- **config/** - Database configuration management

### Database Support
Designed for PostgreSQL with support for CryptoPrism's three-database architecture:
- `main` (dbcp) - Primary trading database
- `ai` (cp_ai) - AI analysis database  
- `backtest` (cp_backtest) - Backtesting database
- `backtest_h` (cp_backtest_h) - Historical backtesting

### Core Components

**DatabaseConnection** (`src/crypto_db_utils/core/db_connection.py`)
- Centralized connection management
- Environment-based configuration via `.env` file
- Multi-database support with alias mapping

**BaseAnalyzer** (`src/crypto_db_utils/core/base_analyzer.py`)
- Base class for all analysis tools
- Standardized output directory structure
- Common database interaction patterns

### Configuration
Environment variables are loaded from `.env` file (copy from `.env.example`):
- Database credentials: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- Optional databases: `DB_NAME_AI`, `DB_NAME_BT`, `DB_NAME_BTH`
- Output directory: `OUTPUT_DIR` (default: `./output`)

### Output Organization
Tools generate structured output:
```
output/
├── analysis_reports/     # Schema analysis results
├── benchmark_results/    # Performance test data
├── sql_optimizations/    # Generated optimization SQL
└── visualizations/       # ERD diagrams and charts
```

### Key Design Patterns
- All tools inherit from BaseAnalyzer for consistency
- CLI commands map to specific tool classes via the main CLI router
- Database-agnostic SQL generation with PostgreSQL optimizations
- Comprehensive logging and error handling throughout