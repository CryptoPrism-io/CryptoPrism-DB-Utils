#!/usr/bin/env python3
"""
CryptoPrism Dashboard Setup Script
Automates the 5-step setup process for the Streamlit monitoring dashboard.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_requirements():
    """Check if all required packages are installed."""
    logger.info("Checking Python package requirements...")
    
    required_packages = [
        'streamlit', 'pandas', 'plotly', 'sqlalchemy', 
        'psycopg2', 'python-dotenv', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Installing missing packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        logger.info("Packages installed successfully!")
    else:
        logger.info("All required packages are installed ✅")

def check_environment():
    """Check and validate environment variables."""
    logger.info("Checking environment configuration...")
    
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = []
    
    # Load from .env file if exists
    env_file = Path('.env')
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Loaded environment from .env file")
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        
        if not env_file.exists():
            logger.info("Creating .env file template...")
            create_env_template()
        
        logger.error("Please configure database credentials in .env file before continuing.")
        return False
    
    logger.info("Environment configuration is valid ✅")
    return True

def create_env_template():
    """Create .env template file."""
    template = """# CryptoPrism Dashboard Configuration
# Database connection details
DB_HOST=localhost
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
DB_PORT=5432
DB_NAME=dbcp

# Dashboard authentication
DASHBOARD_PASSWORD=admin123

# Optional: Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional: Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_email_password
"""
    
    with open('.env', 'w') as f:
        f.write(template)
    
    logger.info("Created .env template file. Please configure with your database details.")

def test_database_connection():
    """Test database connection."""
    logger.info("Testing database connection...")
    
    try:
        db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME')
        }
        
        conn_string = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        engine = create_engine(conn_string)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"Database connection successful ✅")
            logger.info(f"PostgreSQL version: {version}")
        
        return engine
    
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        logger.error("Please check your database credentials in .env file")
        return None

def setup_database_tables(engine):
    """Setup ETL tracking tables."""
    logger.info("Setting up ETL tracking tables...")
    
    try:
        setup_file = Path('etl_tracking_setup.sql')
        
        if not setup_file.exists():
            logger.error("etl_tracking_setup.sql not found!")
            return False
        
        with open(setup_file, 'r') as f:
            sql_commands = f.read()
        
        with engine.connect() as conn:
            # Execute the SQL setup script
            conn.execute(text(sql_commands))
            conn.commit()
        
        logger.info("Database tables setup completed ✅")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False

def verify_setup(engine):
    """Verify that tables were created successfully."""
    logger.info("Verifying database setup...")
    
    try:
        with engine.connect() as conn:
            # Check if tables exist
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('etl_runs', 'etl_job_stats', 'data_quality_checks')
            """
            
            result = conn.execute(text(tables_query))
            tables = [row[0] for row in result]
            
            expected_tables = ['etl_runs', 'etl_job_stats', 'data_quality_checks']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                logger.error(f"Missing tables: {', '.join(missing_tables)}")
                return False
            
            # Test ETL tracking functions
            test_query = "SELECT log_etl_start('setup_test')"
            run_id = conn.execute(text(test_query)).scalar()
            
            complete_query = "SELECT log_etl_complete(:run_id, 'success', 0, 0, NULL)"
            conn.execute(text(complete_query), {'run_id': run_id})
            
            conn.commit()
        
        logger.info("Database verification completed ✅")
        return True
        
    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}")
        return False

def launch_dashboard():
    """Launch the Streamlit dashboard."""
    logger.info("Starting Streamlit dashboard...")
    
    try:
        dashboard_file = Path('streamlit_app.py')
        
        if not dashboard_file.exists():
            logger.error("streamlit_app.py not found!")
            return False
        
        logger.info("🚀 Starting dashboard at http://localhost:8501")
        logger.info("Use Ctrl+C to stop the dashboard")
        logger.info(f"Login password: {os.getenv('DASHBOARD_PASSWORD', 'admin123')}")
        
        # Start Streamlit
        subprocess.run([
            'streamlit', 'run', 'streamlit_app.py',
            '--server.port=8501',
            '--server.address=0.0.0.0',
            '--server.headless=false'
        ])
        
        return True
        
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
        return True
    except Exception as e:
        logger.error(f"Failed to start dashboard: {str(e)}")
        return False

def main():
    """Main setup function."""
    print("🚀 CryptoPrism Dashboard Setup")
    print("=" * 50)
    
    # Step 1: Check requirements
    try:
        check_requirements()
    except Exception as e:
        logger.error(f"Requirements check failed: {str(e)}")
        sys.exit(1)
    
    # Step 2: Check environment
    if not check_environment():
        logger.error("Environment setup required. Please configure .env file and run again.")
        sys.exit(1)
    
    # Step 3: Test database connection
    engine = test_database_connection()
    if not engine:
        sys.exit(1)
    
    # Step 4: Setup database tables
    if not setup_database_tables(engine):
        sys.exit(1)
    
    # Step 5: Verify setup
    if not verify_setup(engine):
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("=" * 50)
    
    # Launch dashboard
    launch_dashboard()

if __name__ == "__main__":
    main()