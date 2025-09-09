#!/usr/bin/env python3
"""
Logs and Artifacts Dashboard Page

Manages and displays log files and system information for monitoring.
"""

import streamlit as st
import os
from datetime import datetime
from sqlalchemy import text # Direct import for testing connection


def render_logs_page():
    """Logs and artifacts management page."""
    st.markdown('<div class="main-header">📜 Logs & Artifacts</div>', unsafe_allow_html=True)
    
    st.subheader("📁 Log Files")
    
    # Check for common log locations
    log_locations = [
        "./logs",
        "./output", 
        ".",
        "../logs"
    ]
    
    log_files = []
    for location in log_locations:
        try:
            if os.path.exists(location):
                for file in os.listdir(location):
                    if file.endswith(('.log', '.txt', '.md', '.json')) and 'log' in file.lower():
                        log_files.append(os.path.join(location, file))
        except:
            continue
    
    if log_files:
        selected_log = st.selectbox("Select log file:", log_files)
        
        if selected_log:
            col1, col2 = st.columns([3, 1])
            
            with col2:
                lines_to_show = st.number_input("Lines to show:", min_value=10, max_value=1000, value=50)
            
            try:
                with open(selected_log, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    if len(lines) > lines_to_show:
                        lines = lines[-lines_to_show:]  # Show last N lines
                    
                    content = ''.join(lines)
                    st.code(content, language='text')
            except Exception as e:
                st.error(f"Unable to read log file: {str(e)}")
    else:
        st.info("No log files found in common locations.")
    
    # System information
    st.subheader("🖥️ System Information")
    
    system_info = {
        "Python Version": f"{os.sys.version}",
        "Current Directory": os.getcwd(),
        "Database Host": os.getenv('DB_HOST', 'Not configured'),
        "Dashboard Version": os.getenv('DASHBOARD_VERSION', '1.0.0'),
        "Last Restart": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    for key, value in system_info.items():
        st.text(f"{key}: {value}")
    
    # Database connection test
    st.subheader("🔌 Connection Test")
    
    if st.button("Test Database Connection"):
        st.error("Cannot test database connection directly from logs.py. Please use the relevant Dashboard pages.") # Placeholder for refactoring to use db_service